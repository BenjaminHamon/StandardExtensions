import json
from typing import Any, Dict, Optional

from benjaminhamon_standard_extensions.serialization.serialization_converter import SerializationConverter
from benjaminhamon_standard_extensions.serialization.serializer import Serializer


class JsonSerializer(Serializer):


    def __init__(self) -> None:
        self._converter_collection: Dict[type,SerializationConverter] = {}
        self.encoding: Optional[str] = "utf-8"
        self.indent: Optional[int] = None
        self.sort_keys: bool = False


    def get_content_type(self) -> str:
        return "application/json"


    def get_file_extension(self) -> str:
        return ".json"


    def add_converter(self, obj_type: type, converter: SerializationConverter) -> None:
        self._converter_collection[obj_type] = converter


    def serialize_to_file(self, obj: Any, file_path: str) -> None:
        obj_as_serializable = self._convert_to_serializable(obj)
        with open(file_path, mode = "w", encoding = self.encoding) as data_file:
            json.dump(obj_as_serializable, data_file, indent = self.indent, sort_keys = self.sort_keys)


    def serialize_to_string(self, obj: Any) -> str:
        obj_as_serializable = self._convert_to_serializable(obj)
        return json.dumps(obj_as_serializable, indent = self.indent, sort_keys = self.sort_keys)


    def deserialize_from_file(self, file_path: str, obj_type: type) -> Any:
        with open(file_path, mode = "r", encoding = self.encoding) as data_file:
            obj_as_serializable = json.load(data_file)
        return self._convert_from_serializable(obj_as_serializable, obj_type)


    def deserialize_from_string(self, obj_serialized: str, obj_type: type) -> Any:
        obj_as_serializable = json.loads(obj_serialized)
        return self._convert_from_serializable(obj_as_serializable, obj_type)


    def _convert_from_serializable(self, obj_as_serializable: Any, obj_type: type) -> Any:
        converter = self._converter_collection.get(obj_type, None)
        obj_deserialized = converter.convert_from_serializable(obj_as_serializable) if converter is not None else obj_as_serializable

        if not isinstance(obj_deserialized, obj_type):
            raise TypeError("Type mismatch after deserialization (Expected: '%s', Actual: '%s')" % (obj_type, type(obj_deserialized)))

        return obj_deserialized


    def _convert_to_serializable(self, obj: Any) -> Any:
        converter = self._converter_collection.get(type(obj), None)
        return converter.convert_to_serializable(obj) if converter is not None else obj
