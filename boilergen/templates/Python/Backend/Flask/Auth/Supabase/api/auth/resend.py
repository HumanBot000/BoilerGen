from flask import request

import modules.auth.register
import modules.auth.verification
import modules.exceptions
from api.api_main import rate_limiter
from . import auth_bp


@auth_bp.route("/resend", methods=["POST"])
@rate_limiter.limit("1/5 minutes")
def resend_email():
    email = request.json.get("email")
    try:
        modules.auth.verification.resend_email(email)
    except modules.exceptions.AuthException as e:
        return {"success": False, "message": str(e)}, 400
    return {"success": True, "message": "Email sent"}, 200
