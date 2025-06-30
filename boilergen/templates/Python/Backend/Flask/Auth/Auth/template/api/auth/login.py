from flask import request

from data.modules.exceptions.AuthExceptions import *
from data.modules.auth.retrieve_jwt import create_session
from . import auth_bp


@auth_bp.route("/login", methods=["POST"])
def login():
    email = request.json.get("email")
    password = request.json.get("password")
    try:
        session = create_session(email, password)
    except InvalidCredentialsException as e:
        return {"success": False, "message": "Invalid credentials"}, 401
    except EmailNotVerifiedException:
        return {"success": False, "message": "This account exists, but is not verified"}, 400
    except AuthException as e:
        return {"success": False, "message": str(e)}, 401
    return {"success": True, "message": "Logged in", "jwt": session.access_token, "refresh_token": session.refresh_token}, 200