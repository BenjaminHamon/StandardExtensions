import abc
from typing import Any

from benjaminhamon_standard_extensions.serialization.serialization_converter import SerializationConverter


class Serializer(abc.ABC):


    @abc.abstractmethod
    def get_content_type(self) -> str:
        pass


    @abc.abstractmethod
    def get_file_extension(self) -> str:
        pass


    @abc.abstractmethod
    def add_converter(self, obj_type: type, converter: SerializationConverter) -> None:
        pass


    @abc.abstractmethod
    def serialize_to_file(self, obj: Any, file_path: str) -> None:
        pass


    @abc.abstractmethod
    def serialize_to_string(self, obj: Any) -> str:
        pass


    @abc.abstractmethod
    def deserialize_from_file(self, file_path: str, obj_type: type) -> Any:
        pass


    @abc.abstractmethod
    def deserialize_from_string(self, obj_serialized: str, obj_type: type) -> Any:
        pass
