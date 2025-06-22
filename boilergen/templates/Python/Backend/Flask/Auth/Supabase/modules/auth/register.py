import supabase
import modules.exceptions
from . import client

def create_user(email:str,password:str,username:str):
    try:
        user = client.auth.sign_up({
            "email": email,
            "password": password,
            "username": username
        })
    except supabase.AuthError as e:
        if e.message == "User already exists":
            raise modules.exceptions.UserAlreadyExistsException()
        raise modules.exceptions.AuthException(e.message)

    return user.user

