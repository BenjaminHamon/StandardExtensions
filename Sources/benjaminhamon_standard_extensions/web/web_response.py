import dataclasses
from typing import Any, Optional, Union

import aiohttp
import requests


@dataclasses.dataclass(frozen = True)
class WebResponse:
    request_identifier: str
    response_headers: dict
    status_code: int
    data: Optional[Any]
    underlying_object: Union[aiohttp.ClientResponse, requests.Response]
