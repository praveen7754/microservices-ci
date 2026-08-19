from flask import Flask, request, jsonify

app = Flask(__name__)
USERS = {'alice': 'password123'}
TOKENS = {}

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    if username in USERS and USERS[username] == password:
        token = f"token-{username}"
        TOKENS[token] = username
        return jsonify({'token': token, 'user': username})
    return jsonify({'error': 'invalid credentials'}), 401

@app.route('/verify', methods=['POST'])
def verify():
    data = request.get_json() or {}
    token = data.get('token')
    user = TOKENS.get(token)
    if user:
        return jsonify({'user': user})
    return jsonify({'error': 'invalid token'}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
