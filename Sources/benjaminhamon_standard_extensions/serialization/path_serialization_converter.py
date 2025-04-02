import os
from typing import Any

from benjaminhamon_standard_extensions.serialization.serialization_converter import SerializationConverter


class PathSerializationConverter(SerializationConverter):


    def convert_from_serializable(self, obj_as_serializable: Any) -> Any:
        if obj_as_serializable is None:
            return None

        if not isinstance(obj_as_serializable, str):
            raise ValueError("obj_as_serializable is not of the expected type")

        return os.path.normpath(obj_as_serializable)


    def convert_to_serializable(self, obj: Any) -> Any:
        if obj is None:
            return None

        if not isinstance(obj, str):
            raise ValueError("obj is not of the expected type")

        return os.path.normpath(obj).replace("\\", "/")
