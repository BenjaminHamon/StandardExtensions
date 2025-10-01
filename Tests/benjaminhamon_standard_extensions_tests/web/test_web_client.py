""" Unit tests for WebServiceClient """

import logging
import os

import pytest
import pytest_asyncio
import requests

from benjaminhamon_standard_extensions.web.form_data import FormData
from benjaminhamon_standard_extensions.web.form_data_field import FormDataField
from benjaminhamon_standard_extensions.web.web_client import WebClient
from benjaminhamon_standard_extensions.web.web_content_exception import WebContentException
from benjaminhamon_standard_extensions.web.web_request_exception import WebRequestException
from benjaminhamon_standard_extensions.web.web_status_exception import WebStatusException

from .website_runner import WebsiteRunner


@pytest_asyncio.fixture(name = "website", scope = "module", loop_scope = "module")
async def website_fixture():
    script_path = os.path.join(os.path.dirname(__file__), "dummy_website.py")
    address = "localhost"
    port = 4999

    async with WebsiteRunner(script_path, address, port) as website:
        yield website.get_url()


def test_send_request_with_simulate():
    logger = logging.getLogger("Tests")

    with requests.Session() as session:
        web_client = WebClient(logger, session)

        response = web_client.send_request("GET", "http://localhost:4998/", simulate = True)

        assert response is not None
        assert response.status_code == 200
        assert response.data is None
        assert isinstance(response.underlying_object, requests.Response)


def test_send_request_connection_error():
    logger = logging.getLogger("Tests")

    with requests.Session() as session:
        web_client = WebClient(logger, session)

        with pytest.raises(WebRequestException) as exception_info:
            web_client.send_request("GET", "http://localhost:4998/")

        assert isinstance(exception_info.value.__cause__, requests.RequestException)
        assert exception_info.value.status_code is None
        assert exception_info.value.response is None


def test_send_request_with_html(website):
    logger = logging.getLogger("Tests")

    with requests.Session() as session:
        web_client = WebClient(logger, session)

        response = web_client.send_request("GET", website + "/")

        assert response is not None
        assert response.status_code == 200
        assert response.data is not None
        assert isinstance(response.data, str)
        assert isinstance(response.underlying_object, requests.Response)


def test_send_request_with_binary(website):
    logger = logging.getLogger("Tests")

    with requests.Session() as session:
        web_client = WebClient(logger, session)

        response = web_client.send_request("GET", website + "/Binary")

        assert response is not None
        assert response.status_code == 200
        assert response.data is not None
        assert isinstance(response.data, bytes)
        assert isinstance(response.underlying_object, requests.Response)


def test_send_request_with_form(website):
    logger = logging.getLogger("Tests")

    with requests.Session() as session:
        web_client = WebClient(logger, session)

        response = web_client.send_request("POST", website + "/Form",
                data_as_form = FormData([ FormDataField("key", "value") ]))

        assert response is not None
        assert response.status_code == 200
        assert response.data is not None
        assert isinstance(response.data, str)
        assert isinstance(response.underlying_object, requests.Response)


def test_send_request_with_form_and_file(tmpdir, website):
    logger = logging.getLogger("Tests")

    with requests.Session() as session:
        web_client = WebClient(logger, session)

        local_file_path = os.path.join(tmpdir, "Working", "ToUpload.txt")

        os.makedirs(os.path.dirname(local_file_path))
        with open(local_file_path, mode = "w", encoding = "utf-8") as local_file:
            local_file.write("Okay")

        with open(local_file_path, mode = "r", encoding = "utf-8") as local_file:
            response = web_client.send_request("POST", website + "/FormWithFile",
                    data_as_form = FormData([ FormDataField("file", local_file, "Uploaded.txt") ]))

        assert response is not None
        assert response.status_code == 200
        assert response.data is not None
        assert isinstance(response.data, str)
        assert isinstance(response.underlying_object, requests.Response)


def test_send_request_with_unexpected_content_type(website):
    logger = logging.getLogger("Tests")

    with requests.Session() as session:
        web_client = WebClient(logger, session)

        with pytest.raises(WebContentException) as exception_info:
            web_client.send_request("GET", website + "/", extra_headers = { "Accept": "application/json" })

        assert isinstance(exception_info.value.__cause__, TypeError)

        response = exception_info.value.response

        assert response is not None
        assert response.status_code == 200
        assert response.data is None
        assert isinstance(response.underlying_object, requests.Response)


def test_send_request_not_found(website):
    logger = logging.getLogger("Tests")

    with requests.Session() as session:
        web_client = WebClient(logger, session)

        with pytest.raises(WebStatusException) as exception_info:
            web_client.send_request("GET", website + "/NotFound")

        assert isinstance(exception_info.value.__cause__, requests.HTTPError)

        response = exception_info.value.response

        assert response is not None
        assert response.status_code == 404
        assert response.data is None
        assert isinstance(response.underlying_object, requests.Response)


def test_upload(tmpdir, website):
    logger = logging.getLogger("Tests")

    with requests.Session() as session:
        web_client = WebClient(logger, session)

        local_file_path = os.path.join(tmpdir, "Working", "ToUpload.txt")

        os.makedirs(os.path.dirname(local_file_path))
        with open(local_file_path, mode = "w", encoding = "utf-8") as local_file:
            local_file.write("Okay")

        response = web_client.upload("POST", website + "/Upload", local_file_path)

        assert response is not None
        assert response.status_code == 200
        assert response.data is not None
        assert isinstance(response.data, str)
        assert isinstance(response.underlying_object, requests.Response)


def test_download(tmpdir, website):
    logger = logging.getLogger("Tests")

    with requests.Session() as session:
        web_client = WebClient(logger, session)

        local_file_path = os.path.join(tmpdir, "Working", "Downloaded.txt")

        os.makedirs(os.path.dirname(local_file_path))
        response = web_client.download(website + "/Download", local_file_path)

        assert response is not None
        assert response.status_code == 200
        assert response.data is None
        assert isinstance(response.underlying_object, requests.Response)

        assert os.path.exists(local_file_path)
        with open(local_file_path, mode = "r", encoding = "utf-8") as local_file:
            assert local_file.read() == "Okay"
