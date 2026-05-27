from .phonology import PhonologyHandler
from morphosyntax_analyzer import VowelHarmonyHandler
from typing import Dict, List, Optional, Tuple, Union
import re
import random
import hashlib


class RootSystemHandler:
    def __init__(self, profile: Dict, phonology_handler: PhonologyHandler):
        self.profile = profile
        self.phonology_handler = phonology_handler
        self.root_config = profile.get('root_system', {})
        self.enabled = self.root_config.get('enabled', False)
        self.binyanim = self.root_config.get('binyanim', [])
        self.nominal_patterns = self.root_config.get('nominal_patterns', [])
        self.root_registry = self.root_config.get('root_registry', {})
        self.root_size = self.root_config.get('root_size', 3)
        self.seed = profile.get('global_seed', 12345)
        self.consonants = self.phonology_handler.consonants

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

        root = []
        if self.root_size > 0:
            root.append(rng.choice(pref_initial))
        for _ in range(1, self.root_size - 1):
            root.append(rng.choice(list(self.consonants)))
        if self.root_size > 1:
            root.append(rng.choice(pref_final))

        return root

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
                if char == 'C' and i + 1 < len(pattern) and pattern[i+1].isdigit():
                    idx_str = ""
                    j = i + 1
                    while j < len(pattern) and pattern[j].isdigit():
                        idx_str += pattern[j]
                        j += 1
                    idx = int(idx_str) - 1
                    if 0 <= idx < len(root):
                        result.append(root[idx])
                    i = j
                elif char.isdigit():
                    idx = int(char) - 1
                    if 0 <= idx < len(root):
                        result.append(root[idx])
                    i += 1
                elif char == 'C':
                    if c_count < len(root):
                        result.append(root[c_count])
                    else:
                        result.append(char)
                    c_count += 1
                    i += 1
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


class ConsonantMutationHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get('consonant_mutation', {})
        self.enabled = self.config.get('enabled', False)
        self.rules = self.config.get('rules', [])

    def apply_mutation(self, current_word: str, previous_word: Optional[str], previous_func: Optional[Dict]) -> str:
        if not self.enabled or not current_word:
            return current_word

        if not previous_word and not previous_func:
            return current_word

        processed_word = current_word

        for rule in self.rules:
            triggers = rule.get('triggers', {})
            mutations = rule.get('mutations', {})
            triggered = False

            trigger_words = set(w.lower() for w in triggers.get('words', []))
            if previous_word and previous_word.lower() in trigger_words:
                triggered = True

            if not triggered and previous_func:
                trigger_pos = set(triggers.get('pos', []))
                if previous_func.get('pos') in trigger_pos:
                    triggered = True

            if not triggered and previous_word:
                trigger_ending_chars = triggers.get('ending_chars', [])
                if trigger_ending_chars:
                    for char in trigger_ending_chars:
                        if previous_word.lower().endswith(char):
                            triggered = True
                            break

            if triggered:
                first_char = processed_word[0]
                rest = processed_word[1:]

                is_upper = first_char.isupper()
                lower_char = first_char.lower()

                if lower_char in mutations:
                    new_char = mutations[lower_char]
                    if is_upper:
                        new_char = new_char.upper()
                    processed_word = new_char + rest

        return processed_word


class GenderHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get('gender_system', {})
        self.enabled = self.config.get('enabled', False)
        self.inference_rules = self.config.get('inference', [])
        self.markers = self.config.get('markers', {})
        self.default_gender = self.config.get('default', 'masculine')
        self.harmony_handler = VowelHarmonyHandler(profile)

    def infer_gender(self, word: str) -> str:
        if not self.enabled or not word:
            return self.default_gender

        word_lower = word.lower()
        for rule in self.inference_rules:
            suffix = rule.get('suffix', '')
            if suffix and word_lower.endswith(suffix):
                return rule.get('gender', self.default_gender)

        return self.default_gender

    def apply_agreement(self, word: str, target_gender: str, pos: str) -> str:
        if not self.enabled or not target_gender:
            return word

        marker_config = self.markers.get(target_gender)
        if not marker_config:
            return word

        targets = marker_config.get('targets', [])
        if pos not in targets:
            return word

        marker = marker_config.get('marker', '')
        position = marker_config.get('position', 'suffix')

        if not marker:
            return word

        if self.harmony_handler.enabled and position == 'suffix':
            marker = self.harmony_handler.apply_harmony(word, marker)

        if position == 'suffix':
            return word + marker
        elif position == 'prefix':
            return marker + word

        return word


