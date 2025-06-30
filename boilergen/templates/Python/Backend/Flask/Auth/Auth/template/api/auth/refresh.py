from flask import request

from data.modules.exceptions.AuthExceptions import AuthException
from data.modules.auth.retrieve_jwt import refresh_session
from . import auth_bp


@auth_bp.route("/refresh", methods=["POST"])
def refresh_jwt():
    token = request.json.get("refresh_token")
    try:
        session = refresh_session(token)
    except AuthException as e:
        return {"success": False, "message": str(e)}, 400
    return {"success": True, "message": "Refreshed", "jwt": session.access_token, "refresh_token": session.refresh_token}, 200