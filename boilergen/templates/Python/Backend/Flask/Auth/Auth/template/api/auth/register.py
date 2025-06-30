from flask import request

from data.modules.auth.register import create_user
from data.modules.exceptions.AuthExceptions import *
from . import auth_bp


@auth_bp.route("/register", methods=["POST"])
def register_user():
    email = request.json.get("email")
    password = request.json.get("password")
    username = request.json.get("username")
    try:
        create_user(email, password, username)
    except UserAlreadyExistsException:
        return {"success": False, "message": "User already exists"}, 409
    except EmailNotVerifiedException as e:
        return {"success": False, "message": str(e)}, 400
    except AuthException as e:
        return {"success": False, "message": str(e)}, 400
    return {"success": True, "message": "User created", "note": "Verify email, then use login endpoint!"}, 201