import argparse
import http

import flask


def main() -> None:
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
    flask_application.add_url_rule("/Html", methods = [ "GET" ], view_func = html_reponse)
    flask_application.add_url_rule("/HtmlNotFound", methods = [ "GET" ], view_func = html_reponse_notfound)
    flask_application.add_url_rule("/Json", methods = [ "GET" ], view_func = json_response)
    flask_application.add_url_rule("/JsonNotFound", methods = [ "GET" ], view_func = json_reponse_notfound)


def home() -> flask.Response:
    return flask.Response()


def html_reponse() -> flask.Response:
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


def html_reponse_notfound() -> flask.Response:
    return flask.Response(status = http.HTTPStatus.NOT_FOUND, mimetype = "text/html")


def json_response() -> flask.Response:
    json_as_text = """
{
    "key": "value"
}
"""

    return flask.Response(json_as_text.strip(), mimetype = "application/json")


def json_reponse_notfound() -> flask.Response:
    return flask.Response(status = http.HTTPStatus.NOT_FOUND, mimetype = "application/json")


if __name__ == "__main__":
    main()
