import json
import hashlib
import random
from pathlib import Path

class OriginalLanguageEngine:
    def __init__(self, profile_path):
        self.profile = {}
        self.load_profile(profile_path)
        
    def load_profile(self, profile_path):
        with open(profile_path, 'r', encoding='utf-8') as f:
            self.profile = json.load(f)
        self.seed = self.profile.get("global_seed", 0)
        self.phonotactics = self.profile.get("phonotactics", {})
        self.vowels = self.phonotactics.get("vowels", [])
        self.consonants = self.phonotactics.get("consonants", [])
        self.templates = self.phonotactics.get("syllable_templates", ["CV"])

    def process_text(self, text):
        words = text.split()
        translated_words = []
        
        for word in words:
            translated_words.append(self._generate_deterministic_word(word))
            
        return " ".join(translated_words)

    def _generate_deterministic_word(self, word):
        clean_word = "".join(filter(str.isalpha, word.lower()))
        if not clean_word:
            return word

        input_str = f"{clean_word}_{self.seed}"
        hash_obj = hashlib.sha256(input_str.encode())
        hash_int = int(hash_obj.hexdigest(), 16)
        
        random.seed(hash_int)
        
        num_syllables = random.randint(
            self.phonotactics.get("min_syllables", 1),
            self.phonotactics.get("max_syllables", 3)
        )
        
        generated_word = ""
        for _ in range(num_syllables):
            template = random.choice(self.templates)
            for char_type in template:
                if char_type == "C":
                    generated_word += random.choice(self.consonants)
                elif char_type == "V":
                    generated_word += random.choice(self.vowels)
        
        if self.profile.get("style", {}).get("capitalization", False) and word[0].isupper():
            return generated_word.capitalize()
            
        return generated_word