import argparse
import http
import logging
import sys
from typing import Any

import flask

from benjaminhamon_standard_extensions.serialization.json_serializer import JsonSerializer


serializer = JsonSerializer()


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
    flask_application.add_url_rule("/Resource", methods = [ "GET" ], view_func = get_resource)
    flask_application.add_url_rule("/Resource", methods = [ "POST" ], view_func = post_resource)
    flask_application.add_url_rule("/Nothing", methods = [ "GET" ], view_func = nothing)
    flask_application.add_url_rule("/BadContentType", methods = [ "GET" ], view_func = bad_content_type)
    flask_application.add_url_rule("/NotFound", methods = [ "GET" ], view_func = not_found)


def home() -> flask.Response:
    return flask.Response()


def get_resource() -> flask.Response:
    try:
        assert dict(flask.request.args) == { "key": "value" }
    except Exception: # pylint: disable = broad-exception-caught
        logging.error("Exception", exc_info = True)
        return create_response({ "status": "error" }, http.HTTPStatus.BAD_REQUEST)

    return create_response({ "key": "value" }, http.HTTPStatus.OK)


def post_resource() -> flask.Response:
    try:
        assert serializer.deserialize_from_string(flask.request.get_data(as_text = True), dict) == { "key": "value" }
    except Exception: # pylint: disable = broad-exception-caught
        logging.error("Exception", exc_info = True)
        return create_response({ "status": "error" }, http.HTTPStatus.BAD_REQUEST)

    return create_response({ "status": "okay" }, http.HTTPStatus.OK)


def nothing() -> flask.Response:
    return flask.Response(mimetype = serializer.get_content_type())


def bad_content_type() -> flask.Response:
    data = { "key": "value" }
    serialized_data = serializer.serialize_to_string(data)
    return flask.Response(serialized_data, mimetype = "application/octet-stream")


def not_found() -> flask.Response:
    return create_response({ "status": "error" }, http.HTTPStatus.NOT_FOUND)


def create_response(data: Any, status: http.HTTPStatus) -> flask.Response:
    serialized_data = serializer.serialize_to_string(data)
    return flask.Response(serialized_data, status = status, mimetype = serializer.get_content_type())


if __name__ == "__main__":
    main()
