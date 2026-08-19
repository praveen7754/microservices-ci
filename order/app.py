from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)
ORDERS = []
NEXT_ID = 1

@app.route('/orders', methods=['POST'])
def create_order():
    global NEXT_ID
    data = request.get_json() or {}
    user = data.get('user')
    items = data.get('items', [])
    order = {
        'id': NEXT_ID,
        'user': user,
        'items': items,
        'created_at': datetime.utcnow().isoformat() + 'Z'
    }
    NEXT_ID += 1
    ORDERS.append(order)
    return jsonify(order), 201

@app.route('/orders')
def list_orders():
    user = request.args.get('user')
    if user:
        filtered = [o for o in ORDERS if o['user'] == user]
        return jsonify(filtered)
    return jsonify(ORDERS)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)
