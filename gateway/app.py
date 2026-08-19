from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

AUTH_URL = 'http://auth:5001'
PRODUCT_URL = 'http://product:5002'
ORDER_URL = 'http://order:5003'
CART_URL = 'http://cart:5004'

@app.route('/products', methods=['GET', 'POST'])
def products():
    if request.method == 'POST':
        resp = requests.post(f'{PRODUCT_URL}/products', json=request.get_json() or {}, timeout=10)
    else:
        resp = requests.get(f'{PRODUCT_URL}/products', timeout=10)
    return jsonify(resp.json()), resp.status_code

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    resp = requests.post(f'{AUTH_URL}/login', json=data, timeout=10)
    return jsonify(resp.json()), resp.status_code

@app.route('/cart/<user>')
def get_cart(user):
    resp = requests.get(f'{CART_URL}/cart/{user}', timeout=10)
    return jsonify(resp.json()), resp.status_code

@app.route('/cart/<user>/add', methods=['POST'])
def add_cart(user):
    data = request.get_json() or {}
    resp = requests.post(f'{CART_URL}/cart/{user}/add', json=data, timeout=10)
    return jsonify(resp.json()), resp.status_code

@app.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json() or {}
    resp = requests.post(f'{ORDER_URL}/orders', json=data, timeout=10)
    return jsonify(resp.json()), resp.status_code

@app.route('/orders')
def list_orders():
    user = request.args.get('user')
    resp = requests.get(f'{ORDER_URL}/orders', params={'user': user}, timeout=10)
    return jsonify(resp.json()), resp.status_code

@app.route('/health')
def health():
    return jsonify({'service': 'gateway', 'status': 'ok'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
