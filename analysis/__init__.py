"""Cryptanalysis: the code that attacks the ciphers without a key.

Separated from :mod:`cipher` on purpose. The ciphers know nothing about the
attacks, and the attacks depend on the ciphers only through their public
``encrypt``/``decrypt`` functions.
"""
