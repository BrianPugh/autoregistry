.. image:: assets/logo_400w.png

|GHA tests| |Codecov report| |readthedocs|

.. inclusion-marker-do-not-remove

autoregistry
==============

autoregistry is a


Features
========

Installation
============

.. code-block:: bash

   python -m pip install autoregistry


Usage
=====

Class Inheritence
^^^^^^^^^^^^^^^^^

.. code-block:: python

   from dataclasses import dataclass
   from autoregistry import Registry, abstractmethod


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


   print("")
   print(f"{len(Pokemon)} Pokemon registered:")
   print(f"    {list(Pokemon.keys())}")
   # By default, lookup is case-insensitive
   charmander = Pokemon["cHaRmAnDer"](level=7, hp=31)
   print(f"Created Pokemon: {charmander}")
   print("")

This code block produces the following output:

.. code-block::

   3 Pokemon registered:
       ['charmander', 'pikachu', 'surfingpikachu']
   Created Pokemon: Charmander(level=7, hp=31)


Function Registry
^^^^^^^^^^^^^^^^^

.. code-block:: python

   from autoregistry import Registry

   pokeballs = Registry()


   @pokeballs
   def masterball(target):
       return 1.0


   @pokeballs
   def pokeball(target):
       return 0.1


   print("")
   for ball in ["pokeball", "masterball"]:
       success_rate = pokeballs[ball](None)
       print(f"Ash used {ball} and had {success_rate=}")
   print("")

This code block produces the following output:

.. code-block::

   Ash used pokeball and had success_rate=0.1
   Ash used greatball and had success_rate=0.3
   Ash used ultraball and had success_rate=0.5
   Ash used masterball and had success_rate=1.0


.. |GHA tests| image:: https://github.com/BrianPugh/autoregistry/workflows/tests/badge.svg
   :target: https://github.com/BrianPugh/autoregistry/actions?query=workflow%3Atests
   :alt: GHA Status
.. |Codecov report| image:: https://codecov.io/github/BrianPugh/autoregistry/coverage.svg?branch=main
   :target: https://codecov.io/github/BrianPugh/autoregistry?branch=main
   :alt: Coverage
.. |readthedocs| image:: https://readthedocs.org/projects/autoregistry/badge/?version=latest
        :target: https://autoregistry.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status
