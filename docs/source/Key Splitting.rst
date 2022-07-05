.. _Key Splitting:

Key Splitting
=============
Consider the following code example:

.. code-block:: python

   class Pokemon(Registry, case_sensitive=False):
       pass


   class Pikachu(Pokemon):
       pass


   class SurfingPikachu(Pokemon):
       pass

We can naively access the ``SurfingPikachu`` constructor via
``Pokemon["pikachu"]["surfingpikachu"]``.
We can also access the same constructor using dot or slash
notation from a single string. The query string will be split
on dots and dashes, and iteratively queried:

.. code-block:: python

   assert SurfingPikachu == Pokemon["pikachu"]["surfingpikachu"]
   assert SurfingPikachu == Pokemon["pikachu.surfingpikachu"]
   assert SurfingPikachu == Pokemon["pikachu/surfingpikachu"]
