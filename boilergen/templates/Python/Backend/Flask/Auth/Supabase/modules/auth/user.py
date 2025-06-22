import gotrue
import supabase
import modules.exceptions


def fetch_user(jwt: str) -> gotrue.UserResponse:
    try:
        user = modules.auth.client.auth.get_user(jwt)
    except supabase.AuthError as e:
        raise modules.exceptions.AuthException(e.message)
    return user
