import random

DEFAULT_RNG = random.Random()
"""Shared generator for anything that doesn't need to be seeded."""


def resolve_rng(rng: random.Random | None = None):
    return rng or DEFAULT_RNG
