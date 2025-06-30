import gotrue
import supabase

from data.modules.exceptions.AuthExceptions import *
from .. import auth

def fetch_user(jwt: str) -> gotrue.UserResponse:
    try:
        user = auth.client.auth.get_user(jwt)
    except supabase.AuthError as e:
        raise AuthException(e.message)
    return user