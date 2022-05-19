.. _Configuration:

Configuration
=============

Configuring Inheritence-Based
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When inheriting from the ``Registry`` class, keyword configuration values can be passed
along side it when defining the subclass. For example:


.. code-block:: python

   class Pokemon(Registry, case_sensitive=True):
       pass

Each subclass registry will copy the configuration of its parent,
and update it with newly passed in values. For example:

.. code-block:: python

 class Pokemon(Registry, suffix="Type", recursive=False):
     pass


 class RockType(Pokemon, suffix=""):
     pass


 class Geodude(RockType):
     pass


 # it's just "rock" instead of "rocktype" because we strip the suffix by default.
 geodude = Pokemon["rock"]["geodude"]()

All direct children of ``Pokemon`` MUST end with ``"Type"``.
Children of ``RockType`` will NOT be registered with ``RockType``'s parent, ``Pokemon``
because ``recursive=False`` is set.
For ``RockType``, setting ``suffix=""`` overrides its parent's
``suffix`` setting, allowing the definition of the subclass ``Geodude``,
despite it not ending with ``"Type"``.


Configuring Decorator-Based
^^^^^^^^^^^^^^^^^^^^^^^^^^^
When directly declaring a ``Registry``, the configurations are passed directly as keyword arguments:

.. code-block:: python

   readers = Registry(suffix="_read")


   @readers
   def yaml_read(fn):
       pass


   @readers
   def json_read(fn):
       pass


   # it's just "json" instead of "json_read" because we strip the suffix by default.
   data = readers["json"]("my_file.json")


Configurations
^^^^^^^^^^^^^^
This section describes and provides examples for all of the configurable options
in ``autoregistry``.


case_sensitive: bool = False
----------------------------
If ``True``, all lookups are case-sensitive.
Otherwise, all lookups are case-insensitive.
A failed lookup will result in a ``KeyError``.

.. code-block:: python

   class Pokemon(Registry, case_sensitive=False):
       pass


   class Pikachu(Pokemon):
       pass


   class SurfingPikachu(Pokemon):
       pass


   assert list(Pokemon) == ["pikachu", "surfingpikachu"]
   assert list(Pikachu) == ["surfingpikachu"]
   pikachu = Pokemon["piKaCHu"]()


.. code-block:: python

   class Pokemon(Registry, case_sensitive=True):
       pass


   class Pikachu(Pokemon):
       pass


   class SurfingPikachu(Pokemon):
       pass


   assert list(Pokemon) == ["Pikachu", "SurfingPikachu"]
   assert list(Pikachu) == ["SurfingPikachu"]
   pikachu = Pokemon["Pikachu"]()

   # This will raise a KeyError due to the lowercase "p".
   pikachu = Pokemon["pikachu"]()


suffix: str = ""
----------------
Registered items **MUST** end with this suffix.
If a registered item does **NOT** end with this suffix, ``InvalidNameError``
will be raised.

.. code-block:: python

   class Sensor(Registry, suffix="Sensor"):
       pass


   # This will raise an InvalidNameError because the class name doesn't end with "Sensor"
   class Temperature(Sensor):
       pass


   class TemperatureSensor(Sensor):
       pass


strip_suffix: bool = True
-------------------------
If ``True``, the ``suffix`` will be removed from registered items.
This generally allows for a more natural lookup.

.. code-block:: python

   class Sensor(Registry, suffix="Sensor", strip_suffix=True):
       pass


   class TemperatureSensor(Sensor):
       pass


   class HumiditySensor(Sensor):
       pass


   assert list(Sensor) == ["temperature", "humidity"]
   my_temperature_sensor = Sensor["temperature"]()


register_self: bool = False
---------------------------
If ``True``, each registry class is registered in its own registry.

.. code-block:: python

   class Pokeball(Registry, register_self=True):
       def probability(self, target):
           return 0.2


   class Masterball(Pokeball):
       def probability(self, target):
           return 1.0


   assert list(Pokeball) == ["pokeball", "masterball"]


recursive: bool = True
----------------------
If ``True``, all subclasses will be recursively registered to their parents.
If registering a ``module``, this means all submodules will be recursively traversed.

.. code-block:: python

   class Pokemon(Registry, recursive=True):
       pass


   class Pikachu(Pokemon):
       pass


   class SurfingPikachu(Pokemon):
       pass


   assert list(Pokemon) == ["pikachu", "surfingpikachu"]
   assert list(Pikachu) == ["surfingpikachu"]


.. code-block:: python

   class Pokemon(Registry, recursive=False):
       pass


   class Pikachu(Pokemon):
       pass


   class SurfingPikachu(Pokemon):
       pass


   assert list(Pokemon) == ["pikachu"]
   assert list(Pikachu) == ["surfingpikachu"]


snake_case: bool = False
------------------------
By default, for case-insensitive queries, the key is derived
by taking the all-lowercase version of the class name.
If ``snake_case=True``, the PascalCase class names will be
instead converted to snake_case.

.. code-block:: python

   class Tools(Registry, snake_case=True):
       pass


   class Hammer(Tools):
       pass


   class SocketWrench(Tools):
       pass


   assert list(Tools) == ["hammer", "socket_wrench"]


overwrite: bool = False
-----------------------
If ``overwrite=False``, attempting to register an object that would overwrite
an existing registered item would result in a ``KeyCollisionError``.
If ``overwrite=True``, then the previous entry will be overwritten and no
exception will be raised.

.. code-block:: python

   registry = Registry()


   @registry
   def foo():
       pass


   # This will raise a ``KeyCollisionError``
   @registry
   def foo():
       pass

.. code-block:: python

   registry = Registry(overwrite=True)


   @registry
   def foo():
       return 1


   @registry
   def foo():
       return 2


   assert registry["foo"]() == 2
