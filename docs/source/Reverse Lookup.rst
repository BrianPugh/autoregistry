Reverse Lookup
==============
Consider the following class hierarchy:

.. code-block:: python

   class Pokemon(Registry, case_sensitive=False):
       pass


   class Pikachu(Pokemon):
       pass


   class SurfingPikachu(Pokemon):
       pass


Subclasses can be accessed via the standard AutoRegistry indexing, i.e:

.. code-block:: python

   assert Pokemon["pikachu"] == Pikachu

To perform the reverse-lookup, i.e. obtain the string ``"pikachu"`` from the
class ``Pikachu``, access the ``__registry_name__`` attribute:

.. code-block:: python

   assert Pikachu.__registry_name__ == "pikachu"