class CaseMorphology:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.case_system = profile.get('case_system', {})
        self.enabled = self.case_system.get('enabled', False)
        self.preposition_handling = self.case_system.get(
            'preposition_handling', 'coexist')
        self.harmony_config = profile.get('vowel_harmony', {})
        self.harmony_enabled = self.harmony_config.get('enabled', False)
        self.vowel_harmony_handler = VowelHarmonyHandler(profile)
        self.alignment = profile.get('alignment', 'nominative-accusative')
        self.semantic_config = profile.get('semantic_fields', {})
        self.animate_domains = set(self.semantic_config.get(
            'animate_domains', ['família', 'religião', 'human']))
        self.manual_groups = self.semantic_config.get('manual_groups', {})

    def _get_marker_config(self, key: str) -> Tuple[str, str, List[str], bool]:
        case_markers = self.case_system.get('markers', {})
        config = case_markers.get(key, '')

        default_pos = self.case_system.get('marker_position', 'suffix')

        if isinstance(config, dict):
            return (config.get('marker', ''),
                    config.get('type', default_pos),
                    config.get('conditions', []),
                    config.get('shift_to_determiner', False))
        return config, default_pos, [], False

    def _is_animate(self, func_data: Dict) -> bool:
        lemma = func_data.get('lemma', '').lower()
        if lemma in self.manual_groups:
            group = self.manual_groups[lemma]
            if group in self.animate_domains:
                return True

        pos = func_data.get('pos', '')
        if pos in {'PROPN', 'PRON'} or 'Animacy=Anim' in func_data.get('feats', ''):
            return True

        return False

    def _is_definite(self, func_data: Dict, all_functions: List[Dict] = None) -> bool:
        feats = func_data.get('feats', '')
        if 'Definite=Def' in feats:
            return True

        pos = func_data.get('pos', '')
        if pos in {'PROPN', 'PRON'}:
            return True

        my_index = func_data.get('index')
        if all_functions:
            for f in all_functions:
                if my_index in f.get('dependencies', []) and f.get('pos') == 'DET':
                    f_feats = f.get('feats', '')
                    if 'Definite=Def' in f_feats or 'PronType=Art' in f_feats:
                        return True

        return False

    def apply_case(self, word: str, function: str, word_order: str, deprel: str = '', clause_transitivity: bool = False, func_data: Dict = None, all_functions: List[Dict] = None) -> str:
        if not self.enabled:
            return word

        if self.preposition_handling == 'none' and function not in {'SUBJECT', 'OBJECT', 'S', 'O'}:
            return word
        target_key = ''
        current_deprel = deprel
        current_function = function
        if func_data and func_data.get('pos') == 'DET' and all_functions:
            head_idx = func_data['dependencies'][0] if func_data['dependencies'] else -1
            if head_idx != -1:
                head_func = next(
                    (f for f in all_functions if f['index'] == head_idx), None)
                if head_func:
                    current_deprel = head_func.get('deprel', '')
                    current_function = head_func.get('function', '')
                    effective_func_data = head_func
                else:
                    effective_func_data = func_data
            else:
                effective_func_data = func_data
        else:
            effective_func_data = func_data

        if current_deprel:
            core_dep = current_deprel.split(':')[0]
            if core_dep == 'obj':
                target_key = 'accusative'
                if self.alignment == 'ergative-absolutive':
                    target_key = 'absolutive'
            elif core_dep == 'iobj':
                target_key = 'dative'
            elif core_dep == 'obl':
                target_key = 'locative'
                if not self.case_system.get('markers', {}).get('locative'):
                    target_key = 'dative'
            elif core_dep == 'nsubj':
                if self.alignment == 'ergative-absolutive':
                    target_key = 'ergative' if clause_transitivity else 'absolutive'
                else:
                    target_key = 'nominative'

        if self.preposition_handling == 'none' and effective_func_data and all_functions:
            my_idx = effective_func_data.get('index')
            for child in all_functions:
                if my_idx in child.get('dependencies', []) and child.get('deprel') == 'case':
                    prep_lemma = child.get('lemma', '').lower()
                    prep_to_case = self.case_system.get(
                        'preposition_case_mapping', {})
                    if prep_lemma in prep_to_case:
                        target_key = prep_to_case[prep_lemma]
                        break

        if not target_key:
            if current_function in {'SUBJECT', 'S'}:
                if self.alignment == 'ergative-absolutive':
                    target_key = 'ergative' if clause_transitivity else 'absolutive'
                else:
                    target_key = 'nominative'
            elif current_function in {'OBJECT', 'O'}:
                if self.alignment == 'ergative-absolutive':
                    target_key = 'absolutive'
                else:
                    target_key = 'accusative'
            elif current_function in {'ADJUNCT', 'ADJ'}:
                target_key = 'locative'
                if not self.case_system.get('markers', {}).get('locative'):
                    target_key = 'dative'

        if not target_key:
            return word

        marker_text, marker_type, conditions, shift_to_determiner = self._get_marker_config(
            target_key)

        if not marker_text:
            return word

        conditions_met = True
        if conditions and effective_func_data:
            for cond in conditions:
                if cond == 'animate':
                    if not self._is_animate(effective_func_data):
                        conditions_met = False
                        break
                elif cond == 'definite':
                    if not self._is_definite(effective_func_data, all_functions):
                        conditions_met = False
                        break

        if not conditions_met:
            return word

        is_det = func_data.get('pos') == 'DET' if func_data else False
        is_noun = func_data.get('pos') in {
            'NOUN', 'PROPN', 'PRON'} if func_data else False

        if shift_to_determiner:
            if is_noun and all_functions:
                has_det = False
                my_index = func_data.get('index')
                for f in all_functions:
                    if my_index in f.get('dependencies', []) and f.get('pos') == 'DET':
                        has_det = True
                        break
                if has_det:
                    return word

            if is_noun and not has_det:
                pass
            elif is_det:
                pass
            else:
                return word

        if isinstance(marker_text, str) and marker_text.startswith('-'):
            marker_text = marker_text[1:]

        if self.harmony_enabled:
            marker_text = self.vowel_harmony_handler.apply_harmony(
                word, marker_text)

        if marker_type == 'suffix':
            return word + marker_text
        elif marker_type == 'prefix':
            is_capitalized = word and word[0].isupper()
            result = marker_text + word.lower()
            if is_capitalized:
                result = result[0].upper() + result[1:]
            return result
        elif marker_type == 'particle_before':
            if marker_text:
                return f"{marker_text} {word}"
            else:
                return word
        elif marker_type == 'particle_after':
            if marker_text:
                return f"{word} {marker_text}"
            else:
                return word

        return word + marker_text


