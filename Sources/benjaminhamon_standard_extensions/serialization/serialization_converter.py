import abc
from typing import Any


class SerializationConverter(abc.ABC):


    @abc.abstractmethod
    def convert_from_serializable(self, obj_as_serializable: Any) -> Any:
        pass


    @abc.abstractmethod
    def convert_to_serializable(self, obj: Any) -> Any:
        pass
