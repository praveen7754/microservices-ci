import json
import os
import threading
import time
from datetime import datetime, timezone

import redis
from flask import Flask, jsonify, request
from kafka import KafkaConsumer, KafkaProducer

app = Flask(__name__)

PRODUCT_FILE = os.getenv("PRODUCT_DATA_FILE", "/data/products.json")
KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "product-kafka:9092").split(",")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "product-ingestion")
KAFKA_GROUP = os.getenv("KAFKA_CONSUMER_GROUP", "product-ingestion-group")
REDIS_URL = os.getenv("REDIS_URL", "redis://product-redis:6379/0")
REDIS_KEY = "products:all"

DEFAULT_PRODUCTS = [
    {"id": 1, "name": "T-Shirt", "price": 19.99},
    {"id": 2, "name": "Mug", "price": 9.99},
    {"id": 3, "name": "Sticker", "price": 2.99},
]

_file_lock = threading.Lock()
_producer = None
_redis_client = None


def load_products():
    os.makedirs(os.path.dirname(PRODUCT_FILE), exist_ok=True)
    with _file_lock:
        if not os.path.exists(PRODUCT_FILE):
            save_products(DEFAULT_PRODUCTS)
        with open(PRODUCT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)


def save_products(products):
    os.makedirs(os.path.dirname(PRODUCT_FILE), exist_ok=True)
    temp_file = PRODUCT_FILE + ".tmp"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(products, f)
    os.replace(temp_file, PRODUCT_FILE)


def get_redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
    return _redis_client


def get_producer():
    global _producer
    if _producer is None:
        _producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKERS,
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
            retries=10,
            request_timeout_ms=10000,
            acks="all",
        )
    return _producer


def cache_products(products):
    try:
        get_redis().set(REDIS_KEY, json.dumps(products))
    except Exception as exc:
        app.logger.warning("Redis cache unavailable: %s", exc)


def publish_event(event):
    try:
        get_producer().send(KAFKA_TOPIC, event).get(timeout=10)
        app.logger.info("Published Kafka event: %s", event["event"])
    except Exception as exc:
        app.logger.warning("Kafka unavailable; event was not published: %s", exc)


def consume_events():
    while True:
        try:
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_BROKERS,
                group_id=KAFKA_GROUP,
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                value_deserializer=lambda value: json.loads(value.decode("utf-8")),
                request_timeout_ms=15000,
                session_timeout_ms=10000,
            )
            app.logger.info(
                "Kafka consumer connected: brokers=%s topic=%s group=%s",
                KAFKA_BROKERS,
                KAFKA_TOPIC,
                KAFKA_GROUP,
            )
            for message in consumer:
                event = message.value
                if event.get("event") == "product.created":
                    products = load_products()
                    cache_products(products)
                    app.logger.info("Consumed product.created event for product_id=%s",
                                    event.get("product", {}).get("id"))
        except Exception as exc:
            app.logger.warning("Kafka consumer unavailable: %s", exc)
            time.sleep(5)


@app.route("/products", methods=["GET"])
def list_products():
    try:
        cached = get_redis().get(REDIS_KEY)
        if cached:
            return jsonify(json.loads(cached))
    except Exception as exc:
        app.logger.warning("Redis read unavailable: %s", exc)

    products = load_products()
    cache_products(products)
    return jsonify(products)


@app.route("/products", methods=["POST"])
def create_product():
    data = request.get_json() or {}
    if not data.get("name") or data.get("price") is None:
        return jsonify({"error": "name and price are required"}), 400

    products = load_products()
    with _file_lock:
        next_id = max((p["id"] for p in products), default=0) + 1
        product = {
            "id": next_id,
            "name": data["name"],
            "price": float(data["price"]),
        }
        products.append(product)
        save_products(products)

    cache_products(products)

    event = {
        "event": "product.created",
        "event_id": f"product-{product['id']}-{int(time.time() * 1000)}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "product": product,
    }
    publish_event(event)

    return jsonify(product), 201


@app.route("/products/<int:pid>")
def get_product(pid):
    for product in load_products():
        if product["id"] == pid:
            return jsonify(product)
    return jsonify({"error": "not found"}), 404


@app.route("/health")
def health():
    result = {"service": "product", "status": "ok", "kafka": False, "redis": False}

    try:
        get_redis().ping()
        result["redis"] = True
    except Exception:
        pass

    try:
        producer = get_producer()
        producer.bootstrap_connected()
        result["kafka"] = True
    except Exception:
        pass

    return jsonify(result)


if __name__ == "__main__":
    load_products()
    threading.Thread(target=consume_events, daemon=True, name="kafka-consumer").start()
    app.run(host="0.0.0.0", port=5002)
