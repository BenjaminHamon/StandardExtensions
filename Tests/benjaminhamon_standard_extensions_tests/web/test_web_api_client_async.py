""" Unit tests for WebServiceClient """

import logging
import os
import sys
from pathlib import Path
from typing import AsyncGenerator

import aiohttp
import pytest
import pytest_asyncio

from benjaminhamon_standard_extensions.serialization.json_serializer import JsonSerializer
from benjaminhamon_standard_extensions.serialization.serialization_exception import SerializationException
from benjaminhamon_standard_extensions.web.form_data import FormData
from benjaminhamon_standard_extensions.web.form_data_field import FormDataField
from benjaminhamon_standard_extensions.web.web_api_client_async import WebApiClientAsync
from benjaminhamon_standard_extensions.web.web_content_exception import WebContentException
from benjaminhamon_standard_extensions.web.web_request_exception import WebRequestException
from benjaminhamon_standard_extensions.web.web_status_exception import WebStatusException

from .website_runner import WebsiteRunner


@pytest_asyncio.fixture(name = "service", scope = "module", loop_scope = "module")
async def service_fixture() -> AsyncGenerator[WebsiteRunner]:
    python_executable = sys.executable
    script_path = os.path.join(os.path.dirname(__file__), "dummy_service.py")
    address = "localhost"
    port = 4999

    command = [ python_executable, script_path, "--address", address, "--port", str(port) ]

    async with WebsiteRunner(command, address, port) as website_runner:
        yield website_runner


@pytest.mark.asyncio
async def test_send_request_with_simulate() -> None:
    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()

    async with aiohttp.ClientSession() as session:
        web_client = WebApiClientAsync(logger, serializer, session)

        response = await web_client.send_request("GET", "http://localhost:4998/", simulate = True)

        assert response is not None
        assert response.status_code == 200
        assert response.data is None
        assert isinstance(response.underlying_object, aiohttp.ClientResponse)


@pytest.mark.asyncio
async def test_send_request_connection_error() -> None:
    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()

    async with aiohttp.ClientSession() as session:
        web_client = WebApiClientAsync(logger, serializer, session)

        with pytest.raises(WebRequestException) as exception_info:
            await web_client.send_request("GET", "http://localhost:4998/")

        assert isinstance(exception_info.value.__cause__, aiohttp.ClientConnectionError)
        assert exception_info.value.status_code is None
        assert exception_info.value.response is None


@pytest.mark.asyncio
async def test_send_request_with_none(service: WebsiteRunner) -> None:
    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()

    async with aiohttp.ClientSession() as session:
        web_client = WebApiClientAsync(logger, serializer, session)

        response = await web_client.send_request("GET", service.get_url() + "/Nothing")

        assert response is not None
        assert response.status_code == 200
        assert response.data is None
        assert isinstance(response.underlying_object, aiohttp.ClientResponse)


@pytest.mark.asyncio
async def test_send_request_with_get(service: WebsiteRunner) -> None:
    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()

    async with aiohttp.ClientSession() as session:
        web_client = WebApiClientAsync(logger, serializer, session)

        response = await web_client.send_request("GET", service.get_url() + "/Resource", parameters = { "key": "value" }, response_success_obj_type = dict)

        assert response is not None
        assert response.status_code == 200
        assert response.data is not None
        assert isinstance(response.data, dict)
        assert isinstance(response.underlying_object, aiohttp.ClientResponse)


@pytest.mark.asyncio
async def test_send_request_with_post(service: WebsiteRunner) -> None:
    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()

    async with aiohttp.ClientSession() as session:
        web_client = WebApiClientAsync(logger, serializer, session)

        response = await web_client.send_request("POST", service.get_url() + "/Resource", data = { "key": "value" }, response_success_obj_type = dict)

        assert response is not None
        assert response.status_code == 200
        assert response.data is not None
        assert isinstance(response.data, dict)
        assert isinstance(response.underlying_object, aiohttp.ClientResponse)


@pytest.mark.asyncio
async def test_send_request_with_unexpected_content_type(service: WebsiteRunner) -> None:
    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()

    async with aiohttp.ClientSession() as session:
        web_client = WebApiClientAsync(logger, serializer, session)

        with pytest.raises(WebContentException) as exception_info:
            await web_client.send_request("GET", service.get_url() + "/BadContentType")

        assert isinstance(exception_info.value.__cause__, TypeError)

        response = exception_info.value.response

        assert response is not None
        assert response.status_code == 200
        assert response.data is None
        assert isinstance(response.underlying_object, aiohttp.ClientResponse)


@pytest.mark.asyncio
async def test_send_request_with_unexpected_obj_type(service: WebsiteRunner) -> None:
    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()

    async with aiohttp.ClientSession() as session:
        web_client = WebApiClientAsync(logger, serializer, session)

        with pytest.raises(WebContentException) as exception_info:
            await web_client.send_request("GET", service.get_url() + "/Resource", parameters = { "key": "value" }, response_success_obj_type = int)

        assert isinstance(exception_info.value.__cause__, SerializationException)

        response = exception_info.value.response

        assert response is not None
        assert response.status_code == 200
        assert response.data is not None
        assert isinstance(response.data, str)
        assert isinstance(response.underlying_object, aiohttp.ClientResponse)


@pytest.mark.asyncio
async def test_send_request_not_found(service: WebsiteRunner) -> None:
    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()

    async with aiohttp.ClientSession() as session:
        web_client = WebApiClientAsync(logger, serializer, session)

        with pytest.raises(WebStatusException) as exception_info:
            await web_client.send_request("GET", service.get_url() + "/NotFound", response_error_obj_type = dict)

        assert isinstance(exception_info.value.__cause__, aiohttp.ClientResponseError)

        response = exception_info.value.response

        assert response is not None
        assert response.status_code == 404
        assert response.data is not None
        assert isinstance(response.data, dict)
        assert isinstance(response.underlying_object, aiohttp.ClientResponse)


@pytest.mark.asyncio
async def test_send_request_with_upload(tmp_path: Path, service: WebsiteRunner) -> None:
    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()

    async with aiohttp.ClientSession() as session:
        web_client = WebApiClientAsync(logger, serializer, session)

        local_file_path = tmp_path / "Working" / "ToUpload.txt"

        os.makedirs(local_file_path.parent)
        with open(local_file_path, mode = "w", encoding = "utf-8") as local_file:
            local_file.write("Okay")

        with open(local_file_path, mode = "r", encoding = "utf-8") as local_file:
            response = await web_client.send_request("POST", service.get_url() + "/Upload",
                    data_as_form = FormData([ FormDataField("file", local_file, "Uploaded.txt") ]), response_success_obj_type = dict)

        assert response is not None
        assert response.status_code == 200
        assert response.data is not None
        assert isinstance(response.data, dict)
        assert isinstance(response.underlying_object, aiohttp.ClientResponse)
