import dataclasses
from typing import Any, Optional


@dataclasses.dataclass(frozen = True)
class FormDataField:
    key: str
    value: Any
    filename: Optional[str] = None
    content_type: Optional[str] = None
