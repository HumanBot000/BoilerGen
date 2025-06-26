# The email sending is done by supabase
import supabase
import modules.exceptions
from . import client

def user_is_verified(jwt: str) -> bool:
    try:
        user = client.auth.get_user(jwt)
    except supabase.AuthError as e:
        raise modules.exceptions.AuthException(e.message)
    return user.user.user_metadata["email_verified"]

def resend_email(email: str) -> None:
    try:
        client.auth.resend(
            {
                "type": "signup",
                "email": email,
            }
        )
    except supabase.AuthError as e:
        raise modules.exceptions.AuthException(e.message)