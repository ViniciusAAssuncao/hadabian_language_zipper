import hashlib
import random
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict
import math


class SyllableGenerator:
    def __init__(self,
                 phoneme_inventory: Dict[str, List[str]],
                 phonotactic_constraints: Dict,
                 seed: int = 42):
        self.vowels = set(phoneme_inventory['vowels'])
        self.consonants = set(phoneme_inventory['consonants'])
        self.diphthongs = phoneme_inventory.get('diphthongs', [])
        self.constraints = phonotactic_constraints
        self.seed = seed
        self._rng = random.Random(seed)

        self.syllable_cache = {}

    def get_deterministic_hash(self, input_str: str, salt: str = "") -> int:
        combined = f"{input_str}_{salt}_{self.seed}"
        hash_value = hashlib.sha256(combined.encode()).hexdigest()
        return int(hash_value, 16)

    def generate_syllable(self, word_position: str = 'medial',
                          concept_seed: str = "",
                          syllable_index: int = 0) -> str:
        cache_key = f"{word_position}_{concept_seed}_{syllable_index}"
        if cache_key in self.syllable_cache:
            return self.syllable_cache[cache_key]

        hash_val = self.get_deterministic_hash(
            concept_seed, f"{word_position}_{syllable_index}")
        local_rng = random.Random(hash_val)

        template = local_rng.choice(self.constraints['syllable_templates'])

        syllable_parts = {
            'onset': '',
            'nucleus': '',
            'coda': ''
        }

        for char in template:
            if char == 'C':
                if not syllable_parts['nucleus']:
                    consonant = self._select_consonant(
                        local_rng, 'onset', word_position)
                    syllable_parts['onset'] += consonant
                else:
                    consonant = self._select_consonant(
                        local_rng, 'coda', word_position)
                    syllable_parts['coda'] += consonant
            elif char == 'V':
                vowel = self._select_vowel(local_rng, syllable_parts['onset'])
                syllable_parts['nucleus'] += vowel

        syllable = syllable_parts['onset'] + \
            syllable_parts['nucleus'] + syllable_parts['coda']

        syllable = self._apply_phonotactic_repairs(syllable, syllable_parts)

        self.syllable_cache[cache_key] = syllable
        return syllable

    def _select_consonant(self, rng: random.Random, position: str, word_position: str) -> str:
        available = list(self.consonants)

        if position == 'coda':
            forbidden = set(self.constraints.get('forbidden_codas', []))
            available = [c for c in available if c not in forbidden]

            if word_position == 'final':
                allowed_final = set(self.constraints['word_final_constraints'].get(
                    'allowed_final_consonants', available))
                available = [c for c in available if c in allowed_final]

        elif position == 'onset':
            forbidden = set(self.constraints.get('forbidden_onsets', []))
            available = [c for c in available if c not in forbidden]

            if word_position == 'initial':
                allowed_initial = set(self.constraints['word_initial_constraints'].get(
                    'allowed_initial_consonants', available))
                available = [c for c in available if c in allowed_initial]

        if not available:
            available = list(self.consonants)

        return rng.choice(available)

    def _select_vowel(self, rng: random.Random, onset: str = "") -> str:
        available = list(self.vowels)

        if rng.random() < 0.3 and self.diphthongs:
            valid_diphthongs = [d for d in self.diphthongs
                                if all(v in self.vowels for v in d if v.isalpha())]
            if valid_diphthongs:
                return rng.choice(valid_diphthongs)

        forbidden_nuclei = set(self.constraints.get('forbidden_nuclei', []))
        available = [v for v in available if v not in forbidden_nuclei]

        if not available:
            available = list(self.vowels)

        return rng.choice(available)

    def _apply_phonotactic_repairs(self, syllable: str, parts: Dict[str, str]) -> str:
        onset_len = len(parts['onset'])
        nucleus_len = len(parts['nucleus'])
        coda_len = len(parts['coda'])

        if onset_len > self.constraints['max_onset_consonants']:
            parts['onset'] = parts['onset'][:self.constraints['max_onset_consonants']]

        if coda_len > self.constraints['max_coda_consonants']:
            parts['coda'] = parts['coda'][:self.constraints['max_coda_consonants']]

        if nucleus_len > self.constraints['max_nucleus_vowels']:
            parts['nucleus'] = parts['nucleus'][:self.constraints['max_nucleus_vowels']]

        return parts['onset'] + parts['nucleus'] + parts['coda']


