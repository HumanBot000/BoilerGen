import gotrue
import gotrue.errors

from data.modules.exceptions.AuthExceptions import *
from . import client


def create_session(email: str, password: str) -> gotrue.Session:
    try:
        response = client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
    except gotrue.errors.AuthApiError as e:
        if e.message == "Email not confirmed":
            raise EmailNotVerifiedException
        if e.message == "Invalid login credentials":
            raise InvalidCredentialsException
        raise AuthException(str(e))
    except Exception as e:
        raise AuthException(str(e))

    return response.session

def refresh_session(refresh_token: str) -> gotrue.Session:
    try:
        response = client.auth.refresh_session(refresh_token)
    except Exception as e:
        raise AuthException("The provided refresh token is invalid")
    return response.session