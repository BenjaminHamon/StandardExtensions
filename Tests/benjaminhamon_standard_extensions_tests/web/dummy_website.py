# cspell:words booleaness

import argparse
import base64
import http
import logging
import sys

import flask


def main() -> None:
    logging.basicConfig(stream = sys.stdout, level = logging.DEBUG)
    argument_parser = create_argument_parser()
    arguments = argument_parser.parse_args()
    run_website(arguments.address, arguments.port)


def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", required = True, help = "set the address for the server to listen to")
    parser.add_argument("--port", required = True, type = int, help = "set the port for the server to listen to")
    return parser


def run_website(address: str, port: int) -> None:
    flask_application = create_application()
    flask_application.run(host = address, port = port, debug = False)


def create_application() -> flask.Flask:
    flask_application = flask.Flask(__file__)
    register_routes(flask_application)
    return flask_application


def register_routes(flask_application: flask.Flask) -> None:
    flask_application.add_url_rule("/", methods = [ "GET" ], view_func = home)
    flask_application.add_url_rule("/Binary", methods = [ "GET" ], view_func = binary)
    flask_application.add_url_rule("/Form", methods = [ "POST" ], view_func = form)
    flask_application.add_url_rule("/FormWithFile", methods = [ "POST" ], view_func = form_with_file)
    flask_application.add_url_rule("/NotFound", methods = [ "GET" ], view_func = not_found)
    flask_application.add_url_rule("/Upload", methods = [ "POST" ], view_func = upload)
    flask_application.add_url_rule("/Download", methods = [ "GET" ], view_func = download)


def home() -> flask.Response:
    html_as_text = """
<!doctype html>
<html>

    <head>
        <title>Dummy website for tests</title>
    </head>

    <body>
        <main>
            <p>Hello world</p>
        </main>
    </body>

</html>
"""

    return flask.Response(html_as_text.strip(), mimetype = "text/html")


def binary() -> flask.Response:
    return flask.Response(base64.b64encode(b"Okay"), mimetype = "application/octet-stream")


def form() -> flask.Response:
    try:
        assert dict(flask.request.form) == { "key": "value" }
    except Exception: # pylint: disable = broad-exception-caught
        logging.error("Exception", exc_info = True)
        return flask.Response(status = http.HTTPStatus.BAD_REQUEST)

    return flask.Response("", mimetype = "text/html")


def form_with_file() -> flask.Response:
    try:
        assert dict(flask.request.form) == {} # pylint: disable = use-implicit-booleaness-not-comparison
        assert list(flask.request.files.keys()) == [ "file" ]
        assert flask.request.files["file"].filename == "Uploaded.txt"
        assert flask.request.files["file"].stream.read() == b"Okay"
    except Exception: # pylint: disable = broad-exception-caught
        logging.error("Exception", exc_info = True)
        return flask.Response(status = http.HTTPStatus.BAD_REQUEST)

    return flask.Response("", mimetype = "text/html")


def not_found() -> flask.Response:
    return flask.Response(status = http.HTTPStatus.NOT_FOUND)


def upload() -> flask.Response:
    try:
        assert flask.request.stream.read() == b"Okay"
    except Exception: # pylint: disable = broad-exception-caught
        logging.error("Exception", exc_info = True)
        return flask.Response(status = http.HTTPStatus.BAD_REQUEST)

    return flask.Response("", mimetype = "text/html")


def download() -> flask.Response:
    return flask.Response("Okay", mimetype = "text/plain")


if __name__ == "__main__":
    main()
