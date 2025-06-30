from flask import request

import data.modules.auth.verification
from data.modules.exceptions.AuthExceptions import *
from . import auth_bp


@auth_bp.route("/resend", methods=["POST"])
def resend_email():
    email = request.json.get("email")
    try:
        data.modules.auth.verification.resend_email(email)
    except AuthException as e:
        return {"success": False, "message": str(e)}, 400
    return {"success": True, "message": "Email sent"}, 200