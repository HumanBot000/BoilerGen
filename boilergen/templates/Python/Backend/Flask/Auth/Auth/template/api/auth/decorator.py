from functools import wraps
from flask import request, jsonify
import jwt
import os

import data.modules.auth.user

SECRET_KEY = os.getenv("SUPABASE_JWT_SECRET")


# this decorator needs to be under the flask route decorator
def authenticated(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authorization header missing"}), 400

        token = auth_header.split(" ")[1]
        try:
            #decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.user = data.modules.auth.user.fetch_user(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 403
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)

    return decorated_function