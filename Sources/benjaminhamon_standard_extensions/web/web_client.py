import datetime
import logging
from typing import Any, Callable, Dict, Optional
import uuid

import requests

from benjaminhamon_standard_extensions.web.form_data import FormData
from benjaminhamon_standard_extensions.web.web_content_exception import WebContentException
from benjaminhamon_standard_extensions.web.web_request_exception import WebRequestException
from benjaminhamon_standard_extensions.web.web_response import WebResponse
from benjaminhamon_standard_extensions.web.web_status_exception import WebStatusException


class WebClient:


    def __init__(self, logger: logging.Logger, *, authentication: Optional[str] = None) -> None:
        self._logger = logger
        self._authentication = authentication

        self.chunk_size: int = 1024 * 1024
        self.timeout = datetime.timedelta(seconds = 30)


    def send_request(self, # pylint: disable = too-many-arguments
            session: requests.Session,
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

        def handle_data(response: requests.Response) -> Optional[Any]:
            return self._handle_web_response_data(response)

        headers = {}
        if extra_headers is not None:
            headers.update(extra_headers)

        return self._send_request_internal(session, method, url, handle_data,
                check = check, headers = extra_headers, parameters = parameters, data = data, data_as_form = data_as_form, simulate = simulate)


    def upload(self, # pylint: disable = too-many-arguments
            session: requests.Session,
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

        def handle_data(response: requests.Response) -> Optional[Any]:
            return self._handle_web_response_data(response)

        headers = {}
        if content_type is not None:
            headers["Content-Type"] = content_type
        if extra_headers is not None:
            headers.update(extra_headers)

        with open(local_file_path, mode = "rb") as local_file:
            return self._send_request_internal(session, method, url, handle_data,
                    check = check, headers = headers, parameters = parameters, data = local_file, simulate = simulate)


    def download(self, # pylint: disable = too-many-arguments
            session: requests.Session,
            url: str,
            local_file_path: str,
            *,
            check: bool = True,
            extra_headers: Optional[dict] = None,
            parameters: Optional[dict] = None,
            content_type: Optional[str] = None,
            simulate: bool = False,
        ) -> WebResponse:

        def handle_data(response: requests.Response) -> Optional[Any]:
            return self._handle_download_response_data(local_file_path, response, simulate = simulate)

        method = "GET"

        headers = {}
        if content_type is not None:
            headers["Accept"] = content_type
        if extra_headers is not None:
            headers.update(extra_headers)

        return self._send_request_internal(session, method, url, handle_data,
                check = check, headers = headers, parameters = parameters, simulate = simulate)


    def _send_request_internal(self, # pylint: disable = too-many-arguments, too-many-locals
            session: requests.Session,
            method: str,
            url: str,
            data_handler: Callable[[requests.Response],Optional[Any]],
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
                response = session.request(method, url,
                        headers = headers, params = parameters, data = data, files = data_as_form_for_requests,
                        stream = True, timeout = self.timeout.total_seconds())
        except requests.RequestException as exception:
            raise WebRequestException(request_identifier, method, url, status_code = None, response = None) from exception

        try:
            response_content_length = self._get_response_content_length(response)

            self._logger.debug("(WebResponse) %s %s (Identifier: '%s', StatusCode: %s, ContentLength: %s)",
                method, url, request_identifier, response.status_code, response_content_length if response_content_length is not None else "Unknown")

            if check:
                self._check_response_status(request_identifier, method, url, response)
                self._check_response_content(request_identifier, method, url, headers, response)

            response_data = data_handler(response)

            return WebResponse(request_identifier, dict(response.headers), response.status_code, response_data, response)

        finally:
            if not simulate:
                response.close()


    def _fake_response(self) -> requests.Response:
        response = requests.Response()
        response.status_code = 200
        return response


    def _check_response_status(self, request_identifier: str, method: str, url: str, response: requests.Response) -> None:
        try:
            response.raise_for_status()
        except requests.HTTPError as exception:
            local_response = WebResponse(request_identifier, dict(response.headers), response.status_code, None, response)
            raise WebStatusException(request_identifier, method, url, response.status_code, local_response) from exception


    def _check_response_content(self, # pylint: disable = too-many-arguments, too-many-positional-arguments
            request_identifier: str, method: str, url: str, headers: dict, response: requests.Response) -> None:

        if response.status_code == 204:
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
            local_response = WebResponse(request_identifier, dict(response.headers), response.status_code, None, response)
            raise WebContentException(request_identifier, method, url, response.status_code, local_response) from exception


    def _get_response_content_length(self, response: requests.Response) -> Optional[int]:
        content_length_value = response.headers.get("Content-Length")
        if content_length_value is not None and content_length_value != "":
            return int(content_length_value)
        return None


    def _handle_web_response_data(self, response: requests.Response) -> Optional[Any]:
        if response.status_code == 204:
            return None
        if response.content is None:
            return None

        content_type = response.headers.get("Content-Type")
        if content_type is not None and content_type.startswith("text/"):
            return response.text

        return response.content


    def _handle_download_response_data(self, local_file_path: str, response: requests.Response, *, simulate: bool = False) -> None:
        if not simulate:
            with open(local_file_path, mode = "wb") as local_file:
                for chunk in response.iter_content(self.chunk_size):
                    local_file.write(chunk)
