import base64


def get_authentication_for_basic(username: str, password: str, encoding: str = "utf-8") -> str:
    return "Basic" + " " + base64.b64encode(b"%s:%s" % (username.encode(encoding), password.encode(encoding))).decode()


def get_authentication_for_bearer(token: str) -> str:
    return "Bearer" + " " + token
