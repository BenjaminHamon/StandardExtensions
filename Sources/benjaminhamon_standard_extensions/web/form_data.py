import dataclasses
from typing import List

from benjaminhamon_standard_extensions.web.form_data_field import FormDataField


@dataclasses.dataclass(frozen = True)
class FormData:
    fields: List[FormDataField]
