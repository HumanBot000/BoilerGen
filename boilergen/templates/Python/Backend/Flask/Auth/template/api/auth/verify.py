from flask import request
from . import auth_bp
import modules.auth.retrieve_jwt
import modules.exceptions
from .decorator import authenticated


@auth_bp.route("/test", methods=["POST"])
@authenticated
def test_token():
    # If there is an error, it will be caught by the decorator
    return {"success": True, "message": "Token is valid"}, 200