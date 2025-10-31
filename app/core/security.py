#потом

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return True


def get_password_hash(password: str) -> str:
    return password


def create_access_token(data: dict) -> str:
    return f"fake-token-{data.get('username', 'user')}"


def verify_token(token: str) -> dict:
    return {"username": "user", "is_superuser": False}


def get_current_user():
    return {"username": "user", "is_superuser": False}