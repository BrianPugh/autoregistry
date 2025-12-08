Pydantic Integration
====================

AutoRegistry provides a drop-in replacement for pydantic's :class:`pydantic:pydantic.BaseModel` class.

Basic Usage
-----------

.. code-block:: python

   from autoregistry.pydantic import BaseModel


   class Pokemon(BaseModel):
       health: int


   class Pikachu(Pokemon):
       health: int = 100


   class Charmander(Pokemon):
       health: int = 90

This gives you both AutoRegistry and Pydantic features:

.. code-block:: pycon

   >>> # AutoRegistry features work at the CLASS level
   >>> list(Pokemon)
   ['pikachu', 'charmander']
   >>> Pokemon["pikachu"]
   <class '__main__.Pikachu'>

   >>> # Pydantic features work at the INSTANCE level
   >>> pikachu = Pikachu()
   >>> pikachu.model_dump()
   {'health': 100}
   >>> pikachu.health
   100

Configuration Options
^^^^^^^^^^^^^^^^^^^^^

All of AutoRegistry's configuration options work with Pydantic models:

.. code-block:: python

   from autoregistry.pydantic import BaseModel


   class Fruit(BaseModel, snake_case=True):
       color: str


   class RedApple(Fruit):
       color: str = "red"


   class GreenApple(Fruit):
       color: str = "green"

.. code-block:: pycon

   >>> # snake_case converts RedApple -> red_apple
   >>> list(Fruit)
   ['red_apple', 'green_apple']

See :ref:`Configuration` for all available options.

How it Works
------------

The integration uses multiple inheritance and a custom metaclass:

.. code-block:: python

   from pydantic import BaseModel as PydanticBaseModel
   from autoregistry import Registry
   from autoregistry.pydantic import PydanticRegistryMeta


   class BaseModel(PydanticBaseModel, Registry, metaclass=PydanticRegistryMeta, base=True):
       """Base class combining Pydantic's BaseModel with AutoRegistry."""

The :class:`PydanticRegistryMeta` metaclass merges both Pydantic's and AutoRegistry's metaclasses, ensuring registry dict-like methods (like ``keys()``, ``items()``) operate at the class level while Pydantic's validation works at the instance level.

The ``base=True`` parameter marks this as a base registry class, so subclasses will **not** be registered to ``BaseModel`` itself (see :ref:`base <base>` for details).

This is actually how :class:`autoregistry.pydantic.BaseModel` is exactly defined (no body!). **All** logic is within :class:`PydanticRegistryMeta`; :class:`autoregistry.pydantic.BaseModel` only responsibility is to combine these class/metaclass definitions so that inheritance is correct.
