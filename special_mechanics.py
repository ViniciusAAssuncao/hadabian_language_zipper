import hashlib
import random
from typing import Dict


class SuffixReplacementHandler:
    def __init__(self, config: Dict):
        self.percentage = config.get('percentage', 100)
        self.suffixes = config.get('suffixes', [])

    def apply(self, word: str, original_lemma: str, seed: int) -> str:
        if not self.suffixes:
            return word
        hash_input = f"{original_lemma}_suffix_replacement_{seed}"
        hash_val = int(hashlib.sha256(hash_input.encode()).hexdigest(), 16)
        if (hash_val % 100) >= self.percentage:
            return word
        rng = random.Random(hash_val)
        chosen_suffix = rng.choice(self.suffixes)
        if chosen_suffix.startswith('-'):
            chosen_suffix = chosen_suffix[1:]
        suffix_len = len(chosen_suffix)
        if len(word) > suffix_len:
            return word[:-suffix_len] + chosen_suffix
        else:
            return word[:1] + chosen_suffix


class SpecialMechanicsHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.mechanics = profile.get('special_mechanics', {})
        self.enabled = bool(self.mechanics)
        self.handlers = []
        for key, config in self.mechanics.items():
            if config.get('type') == 'suffix_replacement':
                self.handlers.append(SuffixReplacementHandler(config))

    def apply_mechanics(self, word: str, original_lemma: str, seed: int) -> str:
        if not self.enabled or not word:
            return word
        current_word = word
        for handler in self.handlers:
            current_word = handler.apply(current_word, original_lemma, seed)
        return current_word
