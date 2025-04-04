import datetime
import logging
from typing import Any, Optional
import uuid

import aiohttp

from benjaminhamon_standard_extensions.serialization.serializer import Serializer
from benjaminhamon_standard_extensions.web.web_content_exception import WebContentException
from benjaminhamon_standard_extensions.web.web_request_exception import WebRequestException
from benjaminhamon_standard_extensions.web.web_response import WebResponse
from benjaminhamon_standard_extensions.web.web_status_exception import WebStatusException


class WebClientAsync:


    def __init__(self,
            logger: logging.Logger, serializer: Serializer, session: aiohttp.ClientSession, *, authentication: Optional[str] = None) -> None:

        self._logger = logger
        self._serializer = serializer
        self._session = session
        self._authentication = authentication

        self.chunk_size: int = 1024 * 1024
        self.timeout = datetime.timedelta(seconds = 30)


    async def send_web_request(self, # pylint: disable = too-many-arguments
            method: str, url: str, *,
            check: bool = True, extra_headers: Optional[dict] = None,
            parameters: Optional[dict] = None, data: Optional[Any] = None,
            response_content_type: Optional[str] = None,
        ) -> WebResponse:

        request_identifier = str(uuid.uuid4())

        headers = {} if extra_headers is None else extra_headers
        if self._authentication is not None:
            headers["Authorization"] = self._authentication

        self._logger.debug("(WebRequest) %s %s (Identifier: '%s')", method, url, request_identifier)

        try:
            response = await self._session.request(method, url,
                headers = headers, params = parameters, data = data, timeout = self.timeout.total_seconds())
        except aiohttp.ClientConnectionError as exception:
            raise WebRequestException(request_identifier, method, url, status_code = None, response = None) from exception

        response_content_length = self._get_response_content_length(response)

        self._logger.debug("(WebResponse) %s %s (Identifier: '%s', StatusCode: %s, ContentLength: %s)",
            method, url, request_identifier, response.status, response_content_length if response_content_length is not None else "Unknown")

        if check:
            self._check_response_status(request_identifier, method, url, response)
            self._check_response_content(request_identifier, method, url, response, response_content_type)

        response_data = await self._get_web_response_data(response, response_content_type)

        return WebResponse(request_identifier, dict(response.headers), response.status, response_data, response)


    async def send_api_request(self, # pylint: disable = too-many-arguments
            method: str, url: str, *,
            check: bool = True, extra_headers: Optional[dict] = None,
            parameters: Optional[dict] = None, data: Optional[dict] = None,
            response_content_type: Optional[str] = None, response_obj_type: Optional[type] = None,
        ) -> WebResponse:

        def get_headers() -> dict:
            headers = {}

            headers["Accept"] = self._serializer.get_content_type()

            if data is not None:
                headers["Content-Type"] = self._serializer.get_content_type()

            if extra_headers is not None:
                headers.update(extra_headers)

            return headers

        headers = get_headers()

        serialized_data = None
        if data is not None:
            serialized_data = self._serializer.serialize_to_string(data)

        if response_content_type is None:
            response_content_type = self._serializer.get_content_type()

        response = await self.send_web_request(method, url, check = check,
                extra_headers = headers, parameters = parameters, data = serialized_data,
                response_content_type = response_content_type)

        if not isinstance(response.underlying_object, aiohttp.ClientResponse):
            raise RuntimeError("Underlying object should be a ClientResponse object")

        response_data = await self._get_api_response_data(response.request_identifier, method, url,
            response.underlying_object, response_content_type, response_obj_type)

        return WebResponse(response.request_identifier, response.response_headers, response.status_code, response_data, response.underlying_object)


    async def upload(self, # pylint: disable = too-many-arguments
            url: str, local_file_path: str, *,
            check: bool = True, extra_headers: Optional[dict] = None,
            parameters: Optional[dict] = None, content_type: Optional[str] = None) -> WebResponse:

        headers = {}
        if content_type is not None:
            headers["Content-Type"] = content_type
        if extra_headers is not None:
            headers.update(extra_headers)

        with open(local_file_path, mode = "rb") as local_file:
            return await self.send_web_request("POST", url, check = check, extra_headers = headers, parameters = parameters, data = local_file)


    async def download(self, # pylint: disable = too-many-arguments, too-many-locals
            url: str, local_file_path: str, *,
            check: bool = True, extra_headers: Optional[dict] = None,
            parameters: Optional[dict] = None, response_content_type: Optional[str] = None) -> WebResponse:

        request_identifier = str(uuid.uuid4())
        method = "GET"

        headers = {}
        if response_content_type is not None:
            headers["Accept"] = response_content_type
        if extra_headers is not None:
            headers.update(extra_headers)

        if self._authentication is not None:
            headers["Authorization"] = self._authentication

        self._logger.debug("(WebRequest) %s %s (Identifier: '%s')", method, url, request_identifier)

        try:
            response = await self._session.request(method, url,
                headers = headers, params = parameters, timeout = self.timeout.total_seconds())
        except aiohttp.ClientConnectionError as exception:
            raise WebRequestException(request_identifier, method, url, status_code = None, response = None) from exception

        try:
            response_content_length = self._get_response_content_length(response)

            self._logger.debug("(WebResponse) %s %s (Identifier: '%s', StatusCode: %s, ContentLength: %s)",
                method, url, request_identifier, response.status, response_content_length if response_content_length is not None else "Unknown")

            if check:
                self._check_response_status(request_identifier, method, url, response)
                self._check_response_content(request_identifier, method, url, response, response_content_type)

            with open(local_file_path, mode = "wb") as local_file:
                async for chunk in response.content.iter_chunked(self.chunk_size):
                    local_file.write(chunk)

            response_data = await self._get_web_response_data(response, response_content_type)

            return WebResponse(request_identifier, dict(response.headers), response.status, response_data, response)

        finally:
            response.close()


    def _get_request_headers(self, extra_headers: Optional[dict], has_data: bool) -> dict:
        headers = {}

        if self._authentication is not None:
            headers["Authorization"] = self._authentication

        headers["Accept"] = self._serializer.get_content_type()

        if has_data:
            headers["Content-Type"] = self._serializer.get_content_type()

        if extra_headers is not None:
            headers.update(extra_headers)

        return headers


    def _check_response_status(self, request_identifier: str, method: str, url: str, response: aiohttp.ClientResponse) -> None:
        try:
            response.raise_for_status()
        except aiohttp.ClientResponseError as exception:
            local_response = WebResponse(request_identifier, dict(response.headers), response.status, None, response)
            raise WebStatusException(request_identifier, method, url, response.status, local_response) from exception


    def _check_response_content(self, # pylint: disable = too-many-arguments, too-many-positional-arguments
            request_identifier: str, method: str, url: str, response: aiohttp.ClientResponse, expected_content_type: Optional[str]) -> None:

        if response.status == 204:
            return
        if expected_content_type is None:
            return
        if response.content is None:
            return

        try:
            actual_content_type = response.headers.get("Content-Type")
            media_type = actual_content_type.split(";")[0] if actual_content_type is not None else None

            if expected_content_type not in (actual_content_type, media_type):
                raise TypeError("Content type is not as expected (Actual: '%s', Expected: '%s')" % (actual_content_type, expected_content_type))

        except TypeError as exception:
            local_response = WebResponse(request_identifier, dict(response.headers), response.status, None, response)
            raise WebContentException(request_identifier, method, url, response.status, local_response) from exception


    def _get_response_content_length(self, response: aiohttp.ClientResponse) -> Optional[int]:
        content_length_value = response.headers.get("Content-Length")
        if content_length_value is not None and content_length_value != "":
            return int(content_length_value)
        return None


    async def _get_web_response_data(self, response: aiohttp.ClientResponse, expected_content_type: Optional[str]) -> Optional[Any]:
        if response.status == 204:
            return None
        if expected_content_type is None:
            return None
        if response.content is None:
            return None

        if expected_content_type.startswith("text/"):
            response_content_as_text = await response.text()
            if response_content_as_text == "":
                return None
            return response_content_as_text
        return response.content


    async def _get_api_response_data(self, # pylint: disable = too-many-arguments, too-many-positional-arguments, too-many-return-statements
            request_identifier: str, method: str, url: str, response: aiohttp.ClientResponse,
            expected_content_type: Optional[str], expected_obj_type: Optional[type]) -> Optional[Any]:

        if response.status == 204:
            return None
        if expected_content_type is None:
            return None
        if response.content is None:
            return None
        if expected_obj_type is None:
            return None

        response_content_as_text = await response.text()
        if response_content_as_text == "":
            return None

        try:
            if expected_content_type.startswith("text/"):
                if expected_obj_type != str:
                    raise TypeError("Expected type '%s' but received text" % expected_obj_type)
                return response_content_as_text

            serialized_data = response_content_as_text
            if serialized_data is None or serialized_data == "":
                return None

            if expected_content_type != self._serializer.get_content_type():
                raise TypeError("Expected type '%s' but received type '%s'" % (self._serializer.get_content_type()), expected_content_type)

            return self._serializer.deserialize_from_string(serialized_data, expected_obj_type)

        except TypeError as exception:
            local_response = WebResponse(request_identifier, dict(response.headers), response.status, response_content_as_text, response)
            raise WebContentException(request_identifier, method, url, response.status, local_response) from exception
