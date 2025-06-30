import supabase

from data.modules.exceptions.AuthExceptions import *
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
            raise UserAlreadyExistsException()
        raise AuthException(e.message)

    return user.user
