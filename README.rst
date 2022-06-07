.. image:: https://raw.githubusercontent.com/BrianPugh/autoregistry/main/assets/logo_400w.png

|Python compat| |PyPi| |GHA tests| |Codecov report| |readthedocs|

.. inclusion-marker-do-not-remove

AutoRegistry
============

Invoking functions and class-constructors from a string is a common design pattern
that AutoRegistry aims to solve.
For example, a user might specify a backend of type ``"sqlite"`` in a yaml configuration
file, for which our program needs to construct the ``SQLite`` subclass of our ``Database`` class.
Classically, you would need to manually create a lookup, mapping the string ``"sqlite"`` to
the ``SQLite`` constructor.
With AutoRegistry, the lookup is automatically created for you.


AutoRegistry has a single  powerful class ``Registry`` that can do the following:

* Be inherited to automatically register subclasses by their name.

* Be directly invoked ``my_registery = Registry()`` to create a decorator
  for registering callables like functions.

* Traverse and automatically create registries for other python libraries.

.. inclusion-marker-remove

Installation
============
AutoRegistry requires Python ``>=3.8``.

.. code-block:: bash

   python -m pip install autoregistry


Examples
========

Class Inheritance
^^^^^^^^^^^^^^^^^

``Registry`` adds a dictionary-like interface to class constructors
for looking up subclasses.

.. code-block:: python

   from abc import abstractmethod
   from dataclasses import dataclass
   from autoregistry import Registry


   @dataclass
   class Pokemon(Registry):
       level: int
       hp: int

       @abstractmethod
       def attack(self, target):
           """Attack another Pokemon."""


   class Charmander(Pokemon):
       def attack(self, target):
           return 1


   class Pikachu(Pokemon):
       def attack(self, target):
           return 2


   class SurfingPikachu(Pikachu):
       def attack(self, target):
           return 3


   print(f"{len(Pokemon)} Pokemon types registered:")
   print(f"    {list(Pokemon)}")
   # By default, lookup is case-insensitive
   charmander = Pokemon["cHaRmAnDer"](level=7, hp=31)
   print(f"Created Pokemon: {charmander}")

This code block produces the following output:

.. code-block::

   3 Pokemon types registered:
       ['charmander', 'pikachu', 'surfingpikachu']
   Created Pokemon: Charmander(level=7, hp=31)


Function Registry
^^^^^^^^^^^^^^^^^

Directly instantiating a ``Registry`` object allows you to
register functions by decorating them.

.. code-block:: python

   from autoregistry import Registry

   pokeballs = Registry()


   @pokeballs
   def masterball(target):
       return 1.0


   @pokeballs
   def pokeball(target):
       return 0.1


   for ball in ["pokeball", "masterball"]:
       success_rate = pokeballs[ball](None)
       print(f"Ash used {ball} and had {success_rate=}")

This code block produces the following output:

.. code-block:: text

   Ash used pokeball and had success_rate=0.1
   Ash used masterball and had success_rate=1.0


Module Registry
^^^^^^^^^^^^^^^

Create a registry for another python module.

.. code-block:: python

   import torch
   from autoregistry import Registry

   optims = Registry(torch.optim)

   # "adamw" and ``lr`` could be coming from a configuration file.
   optimizer = optims["adamw"](model.parameters(), lr=3e-3)

   assert list(optims) == [
       "asgd",
       "adadelta",
       "adagrad",
       "adam",
       "adamw",
       "adamax",
       "lbfgs",
       "nadam",
       "optimizer",
       "radam",
       "rmsprop",
       "rprop",
       "sgd",
       "sparseadam",
       "lr_scheduler",
       "swa_utils",
   ]


.. |GHA tests| image:: https://github.com/BrianPugh/autoregistry/workflows/tests/badge.svg
   :target: https://github.com/BrianPugh/autoregistry/actions?query=workflow%3Atests
   :alt: GHA Status
.. |Codecov report| image:: https://codecov.io/github/BrianPugh/autoregistry/coverage.svg?branch=main
   :target: https://codecov.io/github/BrianPugh/autoregistry?branch=main
   :alt: Coverage
.. |readthedocs| image:: https://readthedocs.org/projects/autoregistry/badge/?version=latest
        :target: https://autoregistry.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status
.. |Python compat| image:: https://img.shields.io/badge/>=python-3.8-blue.svg
.. |PyPi| image:: https://img.shields.io/pypi/v/autoregistry.svg
        :target: https://pypi.python.org/pypi/autoregistry
