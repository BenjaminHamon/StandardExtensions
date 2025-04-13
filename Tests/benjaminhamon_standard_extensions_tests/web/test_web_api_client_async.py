""" Unit tests for WebServiceClient """

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
from benjaminhamon_standard_extensions.web.web_api_client_async import WebApiClientAsync
from benjaminhamon_standard_extensions.web.web_content_exception import WebContentException
from benjaminhamon_standard_extensions.web.web_request_exception import WebRequestException
from benjaminhamon_standard_extensions.web.web_status_exception import WebStatusException


@pytest_asyncio.fixture(name = "service", scope = "module", loop_scope = "module")
async def service_fixture():
    timeout_seconds = 5

    script_path = os.path.join(os.path.dirname(__file__), "dummy_service.py")
    address = "localhost"
    port = 4999
    service_url = "http://" + address + ":" + str(port)

    command = [ sys.executable, script_path, "--address", address, "--port", str(port) ]

    process = await asyncio.create_subprocess_exec(*command,
        stdin = subprocess.DEVNULL, stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)

    try:
        response = requests.request("GET", service_url + "/", timeout = timeout_seconds)
        response.raise_for_status()
    except requests.RequestException as exception:
        raise RuntimeError("Dummy service failed to start") from exception

    yield service_url

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
        raise RuntimeError("Dummy service failed to terminate")


@pytest.mark.asyncio
async def test_send_request_with_simulate():
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
async def test_send_request_connection_error():
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
async def test_send_request_with_none(service):
    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()

    async with aiohttp.ClientSession() as session:
        web_client = WebApiClientAsync(logger, serializer, session)

        response = await web_client.send_request("GET", service + "/Nothing")

        assert response is not None
        assert response.status_code == 200
        assert response.data is None
        assert isinstance(response.underlying_object, aiohttp.ClientResponse)


@pytest.mark.asyncio
async def test_send_request_with_get(service):
    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()

    async with aiohttp.ClientSession() as session:
        web_client = WebApiClientAsync(logger, serializer, session)

        response = await web_client.send_request("GET", service + "/Resource", parameters = { "key": "value" }, response_obj_type = dict)

        assert response is not None
        assert response.status_code == 200
        assert response.data is not None
        assert isinstance(response.data, dict)
        assert isinstance(response.underlying_object, aiohttp.ClientResponse)


@pytest.mark.asyncio
async def test_send_request_with_post(service):
    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()

    async with aiohttp.ClientSession() as session:
        web_client = WebApiClientAsync(logger, serializer, session)

        response = await web_client.send_request("POST", service + "/Resource", data = { "key": "value" }, response_obj_type = dict)

        assert response is not None
        assert response.status_code == 200
        assert response.data is not None
        assert isinstance(response.data, dict)
        assert isinstance(response.underlying_object, aiohttp.ClientResponse)


@pytest.mark.asyncio
async def test_send_request_with_unexpected_content_type(service):
    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()

    async with aiohttp.ClientSession() as session:
        web_client = WebApiClientAsync(logger, serializer, session)

        with pytest.raises(WebContentException) as exception_info:
            await web_client.send_request("GET", service + "/BadContentType")

        assert isinstance(exception_info.value.__cause__, TypeError)

        response = exception_info.value.response

        assert response is not None
        assert response.status_code == 200
        assert response.data is None
        assert isinstance(response.underlying_object, aiohttp.ClientResponse)


@pytest.mark.asyncio
async def test_send_request_with_unexcepted_obj_type(service):
    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()

    async with aiohttp.ClientSession() as session:
        web_client = WebApiClientAsync(logger, serializer, session)

        with pytest.raises(WebContentException) as exception_info:
            await web_client.send_request("GET", service + "/Resource", parameters = { "key": "value" }, response_obj_type = int)

        assert isinstance(exception_info.value.__cause__, TypeError)

        response = exception_info.value.response

        assert response is not None
        assert response.status_code == 200
        assert response.data is not None
        assert isinstance(response.data, str)
        assert isinstance(response.underlying_object, aiohttp.ClientResponse)


@pytest.mark.asyncio
async def test_send_request_not_found(service):
    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()

    async with aiohttp.ClientSession() as session:
        web_client = WebApiClientAsync(logger, serializer, session)

        with pytest.raises(WebStatusException) as exception_info:
            await web_client.send_request("GET", service + "/NotFound", response_obj_type = dict)

        assert isinstance(exception_info.value.__cause__, aiohttp.ClientResponseError)

        response = exception_info.value.response

        assert response is not None
        assert response.status_code == 404
        assert response.data is not None
        assert isinstance(response.data, dict)
        assert isinstance(response.underlying_object, aiohttp.ClientResponse)
