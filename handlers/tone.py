import hashlib
from typing import Dict, List, Tuple


class ToneSystem:
    def __init__(self, profile: Dict, vowels: str):
        self.profile = profile
        self.config = profile.get('tone_system', {})
        self.enabled = self.config.get('enabled', False)
        self.vowels = set(vowels) if vowels else set()
        self.tones = self.config.get('tones', [])
        self.sandhi_rules = self.config.get('sandhi_rules', [])
        self.applies_to = self.config.get('applies_to', 'penultimate')
        self.tone_cache = {}

    def is_enabled(self) -> bool:
        return self.enabled

    def assign_lexical_tone(self, lemma: str) -> str:
        if not self.enabled or not self.tones:
            return ""
        hash_val = int(hashlib.sha256(lemma.encode()).hexdigest(), 16)
        tone = self.tones[hash_val % len(self.tones)]
        return tone.get('name', '')

    def find_main_vowel_index(self, word: str) -> int:
        if not self.enabled:
            return -1
        vowel_indices = [i for i, char in enumerate(
            word) if char.lower() in self.vowels]
        if not vowel_indices:
            return -1
        if len(vowel_indices) == 1:
            return vowel_indices[0]
        if self.applies_to == 'ultimate':
            return vowel_indices[-1]
        elif self.applies_to == 'antepenultimate':
            return vowel_indices[-3] if len(vowel_indices) >= 3 else vowel_indices[0]
        elif self.applies_to == 'initial':
            return vowel_indices[0]
        return vowel_indices[-2] if len(vowel_indices) >= 2 else vowel_indices[0]

    def apply_tone_diacritic(self, word: str, tone_name: str) -> str:
        if not self.enabled or not word or not tone_name:
            return word
        tone_config = next(
            (t for t in self.tones if t.get('name') == tone_name), None)
        if not tone_config:
            return word
        dia = tone_config.get('diacritic', '')
        mapping = tone_config.get('mapping', {})
        if not dia and not mapping:
            return word
        idx = self.find_main_vowel_index(word)
        if idx == -1:
            return word
        chars = list(word)
        vowel = chars[idx]
        if mapping and vowel.lower() in mapping:
            replacement = mapping[vowel.lower()]
            if vowel.isupper():
                replacement = replacement.upper()
            chars[idx] = replacement
            return "".join(chars)
        if dia:
            chars.insert(idx + 1, dia)
            return "".join(chars)
        return word

    def strip_tone_diacritic(self, word: str) -> str:
        if not self.enabled or not word:
            return word
        current_word = word
        for tone in self.tones:
            dia = tone.get('diacritic', '')
            if dia:
                current_word = current_word.replace(dia, '')
            mapping = tone.get('mapping', {})
            for base, toned in mapping.items():
                current_word = current_word.replace(toned, base)
                current_word = current_word.replace(
                    toned.upper(), base.upper())
        return current_word

    def apply_sandhi(self, words: List[str], tones: List[str]) -> Tuple[List[str], List[str]]:
        if not self.enabled or not self.sandhi_rules:
            return words, tones
        new_words = list(words)
        new_tones = list(tones)
        for rule in self.sandhi_rules:
            seq = rule.get('sequence', [])
            repl = rule.get('replacement', [])
            if not seq or not repl or len(seq) != len(repl):
                continue
            seq_len = len(seq)
            for i in range(len(new_tones) - seq_len + 1):
                match = True
                for j in range(seq_len):
                    if new_tones[i+j] != seq[j]:
                        match = False
                        break
                if match:
                    for j in range(seq_len):
                        if new_tones[i+j] != repl[j]:
                            new_tones[i+j] = repl[j]
                            stripped = self.strip_tone_diacritic(
                                new_words[i+j])
                            new_words[i +
                                      j] = self.apply_tone_diacritic(stripped, repl[j])
        return new_words, new_tones

    def get_tone_for_lemma(self, lemma: str) -> str:
        if not self.enabled:
            return ""
        if lemma in self.tone_cache:
            return self.tone_cache[lemma]
        tone = self.assign_lexical_tone(lemma)
        self.tone_cache[lemma] = tone
        return tone
