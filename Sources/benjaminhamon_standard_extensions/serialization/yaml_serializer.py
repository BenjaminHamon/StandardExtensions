from typing import Any, Dict, Optional

import yaml

from benjaminhamon_standard_extensions.serialization.serializer import Serializer
from benjaminhamon_standard_extensions.serialization.serialization_converter import SerializationConverter


class YamlSerializer(Serializer):


    def __init__(self) -> None:
        self._converter_collection: Dict[type,SerializationConverter] = {}
        self.encoding: Optional[str] = "utf-8"
        self.indent: Optional[int] = None
        self.max_width: Optional[int] = None
        self.sort_keys: bool = False


    def get_content_type(self) -> str:
        return "application/yaml"


    def get_file_extension(self) -> str:
        return ".yaml"


    def add_converter(self, obj_type: type, converter: SerializationConverter) -> None:
        self._converter_collection[obj_type] = converter


    def serialize_to_file(self, obj: Any, file_path: str) -> None:
        obj_as_serializable = self._convert_to_serializable(obj)
        with open(file_path, mode = "w", encoding = self.encoding) as data_file:
            yaml.safe_dump(obj_as_serializable, data_file, allow_unicode = True, indent = self.indent, width = self.max_width, sort_keys = self.sort_keys)


    def serialize_to_string(self, obj: Any) -> str:
        obj_as_serializable = self._convert_to_serializable(obj)
        return yaml.safe_dump(obj_as_serializable, allow_unicode = True, indent = self.indent, width = self.max_width, sort_keys = self.sort_keys)


    def deserialize_from_file(self, file_path: str, obj_type: type) -> Any:
        with open(file_path, mode = "r", encoding = self.encoding) as data_file:
            obj_as_serializable = yaml.safe_load(data_file)
        return self._convert_from_serializable(obj_as_serializable, obj_type)


    def deserialize_from_string(self, obj_serialized: str, obj_type: type) -> Any:
        obj_as_serializable = yaml.safe_load(obj_serialized)
        return self._convert_from_serializable(obj_as_serializable, obj_type)


    def _convert_from_serializable(self, obj_as_serializable: Any, obj_type: type) -> Any:
        converter = self._converter_collection.get(obj_type, None)
        if converter is not None:
            return converter.convert_from_serializable(obj_as_serializable)
        return obj_as_serializable


    def _convert_to_serializable(self, obj: Any) -> Any:
        converter = self._converter_collection.get(type(obj), None)
        if converter is not None:
            return converter.convert_to_serializable(obj)
        return obj
