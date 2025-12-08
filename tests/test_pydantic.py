"""Tests for Pydantic integration with AutoRegistry."""

import pytest

pydantic = pytest.importorskip("pydantic")

from abc import abstractmethod
from typing import Dict, List

from pydantic import ValidationError

from autoregistry.pydantic import BaseModel


def test_basic_usage():
    """Test basic BaseModel usage."""

    class Animal(BaseModel):
        name: str
        age: int

    class Dog(Animal):
        name: str = "Buddy"
        age: int = 5

    class Cat(Animal):
        name: str = "Whiskers"
        age: int = 3

    # Test AutoRegistry functionality
    assert "dog" in Animal
    assert "cat" in Animal
    assert list(Animal) == ["dog", "cat"]

    # Test Pydantic functionality
    dog = Dog()
    assert dog.name == "Buddy"
    assert dog.age == 5

    # Test serialization
    assert dog.model_dump() == {"name": "Buddy", "age": 5}


def test_registry_lookup():
    """Test registry lookup functionality."""

    class Pet(BaseModel):
        name: str
        age: int

    class Labrador(Pet):
        name: str = "Buddy"
        age: int = 5

    class Tabby(Pet):
        name: str = "Whiskers"
        age: int = 3

    # Test registry lookup
    LabradorClass = Pet["labrador"]
    assert LabradorClass is Labrador

    # Create via registry
    buddy = Pet["labrador"](name="Max", age=3)
    assert buddy.name == "Max"
    assert buddy.age == 3


def test_registry_lookup_with_custom_values():
    """Test creating instances via registry lookup with custom values."""

    class Vehicle(BaseModel):
        wheels: int
        engine: str

    class Car(Vehicle):
        wheels: int = 4
        engine: str = "V6"

    class Motorcycle(Vehicle):
        wheels: int = 2
        engine: str = "Single Cylinder"

    # Create via registry lookup
    CarClass = Vehicle["car"]
    car = CarClass()
    assert car.wheels == 4
    assert car.engine == "V6"

    # Create with custom values
    custom_car = Vehicle["car"](wheels=6, engine="V8")
    assert custom_car.wheels == 6
    assert custom_car.engine == "V8"


def test_pydantic_validation():
    """Test that Pydantic validation still works."""

    class Product(BaseModel):
        name: str
        price: float

    class Laptop(Product):
        name: str = "MacBook"
        price: float = 1999.99

    # Valid creation
    laptop = Laptop()
    assert laptop.price == 1999.99

    # Invalid type should raise ValidationError
    with pytest.raises(ValidationError):
        Laptop(name="Dell", price="not a number")


def test_no_registry_methods_in_instance_dict():
    """Test that Registry methods don't pollute instance __dict__."""

    class Item(BaseModel):
        value: int

    class Sword(Item):
        value: int = 100

    sword = Sword()

    # Registry methods should NOT be in instance __dict__
    assert "clear" not in sword.__dict__
    assert "get" not in sword.__dict__
    assert "keys" not in sword.__dict__
    assert "values" not in sword.__dict__
    assert "items" not in sword.__dict__

    # Only actual fields should be there
    assert "value" in sword.__dict__


def test_model_dump_no_registry_methods():
    """Test that model_dump() doesn't include Registry methods."""

    class Character(BaseModel):
        health: int
        mana: int

    class Wizard(Character):
        health: int = 80
        mana: int = 150

    wizard = Wizard()
    data = wizard.model_dump()

    # Should only have actual fields
    assert set(data.keys()) == {"health", "mana"}
    assert data == {"health": 80, "mana": 150}


def test_class_level_registry_methods():
    """Test that Registry methods work at class level."""

    class Shape(BaseModel):
        sides: int

    class Triangle(Shape):
        sides: int = 3

    class Square(Shape):
        sides: int = 4

    # Class-level dict methods should work
    assert "triangle" in Shape
    assert len(Shape) == 2
    assert set(Shape.keys()) == {"triangle", "square"}
    assert Shape["triangle"] is Triangle
    assert Shape["square"] is Square


