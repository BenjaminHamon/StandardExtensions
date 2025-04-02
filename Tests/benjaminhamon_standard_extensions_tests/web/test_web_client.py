""" Unit tests for WebServiceClient """

import logging

import pytest
import requests

from benjaminhamon_standard_extensions.serialization.json_serializer import JsonSerializer
from benjaminhamon_standard_extensions.web.web_client import WebClient
from benjaminhamon_standard_extensions.web.web_content_exception import WebContentException
from benjaminhamon_standard_extensions.web.web_request_exception import WebRequestException
from benjaminhamon_standard_extensions.web.web_status_exception import WebStatusException


_skip_tests_with_external_dependencies = True


def test_send_request_connection_error():
    if _skip_tests_with_external_dependencies:
        pytest.skip()

    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()
    web_client = WebClient(logger, serializer)

    with pytest.raises(WebRequestException) as exception_info:
        web_client.send_request("GET", "https://localhost:404/")

    assert isinstance(exception_info.value.__cause__, requests.RequestException)
    assert exception_info.value.status_code is None
    assert exception_info.value.response_data is None


def test_send_request_html():
    if _skip_tests_with_external_dependencies:
        pytest.skip()

    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()
    web_client = WebClient(logger, serializer)

    assert web_client.send_request("GET", "https://www.benjaminhamon.com/", response_content_type = "text/html", response_obj_type = str) is not None


def test_send_request_html_discarded():
    if _skip_tests_with_external_dependencies:
        pytest.skip()

    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()
    web_client = WebClient(logger, serializer)

    assert web_client.send_request("GET", "https://www.benjaminhamon.com/") is None


def test_send_request_html_unexcepted_content_type():
    if _skip_tests_with_external_dependencies:
        pytest.skip()

    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()
    web_client = WebClient(logger, serializer)

    with pytest.raises(WebContentException) as exception_info:
        assert web_client.send_request("GET", "https://www.benjaminhamon.com/", response_content_type = "application/json") is None

    assert isinstance(exception_info.value.__cause__, TypeError)
    assert exception_info.value.status_code == 200
    assert exception_info.value.response_data is not None


def test_send_request_html_unexcepted_obj_type():
    if _skip_tests_with_external_dependencies:
        pytest.skip()

    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()
    web_client = WebClient(logger, serializer)

    with pytest.raises(WebContentException) as exception_info:
        assert web_client.send_request("GET", "https://www.benjaminhamon.com/", response_content_type = "text/html", response_obj_type = dict) is None

    assert isinstance(exception_info.value.__cause__, TypeError)
    assert exception_info.value.status_code == 200
    assert exception_info.value.response_data is not None


def test_send_request_html_not_found():
    if _skip_tests_with_external_dependencies:
        pytest.skip()

    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()
    web_client = WebClient(logger, serializer)

    with pytest.raises(WebStatusException) as exception_info:
        web_client.send_request("GET", "https://www.benjaminhamon.com/DoesNotExist")

    assert isinstance(exception_info.value.__cause__, requests.HTTPError)
    assert exception_info.value.status_code == 404
    assert exception_info.value.response_data is None


def test_send_request_json():
    if _skip_tests_with_external_dependencies:
        pytest.skip()

    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()
    web_client = WebClient(logger, serializer)

    assert web_client.send_request("GET", "https://api.github.com/", response_content_type = "application/json", response_obj_type = dict) is not None


def test_send_request_json_discarded():
    if _skip_tests_with_external_dependencies:
        pytest.skip()

    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()
    web_client = WebClient(logger, serializer)

    assert web_client.send_request("GET", "https://api.github.com/") is None


def test_send_request_json_not_found():
    if _skip_tests_with_external_dependencies:
        pytest.skip()

    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()
    web_client = WebClient(logger, serializer)

    with pytest.raises(WebStatusException) as exception_info:
        web_client.send_request("GET", "https://api.github.com/DoesNotExist")

    assert isinstance(exception_info.value.__cause__, requests.HTTPError)
    assert exception_info.value.status_code == 404
    assert exception_info.value.response_data is None


def test_send_request_json_unexcepted_content_type():
    if _skip_tests_with_external_dependencies:
        pytest.skip()

    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()
    web_client = WebClient(logger, serializer)

    with pytest.raises(WebContentException) as exception_info:
        assert web_client.send_request("GET", "https://api.github.com/", response_content_type = "text/html") is None

    assert isinstance(exception_info.value.__cause__, TypeError)
    assert exception_info.value.status_code == 200
    assert exception_info.value.response_data is not None


def test_send_request_json_unexcepted_obj_type():
    if _skip_tests_with_external_dependencies:
        pytest.skip()

    logger = logging.getLogger("Tests")
    serializer = JsonSerializer()
    web_client = WebClient(logger, serializer)

    with pytest.raises(WebContentException) as exception_info:
        assert web_client.send_request("GET", "https://api.github.com/", response_content_type = "application/json", response_obj_type = int) is None

    assert isinstance(exception_info.value.__cause__, TypeError)
    assert exception_info.value.status_code == 200
    assert exception_info.value.response_data is not None
