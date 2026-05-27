from typing import Dict, List, Optional


class MorphologyTemplateHandler:
    pass


class AblauthSystem:
    def __init__(self, profile: Dict, vowels: str = "aeiou"):
        self.profile = profile
        self.config = profile.get('ablaut_system', {})
        self.enabled = self.config.get('enabled', False)
        self.grades = self.config.get('grades', {})
        self.alternation_sets = self.config.get('alternation_sets', [])
        self.umlaut_rules = self.config.get('umlaut_rules', [])
        phonotactics = profile.get('phonotactics', {})
        self.vowels = set(phonotactics.get('vowels', vowels))
        self.applies_to = self.config.get('applies_to', 'penultimate')

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

    def apply_vowel_grade(self, word: str, alternation_set_id: str, slot: str) -> str:
        if not self.enabled or not word:
            return word
        target_set = next((s for s in self.alternation_sets if s.get(
            'set_id') == alternation_set_id), None)
        if not target_set:
            return word
        slots = target_set.get('slots', {})
        if slot not in slots:
            return word
        grade_name = slots[slot]
        if grade_name not in self.grades:
            return word
        grade_value = self.grades[grade_name]
        idx = self.find_main_vowel_index(word)
        if idx == -1:
            return word
        return word[:idx] + grade_value + word[idx+1:]

    def apply_umlaut(self, word: str, trigger_context: str) -> str:
        if not self.enabled or not word:
            return word
        idx = self.find_main_vowel_index(word)
        if idx == -1:
            return word
        vowel = word[idx]
        vowel_lower = vowel.lower()
        for rule in self.umlaut_rules:
            if rule.get('trigger') == trigger_context and rule.get('input_vowel') == vowel_lower:
                output = rule.get('output_vowel', '')
                if vowel.isupper():
                    output = output.upper()
                return word[:idx] + output + word[idx+1:]
        return word
