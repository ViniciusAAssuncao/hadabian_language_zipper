import hashlib
import random
import re
from typing import Dict, List, Optional, Union
from morphosyntax_analyzer import VowelHarmonyHandler
from .phonology import PhonologyHandler


class RootSystemHandler:
    def __init__(self, profile: Dict, phonology_handler: PhonologyHandler):
        self.profile = profile
        self.phonology_handler = phonology_handler
        self.morph_config = profile.get('morphological_derivation', {})
        self.root_config = profile.get('root_system', {})
        self.enabled = self.morph_config.get(
            'root_based', False) or self.root_config.get('enabled', False)
        self.binyanim = self.morph_config.get('binyanim', [])
        if not self.binyanim and 'binyanim' in self.root_config:
            self.binyanim = self.root_config['binyanim']
        self.nominal_patterns = self.morph_config.get('nominal_patterns', [])
        self.root_registry = self.morph_config.get('root_registry', {})
        self.seed = profile.get('global_seed', 12345)
        self.consonants = self.phonology_handler.consonants


class AffixHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.affix_system = profile.get('affix_system', {})
        self.enabled = self.affix_system.get('enabled', False)
        self.derivation_rules = self.affix_system.get('derivation_rules', [])
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

    def get_derivation_rule(self, from_pos: str, to_pos: str, derivation_type: str = None) -> Optional[Dict]:
        if not self.enabled:
            return None
        for rule in self.derivation_rules:
            if rule['from_pos'] == from_pos and rule['to_pos'] == to_pos:
                if derivation_type:
                    if rule.get('type') == derivation_type:
                        return rule
                else:
                    return rule
        return None

    def apply_affix(self, word: str, rule: Dict, harmony_handler=None) -> str:
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
        if position == 'suffix' and harmony_handler and harmony_handler.enabled:
            affix = harmony_handler.apply_harmony(word, affix)
        if position == 'prefix':
            return f"{affix}{word}"
        elif position == 'suffix':
            return f"{word}{affix}"
        elif position == 'infix':
            mid = len(word) // 2
            return f"{word[:mid]}{affix}{word[mid:]}"
        return word

    def try_derive_from_source(self, lemma: str, pos: Optional[str], engine_ref, current_depth: int = 0, skip_cache: bool = False, harmony_handler=None) -> Optional[str]:
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
            derivation_type = rule.get('derivation_type')
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
                    base_source_lemma, tags=None, pos=target_pos, derivation_depth=current_depth + 1, skip_cache=skip_cache)
                derivation_rule = None
                if effective_to_pos:
                    derivation_rule = self.get_derivation_rule(
                        from_pos=target_pos, to_pos=effective_to_pos, derivation_type=derivation_type)
                    if derivation_rule:
                        if engine_ref.root_handler.enabled:
                            d_type = derivation_rule.get('type')
                            if d_type:
                                pat_def = engine_ref.root_handler.get_pattern_by_type(
                                    d_type)
                                if pat_def:
                                    root = engine_ref.root_handler.generate_root(
                                        base_source_lemma)
                                    return engine_ref.root_handler.apply_pattern(root, pat_def)
                        return self.apply_affix(base_conlang_word, derivation_rule, harmony_handler)
                if replacement and not derivation_rule:
                    source_stem = lemma[:-len(suf)]
                    base_stem_word = engine_ref._get_word_form(source_stem, tags=[
                                                               'stem'], pos=target_pos, derivation_depth=current_depth + 1, skip_cache=skip_cache)
                    return self.apply_affix(base_stem_word, {'affix': replacement, 'position': 'suffix', 'force': True}, harmony_handler)
        return None


class BrokenPluralHandler:
    def __init__(self, profile: Dict, phonology_handler: PhonologyHandler):
        self.profile = profile
        self.phonology = phonology_handler
        self.config = profile.get(
            'number_system', {}).get('broken_plurals', {})
        self.enabled = self.config.get('enabled', False)
        self.patterns = self.config.get('patterns', [])
        self.number_system = profile.get('number_system', {})
        self.plural_markers = self.number_system.get(
            'markers', {}).get('plural', {})
        self.consonants = set(phonology_handler.consonants)

    def apply_plural(self, word: str, feats_str: str, pos: str) -> str:
        if not word:
            return word
        if not feats_str or 'Number=Plur' not in feats_str:
            return word
        if not self.enabled:
            return word
        if pos not in {'NOUN', 'ADJ', 'PROPN'}:
            return word
        word_lower = word.lower()
        for pat in self.patterns:
            s_pat = pat.get('singular_pattern', '')
            p_pat = pat.get('plural_pattern', '')
            if not s_pat or not p_pat:
                continue
            regex_pattern = "^"
            for char in s_pat:
                if char == 'C':
                    regex_pattern += "([{}]+)".format("".join(self.consonants))
                else:
                    regex_pattern += re.escape(char)
            regex_pattern += "$"
            match = re.match(regex_pattern, word_lower)
            if match:
                radicals = match.groups()
                plural_word = ""
                rad_idx = 0
                possible = True
                for char in p_pat:
                    if char == 'C':
                        if rad_idx < len(radicals):
                            plural_word += radicals[rad_idx]
                            rad_idx += 1
                        else:
                            possible = False
                            break
                    else:
                        plural_word += char
                if possible:
                    if word[0].isupper():
                        return plural_word.capitalize()
                    return plural_word
        marker = self.plural_markers.get('marker', '')
        if marker:
            return word + marker
        alts = self.plural_markers.get('alternatives', [])
        if alts:
            return word + alts[0]
        return word


