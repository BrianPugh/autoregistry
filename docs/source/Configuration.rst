.. _Configuration:

Configuration
=============

Configuring Inheritance
^^^^^^^^^^^^^^^^^^^^^^^

When inheriting from the :class:`Registry` class, keyword configuration values can be passed
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

Configuring Decorator
^^^^^^^^^^^^^^^^^^^^^
When directly declaring a :class:`Registry`, configurations are passed as keyword arguments
when instantiating the :class:`Registry` object:

.. code-block:: python

   readers = Registry(suffix="_read")


   @readers
   def yaml_read(fn):
       pass


   @readers()  # This also works.
   def json_read(fn):
       pass


   # it's just "json" instead of "json_read" because we strip the suffix by default.
   data = readers["json"]("my_file.json")


Name Override and Aliases
^^^^^^^^^^^^^^^^^^^^^^^^^
There are two special configuration values: ``name`` and ``aliases``.
``name`` overrides the auto-derived string to register the class/function under, while
``aliases`` registers *additional* string(s) to the class/function, but
doesn't impact the auto-derived registration key.
``aliases`` may be a single string, or a list of strings.

``name`` and ``aliases`` values are **not** subject to configured naming rules and will **not** be modified
by configurations like ``strip_suffix``.
Similarly, directly setting a registry element ``my_registry["myfunction"] = myfunction`` is not subject to naming rules.
However, values are still subject to the ``overwrite`` configuration and will raise :exc:`.KeyCollisionError` if
``name`` or ``aliases`` attempts to overwrite an existing entry while ``overwrite=False``.
Additionally, ``name`` and ``aliases`` may **not** contain a  ``.`` or a ``/`` due to :ref:`Key Splitting`.

These parameters are intended to aid developers maintain backwards compatibility as their codebase changes.

Inheritance
-----------

Name and aliases are provided as additional class keyword arguments.

.. code-block:: python

   class Pokemon(Registry):
       pass


   class Ekans(name="snake"):
       pass


   class Pikachu(aliases=["electricmouse"]):
       pass


   my_pokemon = []
   # Pokemon["ekans"] will raise a KeyError
   my_pokemon.append(Pokemon["snake"]())
   my_pokemon.append(Pokemon["pikachu"]())
   my_pokemon.append(Pokemon["electricmouse"]())

To not register a subclass to the appropriate registry(s), set the parameter ``skip=True``.

.. code-block:: python

    class Sensor(Registry):
        pass


    class Oxygen(Sensor, skip=True):
        pass


    class Temperature(Sensor):
        pass


    assert list(Sensor.keys()) == ["temperature"]


Decorator
---------

Name and aliases are provided as additional decorator keyword arguments.

.. code-block:: python

   registry = Registry()


   @registry(name="foo")
   def foo2():
       pass


   @registry(aliases=["baz", "bop"])
   def bar():
       pass


   assert list(registry) == ["foo", "bar", "baz", "bop"]


Parameters
^^^^^^^^^^
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


regex: str = ""
---------------
Registered items **MUST** match this regular expression.
If a registered item does **NOT** match this regex, ``InvalidNameError`` will be raised.

.. code-block:: python

   # Capital letters only
   registry = Registry(regex="[A-Z]+", case_sensitive=True)


   @registry
   def FOO():
       pass


   # This will raise an InvalidNameError, because the supplied regex only allows for capital letters.
   @registry
   def bar():
       pass


   assert list(registry) == ["FOO"]


prefix: str = ""
----------------
Registered items **MUST** start with this prefix.
If a registered item does **NOT** start with this prefix, ``InvalidNameError`` will be raised.

.. code-block:: python

   class Sensor(Registry, prefix="Sensor"):
       pass


   # This will raise an InvalidNameError because the class name doesn't start with "Sensor"
   class Temperature(Sensor):
       pass


   class SensorTemperature(Sensor):
       pass


suffix: str = ""
----------------
Registered items **MUST** end with this suffix.
If a registered item does **NOT** end with this suffix, ``InvalidNameError`` will be raised.

