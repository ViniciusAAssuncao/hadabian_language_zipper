import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from syntax_engine import SyntaxEngine, SyntacticFunction
from morphosyntax_analyzer import (
    DependencyParser, ConstituentAnalyzer, ClauseSegmenter,
    AgreementChecker, SyntacticComplexityAnalyzer,
    TopicalizationHandler, FocusStructureHandler, TAMHandler
)


class AffixHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.affix_system = profile.get('affix_system', {})
        self.enabled = self.affix_system.get('enabled', False)
        self.derivation_rules = self.affix_system.get('derivation_rules', [])

    def get_derivation_rule(self, from_pos: str, to_pos: str) -> Optional[Dict]:
        if not self.enabled:
            return None
        for rule in self.derivation_rules:
            if rule['from_pos'] == from_pos and rule['to_pos'] == to_pos:
                return rule
        return None

    def apply_affix(self, word: str, rule: Dict) -> str:
        affix = rule.get('affix', '')
        position = rule.get('position', 'suffix')
        if not affix:
            return word
        if position == 'prefix':
            return f"{affix}{word}"
        elif position == 'suffix':
            return f"{word}{affix}"
        elif position == 'infix':
            mid = len(word) // 2
            return f"{word[:mid]}{affix}{word[mid:]}"
        return word


class DegreeHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get('degree_system', {})
        self.enabled = self.config.get('enabled', False)
        self.rules = self.config.get('rules', {})
        self.source_rules = self.config.get('source_rules', [])

    def detect_degree(self, word: str, lemma: str, feats_str: str) -> Optional[str]:
        if not self.enabled:
            return None

        if feats_str and feats_str != '_':
            feats = feats_str.split('|')
            if 'Degree=Dim' in feats:
                return 'diminutive'
            if 'Degree=Aug' in feats:
                return 'augmentative'
            if 'Degree=Abs' in feats or 'Degree=Sup' in feats:
                return 'superlative'

        w = word.lower()
        for rule in self.source_rules:
            suffix = rule.get('suffix', '')
            if suffix and w.endswith(suffix):
                return rule.get('type')

        return None

    def get_base_lemma(self, word: str, lemma: str, degree_type: str, feats_str: str) -> str:
        if not degree_type:
            return lemma

        w = word.lower()

        for rule in self.source_rules:
            if rule.get('type') == degree_type:
                suffix = rule.get('suffix', '')
                if suffix and w.endswith(suffix):
                    replacement = rule.get('replacement', '')
                    return w[:-len(suffix)] + replacement

        if feats_str and feats_str != '_':
            return lemma

        return lemma

    def apply_degree(self, word: str, degree_type: str) -> str:
        if not self.enabled or not degree_type:
            return word
        rule = self.rules.get(degree_type)
        if not rule:
            return word
        affix = rule.get('affix', '')
        position = rule.get('position', 'suffix')
        if position == 'suffix':
            return f"{word}{affix}"
        elif position == 'prefix':
            return f"{affix}{word}"
        return word


class ReduplicationHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get('reduplication', {})
        self.enabled = self.config.get('enabled', False)
        self.rules = self.config.get('rules', [])
        phonotactics = profile.get('phonotactics', {})
        self.vowels = phonotactics.get('vowels', 'aeiou')
        self.consonants = phonotactics.get(
            'consonants', 'bcdfghjklmnpqrstvwxyz')

    def apply_reduplication(self, word: str, feats_str: str) -> str:
        if not self.enabled or not word or not feats_str or feats_str == '_':
            return word

        feats = set(feats_str.split('|'))

        for rule in self.rules:
            rule_feats = set(rule.get('features', []))
            if rule_feats.issubset(feats):
                method = rule.get('method', 'whole_word')
                separator = rule.get('separator', '')

                if method == 'whole_word':
                    return f"{word}{separator}{word}"
                elif method == 'first_syllable':
                    syllable = self._get_first_syllable(word)
                    if syllable:
                        return f"{syllable}{separator}{word}"

        return word

    def _get_first_syllable(self, word: str) -> str:
        import re
        c_set = re.escape(self.consonants)
        v_set = re.escape(self.vowels)
        match = re.match(f"^[{c_set}]*[{v_set}]+", word, re.IGNORECASE)
        if match:
            return match.group(0)
        return ""


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
        self.affix_handler = AffixHandler(self.profile)
        self.degree_handler = DegreeHandler(self.profile)
        self.tam_handler = TAMHandler(self.profile)
        self.reduplication_handler = ReduplicationHandler(self.profile)
        self.word_cache: Dict[str, str] = {}
        self.load_word_cache()

    def load_word_cache(self):
        cache_dir = Path("./cache")
        if not cache_dir.exists():
            cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f"{self.profile_id}_words.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    self.word_cache = json.load(f)
            except:
                self.word_cache = {}
        else:
            self.word_cache = {}

    def save_word_cache(self):
        cache_dir = Path("./cache")
        cache_dir.mkdir(parents=True, exist_ok=True)
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
            lemma_map = {}
            pos_map = {}
            feats_map = {}
            for f in all_functions:
                w = f.get("word")
                func_map[w] = f.get("function", "")
                lemma_map[w] = f.get("lemma", "")
                pos_map[w] = f.get("pos", "")
                feats_map[w] = f.get("feats", "")
                if f.get("named_entity", False):
                    named_entities.add(w)

            translated_words = []
            for idx, orig_word in enumerate(words):
                clean_word_lower = self._clean_word(orig_word).lower()
                prefix, suffix = self._extract_punctuation(orig_word)

                raw_lemma = lemma_map.get(orig_word, clean_word_lower).lower()
                word_feats = feats_map.get(orig_word, "")

                degree_type = None
                if self.degree_handler.enabled:
                    degree_type = self.degree_handler.detect_degree(
                        clean_word_lower, raw_lemma, word_feats)

                translated = None

                if degree_type:
                    base_lemma = self.degree_handler.get_base_lemma(
                        clean_word_lower, raw_lemma, degree_type, word_feats)

                    if base_lemma not in self.word_cache:
                        self.word_cache[base_lemma] = self._generate_deterministic_word(
                            base_lemma)

                    base_translation = self.word_cache[base_lemma]
                    translated = self.degree_handler.apply_degree(
                        base_translation, degree_type)

                elif clean_word_lower in self.word_cache:
                    translated = self.word_cache[clean_word_lower]
                else:
                    target_lemma = raw_lemma
                    current_pos = pos_map.get(orig_word, 'NOUN')

                    if self.affix_handler.enabled:
                        source_suffixes = self.profile.get(
                            'affix_system', {}).get('source_suffixes', [])
                        for suffix_rule in source_suffixes:
                            suf_str = suffix_rule.get('suffix', '')
                            input_pos = suffix_rule.get('input_pos', 'NOUN')

                            if current_pos == input_pos and clean_word_lower.endswith(suf_str):
                                replacement = suffix_rule.get(
                                    'replacement', '')
                                target_pos_req = suffix_rule.get(
                                    'target_pos', 'VERB')
                                possible_stem = clean_word_lower[:-
                                                                 len(suf_str)] + replacement

                                if possible_stem in lemma_map.values() or self.syntax_engine.estimate_lemma_pos(possible_stem) == target_pos_req:
                                    target_lemma = possible_stem
                                    break

                        if target_lemma and target_lemma != clean_word_lower:
                            lemma_pos = self.syntax_engine.estimate_lemma_pos(
                                target_lemma)
                            rule = self.affix_handler.get_derivation_rule(
                                lemma_pos, current_pos)

                            if rule:
                                if target_lemma not in self.word_cache:
                                    self.word_cache[target_lemma] = self._generate_deterministic_word(
                                        target_lemma)

                                base_translation = self.word_cache[target_lemma]
                                translated = self.affix_handler.apply_affix(
                                    base_translation, rule)

                    if translated is None:
                        if target_lemma not in self.word_cache:
                            self.word_cache[target_lemma] = self._generate_deterministic_word(
                                target_lemma)
                        translated = self.word_cache[target_lemma]

                    if not degree_type:
                        self.word_cache[clean_word_lower] = translated

                if self.reduplication_handler.enabled:
                    translated = self.reduplication_handler.apply_reduplication(
                        translated, word_feats)

                if self.tam_handler.enabled and pos_map.get(orig_word) == 'VERB':
                    translated = self.tam_handler.apply_tam(
                        translated, word_feats)

                translated = translated.lower()
                if clean_word_lower in named_entities:
                    translated = translated.capitalize()

                translated_words.append(prefix + translated + suffix)

            if self.profile.get("style", {}).get("capitalization", True) and translated_words:
                for i, token in enumerate(translated_words):
                    if any(c.isalpha() for c in token):
                        first_letter_idx = next(
                            idx for idx, c in enumerate(token) if c.isalpha())
                        translated_words[i] = token[:first_letter_idx] + \
                            token[first_letter_idx].upper(
                        ) + token[first_letter_idx+1:]
                        break
            final_sentences.append(' '.join(translated_words))

        self.save_word_cache()
        return ' '.join(final_sentences)

    def process_with_analysis(self, text: str) -> Dict:
        reordered_text, functions_info = self.syntax_engine.process_text(text)
        return {
            'original': text,
            'reordered': reordered_text,
            'translated': self.process_text(text),
            'syntax_info': functions_info,
            'word_order': self.syntax_engine.word_order,
            'cache_size': len(self.word_cache)
        }

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
        tagged = self.syntax_engine.pos_tagger.tag_sentence(
            words) if hasattr(self.syntax_engine, 'pos_tagger') else []
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
