import http.client
from typing import Optional

from benjaminhamon_standard_extensions.web.web_response import WebResponse


class WebRequestException(Exception):
    """ Exception raised when a web request failed to complete successfully """


    def __init__(self, # pylint: disable = too-many-arguments, too-many-positional-arguments
            request_identifier: str, method: str, url: str, status_code: Optional[int], response: Optional[WebResponse]) -> None:

        self.request_identifier = request_identifier
        self.method = method
        self.url = url
        self.status_code = status_code
        self.status_message = http.client.responses[status_code] if status_code is not None else None
        self.response = response

        status_for_exception = "%s (%s)" % (self.status_code, self.status_message) if self.status_code is not None else "Unknown"
        exception_message = "(WebRequestException) %s %s" % (self.method, self.url)
        exception_message += " (Identifier: '%s', Status: '%s')" % (self.request_identifier, status_for_exception)

        super().__init__(exception_message)
