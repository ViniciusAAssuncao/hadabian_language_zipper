import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from syntax_engine import SyntaxEngine, SyntacticFunction
from morphosyntax_analyzer import (
    DependencyParser, ConstituentAnalyzer, ClauseSegmenter,
    AgreementChecker, SyntacticComplexityAnalyzer,
    TopicalizationHandler, FocusStructureHandler
)


class OriginalLanguageEngine:
    def __init__(self, profile_path: str):
        with open(profile_path, 'r', encoding='utf-8') as f:
            self.profile = json.load(f)

        self.profile_id = self.profile.get('id', 'unknown')
        self.global_seed = self.profile.get('global_seed', 12345)

        self.phonotactics = self.profile.get('phonotactics', {})
        self.vowels = self.phonotactics.get('vowels', 'aeiou')
        self.consonants = self.phonotactics.get(
            'consonants', 'bcdfghjklmnpqrstvwxyz')
        self.templates = self.phonotactics.get(
            'syllable_templates', ['CV', 'CVC'])

        self.syntax_engine = SyntaxEngine(profile_path)

        self.dependency_parser = DependencyParser()
        self.constituent_analyzer = ConstituentAnalyzer()
        self.clause_segmenter = ClauseSegmenter()
        self.agreement_checker = AgreementChecker(self.profile)
        self.complexity_analyzer = SyntacticComplexityAnalyzer()
        self.topicalization_handler = TopicalizationHandler(self.profile)
        self.focus_handler = FocusStructureHandler(self.profile)

        self.word_cache: Dict[str, str] = {}
        self.load_word_cache()

    def load_word_cache(self):
        cache_file = Path(f"./cache/{self.profile_id}_words.json")
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    self.word_cache = json.load(f)
            except:
                pass

    def save_word_cache(self):
        cache_dir = Path("./cache")
        cache_dir.mkdir(exist_ok=True)
        cache_file = cache_dir / f"{self.profile_id}_words.json"

        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.word_cache, f, indent=2, ensure_ascii=False)
            
    def process_text(self, text: str) -> str:
        reordered_text, functions_info = self.syntax_engine.process_text(text)

        final_sentences = []
        for sent_data in functions_info:
            words = sent_data['reordered'].split()
            all_functions = sent_data['functions']

            func_map = {}
            named_entities = set()
            for f in all_functions:
                w = f.get("word")
                func_map[w] = f.get("function", "")
                if f.get("named_entity", False):
                    named_entities.add(w)

            translated_words = []
            for idx, orig_word in enumerate(words):
                clean_word_lower = self._clean_word(orig_word).lower()
                prefix, suffix = self._extract_punctuation(orig_word)

                if clean_word_lower in self.word_cache:
                    translated = self.word_cache[clean_word_lower]
                else:
                    translated = self._generate_deterministic_word(clean_word_lower)
                    self.word_cache[clean_word_lower] = translated

                translated = translated.lower()

                if clean_word_lower in named_entities:
                    translated = translated.capitalize()

                translated_words.append(prefix + translated + suffix)

            if self.profile.get("style", {}).get("capitalization", True) and translated_words:
                for i, token in enumerate(translated_words):
                    if any(c.isalpha() for c in token):
                        first_letter_idx = next(idx for idx, c in enumerate(token) if c.isalpha())
                        translated_words[i] = token[:first_letter_idx] + token[first_letter_idx].upper() + token[first_letter_idx+1:]
                        break

            final_sentences.append(' '.join(translated_words))

        self.save_word_cache()
        return ' '.join(final_sentences)

    def process_with_analysis(self, text: str) -> Dict:
        reordered_text, functions_info = self.syntax_engine.process_text(text)

        words = reordered_text.split()
        translated_words = []

        for word in words:
            clean_word = self._clean_word(word)
            prefix, suffix = self._extract_punctuation(word)

            if clean_word in self.word_cache:
                generated = self.word_cache[clean_word]
            else:
                generated = self._generate_deterministic_word(clean_word)
                self.word_cache[clean_word] = generated

            is_capitalized = clean_word and clean_word[0].isupper()
            if is_capitalized:
                generated = generated.capitalize()

            translated_words.append(prefix + generated + suffix)

        self.save_word_cache()

        analysis = {
            'original': text,
            'reordered': reordered_text,
            'translated': ' '.join(translated_words),
            'syntax_info': functions_info,
            'word_order': self.syntax_engine.word_order,
            'cache_size': len(self.word_cache)
        }

        return analysis

    def _clean_word(self, word: str) -> str:
        import re
        return re.sub(r'[^\w]', '', word)

    def _extract_punctuation(self, word: str) -> Tuple[str, str]:
        import re
        prefix = ""
        suffix = ""

        if word:
            m_start = re.match(r"^([^\w]*)", word)
            if m_start:
                prefix = m_start.group(1)
            m_end = re.search(r"([^\w]*)$", word)
            if m_end:
                suffix = m_end.group(1)

        return prefix, suffix

    def _generate_deterministic_word(self, word: str) -> str:
        clean_word = "".join(filter(str.isalpha, word.lower()))
        if not clean_word:
            return word

        input_str = f"{clean_word}_{self.global_seed}_{self.profile_id}"
        hash_obj = hashlib.sha256(input_str.encode())
        hash_int = int(hash_obj.hexdigest(), 16)

        import random
        random.seed(hash_int)

        num_syllables = random.randint(
            self.phonotactics.get('min_syllables', 1),
            self.phonotactics.get('max_syllables', 3)
        )

        generated_word = ""
        for _ in range(num_syllables):
            template = random.choice(self.templates)
            for char_type in template:
                if char_type == 'C':
                    if self.consonants:
                        generated_word += random.choice(list(self.consonants))
                elif char_type == 'V':
                    if self.vowels:
                        generated_word += random.choice(list(self.vowels))

        return generated_word if generated_word else word

    def analyze_sentence_structure(self, text: str) -> Dict:
        reordered_text, functions_info = self.syntax_engine.process_text(text)

        words = reordered_text.split()
        tagged = self.syntax_engine.pos_tagger.tag_sentence(words)

        dependencies = self.dependency_parser.parse(tagged)
        constituents = self.constituent_analyzer.identify_constituents(tagged)
        clauses = self.clause_segmenter.segment(words)

        functions = []
        if functions_info:
            for info in functions_info:
                if 'functions' in info:
                    functions.extend(info['functions'])

        agreement_violations = self.agreement_checker.check_agreement(
            functions)
        complexity_metrics = self.complexity_analyzer.analyze(
            functions, dependencies)

        return {
            'original_text': text,
            'reordered_text': reordered_text,
            'tagged_words': tagged,
            'dependencies': dependencies,
            'constituents': constituents,
            'clauses': clauses,
            'functions': functions,
            'agreement_violations': agreement_violations,
            'complexity': complexity_metrics,
            'word_order': self.syntax_engine.word_order
        }

    def get_statistics(self) -> Dict:
        syntax_stats = self.syntax_engine.get_statistics()

        return {
            'profile_id': self.profile_id,
            'word_order': self.syntax_engine.word_order,
            'cached_words': len(self.word_cache),
            'syntax': syntax_stats,
            'phonotactics': {
                'vowels': len(self.vowels),
                'consonants': len(self.consonants),
                'templates': len(self.templates)
            }
        }
