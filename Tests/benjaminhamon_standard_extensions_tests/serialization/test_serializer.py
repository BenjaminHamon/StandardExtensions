""" Unit tests for Serializer and its implementations """

import os
from typing import Any, List, Optional

import pytest

from benjaminhamon_standard_extensions.serialization.json_serializer import JsonSerializer
from benjaminhamon_standard_extensions.serialization.serialization_converter import SerializationConverter
from benjaminhamon_standard_extensions.serialization.serializer import Serializer
from benjaminhamon_standard_extensions.serialization.yaml_serializer import YamlSerializer

all_serializer_types = [ "json", "yaml" ]


def create_serializer(serializer_type: str) -> Serializer:
    if serializer_type == "json":
        return JsonSerializer()
    if serializer_type == "yaml":
        return YamlSerializer()

    raise ValueError("Unsupported serializer type: '%s'" % serializer_type)


class _MyCollection:

    def __init__(self) -> None:
        self.identifier: Optional[str] = None
        self.all_items: List[_MyCollectionItem] = []


class _MyCollectionItem:

    def __init__(self, data: str) -> None:
        self.data = data


class _MyCollectionSerializationConverter(SerializationConverter):

    def __init__(self, item_converter: SerializationConverter) -> None:
        self._item_converter = item_converter

    def convert_from_serializable(self, obj_as_serializable: Any) -> Any:
        if not isinstance(obj_as_serializable, dict):
            raise ValueError("obj_as_serializable is not of the expected type")

        collection = _MyCollection()
        collection.identifier = obj_as_serializable["identifier"]
        for item_as_serializable in obj_as_serializable["all_items"]:
            item = self._item_converter.convert_from_serializable(item_as_serializable)
            collection.all_items.append(item)
        return collection

    def convert_to_serializable(self, obj: Any) -> Any:
        if not isinstance(obj, _MyCollection):
            raise ValueError("obj is not of the expected type")

        all_items_as_serializable: List[Any] = []
        for item in obj.all_items:
            item_as_serializable = self._item_converter.convert_to_serializable(item)
            all_items_as_serializable.append(item_as_serializable)
        return { "identifier": obj.identifier, "all_items": all_items_as_serializable }


class _MyCollectionItemSerializationConverter(SerializationConverter):

    def convert_from_serializable(self, obj_as_serializable: Any) -> Any:
        if not isinstance(obj_as_serializable, dict):
            raise ValueError("obj_as_serializable is not of the expected type")
        return _MyCollectionItem(obj_as_serializable["data"])

    def convert_to_serializable(self, obj: Any) -> Any:
        if not isinstance(obj, _MyCollectionItem):
            raise ValueError("obj is not of the expected type")
        return { "data": obj.data }


@pytest.mark.parametrize("serializer_type", all_serializer_types)
def test_serialize_to_string(serializer_type):
    serializer = create_serializer(serializer_type)

    data = 123
    data_serialized = serializer.serialize_to_string(data)
    data_deserialized = serializer.deserialize_from_string(data_serialized, type(data))
    assert data_deserialized == data

    data = "StringValue"
    data_serialized = serializer.serialize_to_string(data)
    data_deserialized = serializer.deserialize_from_string(data_serialized, type(data))
    assert data_deserialized == data

    data = "Text\nWith\nNewlines\n"
    data_serialized = serializer.serialize_to_string(data)
    data_deserialized = serializer.deserialize_from_string(data_serialized, type(data))
    assert data_deserialized == data

    data = [ "first", "second", "three" ]
    data_serialized = serializer.serialize_to_string(data)
    data_deserialized = serializer.deserialize_from_string(data_serialized, type(data))
    assert data_deserialized == data

    data = { "key": "value" }
    data_serialized = serializer.serialize_to_string(data)
    data_deserialized = serializer.deserialize_from_string(data_serialized, type(data))
    assert data_deserialized == data


@pytest.mark.parametrize("serializer_type", all_serializer_types)
def test_serialize_to_string_with_mismatched_types(serializer_type):
    serializer = create_serializer(serializer_type)

    data = 123
    data_serialized = serializer.serialize_to_string(data)
    with pytest.raises(TypeError):
        serializer.deserialize_from_string(data_serialized, str)

    data = "StringValue"
    data_serialized = serializer.serialize_to_string(data)
    with pytest.raises(TypeError):
        serializer.deserialize_from_string(data_serialized, int)


@pytest.mark.parametrize("serializer_type", all_serializer_types)
def test_serialize_to_file(tmpdir, serializer_type):
    serializer = create_serializer(serializer_type)
    file_path = os.path.join(tmpdir, "Working", "Data" + serializer.get_file_extension())

    os.makedirs(os.path.dirname(file_path))

    data = 123
    serializer.serialize_to_file(data, file_path)
    data_deserialized = serializer.deserialize_from_file(file_path, type(data))
    assert data_deserialized == data

    data = "StringValue"
    serializer.serialize_to_file(data, file_path)
    data_deserialized = serializer.deserialize_from_file(file_path, type(data))
    assert data_deserialized == data

    data = "Text\nWith\nNewlines\n"
    serializer.serialize_to_file(data, file_path)
    data_deserialized = serializer.deserialize_from_file(file_path, type(data))
    assert data_deserialized == data

    data = [ "first", "second", "three" ]
    serializer.serialize_to_file(data, file_path)
    data_deserialized = serializer.deserialize_from_file(file_path, type(data))
    assert data_deserialized == data

    data = { "key": "value" }
    serializer.serialize_to_file(data, file_path)
    data_deserialized = serializer.deserialize_from_file(file_path, type(data))
    assert data_deserialized == data


@pytest.mark.parametrize("serializer_type", all_serializer_types)
def test_serialize_to_string_with_converter(serializer_type):
    serializer = create_serializer(serializer_type)
    serializer.add_converter(_MyCollection, _MyCollectionSerializationConverter(_MyCollectionItemSerializationConverter()))

    data = _MyCollection()
    data.identifier = "collection"
    data.all_items.append(_MyCollectionItem("first"))
    data.all_items.append(_MyCollectionItem("second"))
    data.all_items.append(_MyCollectionItem("third"))

    data_serialized = serializer.serialize_to_string(data)
    data_deserialized = serializer.deserialize_from_string(data_serialized, type(data))

    assert isinstance(data_deserialized, _MyCollection)
    assert data_deserialized.identifier == data.identifier
    assert len(data_deserialized.all_items) == len(data.all_items)
    assert all(first.data == second.data for first, second in zip(data_deserialized.all_items, data.all_items))
