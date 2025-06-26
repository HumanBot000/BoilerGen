from flask import request
from . import auth_bp
import modules.auth.register
import modules.auth.retrieve_jwt
import modules.exceptions


@auth_bp.route("/register", methods=["POST"])
def register_user():
    email = request.json.get("email")
    password = request.json.get("password")
    username = request.json.get("username")
    try:
        modules.auth.register.create_user(email, password, username)
    except modules.exceptions.UserAlreadyExistsException:
        return {"success": False, "message": "User already exists"}, 409
    except modules.exceptions.EmailNotVerifiedException as e:
        return {"success": False, "message": str(e)}, 400
    except modules.exceptions.AuthException as e:
        return {"success": False, "message": str(e)}, 400
    return {"success": True, "message": "User created", "note": "Verify email, then use login endpoint!"}, 201
