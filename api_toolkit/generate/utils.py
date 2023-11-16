import re
from itertools import combinations
from typing import Sequence, TypeVar


def name_convert_to_snake(name: str) -> str:
    return re.sub(r'([a-z])([A-Z])', r'\1_\2', name).lower()


def plural(word: str) -> str:
    rules = [
        (r'([bcdfghjklmnpqrstvwxz])y$', r'\1ies'),
        (r'(s|x|z|ch|sh)$', r'\1es'),
        (r'([^aeiou])o$', r'\1oes'),
        (r'$', r's')
    ]

    for pattern, replacement in rules:
        if re.search(pattern, word):
            return re.sub(pattern, replacement, word)

    return word


T = TypeVar('T')


def get_combinations(arr: Sequence[T]) -> Sequence[Sequence[T]]:
    result = []
    for r in range(1, len(arr) + 1):
        for combination in combinations(arr, r):
            result.append(combination)
    return result
