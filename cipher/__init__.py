"""Cipher implementations: the reversible transformations themselves.

Each module here exposes the same shape - ``encrypt``, ``decrypt`` and a key
validator - so adding a third cipher (Affine, Playfair) means adding a module,
not editing existing ones. That is the Open/Closed principle in practice.
"""

from cipher import caesar, vigenere  # noqa: F401

__all__ = ["caesar", "vigenere"]