class DualHandler:
    def __init__(self, profile: Dict, phonology_handler: PhonologyHandler):
        self.profile = profile
        self.phonology = phonology_handler
        self.config = profile.get('number_system', {})
        self.enabled = 'dual' in self.config.get('numbers', [])
        self.markers = self.config.get('dual_markers', {})
        if not self.markers and 'dual_markers' in profile:
            self.markers = profile['dual_markers']

    def apply_dual(self, word: str, feats_str: str, deprel: str, pos: str) -> str:
        if not self.enabled or not word:
            return word
        if 'Number=Dual' not in feats_str:
            return word
        if pos not in {'NOUN', 'ADJ', 'PROPN'}:
            return word
        case_key = 'nominative'
        if deprel:
            if 'obj' in deprel:
                case_key = 'accusative'
            elif 'nsubj' in deprel:
                case_key = 'nominative'
            elif 'obl' in deprel or 'iobj' in deprel:
                case_key = 'accusative'
                if 'genitive' in self.markers:
                    case_key = 'genitive'
        marker = self.markers.get(case_key, '')
        if not marker and case_key not in self.markers:
            if case_key != 'nominative' and 'accusative' in self.markers:
                marker = self.markers['accusative']
            elif 'nominative' in self.markers:
                marker = self.markers['nominative']
        if marker:
            return word + marker
        return word


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


class ConstructStateHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get('case_system', {}).get('construct_state', {})
        self.enabled = self.config.get('enabled', False)
        self.triggers = set(self.config.get(
            'trigger_dependencies', ['nmod', 'nmod:poss']))
        self.suppress_article = self.config.get(
            'suppress_article_on_head', True)
        self.changes = self.config.get('phonological_changes', [])

    def is_construct_head(self, func: Dict, all_functions: List[Dict]) -> bool:
        if not self.enabled:
            return False
        my_index = func['index']
        for f in all_functions:
            deps = f.get('dependencies', [])
            if my_index in deps:
                deprel = f.get('deprel', '')
                if deprel in self.triggers:
                    if f['pos'] in {'NOUN', 'PROPN'}:
                        return True
        return False

    def apply_construct_morphology(self, word: str, func: Dict, gender_handler) -> str:
        if not self.changes:
            return word
        gender = gender_handler.infer_gender(word)
        current_word = word
        for change in self.changes:
            pattern = change['pattern']
            replacement = change['replacement']
            condition = change.get('condition')
            if condition == 'feminine' and gender != 'feminine':
                continue
            match = re.search(pattern, current_word)
            if match:
                current_word = re.sub(pattern, replacement, current_word)
                break
        return current_word

    def generate_root(self, lemma: str) -> List[str]:
        lemma_lower = lemma.lower()
        if lemma_lower in self.root_registry:
            return list(self.root_registry[lemma_lower].replace("-", ""))

        rng = random.Random(self.seed + sum(ord(c) for c in lemma_lower))

        phonotactics = self.profile.get('phonotactics', {})

        allowed_initial = phonotactics.get('allowed_initial_clusters', [])
        if not allowed_initial:
            allowed_initial = list(self.consonants)

        forbidden_finals = set(phonotactics.get(
            'forbidden_final_consonants', []))
        allowed_final = [
            c for c in self.consonants if c not in forbidden_finals]
        if not allowed_final:
            allowed_final = list(self.consonants)

        pref_initial = self.profile.get('root_generation', {}).get(
            'preferred_initial_clusters', allowed_initial)
        pref_final = self.profile.get('root_generation', {}).get(
            'preferred_final_clusters', allowed_final)
        pref_vowels = self.profile.get('root_generation', {}).get(
            'preferred_nuclei', list(self.phonology_handler.vowels))

        c1 = rng.choice(pref_initial)
        v = rng.choice(pref_vowels)
        c2 = rng.choice(pref_final)

        return [c1, v, c2]

    def apply_pattern(self, root: List[str], pattern_def: Union[str, Dict]) -> str:
        if not root:
            return ""

        has_clusters = any(len(part) > 1 for part in root)

        if has_clusters:
            base = "".join(root)
            if isinstance(pattern_def, dict):
                suffix = pattern_def.get('suffix', '')
                base += suffix
            elif isinstance(pattern_def, str):
                base = pattern_def.replace('R', base)
        else:
            pattern = ""
            if isinstance(pattern_def, dict):
                pattern = pattern_def.get('pattern', '1e2e3')
            else:
                pattern = pattern_def or '1e2e3'

            result = []
            i = 0
            c_count = 0
            while i < len(pattern):
                char = pattern[i]
                if char == '1':
                    if len(root) > 0:
                        result.append(root[0])
                elif char == '2':
                    if len(root) > 1:
                        result.append(root[1])
                elif char == '3':
                    if len(root) > 2:
                        result.append(root[2])
                elif char == 'C':
                    if c_count < len(root):
                        result.append(root[c_count])
                    else:
                        result.append(char)
                    c_count += 1
                else:
                    result.append(char)
                i += 1
            base = "".join(result)

        return self.phonology_handler.nativize_word(base)

    def get_binyan_by_meaning(self, meaning_tag: str) -> Optional[Dict]:
        if not self.binyanim:
            return None
        matches = [
            b for b in self.binyanim if meaning_tag in b.get('meaning', '')]
        if matches:
            return matches[0]
        if meaning_tag == 'basic':
            return next((b for b in self.binyanim if b.get('form') == 'I'), self.binyanim[0])
        return None

    def get_pattern_by_type(self, type_tag: str) -> Optional[Dict]:
        for p in self.nominal_patterns:
            if p.get('type') == type_tag:
                return p
        return None
