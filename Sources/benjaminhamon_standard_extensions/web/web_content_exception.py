from typing import Any, Optional

from benjaminhamon_standard_extensions.web.web_request_exception import WebRequestException


class WebContentException(WebRequestException):
    """ Exception raised when a web request returned invalid or unexpected content """


    def __init__(self, # pylint: disable = too-many-arguments, too-many-positional-arguments
            request_identifier: str, method: str, url: str, status_code: int, response_data: Optional[Any]) -> None:

        super().__init__(request_identifier, method, url, status_code, response_data)
