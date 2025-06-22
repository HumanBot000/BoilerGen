from flask import request
from . import auth_bp
import modules.auth.register
import modules.auth.retrieve_jwt
import modules.exceptions


@auth_bp.route("/refresh", methods=["POST"])
def refresh_jwt():
    token = request.json.get("refresh_token")
    try:
        session = modules.auth.retrieve_jwt.refresh_session(token)
    except modules.exceptions.AuthException as e:
        return {"success": False, "message": str(e)}, 400
    return {"success": True, "message": "Refreshed", "jwt": session.access_token, "refresh_token": session.refresh_token}, 200
