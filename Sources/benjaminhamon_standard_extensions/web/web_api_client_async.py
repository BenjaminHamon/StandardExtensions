import datetime
import http
import logging
from typing import Any, Optional
import uuid

import aiohttp
import multidict
import yarl

from benjaminhamon_standard_extensions.serialization.serialization_exception import SerializationException
from benjaminhamon_standard_extensions.serialization.serializer import Serializer
from benjaminhamon_standard_extensions.web.form_data import FormData
from benjaminhamon_standard_extensions.web.web_content_exception import WebContentException
from benjaminhamon_standard_extensions.web.web_request_exception import WebRequestException
from benjaminhamon_standard_extensions.web.web_response import WebResponse
from benjaminhamon_standard_extensions.web.web_status_exception import WebStatusException


class WebApiClientAsync:


    def __init__(self,
            logger: logging.Logger, serializer: Serializer, session: aiohttp.ClientSession, *, authentication: Optional[str] = None) -> None:

        self._logger = logger
        self._serializer = serializer
        self._session = session
        self._authentication = authentication

        self.default_response_success_obj_type: Optional[type] = None
        self.default_response_error_obj_type: Optional[type] = None
        self.timeout = datetime.timedelta(seconds = 30)


    async def send_request(self, # pylint: disable = too-many-arguments, too-many-locals
            method: str,
            url: str,
            *,
            check: bool = True,
            extra_headers: Optional[dict] = None,
            parameters: Optional[dict] = None,
            data: Optional[Any] = None,
            data_as_form: Optional[FormData] = None,
            response_success_obj_type: Optional[type] = None,
            response_error_obj_type: Optional[type] = None,
            simulate: bool = False,
        ) -> WebResponse:

        if data is not None and data_as_form is not None:
            raise ValueError("Only one of 'data' and 'data_as_form' should be set")

        request_identifier = str(uuid.uuid4())
        headers = self._prepare_headers(extra_headers = extra_headers, has_data = data is not None)

        if data is not None:
            data = self._serializer.serialize_to_string(data)

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
                response = await self._session.request(method, url,
                        headers = headers, params = parameters, data = data, timeout = self.timeout.total_seconds())
        except aiohttp.ClientConnectionError as exception:
            raise WebRequestException(request_identifier, method, url, status_code = None, response = None) from exception

        response_content_length = self._get_response_content_length(response)

        self._logger.debug("(WebResponse) %s %s (Identifier: '%s', StatusCode: %s, ContentLength: %s)",
            method, url, request_identifier, response.status, response_content_length if response_content_length is not None else "Unknown")

        try:
            return await self._handle_response(request_identifier, method, url, response,
                    check = check, response_success_obj_type = response_success_obj_type, response_error_obj_type = response_error_obj_type)
        finally:
            response.close()


    def _prepare_headers(self, *, extra_headers: Optional[dict] = None, has_data: bool = False) -> dict:
        headers = {
            "Accept": self._serializer.get_content_type(),
        }

        if extra_headers is not None:
            headers.update(extra_headers)
        if self._authentication is not None:
            headers["Authorization"] = self._authentication
        if has_data:
            headers["Content-Type"] = self._serializer.get_content_type()

        return headers


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

        response.status = 200

        response._headers = multidict.CIMultiDictProxy( # pylint: disable = protected-access
            multidict.CIMultiDict({ "Content-Type": self._serializer.get_content_type() }))

        return response


    def _check_response_status(self, # pylint: disable = too-many-arguments, too-many-positional-arguments
            request_identifier: str, method: str, url: str, response: aiohttp.ClientResponse, *,
            response_data: Optional[Any] = None) -> None:

        try:
            response.raise_for_status()
        except aiohttp.ClientResponseError as exception:
            local_response = WebResponse(request_identifier, dict(response.headers), response.status, response_data, response)
            raise WebStatusException(request_identifier, method, url, response.status, local_response) from exception


    async def _check_response_content(self,
            request_identifier: str, method: str, url: str, response: aiohttp.ClientResponse) -> None:

        if response.status == http.HTTPStatus.NO_CONTENT:
            return

        expected_content_type = self._serializer.get_content_type()
        actual_content_type = response.headers.get("Content-Type")
        media_type = actual_content_type.split(";")[0] if actual_content_type is not None else None

        if actual_content_type is None:
            return

        try:
            if expected_content_type not in (actual_content_type, media_type):
                raise TypeError("Content type is not as expected (Actual: '%s', Expected: '%s')" % (actual_content_type, expected_content_type))
        except TypeError as exception:
            response_data = None
            if media_type is not None and media_type.startswith("text/"):
                response_data = await response.text()
            local_response = WebResponse(request_identifier, dict(response.headers), response.status, response_data, response)
            raise WebContentException(request_identifier, method, url, response.status, local_response) from exception


    def _get_response_content_length(self, response: aiohttp.ClientResponse) -> Optional[int]:
        content_length_value = response.headers.get("Content-Length")
        if content_length_value is not None and content_length_value != "":
            return int(content_length_value)
        return None


    async def _handle_response(self, # pylint: disable = too-many-arguments
            request_identifier: str, method: str, url: str, response: aiohttp.ClientResponse, *,
            check: bool = True, response_success_obj_type: Optional[type] = None, response_error_obj_type: Optional[type] = None,
        ) -> WebResponse:

        if response_success_obj_type is None:
            response_success_obj_type = self.default_response_success_obj_type
        if response_error_obj_type is None:
            response_error_obj_type = self.default_response_error_obj_type

        try:
            if check:
                await self._check_response_content(request_identifier, method, url, response)

            response_data = None
            expected_obj_type = response_success_obj_type if response.ok else response_error_obj_type

            try:
                response_data = await self._convert_response_data(request_identifier, method, url, response, expected_obj_type = expected_obj_type)
            except WebContentException as exception:
                if check:
                    raise
                if exception.response is not None:
                    response_data = exception.response.data

            if check: # Check status after checking and handling content to have response data when possible
                self._check_response_status(request_identifier, method, url, response, response_data = response_data)

            return WebResponse(request_identifier, dict(response.headers), response.status, response_data, response)

        except WebContentException:
            if check: # Status exception takes priority over content exception
                self._check_response_status(request_identifier, method, url, response, response_data = None)
            raise


    async def _convert_response_data(self, # pylint: disable = too-many-arguments
            request_identifier: str, method: str, url: str, response: aiohttp.ClientResponse, *,
            expected_obj_type: Optional[type] = None) -> Optional[Any]:

        if expected_obj_type is None:
            if response.status == http.HTTPStatus.NO_CONTENT:
                return None
            if response.content is None:
                return None

        serialized_data = await response.text()

        if serialized_data == "":
            return None

        if expected_obj_type is None:
            return serialized_data

        try:
            return self._serializer.deserialize_from_string(serialized_data, expected_obj_type)
        except SerializationException as exception:
            local_response = WebResponse(request_identifier, dict(response.headers), response.status, serialized_data, response)
            raise WebContentException(request_identifier, method, url, response.status, local_response) from exception