class WordGenerator:
    def __init__(self,
                 phoneme_inventory: Dict[str, List[str]],
                 phonotactic_constraints: Dict,
                 seed: int = 42):
        self.phoneme_inventory = phoneme_inventory
        self.constraints = phonotactic_constraints
        self.seed = seed
        self._rng = random.Random(seed)

        self.vowels = set(phoneme_inventory['vowels'])
        self.consonants = set(phoneme_inventory['consonants'])
        # --------------------------------------------

        self.syllable_generator = SyllableGenerator(
            phoneme_inventory,
            phonotactic_constraints,
            seed
        )

        self.word_cache = {}

    def generate_word(self, concept: str, semantic_features: Optional[Dict] = None) -> str:
        if concept in self.word_cache:
            return self.word_cache[concept]

        hash_val = self.syllable_generator.get_deterministic_hash(concept)
        local_rng = random.Random(hash_val)

        syllable_count = self._determine_syllable_count(
            concept, semantic_features, local_rng)

        syllables = []
        for i in range(syllable_count):
            if i == 0:
                position = 'initial'
            elif i == syllable_count - 1:
                position = 'final'
            else:
                position = 'medial'

            syllable = self.syllable_generator.generate_syllable(
                word_position=position,
                concept_seed=concept,
                syllable_index=i
            )
            syllables.append(syllable)

        word = ''.join(syllables)

        word = self._apply_phonological_processes(word, local_rng)

        self.word_cache[concept] = word
        return word

    def _determine_syllable_count(self, concept: str,
                                  semantic_features: Optional[Dict],
                                  rng: random.Random) -> int:
        min_syl = self.constraints.get('min_syllables_per_word', 1)
        max_syl = self.constraints.get('max_syllables_per_word', 4)

        concept_len = len(concept)
        if concept_len <= 4:
            base = min_syl
        elif concept_len <= 8:
            base = (min_syl + max_syl) // 2
        else:
            base = max_syl

        variation = rng.randint(-1, 1)
        final = max(min_syl, min(max_syl, base + variation))

        return final

    def _apply_phonological_processes(self, word: str, rng: random.Random) -> str:
        if rng.random() < 0.2:
            word = self._apply_assimilation(word, rng)

        if rng.random() < 0.15:
            word = self._apply_deletion(word, rng)

        if rng.random() < 0.1:
            word = self._apply_epenthesis(word, rng)

        return word

    def _apply_assimilation(self, word: str, rng: random.Random) -> str:
        if len(word) < 3:
            return word

        result = list(word)
        for i in range(len(result) - 1):
            if result[i] in self.consonants and result[i+1] in self.consonants:
                if rng.random() < 0.3:
                    if rng.choice([True, False]):
                        result[i] = result[i+1]
                    else:
                        result[i+1] = result[i]

        return ''.join(result)

    def _apply_deletion(self, word: str, rng: random.Random) -> str:
        if len(word) < 4:
            return word

        result = list(word)
        if result and result[-1] in self.vowels:
            if rng.random() < 0.5:
                result = result[:-1]

        return ''.join(result)

    def _apply_epenthesis(self, word: str, rng: random.Random) -> str:
        result = []
        vowels = list(self.vowels)

        for i, char in enumerate(word):
            result.append(char)
            if i < len(word) - 1:
                if char in self.consonants and word[i+1] in self.consonants:
                    if rng.random() < 0.3:
                        result.append(rng.choice(vowels))

        return ''.join(result)


