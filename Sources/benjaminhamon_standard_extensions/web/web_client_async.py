import datetime
import logging
from typing import Any, Awaitable, Callable, Optional
import uuid

import aiohttp
import multidict
import yarl

from benjaminhamon_standard_extensions.web.form_data import FormData
from benjaminhamon_standard_extensions.web.web_content_exception import WebContentException
from benjaminhamon_standard_extensions.web.web_request_exception import WebRequestException
from benjaminhamon_standard_extensions.web.web_response import WebResponse
from benjaminhamon_standard_extensions.web.web_status_exception import WebStatusException


class WebClientAsync:


    def __init__(self, logger: logging.Logger, *, authentication: Optional[str] = None) -> None:
        self._logger = logger
        self._authentication = authentication

        self.chunk_size: int = 1024 * 1024
        self.timeout = datetime.timedelta(seconds = 30)


    async def send_request(self, # pylint: disable = too-many-arguments
            session: aiohttp.ClientSession,
            method: str,
            url: str,
            *,
            check: bool = True,
            extra_headers: Optional[dict] = None,
            parameters: Optional[dict] = None,
            data: Optional[Any] = None,
            data_as_form: Optional[FormData] = None,
            simulate: bool = False,
        ) -> WebResponse:

        async def handle_data(response: aiohttp.ClientResponse) -> Optional[Any]:
            return await self._handle_web_response_data(response)

        headers = {}
        if extra_headers is not None:
            headers.update(extra_headers)

        return await self._send_request_internal(session, method, url, handle_data,
                check = check, headers = headers, parameters = parameters, data = data, data_as_form = data_as_form, simulate = simulate)


    async def upload(self, # pylint: disable = too-many-arguments
            session: aiohttp.ClientSession,
            method: str,
            url: str,
            local_file_path: str,
            *,
            check: bool = True,
            extra_headers: Optional[dict] = None,
            parameters: Optional[dict] = None,
            content_type: Optional[str] = None,
            simulate: bool = False,
        ) -> WebResponse:

        async def handle_data(response: aiohttp.ClientResponse) -> Optional[Any]:
            return await self._handle_web_response_data(response)

        headers = {}
        if content_type is not None:
            headers["Content-Type"] = content_type
        if extra_headers is not None:
            headers.update(extra_headers)

        with open(local_file_path, mode = "rb") as local_file:
            return await self._send_request_internal(session, method, url, handle_data,
                    check = check, headers = headers, parameters = parameters, data = local_file, simulate = simulate)


    async def download(self, # pylint: disable = too-many-arguments
            session: aiohttp.ClientSession,
            url: str,
            local_file_path: str,
            *,
            check: bool = True,
            extra_headers: Optional[dict] = None,
            parameters: Optional[dict] = None,
            response_content_type: Optional[str] = None,
            simulate: bool = False,
        ) -> WebResponse:

        async def handle_data(response: aiohttp.ClientResponse) -> Optional[Any]:
            return await self._handle_download_response_data(local_file_path, response, simulate = simulate)

        method = "GET"

        headers = {}
        if response_content_type is not None:
            headers["Accept"] = response_content_type
        if extra_headers is not None:
            headers.update(extra_headers)

        return await self._send_request_internal(session, method, url, handle_data,
                check = check, headers = headers, parameters = parameters, simulate = simulate)


    async def _send_request_internal(self, # pylint: disable = too-many-arguments, too-many-locals
            session: aiohttp.ClientSession,
            method: str,
            url: str,
            data_handler: Callable[[aiohttp.ClientResponse],Awaitable[Optional[Any]]],
            *,
            check: bool = True,
            headers: Optional[dict] = None,
            parameters: Optional[dict] = None,
            data: Optional[Any] = None,
            data_as_form: Optional[FormData] = None,
            simulate: bool = False,
        ) -> WebResponse:

        if data is not None and data_as_form is not None:
            raise ValueError("Only one of 'data' and 'data_as_form' should be set")

        request_identifier = str(uuid.uuid4())

        if headers is None:
            headers = {}
        if self._authentication is not None:
            headers["Authorization"] = self._authentication

        if data_as_form is not None:
            data_as_form_for_aiohttp = aiohttp.FormData()
            for field in data_as_form.fields:
                data_as_form_for_aiohttp.add_field(field.key, field.value, filename = field.filename, content_type = field.content_type)
            data = data_as_form_for_aiohttp

        self._logger.debug("(WebRequest) %s %s (Identifier: '%s')", method, url, request_identifier)

        try:
            if simulate:
                response = self._fake_response(method, url)
            else:
                response = await session.request(method, url,
                        headers = headers, params = parameters, data = data, timeout = aiohttp.ClientTimeout(total = self.timeout.total_seconds()))
        except aiohttp.ClientConnectionError as exception:
            raise WebRequestException(request_identifier, method, url, status_code = None, response = None) from exception

        try:
            response_content_length = self._get_response_content_length(response)

            self._logger.debug("(WebResponse) %s %s (Identifier: '%s', StatusCode: %s, ContentLength: %s)",
                method, url, request_identifier, response.status, response_content_length if response_content_length is not None else "Unknown")

            if check:
                self._check_response_status(request_identifier, method, url, response)
                self._check_response_content(request_identifier, method, url, headers, response)

            response_data = await data_handler(response)

            return WebResponse(request_identifier, dict(response.headers), response.status, response_data, response)

        finally:
            response.close()


    def _fake_response(self, method: str, url: str) -> aiohttp.ClientResponse:
        request = aiohttp.ClientRequest(method, yarl.URL(url))

        response = aiohttp.ClientResponse(
            method = method,
            url = yarl.URL(url),
            writer = request._writer, # pylint: disable = protected-access
            continue100 = request._continue, # pylint: disable = protected-access
            timer = request._timer, # pylint: disable = protected-access
            request_info = request.request_info,
            traces = request._traces, # pylint: disable = protected-access
            loop = request.loop,
            session = request._session, # pylint: disable = protected-access
        )

        response._headers = multidict.CIMultiDictProxy(multidict.CIMultiDict()) # pylint: disable = protected-access
        response.status = 200

        return response


    def _check_response_status(self, request_identifier: str, method: str, url: str, response: aiohttp.ClientResponse) -> None:
        try:
            response.raise_for_status()
        except aiohttp.ClientResponseError as exception:
            local_response = WebResponse(request_identifier, dict(response.headers), response.status, None, response)
            raise WebStatusException(request_identifier, method, url, response.status, local_response) from exception


    def _check_response_content(self, # pylint: disable = too-many-arguments, too-many-positional-arguments
            request_identifier: str, method: str, url: str, headers: dict, response: aiohttp.ClientResponse) -> None:

        if response.status == 204:
            return
        if response.content is None:
            return

        expected_content_type = headers.get("Accept")
        if expected_content_type is None:
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


    async def _handle_web_response_data(self, response: aiohttp.ClientResponse) -> Optional[Any]:
        if response.status == 204:
            return None
        if response.content is None:
            return None

        content_type = response.headers.get("Content-Type")
        if content_type is not None and content_type.startswith("text/"):
            return await response.text()

        return await response.read()


    async def _handle_download_response_data(self, local_file_path: str, response: aiohttp.ClientResponse, *, simulate: bool = False) -> None:
        if not simulate:
            with open(local_file_path, mode = "wb") as local_file:
                async for chunk in response.content.iter_chunked(self.chunk_size):
                    local_file.write(chunk)