def test_abstract_methods():
    """Test that abstract methods work correctly."""

    class Pokemon(BaseModel):
        health: int

        @abstractmethod
        def attack(self, target) -> int:
            pass

    class Pikachu(Pokemon):
        health: int = 100

        def attack(self, target):
            return 5

    class Charmander(Pokemon):
        health: int = 90

        def attack(self, target):
            return 4

    # Test that abstract class can't be instantiated
    # Note: Pydantic models can't truly be abstract, but we can test our types work
    pikachu = Pikachu()
    assert pikachu.attack("Bulbasaur") == 5

    charmander = Charmander()
    assert charmander.attack("Squirtle") == 4


def test_inheritance_chain():
    """Test multiple levels of inheritance."""

    class Base(BaseModel):
        id: int

    class Middle(Base):
        id: int = 1
        name: str = "middle"

    class Leaf(Middle):
        id: int = 2
        name: str = "leaf"
        extra: str = "data"

    # All should be registered
    assert "middle" in Base
    assert "leaf" in Base
    assert "leaf" in Middle

    # Create instance
    leaf = Leaf()
    assert leaf.model_dump() == {"id": 2, "name": "leaf", "extra": "data"}


def test_config_options():
    """Test that Registry config options still work."""

    class Fruit(BaseModel, snake_case=True):  # type: ignore[call-arg]
        color: str

    class RedApple(Fruit):
        color: str = "red"

    class GreenApple(Fruit):
        color: str = "green"

    # snake_case should convert RedApple -> red_apple
    assert "red_apple" in Fruit
    assert "green_apple" in Fruit
    assert list(Fruit) == ["red_apple", "green_apple"]


def test_optional_fields():
    """Test Pydantic optional fields."""

    class Task(BaseModel):
        name: str
        priority: int = 1

    class UrgentTask(Task):
        name: str = "Urgent"
        priority: int = 10

    class NormalTask(Task):
        name: str = "Normal"

    urgent = UrgentTask()
    normal = NormalTask()

    assert urgent.model_dump() == {"name": "Urgent", "priority": 10}
    assert normal.model_dump() == {"name": "Normal", "priority": 1}


def test_manual_metaclass():
    """Test that the manual metaclass approach still works for advanced use cases."""
    from pydantic import BaseModel as PydanticBaseModel

    from autoregistry import Registry
    from autoregistry.pydantic import PydanticRegistryMeta

    class Animal(PydanticBaseModel, Registry, metaclass=PydanticRegistryMeta):
        name: str

    class Dog(Animal):
        name: str = "Buddy"

    assert "dog" in Animal
    dog = Dog()
    assert dog.model_dump() == {"name": "Buddy"}


def test_dict_method_field_names():
    """Test that user fields with DICT_METHODS names work correctly.

    Users can define Pydantic fields with names that match Registry's DICT_METHODS
    (keys, values, items, get, clear). The PydanticRegistryMeta metaclass properly
    handles this by:
    1. Suppressing misleading Pydantic warnings during class creation
    2. Cleaning up conflicting method defaults from model_fields
    3. Rebuilding the Pydantic schema with correct user field definitions

    Result: Fields work on instances, methods work on classes - no conflicts.
    """

    class Config(BaseModel, snake_case=True):  # type: ignore[call-arg]
        keys: int
        values: str
        items: float

    class ServerConfig(Config):
        keys: int = 10
        values: str = "production"
        items: float = 3.14

    class ClientConfig(Config):
        keys: int = 5
        values: str = "development"
        items: float = 2.71

    # Test AutoRegistry functionality at class level
    assert "server_config" in Config
    assert "client_config" in Config
    assert set(Config.keys()) == {"server_config", "client_config"}  # type: ignore[misc]

    # Test instance creation and field access
    server = ServerConfig()
    assert server.keys == 10
    assert server.values == "production"
    assert server.items == 3.14

    # Test that instance fields are real fields, not dict methods
    assert "keys" in server.__dict__
    assert "values" in server.__dict__
    assert "items" in server.__dict__

    # Test serialization includes the fields
    data = server.model_dump()
    assert data == {"keys": 10, "values": "production", "items": 3.14}

    # Test creating with custom values
    custom = Config["server_config"](keys=20, values="staging", items=1.23)
    assert custom.keys == 20
    assert custom.values == "staging"
    assert custom.items == 1.23


