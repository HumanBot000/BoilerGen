from . import auth_bp
from .decorator import authenticated


@auth_bp.route("/test", methods=["POST"])
@authenticated
def test_token():
    # If there is an error, it will be caught by the decorator
    return {"success": True, "message": "Token is valid"}, 200