class SemanticWordGenerator:
    def __init__(self,
                 word_generator: WordGenerator,
                 seed: int = 42):
        self.word_generator = word_generator
        self.seed = seed
        self._rng = random.Random(seed)

        self.semantic_categories = self._initialize_semantic_categories()
        self.derivational_affixes = self._initialize_affixes()

    def _initialize_semantic_categories(self) -> Dict[str, Dict]:
        return {
            'concrete_noun': {
                'preferred_length': 2,
                'allow_clusters': True,
                'typical_patterns': ['CVC', 'CVCVC']
            },
            'abstract_noun': {
                'preferred_length': 3,
                'allow_clusters': True,
                'typical_patterns': ['CVCV', 'VCVCV']
            },
            'verb': {
                'preferred_length': 2,
                'allow_clusters': False,
                'typical_patterns': ['CV', 'CVC']
            },
            'adjective': {
                'preferred_length': 2,
                'allow_clusters': True,
                'typical_patterns': ['CVCV', 'CVC']
            },
            'function_word': {
                'preferred_length': 1,
                'allow_clusters': False,
                'typical_patterns': ['CV', 'V']
            }
        }

    def _initialize_affixes(self) -> Dict[str, List[str]]:
        vowels = list(self.word_generator.phoneme_inventory['vowels'])
        consonants = list(self.word_generator.phoneme_inventory['consonants'])

        prefixes = []
        suffixes = []

        for _ in range(5):
            if self._rng.choice([True, False]):
                prefixes.append(self._rng.choice(
                    consonants) + self._rng.choice(vowels))
            else:
                prefixes.append(self._rng.choice(consonants))

        for _ in range(8):
            if self._rng.choice([True, False]):
                suffixes.append(self._rng.choice(vowels) +
                                self._rng.choice(consonants))
            else:
                suffixes.append(self._rng.choice(consonants))

        return {
            'noun_plural': [suffixes[0]],
            'verb_past': [suffixes[1]],
            'verb_progressive': [suffixes[2]],
            'adjective_comparative': [suffixes[3]],
            'adjective_superlative': [suffixes[4]],
            'diminutive': [prefixes[0]],
            'augmentative': [prefixes[1]],
            'negation': [prefixes[2]]
        }

    def generate_with_derivation(self, concept: str,
                                 category: str = 'concrete_noun',
                                 derivation: Optional[str] = None) -> str:
        base_word = self.word_generator.generate_word(
            concept,
            semantic_features=self.semantic_categories.get(category, {})
        )

        if derivation and derivation in self.derivational_affixes:
            affix = self._rng.choice(self.derivational_affixes[derivation])

            if derivation.startswith('noun') or derivation.startswith('verb') or derivation.startswith('adjective'):
                return base_word + affix
            else:
                return affix + base_word

        return base_word


class CompoundWordGenerator:
    def __init__(self, word_generator: WordGenerator):
        self.word_generator = word_generator

    def generate_compound(self, concept1: str, concept2: str,
                          compound_type: str = 'head_final') -> str:
        word1 = self.word_generator.generate_word(concept1)
        word2 = self.word_generator.generate_word(concept2)

        if compound_type == 'head_final':
            compound = word1 + word2
        elif compound_type == 'head_initial':
            compound = word2 + word1
        else:
            compound = word1 + word2

        compound = self._apply_sandhi(compound, word1, word2)

        return compound

    def _apply_sandhi(self, compound: str, word1: str, word2: str) -> str:
        boundary_idx = len(word1)

        if boundary_idx > 0 and boundary_idx < len(compound):
            char_before = compound[boundary_idx - 1]
            char_after = compound[boundary_idx] if boundary_idx < len(
                compound) else ''

            vowels = self.word_generator.phoneme_inventory['vowels']

            if char_before in vowels and char_after in vowels:
                if not self.word_generator.constraints.get('allow_hiatus', True):
                    consonants = list(
                        self.word_generator.phoneme_inventory['consonants'])
                    liaison = consonants[0] if consonants else ''
                    return compound[:boundary_idx] + liaison + compound[boundary_idx:]

        return compound


class NumberWordGenerator:
    def __init__(self, word_generator: WordGenerator, base: int = 10):
        self.word_generator = word_generator
        self.base = base
        self.number_words = {}
        self._generate_base_numbers()

    def _generate_base_numbers(self):
        for i in range(self.base):
            concept = f"number_{i}"
            self.number_words[i] = self.word_generator.generate_word(concept)

        for power in [10, 100, 1000]:
            concept = f"number_power_{power}"
            self.number_words[power] = self.word_generator.generate_word(
                concept)

    def generate_number_word(self, number: int) -> str:
        if number in self.number_words:
            return self.number_words[number]

        if number < self.base:
            return self.number_words[number]

        parts = []

        if number >= 1000:
            thousands = number // 1000
            parts.append(self.number_words[thousands])
            parts.append(self.number_words[1000])
            number %= 1000

        if number >= 100:
            hundreds = number // 100
            parts.append(self.number_words[hundreds])
            parts.append(self.number_words[100])
            number %= 100

        if number >= self.base:
            tens = number // self.base
            parts.append(self.number_words[tens])
            parts.append(self.number_words[10])
            number %= self.base

        if number > 0:
            parts.append(self.number_words[number])

        return ''.join(parts)