def test_all_dict_method_field_names():
    """Test that all DICT_METHODS names can be used as field names.

    All Registry DICT_METHODS ('get', 'clear', 'keys', 'values', 'items') can be
    used as Pydantic field names. The implementation properly separates user fields
    from registry methods, keeping both functional at their appropriate levels
    (fields on instances, methods on classes).
    """

    class Storage(BaseModel, snake_case=True):  # type: ignore[call-arg]
        get: str
        clear: int
        keys: List[str]
        values: List[int]
        items: Dict[str, int]

    class DiskStorage(Storage):
        get: str = "disk"
        clear: int = 1
        keys: List[str] = ["a", "b"]
        values: List[int] = [1, 2]
        items: Dict[str, int] = {"x": 1}

    # Test registry functionality
    assert "disk_storage" in Storage
    disk = DiskStorage()

    # All fields should be accessible as instance attributes
    assert disk.get == "disk"
    assert disk.clear == 1
    assert disk.keys == ["a", "b"]
    assert disk.values == [1, 2]
    assert disk.items == {"x": 1}

    # Fields should be in __dict__
    assert "get" in disk.__dict__
    assert "clear" in disk.__dict__
    assert "keys" in disk.__dict__
    assert "values" in disk.__dict__
    assert "items" in disk.__dict__

    # Registry methods should still work at class level
    assert Storage.get("disk_storage") is DiskStorage  # type: ignore[misc]
    assert list(Storage.keys()) == ["disk_storage"]  # type: ignore[misc]


def test_non_dict_method_shadowing_warnings_still_appear():
    """Test that shadowing warnings for non-DICT_METHODS still appear.

    Our warning suppression should ONLY apply to DICT_METHODS (keys, values,
    items, get, clear). If users shadow their own custom methods, they should
    still see Pydantic's warnings.
    """
    import warnings

    # Create a base with a custom method
    class MyBase(BaseModel):
        name: str

        def custom_method(self):
            return "custom"

    # Shadowing a custom method should still produce a warning
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        class MyModel(MyBase):
            name: str = "test"
            custom_method: str  # Shadow our custom method

        # Should have exactly 1 warning about shadowing custom_method
        assert len(w) == 1
        assert "custom_method" in str(w[0].message)
        assert "shadows an attribute" in str(w[0].message)


def test_mixed_dict_method_and_regular_fields():
    """Test models with both DICT_METHODS names and regular fields.

    Pydantic models can freely mix fields with DICT_METHODS names ('get', 'items')
    and regular field names ('name', 'count'). All fields work correctly regardless
    of whether their names conflict with Registry's dict-like methods.
    """

    class Resource(BaseModel, snake_case=True):  # type: ignore[call-arg]
        name: str
        get: str
        count: int
        items: List[str]

    class ApiResource(Resource):
        name: str = "api"
        get: str = "GET"
        count: int = 100
        items: List[str] = ["item1", "item2"]

    resource = ApiResource()

    assert resource.name == "api"
    assert resource.get == "GET"
    assert resource.count == 100
    assert resource.items == ["item1", "item2"]

    assert resource.model_dump() == {
        "name": "api",
        "get": "GET",
        "count": 100,
        "items": ["item1", "item2"],
    }

    # Registry should still work
    assert "api_resource" in Resource
    assert Resource["api_resource"] is ApiResource


def test_same_name_classes_no_key_collision():
    """Test that two classes with the same name can be registered without KeyCollisionError."""

    class User(BaseModel):  # type: ignore[reportGeneralTypeIssues]
        name: str

        # Should not raise a KeyCollisionError

    class User(BaseModel):  # noqa: F811
        id: int
