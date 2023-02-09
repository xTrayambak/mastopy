import keyring
import keyring.errors


def set(key: str, value: str):
    keyring.set_password("system", key, value)


def get(key: str):
    try:
        return keyring.get_password("system", key)
    except keyring.errors.InitError:
        return None
