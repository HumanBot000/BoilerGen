class AuthException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message


class InvalidCredentialsException(AuthException):
    def __init__(self):
        super().__init__("Invalid credentials")


class EmailNotVerifiedException(AuthException):
    def __init__(self):
        super().__init__("Email not verified")


class UserAlreadyExistsException(AuthException):
    def __init__(self):
        super().__init__("User already exists")