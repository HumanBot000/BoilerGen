from flask import request
from . import auth_bp
import modules.auth.retrieve_jwt
import modules.exceptions


@auth_bp.route("/login", methods=["POST"])
def login():
    email = request.json.get("email")
    password = request.json.get("password")
    try:
        session = modules.auth.retrieve_jwt.create_session(email, password)
    except modules.exceptions.InvalidCredentialsException as e:
        return {"success": False, "message": "Invalid credentials"}, 401
    except modules.exceptions.EmailNotVerifiedException:
        return {"success": False, "message": "This account exists, but is not verified"}, 400
    except modules.exceptions.AuthException as e:
        return {"success": False, "message": str(e)}, 401
    return {"success": True, "message": "Logged in", "jwt": session.access_token, "refresh_token": session.refresh_token}, 200
