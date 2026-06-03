""" Unit tests for WebServiceClient """

import logging
import os
import sys
from pathlib import Path
from typing import AsyncGenerator

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
async def website_fixture() -> AsyncGenerator[WebsiteRunner, None]:
    python_executable = sys.executable
    script_path = os.path.join(os.path.dirname(__file__), "dummy_website.py")
    address = "localhost"
    port = 4999

    command = [ python_executable, script_path, "--address", address, "--port", str(port) ]

    async with WebsiteRunner(command, address, port) as website_runner:
        yield website_runner


def test_send_request_with_simulate() -> None:
    logger = logging.getLogger("Tests")
    web_client = WebClient(logger)

    with requests.Session() as session:
        response = web_client.send_request(session, "GET", "http://localhost:4998/", simulate = True)

    assert response is not None
    assert response.status_code == 200
    assert response.data is None
    assert isinstance(response.underlying_object, requests.Response)


def test_send_request_connection_error() -> None:
    logger = logging.getLogger("Tests")
    web_client = WebClient(logger)

    with requests.Session() as session:
        with pytest.raises(WebRequestException) as exception_info:
            web_client.send_request(session, "GET", "http://localhost:4998/")

    assert isinstance(exception_info.value.__cause__, requests.RequestException)
    assert exception_info.value.status_code is None
    assert exception_info.value.response is None


def test_send_request_with_html(website: WebsiteRunner) -> None:
    logger = logging.getLogger("Tests")
    web_client = WebClient(logger)

    with requests.Session() as session:
        response = web_client.send_request(session, "GET", website.get_url() + "/")

    assert response is not None
    assert response.status_code == 200
    assert response.data is not None
    assert isinstance(response.data, str)
    assert isinstance(response.underlying_object, requests.Response)


def test_send_request_with_binary(website: WebsiteRunner) -> None:
    logger = logging.getLogger("Tests")
    web_client = WebClient(logger)

    with requests.Session() as session:
        response = web_client.send_request(session, "GET", website.get_url() + "/Binary")

    assert response is not None
    assert response.status_code == 200
    assert response.data is not None
    assert isinstance(response.data, bytes)
    assert isinstance(response.underlying_object, requests.Response)


def test_send_request_with_form(website: WebsiteRunner) -> None:
    logger = logging.getLogger("Tests")
    web_client = WebClient(logger)

    with requests.Session() as session:
        response = web_client.send_request(session, "POST", website.get_url() + "/Form",
                data_as_form = FormData([ FormDataField("key", "value") ]))

    assert response is not None
    assert response.status_code == 200
    assert response.data is not None
    assert isinstance(response.data, str)
    assert isinstance(response.underlying_object, requests.Response)


def test_send_request_with_form_and_file(tmp_path: Path, website: WebsiteRunner) -> None:
    logger = logging.getLogger("Tests")
    web_client = WebClient(logger)
    local_file_path = tmp_path / "Working" / "ToUpload.txt"

    os.makedirs(local_file_path.parent)
    with open(local_file_path, mode = "w", encoding = "utf-8") as local_file:
        local_file.write("Okay")

    with requests.Session() as session:
        with open(local_file_path, mode = "r", encoding = "utf-8") as local_file:
            response = web_client.send_request(session, "POST", website.get_url() + "/FormWithFile",
                    data_as_form = FormData([ FormDataField("file", local_file, "Uploaded.txt") ]))

    assert response is not None
    assert response.status_code == 200
    assert response.data is not None
    assert isinstance(response.data, str)
    assert isinstance(response.underlying_object, requests.Response)


def test_send_request_with_unexpected_content_type(website: WebsiteRunner) -> None:
    logger = logging.getLogger("Tests")
    web_client = WebClient(logger)

    with requests.Session() as session:
        with pytest.raises(WebContentException) as exception_info:
            web_client.send_request(session, "GET", website.get_url() + "/", extra_headers = { "Accept": "application/json" })

    assert isinstance(exception_info.value.__cause__, TypeError)

    response = exception_info.value.response

    assert response is not None
    assert response.status_code == 200
    assert response.data is None
    assert isinstance(response.underlying_object, requests.Response)


def test_send_request_not_found(website: WebsiteRunner) -> None:
    logger = logging.getLogger("Tests")
    web_client = WebClient(logger)

    with requests.Session() as session:
        with pytest.raises(WebStatusException) as exception_info:
            web_client.send_request(session, "GET", website.get_url() + "/NotFound")

    assert isinstance(exception_info.value.__cause__, requests.HTTPError)

    response = exception_info.value.response

    assert response is not None
    assert response.status_code == 404
    assert response.data is None
    assert isinstance(response.underlying_object, requests.Response)


def test_upload(tmp_path: Path, website: WebsiteRunner) -> None:
    logger = logging.getLogger("Tests")
    web_client = WebClient(logger)
    local_file_path = tmp_path / "Working" / "ToUpload.txt"

    os.makedirs(local_file_path.parent)
    with open(local_file_path, mode = "w", encoding = "utf-8") as local_file:
        local_file.write("Okay")

    with requests.Session() as session:
        response = web_client.upload(session, "POST", website.get_url() + "/Upload", str(local_file_path))

    assert response is not None
    assert response.status_code == 200
    assert response.data is not None
    assert isinstance(response.data, str)
    assert isinstance(response.underlying_object, requests.Response)


def test_download(tmp_path: Path, website: WebsiteRunner) -> None:
    logger = logging.getLogger("Tests")
    web_client = WebClient(logger)
    local_file_path = tmp_path / "Working" / "Downloaded.txt"

    os.makedirs(local_file_path.parent)

    with requests.Session() as session:
        response = web_client.download(session, website.get_url() + "/Download", str(local_file_path))

    assert response is not None
    assert response.status_code == 200
    assert response.data is None
    assert isinstance(response.underlying_object, requests.Response)

    assert os.path.exists(local_file_path)
    with open(local_file_path, mode = "r", encoding = "utf-8") as local_file:
        assert local_file.read() == "Okay"
