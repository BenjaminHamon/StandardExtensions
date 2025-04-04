""" Unit tests for WebServiceClientAsync """

import asyncio
import logging
import os
import subprocess
import sys

import aiohttp
import pytest
import pytest_asyncio
import requests

from benjaminhamon_standard_extensions.serialization.json_serializer import JsonSerializer
from benjaminhamon_standard_extensions.web.web_client_async import WebClientAsync
from benjaminhamon_standard_extensions.web.web_content_exception import WebContentException
from benjaminhamon_standard_extensions.web.web_request_exception import WebRequestException
from benjaminhamon_standard_extensions.web.web_status_exception import WebStatusException


@pytest_asyncio.fixture(name = "website", scope = "module", loop_scope = "module")
async def website_fixture():
    timeout_seconds = 5

    script_path = os.path.join(os.path.dirname(__file__), "dummy_website.py")
    address = "localhost"
    port = 4999
    website_url = "http://" + address + ":" + str(port)

    command = [ sys.executable, script_path, "--address", address, "--port", str(port) ]

    process = await asyncio.create_subprocess_exec(*command,
        stdin = subprocess.DEVNULL, stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)

    try:
        response = requests.request("GET", website_url + "/", timeout = timeout_seconds)
        response.raise_for_status()
    except requests.RequestException as exception:
        raise RuntimeError("Dummy website failed to start") from exception

    yield website_url

    if process.returncode is None:
        process.terminate()

        try:
            await asyncio.wait_for(process.wait(), timeout_seconds)
        except asyncio.TimeoutError:
            pass

    if process.returncode is None:
        process.kill()

        try:
            await asyncio.wait_for(process.wait(), timeout_seconds)
        except asyncio.TimeoutError:
            pass

    if process.returncode is None:
        raise RuntimeError("Dummy website failed to terminate")


@pytest.mark.asyncio
async def test_send_request_connection_error():
    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()

    async with aiohttp.ClientSession() as session:
        web_client = WebClientAsync(logger, serializer, session)

        with pytest.raises(WebRequestException) as exception_info:
            await web_client.send_web_request("GET", "http://localhost:4998/")

        assert isinstance(exception_info.value.__cause__, aiohttp.ClientConnectionError)
        assert exception_info.value.status_code is None
        assert exception_info.value.response is None

@pytest.mark.asyncio
async def test_send_web_request_html(website):
    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()

    async with aiohttp.ClientSession() as session:
        web_client = WebClientAsync(logger, serializer, session)

        response = await web_client.send_web_request("GET", website + "/Html", response_content_type = "text/html")

        assert response is not None
        assert response.status_code == 200
        assert response.data is not None
        assert isinstance(response.data, str)
        assert isinstance(response.underlying_object, aiohttp.ClientResponse)


@pytest.mark.asyncio
async def test_send_web_request_html_discarded(website):
    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()

    async with aiohttp.ClientSession() as session:
        web_client = WebClientAsync(logger, serializer, session)

        with pytest.raises(WebContentException) as exception_info:
            await web_client.send_web_request("GET", website + "/Html", response_content_type = "application/json")

        assert isinstance(exception_info.value.__cause__, TypeError)
        assert exception_info.value.status_code == 200
        assert exception_info.value.response is not None
        assert exception_info.value.response.data is None
        assert isinstance(exception_info.value.response.underlying_object, aiohttp.ClientResponse)


@pytest.mark.asyncio
async def test_send_web_request_html_unexcepted_content_type(website):
    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()

    async with aiohttp.ClientSession() as session:
        web_client = WebClientAsync(logger, serializer, session)

        with pytest.raises(WebContentException) as exception_info:
            await web_client.send_web_request("GET", website + "/Html", response_content_type = "application/json")

        assert isinstance(exception_info.value.__cause__, TypeError)

        response = exception_info.value.response

        assert response is not None
        assert response.status_code == 200
        assert response.data is None
        assert isinstance(response.underlying_object, aiohttp.ClientResponse)


@pytest.mark.asyncio
async def test_send_web_request_html_not_found(website):
    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()

    async with aiohttp.ClientSession() as session:
        web_client = WebClientAsync(logger, serializer, session)

        with pytest.raises(WebStatusException) as exception_info:
            await web_client.send_web_request("GET", website + "/HtmlNotFound", response_content_type = "text/html")

        assert isinstance(exception_info.value.__cause__, aiohttp.ClientResponseError)

        response = exception_info.value.response

        assert response is not None
        assert response.status_code == 404
        assert response.data is None
        assert isinstance(response.underlying_object, aiohttp.ClientResponse)


@pytest.mark.asyncio
async def test_send_api_request_json(website):
    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()

    async with aiohttp.ClientSession() as session:
        web_client = WebClientAsync(logger, serializer, session)

        response = await web_client.send_api_request("GET", website + "/Json", response_content_type = "application/json", response_obj_type = dict)

        assert response is not None
        assert response.status_code == 200
        assert response.data is not None
        assert isinstance(response.data, dict)
        assert isinstance(response.underlying_object, aiohttp.ClientResponse)

@pytest.mark.asyncio
async def test_send_api_request_json_discarded(website):
    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()

    async with aiohttp.ClientSession() as session:
        web_client = WebClientAsync(logger, serializer, session)

        response = await web_client.send_api_request("GET", website + "/Json")

        assert response is not None
        assert response.status_code == 200
        assert response.data is None
        assert isinstance(response.underlying_object, aiohttp.ClientResponse)


@pytest.mark.asyncio
async def test_send_api_request_json_unexcepted_content_type(website):
    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()

    async with aiohttp.ClientSession() as session:
        web_client = WebClientAsync(logger, serializer, session)

        with pytest.raises(WebContentException) as exception_info:
            await web_client.send_api_request("GET", website + "/Json", response_content_type = "text/html")

        assert isinstance(exception_info.value.__cause__, TypeError)

        response = exception_info.value.response

        assert response is not None
        assert response.status_code == 200
        assert response.data is None
        assert isinstance(response.underlying_object, aiohttp.ClientResponse)


@pytest.mark.asyncio
async def test_send_api_request_json_unexcepted_obj_type(website):
    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()

    async with aiohttp.ClientSession() as session:
        web_client = WebClientAsync(logger, serializer, session)

        with pytest.raises(WebContentException) as exception_info:
            await web_client.send_api_request("GET", website + "/Json", response_content_type = "application/json", response_obj_type = int)

        assert isinstance(exception_info.value.__cause__, TypeError)

        response = exception_info.value.response

        assert response is not None
        assert response.status_code == 200
        assert response.data is not None
        assert isinstance(response.data, str)
        assert isinstance(response.underlying_object, aiohttp.ClientResponse)


@pytest.mark.asyncio
async def test_send_api_request_json_not_found(website):
    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()

    async with aiohttp.ClientSession() as session:
        web_client = WebClientAsync(logger, serializer, session)

        with pytest.raises(WebStatusException) as exception_info:
            await web_client.send_api_request("GET", website + "/JsonNotFound", response_content_type = "application/json", response_obj_type = dict)

        assert isinstance(exception_info.value.__cause__, aiohttp.ClientResponseError)

        response = exception_info.value.response

        assert response is not None
        assert response.status_code == 404
        assert response.data is None
        assert isinstance(response.underlying_object, aiohttp.ClientResponse)
