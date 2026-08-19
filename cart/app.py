import json
import os

import redis
from flask import Flask, jsonify, request

app = Flask(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://cart-redis:6379/0")
_client = None


def get_redis():
    global _client
    if _client is None:
        _client = redis.Redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
    return _client


def cart_key(user):
    return f"cart:{user}"


def get_items(user):
    try:
        data = get_redis().get(cart_key(user))
        return json.loads(data) if data else []
    except Exception as exc:
        app.logger.warning("Redis unavailable: %s", exc)
        return []


def save_items(user, items):
    get_redis().set(cart_key(user), json.dumps(items))


@app.route('/cart/<user>')
def get_cart(user):
    return jsonify(get_items(user))


@app.route('/cart/<user>/add', methods=['POST'])
def add_to_cart(user):
    data = request.get_json() or {}
    item = data.get('item')
    if not item:
        return jsonify({'error': 'no item provided'}), 400

    items = get_items(user)
    items.append(item)

    try:
        save_items(user, items)
    except Exception as exc:
        app.logger.error("Unable to save cart: %s", exc)
        return jsonify({'error': 'cart storage unavailable'}), 503

    return jsonify({'user': user, 'cart': items})


@app.route('/cart/<user>/clear', methods=['POST'])
def clear_cart(user):
    try:
        save_items(user, [])
    except Exception as exc:
        app.logger.error("Unable to clear cart: %s", exc)
        return jsonify({'error': 'cart storage unavailable'}), 503
    return jsonify({'user': user, 'cart': []})


@app.route('/health')
def health():
    try:
        get_redis().ping()
        return jsonify({'service': 'cart', 'status': 'ok', 'redis': True})
    except Exception:
        return jsonify({'service': 'cart', 'status': 'degraded', 'redis': False}), 503


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004)