.. code-block:: python

   class Sensor(Registry, suffix="Sensor"):
       pass


   # This will raise an InvalidNameError because the class name doesn't end with "Sensor"
   class Temperature(Sensor):
       pass


   class TemperatureSensor(Sensor):
       pass


strip_prefix: bool = True
-------------------------
If ``True``, the ``prefix`` will be removed from registered items.
This generally allows for a more natural lookup.

.. code-block:: python

   class Sensor(Registry, prefix="Sensor", strip_prefix=True):
       pass


   class SensorTemperature(Sensor):
       pass


   class SensorHumidity(Sensor):
       pass


   assert list(Sensor) == ["temperature", "humidity"]
   my_temperature_sensor = Sensor["temperature"]()


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

Consider the following more complicated situation:

.. code-block:: python

    class ClassA(Registry, recursive=False):
        pass


    class ClassB(ClassA):
        pass


    class ClassC(ClassB, recursive=True):
        pass


    class ClassD(ClassC):
        pass


    class ClassE(ClassD):
        pass

The registries and configurations are as follows:

* ``ClassA`` has ``recursive=False``, and contains ``["classb"]``, its only direct child.

* ``ClassB`` inherits ``recursive=False``, and contains ``["classc"]``, its only direct child.

* ``ClassC`` overrides ``recursive=True``, and contains all of its children ``["classd", "classe"]``

* ``ClassD`` inherits ``recursive=True``, and contains its child ``["classe"]``.

* ``ClassE`` inherits ``recursive=True``, and is empty since it has no children.


snake_case: bool = False
------------------------
By default, for case-insensitive queries, the key is derived
by taking the all-lowercase version of the class name.
If ``snake_case=True``, the PascalCase class names will be
instead converted to snake_case.

Snake case conversion is performed *after* name validation (like ``prefix`` and ``suffix``) checks are performed.

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
a **different** existing registered item would result in a :exc:`.KeyCollisionError`.
Registering the same object to the same key **will not** raise a :exc:`.KeyCollisionError`.
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


hyphen: bool = False
--------------------
Converts all underscores to hyphens.

.. code-block:: python

   tools = Registry(hyphen=True)


   @registry
   def ballpeen_hammer():
       pass


   @registry
   def socket_wrench():
       pass


   assert list(Tools) == ["ballpeen-hammer", "socket-wrench"]

Can be used in conjunction with ``snake_case``.

.. code-block:: python

   class Tools(Registry, snake_case=True, hyphen=True):
       pass


   class Hammer(Tools):
       pass


   class SocketWrench(Tools):
       pass


   assert list(Tools) == ["hammer", "socket-wrench"]

transform: Optional[Callable] = None
------------------------------------
Provide a custom function to modify the registry for a given function/class name.
Must that in a single string argument, and return a string.
The ``transform`` is called as the **final** name processing step, after all other
transforms like ``snake_case`` and ``hyphen``.

.. code-block::

   def transform(name: str) -> str:
       return f"shiny_{name}"


   class Pokemon(Registry, transform=transform, snake_case=True):
       pass


   class Pikachu(Pokemon):
       pass


   class SurfingPikachu(Pokemon):
       pass


   assert list(Pokemon) == [
       "shiny_pikachu",
       "shiny_surfing_pikachu",
   ]


redirect: bool = True
---------------------
If ``redirect=True``, then methods that would have collided with the dict-like
registry interface are wrapped in a redirect object.
The redirect object will invoke registry methods if called from the class, e.g.
``MyClass.keys()``, but will call the user-defined method if called from an
instantiated object, e.g. ``my_class.keys()``.
Methods decorated with ``@classmethod`` or ``@staticmethod`` will not be wrapped;
they will override the dict-like registry interface.


.. code-block:: python

   class Foo(Registry):
       def keys(self):
           return 0


   class Bar(Foo):
       pass


   foo = Foo()
   assert list(Foo.keys()) == ["bar"]
   assert foo.keys() == 0
