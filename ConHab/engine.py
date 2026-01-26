import json
import hashlib
from pathlib import Path
import re
import random
import unicodedata
from typing import List, Dict, Optional, Tuple, Set, Union
from syntax_engine import SyntaxEngine, SyntacticFunction
from morphosyntax_analyzer import (
    DependencyParser, ConstituentAnalyzer, ClauseSegmenter,
    AgreementChecker, SyntacticComplexityAnalyzer,
    TopicalizationHandler, FocusStructureHandler, TAMHandler,
    VowelHarmonyHandler, TransitivityAnalyzer, ConsonantMutationHandler,
    GenderHandler
)


class PhonologyHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.phonotactics = profile.get('phonotactics', {})
        self.seed = profile.get('global_seed', 12345)
        self.base_consonants = self.phonotactics.get('consonants')
        if self.base_consonants is None:
            self.base_consonants = self._infer_inventory('consonants')
        self.base_vowels = self.phonotactics.get('vowels')
        if self.base_vowels is None:
            self.base_vowels = self._infer_inventory('vowels')
        self.active_style_name = self.phonotactics.get('active_style', None)
        self.styles = self.phonotactics.get('inventory_styles', {})
        if self.active_style_name and self.active_style_name in self.styles:
            style = self.styles[self.active_style_name]
            self.consonants = style.get('consonants', self.base_consonants)
            self.vowels = style.get('vowels', self.base_vowels)
        else:
            self.consonants = self.base_consonants
            self.vowels = self.base_vowels
        self.hierarchy_config = self.phonotactics.get('sonority_hierarchy', {})
        self.enabled = self.hierarchy_config.get('enabled', False)
        self.scale = self.hierarchy_config.get('scale', {})
        self.onset_rules = self.hierarchy_config.get('onset_rules', {})
        self.coda_rules = self.hierarchy_config.get('coda_rules', {})
        self.forbidden_initial = set(
            self.phonotactics.get('forbidden_initial_clusters', []))
        self.forbidden_final = set(self.phonotactics.get(
            'forbidden_final_consonants', []))

    def _infer_inventory(self, type_key: str) -> str:
        rng = random.Random(self.seed + sum(ord(c) for c in type_key))
        if type_key == 'consonants':
            pool = [chr(i) for i in range(97, 123) if chr(i) not in 'aeiou']
            count = rng.randint(5, 18)
            return "".join(sorted(rng.sample(pool, count)))
        elif type_key == 'vowels':
            pool = 'aeiouy'
            count = rng.randint(3, 6)
            return "".join(sorted(rng.sample(pool, count)))
        return ""

    def get_sonority(self, char: str) -> int:
        return self.scale.get(char.lower(), 0)

    def is_valid_onset_cluster(self, c1: str, c2: str) -> bool:
        cluster = f"{c1}{c2}".lower()
        if cluster in self.forbidden_initial:
            return False
        if not self.enabled:
            return True
        s1 = self.get_sonority(c1)
        s2 = self.get_sonority(c2)
        dist = s2 - s1
        min_dist = self.onset_rules.get('min_distance', 1)
        if dist < min_dist:
            return False
        if dist == 0 and not self.onset_rules.get('allow_plateau', False):
            return False
        if dist < 0 and not self.onset_rules.get('allow_reversal', False):
            return False
        return True

    def is_valid_coda_cluster(self, c1: str, c2: str) -> bool:
        if not self.enabled:
            return True
        s1 = self.get_sonority(c1)
        s2 = self.get_sonority(c2)
        dist = s1 - s2
        min_dist = self.coda_rules.get('min_distance', 0)
        if dist < min_dist:
            return False
        if dist == 0 and not self.coda_rules.get('allow_plateau', True):
            return False
        if dist < 0 and not self.coda_rules.get('allow_reversal', True):
            return False
        return True

    def is_valid_contact(self, c1: str, c2: str) -> bool:
        if c1.lower() in self.vowels:
            return True
        if c2.lower() in self.vowels:
            return True
        cluster = f"{c1}{c2}".lower()
        if cluster in self.forbidden_initial:
            return False
        if not self.enabled:
            return True
        s1 = self.get_sonority(c1)
        s2 = self.get_sonority(c2)
        contact_rules = self.hierarchy_config.get('contact_rules', {})
        dist = s1 - s2
        min_dist = contact_rules.get('min_distance', 0)
        if dist < min_dist:
            return False
        if dist == 0 and not contact_rules.get('allow_plateau', True):
            return False
        if dist < 0 and not contact_rules.get('allow_reversal', False):
            return False
        return True

    def is_valid_final(self, char: str) -> bool:
        return char.lower() not in self.forbidden_final

    def normalize_char(self, char: str) -> str:
        normalized = unicodedata.normalize('NFD', char)
        return "".join(c for c in normalized if unicodedata.category(c) != 'Mn')

    def get_closest_phoneme(self, char: str) -> str:
        char = char.lower()
        if char in self.vowels or char in self.consonants:
            return char
        normalized = self.normalize_char(char)
        if normalized in self.vowels or normalized in self.consonants:
            return normalized
        target_pool = self.vowels if char in 'aeiouyäëïöü' else self.consonants
        if not target_pool:
            target_pool = self.vowels + self.consonants
        char_hash = int(hashlib.sha256(char.encode()).hexdigest(), 16)
        return target_pool[char_hash % len(target_pool)]

    def nativize_word(self, word: str) -> str:
        if not word:
            return word
        nativized = []
        for char in word:
            nativized.append(self.get_closest_phoneme(char))
        result = "".join(nativized)
        if result and not self.is_valid_final(result[-1]):
            valid_finals = [c for c in self.consonants if self.is_valid_final(
                c)] + list(self.vowels)
            if valid_finals:
                seed_val = sum(ord(c) for c in result)
                rng = random.Random(seed_val)
                strategy = rng.choice(['drop', 'change', 'add_vowel'])
                if strategy == 'drop':
                    result = result[:-1]
                elif strategy == 'change':
                    result = result[:-1] + rng.choice(valid_finals)
                elif strategy == 'add_vowel' and self.vowels:
                    result = result + rng.choice(list(self.vowels))
        return result


class ConceptHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get('abstract_concepts', {})
        self.enabled = self.config.get('enabled', False)
        self.mappings = self.config.get('mappings', {}).copy()
        root_mappings = profile.get('mappings', {})
        if root_mappings:
            for k, v in root_mappings.items():
                if k not in self.mappings:
                    self.mappings[k] = v
        self.local_overrides = self.config.get('local_overrides', {})
        self.definitions = self.config.get('definitions', {})
        self.purism_level = profile.get('cultural_purism', 0.0)
        self.universal_registry = self._load_universal_registry()

    def _load_universal_registry(self) -> Dict:
        paths_to_try = [
            Path('reserved_universal.json'),
            Path('../conlangs/reserved_universal.json'),
            Path('./conlangs/reserved_universal.json')
        ]
        for p in paths_to_try:
            if p.exists():
                try:
                    with open(p, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except:
                    continue
        return {"concepts": {}, "mappings_ln": {}}

    def resolve_concept(self, lemma: str, engine_instance) -> Optional[Tuple[str, str, Dict]]:
        if not self.enabled:
            return None
        clean_lemma = lemma.lower().strip()
        concept_id = self.mappings.get(clean_lemma)
        if not concept_id:
            concept_id = self.universal_registry.get(
                'mappings_ln', {}).get(clean_lemma)
        if not concept_id:
            return None
        if concept_id in self.local_overrides:
            word = self.local_overrides[concept_id]
            return word, 'override', {'origin': 'local_override', 'concept_id': concept_id}
        if concept_id in self.definitions:
            definition = self.definitions[concept_id]
            concept_type = definition.get('type', 'unique')
            if concept_type == 'composition':
                components = definition.get('components', [])
                connector = definition.get('connector', '')
                composed_parts = []
                for comp in components:
                    translated_part = engine_instance._get_word_form(comp)
                    composed_parts.append(translated_part)
                final_word = connector.join(composed_parts)
                return final_word, 'composition', {}
            elif concept_type == 'adaptation':
                source = definition.get('source_word', lemma)
                if not source:
                    source = lemma
                nativized = engine_instance.phonology_handler.nativize_word(
                    source)
                explanation = definition.get('description', 'Adapted concept.')
                return nativized, 'adaptation', {'description': explanation, 'source_word': source}
            elif concept_type == 'unique':
                explanation = definition.get(
                    'description', 'Concept unique to this conlang.')
                if concept_id in engine_instance.word_cache:
                    entry = engine_instance.word_cache[concept_id]
                    word = entry.get('default', '') if isinstance(
                        entry, dict) else entry
                    return word, 'unique', {'description': explanation}
                generated_word = engine_instance._generate_deterministic_word(
                    concept_id)
                return generated_word, 'unique', {'description': explanation}
        if concept_id in self.universal_registry.get('concepts', {}):
            if self.purism_level >= 0.8:
                return None
            global_entry = self.universal_registry['concepts'][concept_id]
            base_word = global_entry['word']
            nativized_word = engine_instance.loanword_handler.nativize_reserved_term(
                base_word)
            return nativized_word, 'reserved_global', {
                'description': global_entry.get('description', ''),
                'original_term': base_word,
                'concept_id': concept_id
            }
        if concept_id and isinstance(concept_id, str):
            return concept_id, 'direct_mapping', {'origin': 'mapping_table'}
        return None


class StressHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get('stress_system', {})
        self.enabled = self.config.get('enabled', False)
        self.type = self.config.get('type', 'fixed')
        self.position = self.config.get('position', 'penultimate')
        self.graphic = self.config.get('graphic_accent', False)
        self.map = self.config.get(
            'accent_map', {'a': 'á', 'e': 'é', 'i': 'í', 'o': 'ó', 'u': 'ú'})
        self.phonotactics = profile.get('phonotactics', {})
        self.vowels = self.phonotactics.get('vowels')
        if not self.vowels:
            ph_handler = PhonologyHandler(profile)
            self.vowels = ph_handler.base_vowels
        self.vowels = set(self.vowels)

    def apply_stress(self, word: str) -> str:
        if not self.enabled or not word:
            return word
        vowel_indices = [i for i, char in enumerate(
            word) if char.lower() in self.vowels]
        if not vowel_indices:
            return word
        target_vowel_idx = -1
        if self.type == 'fixed':
            if self.position == 'ultimate':
                target_vowel_idx = vowel_indices[-1]
            elif self.position == 'penultimate':
                target_vowel_idx = vowel_indices[-2] if len(
                    vowel_indices) >= 2 else vowel_indices[-1]
            elif self.position == 'antepenultimate':
                target_vowel_idx = vowel_indices[-3] if len(vowel_indices) >= 3 else (
                    vowel_indices[-2] if len(vowel_indices) >= 2 else vowel_indices[-1])
            elif self.position == 'initial':
                target_vowel_idx = vowel_indices[0]
        elif self.type == 'weight':
            if len(vowel_indices) < 2:
                target_vowel_idx = vowel_indices[-1]
            else:
                penult_idx = vowel_indices[-2]
                ult_idx = vowel_indices[-1]
                inter_segment = word[penult_idx+1:ult_idx]
                is_heavy = False
                if len(inter_segment) > 1:
                    is_heavy = True
                if is_heavy:
                    target_vowel_idx = penult_idx
                else:
                    target_vowel_idx = vowel_indices[-3] if len(
                        vowel_indices) >= 3 else penult_idx
        if target_vowel_idx != -1 and self.graphic:
            chars = list(word)
            v = chars[target_vowel_idx]
            lower_v = v.lower()
            if lower_v in self.map:
                replacement = self.map[lower_v]
                if v.isupper():
                    replacement = replacement.upper()
                chars[target_vowel_idx] = replacement
                return "".join(chars)
        return word


class FalseCognateHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get('false_cognates', {})
        self.enabled = self.config.get('enabled', False)
        self.manual_pairs = self.config.get('manual_pairs', {})
        self.natural_chance = self.config.get('natural_confusion_chance', 0.0)

    def get_manual_target(self, lemma: str) -> Optional[str]:
        if not self.enabled:
            return None
        return self.manual_pairs.get(lemma)

    def should_collide_naturally(self, lemma: str, global_seed: int) -> Optional[int]:
        if not self.enabled or self.natural_chance <= 0:
            return None
        input_str = f"{lemma}_collision_check_{global_seed}"
        hash_obj = hashlib.sha256(input_str.encode())
        hash_val = int(hash_obj.hexdigest(), 16)
        if (hash_val % 1000) / 1000.0 < self.natural_chance:
            return hash_val % 100
        return None


class PolysemyHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get('polysemy_rules', {})
        self.enabled = self.config.get('enabled', False)
        self.merges = self.config.get('merges', {})
        self.splits = self.config.get('splits', {})

    def resolve_lemma(self, lemma: str, context: Dict) -> str:
        if not self.enabled:
            return lemma
        clean_lemma = lemma.lower().strip()
        if clean_lemma in self.merges:
            return self.merges[clean_lemma]
        if clean_lemma in self.splits:
            rules = self.splits[clean_lemma]
            context_feats = set(context.get('feats', '').split('|'))
            context_deprel = context.get('deprel', '')
            for rule in rules:
                rule_match = rule.get('rules', {})
                match_feats = set(rule_match.get('feats', []))
                match_deprel = rule_match.get('deprel', [])
                feats_ok = True
                if match_feats:
                    if not match_feats.issubset(context_feats):
                        feats_ok = False
                deprel_ok = True
                if match_deprel:
                    if context_deprel not in match_deprel:
                        deprel_ok = False
                if feats_ok and deprel_ok:
                    suffix = rule.get('target_suffix', '')
                    return f"{clean_lemma}{suffix}"
        return clean_lemma


class SemanticFieldHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get('semantic_fields', {})
        self.enabled = self.config.get('enabled', False)
        self.manual_groups = self.config.get('manual_groups', {})
        self.use_nltk = self.config.get('use_nltk', False)
        self.nltk_ready = False
        if self.enabled and self.use_nltk:
            try:
                import nltk
                from nltk.corpus import wordnet
                try:
                    wordnet.synsets('teste', lang='por')
                except LookupError:
                    nltk.download('wordnet')
                    nltk.download('omw-1.4')
                self.wn = wordnet
                self.nltk_ready = True
            except ImportError:
                self.nltk_ready = False

    def get_semantic_root(self, word: str) -> Optional[str]:
        if not self.enabled:
            return None
        clean_word = word.lower()
        if clean_word in self.manual_groups:
            return self.manual_groups[clean_word]
        if self.nltk_ready:
            try:
                synsets = self.wn.synsets(clean_word, lang='por')
                if not synsets:
                    return None
                synset = synsets[0]
                hypernyms = synset.hypernyms()
                if hypernyms:
                    hyper_lemma = hypernyms[0].lemmas(lang='por')
                    if hyper_lemma:
                        return hyper_lemma[0].name()
                    english_lemma = hypernyms[0].lemmas()[0].name()
                    return english_lemma
            except:
                pass
        return None


class AffixHandler:
    def __init__(self, profile: Dict, harmony_handler: Optional[VowelHarmonyHandler] = None):
        self.profile = profile
        self.affix_system = profile.get('affix_system', {})
        self.enabled = self.affix_system.get('enabled', False)
        self.derivation_rules = self.affix_system.get('derivation_rules', [])
        self.harmony_handler = harmony_handler
        self.agglutination_strength = profile.get(
            'agglutination_strength', 1.0)
        self.seed = profile.get('global_seed', 12345)
        self.morph_config = profile.get('morphological_derivation', {})
        self.morph_derivation_enabled = self.morph_config.get('enabled', False)
        self.max_derivation_depth = self.morph_config.get('max_depth', 3)
        self.exceptions = set(self.morph_config.get('exceptions', []))
        raw_source_suffixes = self.affix_system.get('source_suffixes', [])
        self.source_suffixes = sorted(
            raw_source_suffixes, key=lambda x: x.get('priority', 0), reverse=True)

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
        force = rule.get('force', False)
        if not affix:
            return word
        if not force and self.agglutination_strength < 1.0:
            input_str = f"{word}_{affix}_{self.seed}_agglutination"
            hash_obj = hashlib.sha256(input_str.encode())
            hash_val = int(hash_obj.hexdigest(), 16)
            probability = (hash_val % 1000) / 1000.0
            if probability > self.agglutination_strength:
                return word
        if position == 'suffix' and self.harmony_handler and self.harmony_handler.enabled:
            affix = self.harmony_handler.apply_harmony(word, affix)
        if position == 'prefix':
            return f"{affix}{word}"
        elif position == 'suffix':
            return f"{word}{affix}"
        elif position == 'infix':
            mid = len(word) // 2
            return f"{word[:mid]}{affix}{word[mid:]}"
        return word

    def try_derive_from_source(self, lemma: str, pos: Optional[str], engine_ref, current_depth: int = 0) -> Optional[str]:
        if not self.morph_derivation_enabled:
            return None
        if current_depth >= self.max_derivation_depth:
            return None
        if lemma in self.exceptions:
            return None
        for rule in self.source_suffixes:
            suf = rule.get('suffix', '')
            input_pos = rule.get('input_pos')
            min_len = rule.get('min_word_length', 0)
            mode = rule.get('mode', 'derive')
            if len(lemma) < min_len:
                continue
            if pos and input_pos and pos != input_pos:
                continue
            if lemma.endswith(suf):
                replacement = rule.get('replacement', '')
                base_source_lemma = lemma[:-len(suf)] + replacement
                if base_source_lemma == lemma:
                    continue
                if mode == 'adapt':
                    nativized = engine_ref.phonology_handler.nativize_word(
                        base_source_lemma)
                    return nativized
                target_pos = rule.get('target_pos', 'NOUN')
                effective_to_pos = input_pos if input_pos else pos
                base_conlang_word = engine_ref._get_word_form(
                    base_source_lemma, tags=None, pos=target_pos, derivation_depth=current_depth + 1)
                derivation_rule = None
                if effective_to_pos:
                    derivation_rule = self.get_derivation_rule(
                        from_pos=target_pos, to_pos=effective_to_pos)
                    if derivation_rule:
                        return self.apply_affix(base_conlang_word, derivation_rule)
                if replacement and not derivation_rule:
                    source_stem = lemma[:-len(suf)]
                    base_stem_word = engine_ref._get_word_form(
                        source_stem, tags=['stem'], pos=target_pos, derivation_depth=current_depth + 1)
                    return self.apply_affix(base_stem_word, {'affix': replacement, 'position': 'suffix', 'force': True})
        return None


class DegreeHandler:
    def __init__(self, profile: Dict, harmony_handler: Optional[VowelHarmonyHandler] = None):
        self.profile = profile
        self.config = profile.get('degree_system', {})
        self.enabled = self.config.get('enabled', False)
        self.rules = self.config.get('rules', {})
        self.source_rules = self.config.get('source_rules', [])
        self.harmony_handler = harmony_handler

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
        if position == 'suffix' and self.harmony_handler and self.harmony_handler.enabled:
            affix = self.harmony_handler.apply_harmony(word, affix)
        if position == 'suffix':
            return f"{word}{affix}"
        elif position == 'prefix':
            return f"{affix}{word}"
        return word


class ReduplicationHandler:
    def __init__(self, profile: Dict, phonology_handler: Optional[PhonologyHandler] = None):
        self.profile = profile
        self.config = profile.get('reduplication', {})
        self.enabled = self.config.get('enabled', False)
        self.rules = self.config.get('rules', [])
        self.epenthesis_vowel = self.config.get('epenthesis_vowel')
        self.phonotactics = profile.get('phonotactics', {})
        self.phonology_handler = phonology_handler
        self.agglutination_strength = profile.get(
            'agglutination_strength', 1.0)
        self.seed = profile.get('global_seed', 12345)
        if not self.epenthesis_vowel:
            self.epenthesis_vowel = self.phonotactics.get(
                'epenthesis_vowel', 'i')
        self.vowels = self.phonotactics.get('vowels')
        self.consonants = self.phonotactics.get('consonants')
        if not self.vowels or not self.consonants:
            if not self.phonology_handler:
                self.phonology_handler = PhonologyHandler(profile)
            if not self.vowels:
                self.vowels = self.phonology_handler.base_vowels
            if not self.consonants:
                self.consonants = self.phonology_handler.base_consonants

    def apply_reduplication(self, word: str, feats_str: str, pos: str = None) -> str:
        if not self.enabled or not word or not feats_str or feats_str == '_':
            return word
        if self.agglutination_strength < 1.0:
            input_str = f"{word}_{feats_str}_{self.seed}_reduplication"
            hash_obj = hashlib.sha256(input_str.encode())
            hash_val = int(hash_obj.hexdigest(), 16)
            probability = (hash_val % 1000) / 1000.0
            if probability > self.agglutination_strength:
                return word
        feats = set(feats_str.split('|'))
        for rule in self.rules:
            allowed_pos = rule.get('pos')
            if allowed_pos and pos:
                if pos not in allowed_pos:
                    continue
            rule_feats = set(rule.get('features', []))
            if rule_feats.issubset(feats):
                method = rule.get('method', 'whole_word')
                separator = rule.get('separator', '')
                reduplicated_part = ""
                if method == 'whole_word':
                    reduplicated_part = word
                elif method == 'first_syllable':
                    reduplicated_part = self._get_first_syllable(word)
                if not reduplicated_part:
                    continue
                part1 = reduplicated_part
                part2 = word
                if part1 and part2:
                    last_char = part1[-1]
                    first_char = part2[0]
                    needs_epenthesis = False
                    if self.phonology_handler:
                        if not self.phonology_handler.is_valid_contact(last_char, first_char):
                            needs_epenthesis = True
                    if needs_epenthesis:
                        return f"{part1}{self.epenthesis_vowel}{separator}{part2}"
                    else:
                        return f"{part1}{separator}{part2}"
        return word

    def _get_first_syllable(self, word: str) -> str:
        import re
        c_set = re.escape(self.consonants)
        v_set = re.escape(self.vowels)
        match = re.match(f"^[{c_set}]*[{v_set}]+", word, re.IGNORECASE)
        if match:
            return match.group(0)
        return ""


class SynonymHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.seed = profile.get('global_seed', 12345)
        self.divergence_factor = profile.get('divergence_factor', 0.0)
        self.diachronic_settings = profile.get('diachronic_settings', {})
        if not self.diachronic_settings:
            linguistic_family_path = profile.get('linguistic_family')
            if linguistic_family_path:
                pass
            self.diachronic_settings = {
                'default_divergence_factor': 0.1, 'max_synonym_variants': 3}
        self.max_variants = self.diachronic_settings.get(
            'max_synonym_variants', 3)

    def get_divergent_variant_suffix(self, lemma: str) -> str:
        if self.divergence_factor <= 0:
            return ""
        input_str = f"{lemma}_divergence_check_{self.seed}"
        hash_obj = hashlib.sha256(input_str.encode())
        hash_val = int(hash_obj.hexdigest(), 16)
        probability = (hash_val % 1000) / 1000.0
        if probability < self.divergence_factor:
            variant_seed_str = f"{lemma}_variant_select_{self.seed}"
            var_hash = int(hashlib.sha256(
                variant_seed_str.encode()).hexdigest(), 16)
            variant_idx = (var_hash % (self.max_variants - 1)) + 1
            return f"_var{variant_idx}"
        return ""


class LoanwordHandler:
    def __init__(self, profile: Dict, phonology_handler: PhonologyHandler):
        self.profile = profile
        self.config = profile.get('loanword_policy', {})
        self.enabled = self.config.get('enabled', False)
        self.modes = self.config.get(
            'modes', {'phonetic_adaptation': 0.8, 'calque': 0.15, 'semantic_extension': 0.05})
        self.calque_connector = self.config.get('calque_connector', '')
        self.phonology_handler = phonology_handler
        self.seed = profile.get('global_seed', 12345)

    def nativize_reserved_term(self, word: str) -> str:
        return self.phonology_handler.nativize_word(word)

    def process_loanword(self, foreign_word: str, components: List[str] = None, semantic_tags: List[str] = None, engine_ref=None) -> Tuple[str, str]:
        if not self.enabled:
            return self.phonology_handler.nativize_word(foreign_word), "simple_adapt"
        rng_input = f"{foreign_word}_mode_select_{self.seed}"
        rng_val = int(hashlib.sha256(rng_input.encode()).hexdigest(), 16)
        val = (rng_val % 1000) / 1000.0
        p_adapt = self.modes.get('phonetic_adaptation', 0.8)
        p_calque = self.modes.get('calque', 0.15)
        mode = "phonetic_adaptation"
        if val < p_adapt:
            mode = "phonetic_adaptation"
        elif val < (p_adapt + p_calque):
            mode = "calque"
        else:
            mode = "semantic_extension"
        if mode == "calque" and components and engine_ref:
            return self._create_calque(components, engine_ref), "calque"
        if mode == "semantic_extension" and engine_ref:
            extended_word = self._apply_semantic_extension(
                foreign_word, semantic_tags, engine_ref)
            if extended_word:
                return extended_word, "semantic_extension"
        return self.phonology_handler.nativize_word(foreign_word), "phonetic_adaptation"

    def _create_calque(self, parts: List[str], engine_ref) -> str:
        translated_parts = []
        for part in parts:
            native_word = engine_ref._get_word_form(part)
            translated_parts.append(native_word)
        return self.calque_connector.join(translated_parts)

    def _apply_semantic_extension(self, foreign_word: str, tags: List[str], engine_ref) -> Optional[str]:
        candidates = []
        if tags and engine_ref.semantic_handler.enabled:
            for tag in tags:
                related = engine_ref.semantic_handler.get_semantic_root(tag)
                if related:
                    candidates.append(related)
        if not candidates:
            sample_keys = list(engine_ref.word_cache.keys())
            if sample_keys:
                rng = random.Random(self.seed + sum(ord(c)
                                    for c in foreign_word))
                candidates.append(rng.choice(sample_keys))
        if candidates:
            chosen_lemma = candidates[0]
            if chosen_lemma in engine_ref.word_cache:
                entry = engine_ref.word_cache[chosen_lemma]
                if isinstance(entry, dict):
                    return entry.get("default", "")
                return entry
            return engine_ref._get_word_form(chosen_lemma)
        return None


class OriginalLanguageEngine:
    def __init__(self, profile_path: str):
        with open(profile_path, 'r', encoding='utf-8') as f:
            self.profile = json.load(f)
        self.family_id = None
        self.shared_base_strength = self.profile.get(
            'shared_base_strength', 0.0)
        if 'linguistic_family' in self.profile:
            family_filename = self.profile['linguistic_family']
            path_obj = Path(profile_path)
            family_path = path_obj.parent / family_filename
            if family_path.exists():
                self._load_and_merge_family(family_path)
        self.profile_id = self.profile.get('id', 'unknown')
        self.global_seed = self.profile.get('global_seed', 12345)
        self.phonology_handler = PhonologyHandler(self.profile)
        self.phonotactics = self.profile.get('phonotactics', {})
        self.vowels = self.phonology_handler.vowels
        self.consonants = self.phonology_handler.consonants
        self.templates = self.phonotactics.get('syllable_templates')
        if not self.templates:
            self.templates = self._infer_templates()
        self.syntax_engine = SyntaxEngine(profile_path)
        self.dependency_parser = DependencyParser()
        self.constituent_analyzer = ConstituentAnalyzer()
        self.clause_segmenter = ClauseSegmenter()
        self.agreement_checker = AgreementChecker(self.profile)
        self.complexity_analyzer = SyntacticComplexityAnalyzer()
        self.topicalization_handler = TopicalizationHandler(self.profile)
        self.focus_handler = FocusStructureHandler(self.profile)
        self.vowel_harmony_handler = VowelHarmonyHandler(self.profile)
        self.affix_handler = AffixHandler(
            self.profile, self.vowel_harmony_handler)
        self.degree_handler = DegreeHandler(
            self.profile, self.vowel_harmony_handler)
        self.tam_handler = TAMHandler(self.profile)
        self.reduplication_handler = ReduplicationHandler(
            self.profile, self.phonology_handler)
        self.semantic_handler = SemanticFieldHandler(self.profile)
        self.polysemy_handler = PolysemyHandler(self.profile)
        self.false_cognate_handler = FalseCognateHandler(self.profile)
        self.stress_handler = StressHandler(self.profile)
        self.transitivity_analyzer = TransitivityAnalyzer()
        self.mutation_handler = ConsonantMutationHandler(self.profile)
        self.gender_handler = GenderHandler(self.profile)
        self.synonym_handler = SynonymHandler(self.profile)
        self.loanword_handler = LoanwordHandler(
            self.profile, self.phonology_handler)
        self.concept_handler = ConceptHandler(self.profile)
        self.functional_config = self.profile.get('functional_particles', {})
        self.lexical_registers = self.profile.get('lexical_registers', {})
        if not self.lexical_registers and 'lexical_registers_defaults' in self.profile:
            self.lexical_registers = self.profile['lexical_registers_defaults']
        self.word_cache: Dict[str, Union[str, Dict]] = {}
        self.load_word_cache()

    def _load_and_merge_family(self, family_path: Path):
        try:
            with open(family_path, 'r', encoding='utf-8') as f:
                family_data = json.load(f)
        except:
            return
        if 'family_id' in family_data:
            self.family_id = family_data['family_id']
        if 'diachronic_settings' in family_data:
            self.profile['diachronic_settings'] = family_data['diachronic_settings']
        target_node_id = self.profile.get('family_node')
        if not target_node_id:
            return
        nodes = {}
        for p in family_data.get('proto_languages', []):
            nodes[p['id']] = p
        for b in family_data.get('branches', []):
            nodes[b['id']] = b
        if target_node_id not in nodes:
            return
        chain = []
        current_id = target_node_id
        while current_id:
            if current_id in nodes:
                node = nodes[current_id]
                chain.append(node)
                current_id = node.get('parent_id')
            else:
                break
        chain.reverse()
        if 'phonotactics' not in self.profile:
            self.profile['phonotactics'] = {}
        for node in chain:
            shared_ph = node.get('shared_phonotactics', {})
            if 'vowels' in shared_ph and 'vowels' not in self.profile['phonotactics']:
                self.profile['phonotactics']['vowels'] = shared_ph['vowels']
            if 'consonants' in shared_ph and 'consonants' not in self.profile['phonotactics']:
                self.profile['phonotactics']['consonants'] = shared_ph['consonants']
            if 'shared_lexicon_strength' in node and 'shared_base_strength' not in self.profile:
                self.profile['shared_base_strength'] = node['shared_lexicon_strength']
                self.shared_base_strength = node['shared_lexicon_strength']
            if 'agglutination_strength' in node and 'agglutination_strength' not in self.profile:
                self.profile['agglutination_strength'] = node['agglutination_strength']
            if 'gender_system' in node and 'gender_system' not in self.profile:
                self.profile['gender_system'] = node['gender_system']
            if 'pidgin_rules' in node and 'pidgin_rules' not in self.profile:
                self.profile['pidgin_rules'] = node['pidgin_rules']
            if 'dialect_variation' in node and 'dialect_variation' not in self.profile:
                self.profile['dialect_variation'] = node['dialect_variation']
            if 'lexical_registers_defaults' in node and 'lexical_registers_defaults' not in self.profile:
                self.profile['lexical_registers_defaults'] = node['lexical_registers_defaults']
            if 'loanword_policy_defaults' in node and 'loanword_policy' not in self.profile:
                self.profile['loanword_policy'] = node['loanword_policy_defaults']
        if 'agglutination_strength' not in self.profile:
            self.profile['agglutination_strength'] = 1.0

    def _infer_templates(self) -> List[str]:
        rng = random.Random(self.global_seed + 999)
        options = ['CV', 'CVC', 'V', 'VC', 'CCV', 'CCVC', 'CVCC']
        count = rng.randint(2, 4)
        return sorted(rng.sample(options, count))

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

    def absorb_term(self, foreign_term: str, components: List[str] = None, semantic_tags: List[str] = None) -> Dict:
        result_word, mode = self.loanword_handler.process_loanword(
            foreign_term, components, semantic_tags, self)
        entry = {
            "lemma": foreign_term,
            "default": result_word,
            "synsets": [{"word": result_word, "tags": ["loanword", mode], "affinity": 1.0}],
            "origin": "loanword",
            "absorption_mode": mode
        }
        self.word_cache[foreign_term] = entry
        self.save_word_cache()
        return entry

    def _get_word_form(self, lemma: str, tags: List[str] = None, force_word: str = None, meta: Dict = None, pos: str = None, derivation_depth: int = 0) -> str:
        entry = self.word_cache.get(lemma)
        if not entry and force_word:
            entry = {
                "lemma": lemma,
                "default": force_word,
                "synsets": [{"word": force_word, "tags": tags if tags else ["unique"], "affinity": 1.0}]
            }
            if meta:
                entry.update(meta)
            self.word_cache[lemma] = entry
            return force_word
        if entry:
            if isinstance(entry, str):
                return entry
            if isinstance(entry, dict):
                if tags:
                    synsets = entry.get('synsets', [])
                    for syn in synsets:
                        syn_tags = syn.get('tags', [])
                        for tag in tags:
                            if tag in syn_tags:
                                return syn.get('word', entry.get('default'))
                return entry.get('default')
            return str(entry)
        concept_result = self.concept_handler.resolve_concept(lemma, self)
        if concept_result:
            word, c_type, c_meta = concept_result
            return self._get_word_form(lemma, tags=['concept'], force_word=word, meta=c_meta)
        if self.affix_handler.morph_derivation_enabled:
            derived_word = self.affix_handler.try_derive_from_source(
                lemma, pos, self, current_depth=derivation_depth)
            if derived_word:
                entry = {
                    "lemma": lemma,
                    "default": derived_word,
                    "synsets": [{"word": derived_word, "tags": ["derived", "morphology"], "affinity": 1.0}],
                    "origin": "derived"
                }
                self.word_cache[lemma] = entry
                return derived_word
        return self._generate_deterministic_word(lemma)

    def process_text(self, text: str) -> str:
        reordered_text, functions_info = self.syntax_engine.process_text(text)
        final_sentences = []
        case_system = self.profile.get('case_system', {})
        preposition_handling = case_system.get(
            'preposition_handling', 'coexist')
        topicalization_config = self.profile.get('topicalization', {})
        topic_enabled = topicalization_config.get('enabled', False)
        topic_marker = topicalization_config.get('topic_marker', 'wa')
        focus_config = self.profile.get('focus_structure', {})
        focus_enabled = focus_config.get('enabled', False)
        object_focus_marker = focus_config.get('object_focus_marker', 'ko')
        suppress_case_on_focus = focus_config.get('suppress_case', False)
        ignore_digits = self.profile.get(
            'numeric_handling', {}).get('ignore_digits', True)
        capitalization_enabled = self.profile.get(
            'style', {}).get('capitalization', False)
        punctuation_map = self.profile.get(
            'style', {}).get('punctuation_map', {})
        all_terminators = set(self.profile.get('style', {}).get(
            'sentence_terminators', ['.', '!', '?']))
        all_terminators.update(self.profile.get('style', {}).get(
            'secondary_terminators', [':', ';']))
        for sent_idx, sent_data in enumerate(functions_info):
            ordered_functions = sent_data['functions']
            translated_words = []
            last_func = None
            transitivity_map = self.transitivity_analyzer.analyze(
                ordered_functions)
            topic_idx = self.topicalization_handler.identify_topic(
                ordered_functions)
            sentence_terminator = None
            for func in ordered_functions:
                orig_word = func.get("word", "")
                lemma = func.get("lemma", "")
                pos = func.get("pos", "")
                feats = func.get("feats", "")
                syntactic_func = func.get("function", "")
                deprel = func.get("deprel", "")
                is_named_entity = func.get("named_entity", False)
                if preposition_handling == 'replace' and pos == 'ADP':
                    continue
                clean_word_lower = self._clean_word(orig_word).lower()
                raw_lemma = lemma if lemma else clean_word_lower
                raw_lemma = raw_lemma.lower()
                if pos == 'PUNCT':
                    mapped_punct = punctuation_map.get(orig_word, orig_word)
                    if orig_word in all_terminators:
                        sentence_terminator = mapped_punct
                        continue
                    translated_words.append(mapped_punct)
                    last_func = func
                    continue
                if ignore_digits and pos == 'NUM':
                    if re.search(r'\d', orig_word):
                        translated_words.append(orig_word)
                        last_func = func
                        continue
                if syntactic_func in {SyntacticFunction.QUANTIFIER, SyntacticFunction.VERB_PARTICLE, SyntacticFunction.INTENSIFIER}:
                    mapping = self.functional_config.get(raw_lemma, {})
                    translated_word = ""
                    if syntactic_func == SyntacticFunction.QUANTIFIER:
                        translated_word = mapping.get(
                            'noun_word', self._get_word_form(f'{raw_lemma}_quant'))
                    elif syntactic_func == SyntacticFunction.VERB_PARTICLE:
                        translated_word = mapping.get(
                            'verb_word', self._get_word_form(f'{raw_lemma}_verb'))
                    elif syntactic_func == SyntacticFunction.INTENSIFIER:
                        translated_word = mapping.get(
                            'adj_word', self._get_word_form(f'{raw_lemma}_intens'))
                    if translated_word:
                        if self.mutation_handler.enabled:
                            prev_word = translated_words[-1] if translated_words else None
                            translated_word = self.mutation_handler.apply_mutation(
                                translated_word, prev_word, last_func)
                        translated_words.append(translated_word)
                        last_func = func
                        continue
                degree_type = None
                if self.degree_handler.enabled:
                    degree_type = self.degree_handler.detect_degree(
                        clean_word_lower, raw_lemma, feats)
                base_lemma_for_translation = raw_lemma
                if degree_type:
                    base_lemma_for_translation = self.degree_handler.get_base_lemma(
                        clean_word_lower, raw_lemma, degree_type, feats)
                if self.polysemy_handler.enabled:
                    base_lemma_for_translation = self.polysemy_handler.resolve_lemma(
                        base_lemma_for_translation, func)
                target_lemma = base_lemma_for_translation
                current_pos = pos
                translated_root = None
                context_tags = []
                if self.lexical_registers.get('enabled', False):
                    pass
                if target_lemma not in self.word_cache:
                    pass
                translated_root = self._get_word_form(
                    target_lemma, context_tags, pos=current_pos)
                current_form = translated_root
                if degree_type:
                    current_form = self.degree_handler.apply_degree(
                        current_form, degree_type)
                if self.gender_handler.enabled and (pos in {'ADJ', 'DET', 'VERB'} or syntactic_func in {SyntacticFunction.MODIFIER, SyntacticFunction.COMPLEMENT}):
                    deps = func.get('dependencies', [])
                    head_idx = deps[0] if deps else -1
                    if head_idx != -1:
                        head_func = next(
                            (f for f in ordered_functions if f['index'] == head_idx), None)
                        if head_func and head_func.get('pos') == 'NOUN':
                            head_lemma = head_func.get(
                                'lemma', head_func.get('word').lower())
                            if self.polysemy_handler.enabled:
                                head_lemma = self.polysemy_handler.resolve_lemma(
                                    head_lemma, head_func)
                            head_conlang_word = self._get_word_form(head_lemma)
                            if head_conlang_word:
                                head_gender = self.gender_handler.infer_gender(
                                    head_conlang_word)
                                current_form = self.gender_handler.apply_agreement(
                                    current_form, head_gender, pos)
                is_topic = False
                if topic_enabled and topic_idx is not None:
                    if func['index'] == topic_idx:
                        is_topic = True
                is_focus = False
                if focus_enabled:
                    if syntactic_func == SyntacticFunction.OBJECT:
                        is_focus = True
                apply_case = True
                if is_focus and suppress_case_on_focus:
                    apply_case = False
                if apply_case:
                    is_transitive = transitivity_map.get(func['index'], False)
                    current_form = self.syntax_engine.case_morphology.apply_case(
                        current_form, syntactic_func, self.syntax_engine.word_order, deprel, clause_transitivity=is_transitive)
                if is_topic and topic_marker:
                    current_form = f"{current_form} {topic_marker}"
                if is_focus and object_focus_marker:
                    current_form = f"{current_form} {object_focus_marker}"
                effective_feats = feats
                if is_focus:
                    effective_feats = f"{effective_feats}|Focus=Yes"
                if self.tam_handler.enabled and (pos in {'VERB', 'AUX'} or 'Tense=' in feats or 'Mood=' in feats or 'Aspect=' in feats or 'VerbForm=' in feats):
                    tam_feats = effective_feats
                    current_form = self.tam_handler.apply_tam(
                        current_form, tam_feats, func, ordered_functions)
                if self.reduplication_handler.enabled:
                    current_form = self.reduplication_handler.apply_reduplication(
                        current_form, effective_feats, pos=current_pos)
                if self.stress_handler.enabled:
                    current_form = self.stress_handler.apply_stress(
                        current_form)
                if self.mutation_handler.enabled:
                    prev_word = translated_words[-1] if translated_words else None
                    current_form = self.mutation_handler.apply_mutation(
                        current_form, prev_word, last_func)
                if is_named_entity:
                    current_form = current_form.capitalize()
                if orig_word[0].isupper() and pos == 'PROPN':
                    current_form = current_form.capitalize()
                translated_words.append(current_form)
                last_func = func
            if sentence_terminator:
                translated_words.append(sentence_terminator)
            if capitalization_enabled and translated_words:
                force_capitalization = True
                for idx, word in enumerate(translated_words):
                    clean_w = word.strip()
                    if not clean_w:
                        continue
                    if force_capitalization:
                        if len(word) > 0 and not word[0].isupper():
                            translated_words[idx] = word[0].upper() + word[1:]
                        force_capitalization = False
                    if any(clean_w.endswith(t) for t in all_terminators):
                        force_capitalization = True
                    else:
                        force_capitalization = False
            final_sentence_tokens = self.syntax_engine._glue_tokens(
                translated_words, ordered_functions)
            if final_sentence_tokens:
                if capitalization_enabled:
                    first = final_sentence_tokens[0]
                    if first:
                        final_sentence_tokens[0] = first[0].upper() + first[1:]
            final_sentences.append(' '.join(final_sentence_tokens))
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

    def _mutate_word(self, word: str, seed: int) -> str:
        if not word or len(word) < 2:
            return word
        import random
        random.seed(seed)
        chars = list(word)
        mutable_indices = [i for i, c in enumerate(chars) if c.isalpha()]
        if not mutable_indices:
            return word
        idx_to_mutate = random.choice(mutable_indices)
        original_char = chars[idx_to_mutate]
        is_vowel = original_char.lower() in self.vowels
        if is_vowel:
            if len(self.vowels) > 1:
                options = [v for v in self.vowels if v !=
                           original_char.lower()]
                if options:
                    new_char = random.choice(options)
                    chars[idx_to_mutate] = new_char
        else:
            if len(self.consonants) > 1:
                options = [c for c in self.consonants if c !=
                           original_char.lower()]
                if options:
                    new_char = random.choice(options)
                    chars[idx_to_mutate] = new_char
        return "".join(chars)

    def _generate_word_from_seed(self, clean_word: str, seed: int, is_derived: bool = False, base_conlang_word: str = "") -> str:
        random.seed(seed)
        if is_derived and base_conlang_word:
            split_idx = max(1, int(len(base_conlang_word) * 0.6))
            prefix = base_conlang_word[:split_idx]
            suffix_seed = int(hashlib.sha256(
                clean_word.encode()).hexdigest(), 16)
            random.seed(seed + suffix_seed)
            generated_word = prefix
            template = random.choice(self.templates)
            in_onset = True
            prev_consonant = None
            for char_type in template:
                if char_type == 'C':
                    if self.consonants:
                        candidates = list(self.consonants)
                        random.shuffle(candidates)
                        chosen_c = None
                        if prev_consonant:
                            for cand in candidates:
                                if in_onset:
                                    if self.phonology_handler.is_valid_onset_cluster(prev_consonant, cand):
                                        chosen_c = cand
                                        break
                                else:
                                    if self.phonology_handler.is_valid_coda_cluster(prev_consonant, cand):
                                        chosen_c = cand
                                        break
                            if not chosen_c:
                                chosen_c = candidates[0]
                        else:
                            for cand in candidates:
                                if not in_onset and not self.phonology_handler.is_valid_final(cand):
                                    continue
                                chosen_c = cand
                                break
                            if not chosen_c:
                                chosen_c = candidates[0]
                        generated_word += chosen_c
                        prev_consonant = chosen_c
                elif char_type == 'V':
                    if self.vowels:
                        generated_word += random.choice(list(self.vowels))
                    in_onset = False
                    prev_consonant = None
            return generated_word
        num_syllables = random.randint(self.phonotactics.get(
            'min_syllables', 1), self.phonotactics.get('max_syllables', 3))
        generated_word = ""
        for _ in range(num_syllables):
            template = random.choice(self.templates)
            in_onset = True
            prev_consonant = None
            for i, char_type in enumerate(template):
                if char_type == 'C':
                    if self.consonants:
                        candidates = list(self.consonants)
                        random.shuffle(candidates)
                        chosen_c = None
                        if prev_consonant:
                            for cand in candidates:
                                if in_onset:
                                    if self.phonology_handler.is_valid_onset_cluster(prev_consonant, cand):
                                        chosen_c = cand
                                        break
                                else:
                                    if self.phonology_handler.is_valid_coda_cluster(prev_consonant, cand):
                                        chosen_c = cand
                                        break
                            if not chosen_c:
                                chosen_c = candidates[0]
                        else:
                            is_final_in_syllable = True
                            for j in range(i+1, len(template)):
                                if template[j] == 'V':
                                    is_final_in_syllable = False
                                    break
                            for cand in candidates:
                                if is_final_in_syllable and not self.phonology_handler.is_valid_final(cand):
                                    continue
                                chosen_c = cand
                                break
                            if not chosen_c:
                                chosen_c = candidates[0]
                        generated_word += chosen_c
                        prev_consonant = chosen_c
                elif char_type == 'V':
                    if self.vowels:
                        generated_word += random.choice(list(self.vowels))
                    in_onset = False
                    prev_consonant = None
        return generated_word

    def _generate_deterministic_word(self, word: str) -> str:
        clean_word = "".join(filter(str.isalpha, word.lower()))
        if not clean_word:
            return word
        entry = {
            "lemma": clean_word,
            "default": "",
            "synsets": []
        }
        manual_target = self.false_cognate_handler.get_manual_target(
            clean_word)
        collision_bucket = self.false_cognate_handler.should_collide_naturally(
            clean_word, self.global_seed)
        base_word = ""
        is_manual = False
        if manual_target:
            if manual_target in self.word_cache:
                target_entry = self.word_cache[manual_target]
                if isinstance(target_entry, dict):
                    base_word = target_entry.get("default", "")
                else:
                    base_word = target_entry
            else:
                base_word = self._generate_deterministic_word(manual_target)
                target_entry = self.word_cache[manual_target]
                if isinstance(target_entry, dict):
                    base_word = target_entry.get("default", "")
                else:
                    base_word = target_entry
            mutation_seed = int(hashlib.sha256(
                f"{clean_word}_manual_mut_{self.global_seed}".encode()).hexdigest(), 16)
            base_word = self._mutate_word(base_word, mutation_seed)
            is_manual = True
        elif collision_bucket is not None:
            phantom_base_key = f"PHANTOM_BUCKET_{collision_bucket}"
            if phantom_base_key in self.word_cache:
                phantom_entry = self.word_cache[phantom_base_key]
                if isinstance(phantom_entry, dict):
                    base_word = phantom_entry.get("default", "")
                else:
                    base_word = phantom_entry
            else:
                base_word = self._generate_deterministic_word(phantom_base_key)
                if phantom_base_key in self.word_cache:
                    phantom_entry = self.word_cache[phantom_base_key]
                    if isinstance(phantom_entry, dict):
                        base_word = phantom_entry.get("default", "")
                    else:
                        base_word = phantom_entry
            mutation_seed = int(hashlib.sha256(
                f"{clean_word}_nat_mut_{self.global_seed}".encode()).hexdigest(), 16)
            base_word = self._mutate_word(base_word, mutation_seed)
            is_manual = True
        if not is_manual:
            root_semantic = self.semantic_handler.get_semantic_root(clean_word)
            base_word_str = clean_word
            is_derived = False
            base_conlang_word = ""
            if root_semantic and root_semantic != clean_word:
                if root_semantic in self.word_cache:
                    root_entry = self.word_cache[root_semantic]
                    if isinstance(root_entry, dict):
                        base_conlang_word = root_entry.get("default", "")
                    else:
                        base_conlang_word = root_entry
                else:
                    self._generate_deterministic_word(root_semantic)
                    if root_semantic in self.word_cache:
                        root_entry = self.word_cache[root_semantic]
                        if isinstance(root_entry, dict):
                            base_conlang_word = root_entry.get("default", "")
                        else:
                            base_conlang_word = root_entry
                base_word_str = base_conlang_word
                is_derived = True
            divergent_suffix = self.synonym_handler.get_divergent_variant_suffix(
                base_word_str)
            base_word_str += divergent_suffix
            input_str = f"{base_word_str}_{self.global_seed}_{self.profile_id}"
            using_family_base = False
            if self.shared_base_strength > 0 and self.family_id and not is_derived and not divergent_suffix:
                input_str = f"{clean_word}_{self.family_id}"
                using_family_base = True
            elif not is_derived:
                input_str = f"{clean_word}{divergent_suffix}_{self.global_seed}_{self.profile_id}"
            hash_obj = hashlib.sha256(input_str.encode())
            hash_int = int(hash_obj.hexdigest(), 16)
            base_word = self._generate_word_from_seed(
                clean_word, hash_int, is_derived, base_conlang_word)
            if using_family_base:
                mutation_chance = 1.0 - self.shared_base_strength
                mutation_seed_base = f"{clean_word}_{self.global_seed}_mutation"
                mut_hash = int(hashlib.sha256(
                    mutation_seed_base.encode()).hexdigest(), 16)
                rng_mut = random.Random(mut_hash)
                if rng_mut.random() < mutation_chance:
                    base_word = self._mutate_word(base_word, mut_hash)
        base_word = base_word if base_word else word
        entry["default"] = base_word
        entry["synsets"].append(
            {"word": base_word, "tags": ["common", "neutral"], "affinity": 1.0})
        if self.lexical_registers.get('enabled', False):
            registers = self.lexical_registers.get('registers', [])
            for reg in registers:
                name = reg.get('name')
                chance = reg.get('chance', 0.0)
                mutation_factor = reg.get('mutation_factor', 1)
                reg_seed_str = f"{clean_word}_{name}_{self.global_seed}"
                reg_hash = int(hashlib.sha256(
                    reg_seed_str.encode()).hexdigest(), 16)
                reg_rng = random.Random(reg_hash)
                if reg_rng.random() < chance:
                    variant_word = base_word
                    for _ in range(int(mutation_factor)):
                        mutation_seed = reg_rng.randint(0, 999999)
                        variant_word = self._mutate_word(
                            variant_word, mutation_seed)
                    if variant_word != base_word:
                        entry["synsets"].append({
                            "word": variant_word,
                            "tags": [name],
                            "affinity": 0.9 - (mutation_factor * 0.1)
                        })
        self.word_cache[clean_word] = entry
        return base_word

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