class AgreementChecker:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.agreement_rules = profile.get('agreement_rules', {})
        self.gender_enabled = self.agreement_rules.get(
            'gender_agreement', False)
        self.number_enabled = self.agreement_rules.get(
            'number_agreement', False)
        self.gender_handler = GenderHandler(profile)

    def check_agreement(self, functions: List[Dict]) -> List[Dict]:
        violations = []
        for i, func in enumerate(functions):
            if func['function'] == 'NOUN' and func['pos'] == 'NOUN':
                modifiers = [f for f in functions if i in f.get(
                    'dependencies', [])]
                for mod in modifiers:
                    if self.gender_enabled:
                        violation = self._check_gender_agreement(func, mod)
                        if violation:
                            violations.append(violation)
                    if self.number_enabled:
                        violation = self._check_number_agreement(func, mod)
                        if violation:
                            violations.append(violation)
        return violations

    def _check_gender_agreement(self, head: Dict, modifier: Dict) -> Optional[Dict]:
        head_gender = self.gender_handler.infer_gender(head['word'])
        mod_gender = self.gender_handler.infer_gender(modifier['word'])
        if head_gender != mod_gender:
            return {
                'type': 'gender_mismatch',
                'head': head['word'],
                'modifier': modifier['word'],
                'head_gender': head_gender,
                'modifier_gender': mod_gender
            }
        return None

    def _check_number_agreement(self, head: Dict, modifier: Dict) -> Optional[Dict]:
        head_number = self._infer_number(head['word'])
        mod_number = self._infer_number(modifier['word'])
        if head_number != mod_number:
            return {
                'type': 'number_mismatch',
                'head': head['word'],
                'modifier': modifier['word'],
                'head_number': head_number,
                'modifier_number': mod_number
            }
        return None

    def _infer_number(self, word: str) -> str:
        word_lower = word.lower()
        if word_lower.endswith('s'):
            return 'plural'
        return 'singular'
