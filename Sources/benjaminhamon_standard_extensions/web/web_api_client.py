import datetime
import http
import logging
from typing import Any, Dict, Optional
import uuid

import requests
import requests.structures

from benjaminhamon_standard_extensions.serialization.serialization_exception import SerializationException
from benjaminhamon_standard_extensions.serialization.serializer import Serializer
from benjaminhamon_standard_extensions.web.form_data import FormData
from benjaminhamon_standard_extensions.web.web_content_exception import WebContentException
from benjaminhamon_standard_extensions.web.web_request_exception import WebRequestException
from benjaminhamon_standard_extensions.web.web_response import WebResponse
from benjaminhamon_standard_extensions.web.web_status_exception import WebStatusException


class WebApiClient:


    def __init__(self,
            logger: logging.Logger, serializer: Serializer, session: requests.Session, *, authentication: Optional[str] = None) -> None:

        self._logger = logger
        self._serializer = serializer
        self._session = session
        self._authentication = authentication

        self.default_response_success_obj_type: Optional[type] = None
        self.default_response_error_obj_type: Optional[type] = None
        self.timeout = datetime.timedelta(seconds = 30)


    def send_request(self, # pylint: disable = too-many-arguments, too-many-locals, too-many-branches
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

        if response_success_obj_type is None:
            response_success_obj_type = self.default_response_success_obj_type
        if response_error_obj_type is None:
            response_error_obj_type = self.default_response_error_obj_type

        headers = {
            "Accept": self._serializer.get_content_type(),
        }

        if extra_headers is not None:
            headers.update(extra_headers)
        if self._authentication is not None:
            headers["Authorization"] = self._authentication

        serialized_data = None
        if data is not None:
            headers["Content-Type"] = self._serializer.get_content_type()
            serialized_data = self._serializer.serialize_to_string(data)

        data_as_form_for_requests: Optional[Dict[str,tuple]] = None
        if data_as_form is not None:
            data_as_form_for_requests = {}
            for field in data_as_form.fields:
                data_as_form_for_requests[field.key] = (field.filename, field.value, field.content_type)

        self._logger.debug("(WebRequest) %s %s (Identifier: '%s')", method, url, request_identifier)

        try:
            if simulate:
                response = self._fake_response()
            else:
                response = self._session.request(method, url,
                        headers = headers, params = parameters, data = serialized_data, files = data_as_form_for_requests,
                        stream = True, timeout = self.timeout.total_seconds())
        except requests.RequestException as exception:
            raise WebRequestException(request_identifier, method, url, status_code = None, response = None) from exception

        try:
            response_content_length = self._get_response_content_length(response)

            self._logger.debug("(WebResponse) %s %s (Identifier: '%s', StatusCode: %s, ContentLength: %s)",
                method, url, request_identifier, response.status_code, response_content_length if response_content_length is not None else "Unknown")

            if check:
                self._check_response_content(request_identifier, method, url, response)

            response_data = None
            expected_obj_type = response_success_obj_type if response.ok else response_error_obj_type

            try:
                response_data = self._handle_api_response_data(request_identifier, method, url, response, expected_obj_type)
            except WebContentException as exception:
                if check:
                    raise
                if exception.response is not None:
                    response_data = exception.response.data

            if check:
                self._check_response_status(request_identifier, method, url, response, response_data)

            return WebResponse(request_identifier, dict(response.headers), response.status_code, response_data, response)

        finally:
            if not simulate:
                response.close()


    def _fake_response(self) -> requests.Response:
        response = requests.Response()
        response.status_code = 200
        response.headers = requests.structures.CaseInsensitiveDict({ "Content-Type": self._serializer.get_content_type() })
        return response


    def _check_response_status(self, # pylint: disable = too-many-arguments, too-many-positional-arguments
            request_identifier: str, method: str, url: str, response: requests.Response, response_data: Optional[Any]) -> None:

        try:
            response.raise_for_status()
        except requests.HTTPError as exception:
            local_response = WebResponse(request_identifier, dict(response.headers), response.status_code, response_data, response)
            raise WebStatusException(request_identifier, method, url, response.status_code, local_response) from exception


    def _check_response_content(self,
            request_identifier: str, method: str, url: str, response: requests.Response) -> None:

        if response.status_code == http.HTTPStatus.NO_CONTENT:
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
                response_data = response.text
            local_response = WebResponse(request_identifier, dict(response.headers), response.status_code, response_data, response)
            raise WebContentException(request_identifier, method, url, response.status_code, local_response) from exception


    def _get_response_content_length(self, response: requests.Response) -> Optional[int]:
        content_length_value = response.headers.get("Content-Length")
        if content_length_value is not None and content_length_value != "":
            return int(content_length_value)
        return None


    def _handle_api_response_data(self, # pylint: disable = too-many-arguments, too-many-positional-arguments
            request_identifier: str, method: str, url: str, response: requests.Response, expected_obj_type: Optional[type]) -> Optional[Any]:

        if expected_obj_type is None:
            if response.status_code == http.HTTPStatus.NO_CONTENT:
                return None
            if response.content is None:
                return None

        serialized_data = response.text

        if serialized_data == "":
            return None

        if expected_obj_type is None:
            return serialized_data

        try:
            return self._serializer.deserialize_from_string(serialized_data, expected_obj_type)
        except SerializationException as exception:
            local_response = WebResponse(request_identifier, dict(response.headers), response.status_code, serialized_data, response)
            raise WebContentException(request_identifier, method, url, response.status_code, local_response) from exception
