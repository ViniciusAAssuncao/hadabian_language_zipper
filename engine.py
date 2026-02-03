from collections import defaultdict
from typing import List, Dict, Optional, Tuple, Set, Union
import json
import hashlib
from pathlib import Path
import re
import random
import unicodedata
from post_processor import polish_output
from syntax_engine import SyntaxEngine, SyntacticFunction
from morphosyntax_analyzer import (
    DependencyParser, ConstituentAnalyzer, ClauseSegmenter,
    AgreementChecker, SyntacticComplexityAnalyzer,
    TopicalizationHandler, FocusStructureHandler, TAMHandler,
    VowelHarmonyHandler, TransitivityAnalyzer, ConsonantMutationHandler,
    GenderHandler, PharyngealizationHandler, NegationHandler,
    InterrogativeHandler, CopulaHandler, CompoundingHandler
)


class LexicalConfluenceHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get('lexical_confluence', {})
        self.enabled = self.config.get('enabled', False)
        self.base_stability = self.config.get('base_stability', 100)
        self.strata = self.config.get('strata', [])
        self.sorted_strata = sorted(
            self.strata, key=lambda x: x.get('weight', 0), reverse=True)

    def determine_stratum(self, lemma: str, global_seed: int) -> Dict:
        if not self.enabled:
            return {'type': 'native'}
        input_str = f"{lemma}_confluence_{global_seed}"
        hash_obj = hashlib.sha256(input_str.encode())
        hash_val = int(hash_obj.hexdigest(), 16)
        roll = hash_val % 100
        if roll < self.base_stability:
            return {'type': 'native'}
        current_threshold = self.base_stability
        remaining_roll = roll - self.base_stability
        total_strata_weight = sum(s.get('weight', 0) for s in self.strata)
        if total_strata_weight > 0:
            normalized_roll = (
                remaining_roll / (100 - self.base_stability)) * total_strata_weight
            running_sum = 0
            for stratum in self.sorted_strata:
                weight = stratum.get('weight', 0)
                running_sum += weight
                if normalized_roll < running_sum:
                    return stratum
        return {'type': 'native'}


class AllomorphyHandler:
    def __init__(self, profile: Dict, phonology_handler):
        self.profile = profile
        self.config = profile.get('allomorphy', {})
        self.enabled = self.config.get('enabled', False)
        self.rules = self.config.get('rules', [])
        self.feature_defs = self.config.get('feature_definitions', {})
        self.phonology_handler = phonology_handler

    def apply_allomorphy(self, words: List[str]) -> List[str]:
        if not self.enabled or not words:
            return words
        result = list(words)
        for i in range(len(result) - 1):
            current_word = result[i]
            next_word_raw = result[i+1]
            clean_current = "".join(x for x in current_word if x.isalpha())
            if not clean_current:
                continue
            applicable_rules = [
                r for r in self.rules if r['target_word'] == clean_current.lower()]
            if not applicable_rules:
                continue
            next_start_char = self._get_start_char(next_word_raw)
            if not next_start_char:
                continue
            for rule in applicable_rules:
                env = rule.get('environment')
                replacement = rule.get('replacement')
                match = False
                if env == 'before_vowel':
                    if next_start_char in self.phonology_handler.vowels:
                        match = True
                elif env == 'before_consonant':
                    if next_start_char in self.phonology_handler.consonants:
                        match = True
                elif env == 'before_feature':
                    feat = rule.get('feature')
                    chars = self.feature_defs.get(feat, [])
                    if next_start_char in chars:
                        match = True
                if match:
                    if current_word[0].isupper() and replacement:
                        replacement = replacement[0].upper() + replacement[1:]
                    result[i] = replacement
                    break
        return result

    def _get_start_char(self, text: str) -> Optional[str]:
        clean = "".join(x for x in text if x.isalpha())
        if not clean:
            return None
        return clean[0].lower()


class PrepositionHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get('adposition_system', {}).get(
            'inflected_prepositions', {})
        self.enabled = self.config.get('enabled', False)
        self.forms = self.config.get('forms', {})

    def _get_person_key(self, func: Dict) -> Optional[str]:
        feats_str = func.get('feats', '')
        pos = func.get('pos')
        if not feats_str or feats_str == '_':
            return None
        feat_map = {}
        for f in feats_str.split('|'):
            if '=' in f:
                k, v = f.split('=', 1)
                feat_map[k] = v

        if pos == 'PRON':
            person = feat_map.get('Person')
            number = feat_map.get('Number')
            if not person or not number:
                return None
            num_map = {'Sing': 'sg', 'Plur': 'pl', 'Dual': 'du'}
            base_key = f"{person}{num_map.get(number, 'sg')}"
            gender = feat_map.get('Gender')
            if gender:
                gen_map = {'Masc': 'm', 'Fem': 'f', 'Neut': 'n'}
                gen_code = gen_map.get(gender, '')
                if gen_code:
                    return f"{base_key}_{gen_code}"
            return base_key

        elif pos == 'DET':
            if feat_map.get('Definite') != 'Def':
                return None
            gender = feat_map.get('Gender')
            number = feat_map.get('Number')
            if not gender or not number:
                return None
            gen_map = {'Masc': 'm', 'Fem': 'f', 'Neut': 'n'}
            num_map = {'Sing': 'sg', 'Plur': 'pl'}
            return f"def_{gen_map.get(gender, 'm')}_{num_map.get(number, 'sg')}"

        return None

    def analyze_inflections(self, functions: List[Dict], engine) -> Tuple[Dict[int, str], Set[int]]:
        if not self.enabled:
            return {}, set()
        inflection_map = {}
        absorbed_indices = set()
        for f in functions:
            if f['pos'] == 'ADP':
                prep_lemma = f['lemma'].lower()
                conlang_prep = engine._get_word_form(prep_lemma)
                if conlang_prep not in self.forms:
                    continue
                prep_idx = f['index']
                target_dependent = None
                for dep in functions:
                    if dep['pos'] in {'PRON', 'DET'}:
                        if prep_idx in dep.get('dependencies', []) or dep['index'] in f.get('dependencies', []):
                            target_dependent = dep
                            break
                if target_dependent:
                    lookup_key = self._get_person_key(target_dependent)
                    if lookup_key:
                        inflected_form = self.forms[conlang_prep].get(
                            lookup_key)
                        if not inflected_form and '_' in lookup_key and target_dependent['pos'] == 'PRON':
                            base_key = lookup_key.split('_')[0]
                            inflected_form = self.forms[conlang_prep].get(
                                base_key)
                        if inflected_form:
                            inflection_map[prep_idx] = inflected_form
                            absorbed_indices.add(target_dependent['index'])
        return inflection_map, absorbed_indices


class CliticHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get(
            'pronominal_system', {}).get('clitic_ordering', {})
        self.enabled = self.config.get('enabled', False)
        self.order = self.config.get(
            'order', ['verb', 'obj_direct', 'obj_indirect'])
        self.encliticizes = self.config.get('encliticizes', False)
        self.procliticizes = self.config.get('procliticizes', False)
        self.pronouns = profile.get(
            'pronominal_system', {}).get('object_pronouns', {})

    def _get_person_key(self, feats: str) -> Optional[str]:
        if not feats or feats == '_':
            return None
        feat_map = {}
        for f in feats.split('|'):
            if '=' in f:
                k, v = f.split('=', 1)
                feat_map[k] = v
        person = feat_map.get('Person')
        number = feat_map.get('Number')
        gender = feat_map.get('Gender')
        if not person or not number:
            return None
        num_map = {'Sing': 'sg', 'Plur': 'pl', 'Dual': 'du'}
        num_code = num_map.get(number, 'sg')
        base_key = f"{person}{num_code}"
        if gender:
            gen_map = {'Masc': 'm', 'Fem': 'f', 'Neut': 'n'}
            gen_code = gen_map.get(gender, '')
            if gen_code:
                return f"{base_key}_{gen_code}"
        return base_key

    def get_pronoun_form(self, func: Dict, p_type: str) -> str:
        key = self._get_person_key(func.get('feats', ''))
        if not key:
            return ""
        forms = self.pronouns.get(p_type, {})
        if key in forms:
            return forms[key]
        base_key = key.split('_')[0]
        return forms.get(base_key, "")

    def analyze_clitics(self, functions: List[Dict], negation_handler) -> Tuple[Dict[int, Dict], Set[int]]:
        if not self.enabled:
            return {}, set()
        clitic_map = {}
        absorbed_indices = set()
        negation_in_order = 'neg' in self.order
        for func in functions:
            if func['pos'] in {'VERB', 'AUX'}:
                verb_idx = func['index']
                clitic_data = {
                    'verb': '',
                    'neg': '',
                    'obj_direct': '',
                    'obj_indirect': ''
                }
                has_clitics = False
                if negation_in_order:
                    is_negated, trig_idx, strategy = negation_handler.detect_negation(
                        func, functions)
                    if is_negated and trig_idx is not None:
                        marker = strategy.get('marker', '')
                        clitic_data['neg'] = marker
                        absorbed_indices.add(trig_idx)
                        has_clitics = True
                dependents = [
                    f for f in functions if verb_idx in f.get('dependencies', [])]
                for dep in dependents:
                    if dep['pos'] == 'PRON':
                        deprel = dep.get('deprel', '')
                        form = ""
                        if 'obj' in deprel or 'dobj' in deprel:
                            form = self.get_pronoun_form(dep, 'direct')
                            if form:
                                clitic_data['obj_direct'] = form
                                absorbed_indices.add(dep['index'])
                                has_clitics = True
                        elif 'iobj' in deprel or 'obl' in deprel:
                            form = self.get_pronoun_form(dep, 'indirect')
                            if form:
                                clitic_data['obj_indirect'] = form
                                absorbed_indices.add(dep['index'])
                                has_clitics = True
                if has_clitics:
                    clitic_map[verb_idx] = clitic_data
        return clitic_map, absorbed_indices

    def apply_clitics(self, verb_word: str, verb_idx: int, clitic_map: Dict[int, Dict]) -> str:
        if verb_idx not in clitic_map:
            return verb_word
        data = clitic_map[verb_idx]
        data['verb'] = verb_word
        parts = []
        for element in self.order:
            val = data.get(element, '')
            if val:
                parts.append(val)
        if self.encliticizes:
            return "".join(parts)
        elif self.procliticizes:
            return "".join(parts)
        return " ".join(parts)


class PossessiveHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get(
            'determiner_system', {}).get('possessives', {})
        self.enabled = self.config.get('pronominal_suffixes', False)
        self.suffixes = self.config.get('suffixes', {})
        self.possessive_map = self.config.get('possessive_lemmas', {
            'meu': '1', 'minha': '1', 'meus': '1', 'minhas': '1',
            'teu': '2', 'tua': '2', 'teus': '2', 'tuas': '2',
            'seu': '3', 'sua': '3', 'seus': '3', 'suas': '3',
            'nosso': '1', 'nossa': '1', 'nossos': '1', 'nossas': '1',
            'vosso': '2', 'vossa': '2', 'vossos': '2', 'vossas': '2'
        })

    def get_suffix(self, feats_str: str, lemma: str = '') -> str:
        if not feats_str or feats_str == '_':
            return ""
        feats = {}
        for f in feats_str.split('|'):
            if '=' in f:
                k, v = f.split('=', 1)
                feats[k] = v
        person = feats.get('Person')
        number = feats.get('Number')
        gender = feats.get('Gender')
        if not person and lemma:
            person = self.possessive_map.get(lemma.lower())
        if not person or not number:
            return ""
        key_num = 'sg' if number == 'Sing' else 'pl'
        base_key = f"{person}{key_num}"
        if gender:
            key_gen = 'm' if gender == 'Masc' else 'f'
            full_key = f"{base_key}_{key_gen}"
            if full_key in self.suffixes:
                return self.suffixes[full_key]
        if base_key in self.suffixes:
            return self.suffixes[base_key]
        return ""

    def analyze_possessives(self, functions: List[Dict]) -> Tuple[Dict[int, str], Set[int]]:
        if not self.enabled:
            return {}, set()
        suffix_map = {}
        absorbed_indices = set()
        for f in functions:
            deprel = f.get('deprel', '')
            if 'nmod:poss' in deprel or ('det' in deprel and f.get('pos') == 'DET'):
                head_idx = f['dependencies'][0] if f['dependencies'] else -1
                if head_idx == -1:
                    continue
                head_func = next(
                    (h for h in functions if h['index'] == head_idx), None)
                if not head_func or head_func['pos'] not in {'NOUN', 'PROPN'}:
                    continue
                if f.get('pos') in {'PRON', 'DET'}:
                    suffix = self.get_suffix(
                        f.get('feats', ''), lemma=f.get('lemma', ''))
                    if suffix:
                        suffix_map[head_idx] = suffix
                        absorbed_indices.add(f['index'])
        return suffix_map, absorbed_indices


class SunLetterHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get('determiner_system', {}).get(
            'definite_article', {})
        self.enabled = self.config.get('sun_letter_assimilation', False)
        self.sun_letters = set(self.config.get('sun_letters', []))
        self.forms = set()
        if self.config.get('form'):
            self.forms.add(self.config.get('form').lower())
        if self.config.get('variants'):
            self.forms.update([v.lower()
                               for v in self.config.get('variants', [])])

    def assimilate(self, article: str, next_word: str) -> str:
        if not self.enabled or not article or not next_word:
            return article
        clean_next = "".join(filter(str.isalpha, next_word)).lower()
        if not clean_next:
            return article
        first_char = clean_next[0]
        if first_char not in self.sun_letters:
            return article
        active_form = None
        article_lower = article.lower().strip()
        base_article = article_lower.split(
        )[-1] if ' ' in article_lower else article_lower
        if base_article in self.forms:
            active_form = base_article
        if not active_form:
            for f in self.forms:
                if article_lower.endswith(f):
                    active_form = f
                    break
        if not active_form:
            return article
        match = re.search(r'([bcdfghjklmnpqrstvwxz])(\W*)$',
                          article, re.IGNORECASE)
        if match:
            consonant = match.group(1)
            separator = match.group(2)
            base = article[:match.start(1)]
            new_consonant = first_char
            if consonant.isupper():
                new_consonant = new_consonant.upper()
            return f"{base}{new_consonant}{separator}"
        return article


class SandhiHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get('phonotactics', {}).get('sandhi', {})
        self.enabled = self.config.get('enabled', False)
        self.rules = self.config.get('rules', [])

    def apply_sandhi(self, text: str) -> str:
        if not self.enabled or not text:
            return text
        processed = text
        for rule in self.rules:
            pattern = rule.get('pattern', '')
            replacement = rule.get('replacement', '')
            ignore_case = rule.get('ignore_case', False)
            flags = re.IGNORECASE if ignore_case else 0
            if pattern:
                processed = re.sub(pattern, replacement,
                                   processed, flags=flags)
        return processed


class ConstructStateHandler:
    def __init__(self, profile: Dict, gender_handler):
        self.profile = profile
        self.config = profile.get('case_system', {}).get('construct_state', {})
        self.enabled = self.config.get('enabled', False)
        self.triggers = set(self.config.get(
            'trigger_dependencies', ['nmod', 'nmod:poss']))
        self.suppress_article = self.config.get(
            'suppress_article_on_head', True)
        self.changes = self.config.get('phonological_changes', [])
        self.gender_handler = gender_handler

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

    def apply_construct_morphology(self, word: str, func: Dict) -> str:
        if not self.changes:
            return word
        gender = self.gender_handler.infer_gender(word)
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
        self.phonological_rules = self.phonotactics.get(
            'phonological_rules', [])
        self.compiled_rules = self._compile_all_rules()
        self.monophthong_config = self.phonotactics.get(
            'monophthongization', {})
        self.monophthong_enabled = self.monophthong_config.get(
            'enabled', False)
        self.monophthong_rules = self.monophthong_config.get('rules', [])
        self.transition_config = self.phonotactics.get('transition_matrix', {})
        self.transition_enabled = self.transition_config.get('enabled', False)
        self.transition_matrix = self.transition_config.get('matrix', {})
        self.transition_default_weight = self.transition_config.get(
            'default_weight', 1)
        self.aesthetic = profile.get('aesthetic_profile', {})
        self.syllable_dist = self.aesthetic.get('syllable_count_distribution')
        self.cluster_density = self.aesthetic.get('cluster_density', 0.5)

    def _compile_all_rules(self):
        compiled = []
        for rule in self.phonological_rules:
            input_pat = rule.get('input')
            output_pat = rule.get('output')
            register = rule.get('register')
            if input_pat and output_pat is not None:
                regex, repl = self._compile_rule_regex(input_pat, output_pat)
                compiled.append({
                    'regex': regex,
                    'replacement': repl,
                    'register': register
                })
        return compiled

    def _compile_rule_regex(self, input_pat: str, output_pat: str) -> Tuple[str, str]:
        c_set = "".join(
            self.consonants) if self.consonants else "bcdfghjklmnpqrstvwxz"
        v_set = "".join(self.vowels) if self.vowels else "aeiou"
        regex_parts = []
        input_map = []
        i = 0
        group_idx = 1
        while i < len(input_pat):
            char = input_pat[i]
            if char == 'C':
                regex_parts.append(f"([{c_set}])")
                input_map.append({'type': 'C', 'group': group_idx})
                group_idx += 1
            elif char == 'V':
                regex_parts.append(f"([{v_set}])")
                input_map.append({'type': 'V', 'group': group_idx})
                group_idx += 1
            elif char == '$':
                regex_parts.append("$")
            elif char == '^':
                regex_parts.append("^")
            else:
                regex_parts.append(re.escape(char))
            i += 1
        input_regex = "".join(regex_parts)
        replacement_parts = []
        c_counter = 0
        v_counter = 0
        input_cs = [x for x in input_map if x['type'] == 'C']
        input_vs = [x for x in input_map if x['type'] == 'V']
        i = 0
        while i < len(output_pat):
            char = output_pat[i]
            if char == 'C':
                if c_counter < len(input_cs):
                    g = input_cs[c_counter]['group']
                    replacement_parts.append(f"\\g<{g}>")
                    c_counter += 1
                else:
                    replacement_parts.append("C")
            elif char == 'V':
                if v_counter < len(input_vs):
                    g = input_vs[v_counter]['group']
                    replacement_parts.append(f"\\g<{g}>")
                    v_counter += 1
                else:
                    replacement_parts.append("V")
            else:
                replacement_parts.append(char)
            i += 1
        return input_regex, "".join(replacement_parts)

    def apply_monophthongization(self, word: str) -> str:
        if not self.monophthong_enabled or not word:
            return word
        current_word = word
        sorted_rules = sorted(self.monophthong_rules,
                              key=lambda x: x.get('priority', 0), reverse=True)
        for rule in sorted_rules:
            inp = rule.get('input')
            out = rule.get('output')
            if inp and out:
                current_word = current_word.replace(inp, out)
        return current_word

    def apply_rules(self, word: str, register: str) -> str:
        if not word:
            return word
        current_word = word
        for rule in self.compiled_rules:
            if rule['register'] and rule['register'] != register:
                continue
            try:
                current_word = re.sub(
                    rule['regex'], rule['replacement'], current_word)
            except:
                continue
        return current_word

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
        result = self.apply_monophthongization(result)
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

    def get_weighted_choice(self, candidates: List[str], prev_char: Optional[str], rng) -> str:
        if not self.transition_enabled or not prev_char or not candidates:
            return rng.choice(candidates)

        row = self.transition_matrix.get(prev_char.lower(), {})
        weights = []
        for c in candidates:
            weights.append(row.get(c.lower(), self.transition_default_weight))

        total = sum(weights)
        if total <= 0:
            return rng.choice(candidates)

        threshold = rng.random() * total
        current = 0
        for i, w in enumerate(weights):
            current += w
            if current >= threshold:
                return candidates[i]
        return candidates[-1]

    def get_syllable_count(self, rng) -> int:
        if self.syllable_dist:
            counts = []
            weights = []
            for k, v in self.syllable_dist.items():
                counts.append(int(k))
                weights.append(float(v))

            total = sum(weights)
            if total > 0:
                r = rng.random() * total
                upto = 0
                for c, w in zip(counts, weights):
                    if upto + w >= r:
                        return c
                    upto += w
                return counts[-1]

        return rng.randint(self.phonotactics.get('min_syllables', 1),
                           self.phonotactics.get('max_syllables', 3))

    def select_template(self, rng, templates: List[str]) -> str:
        if not templates:
            return "CV"

        if not self.aesthetic:
            return rng.choice(templates)

        complex_templates = [t for t in templates if 'CC' in t]
        simple_templates = [t for t in templates if 'CC' not in t]

        if not complex_templates:
            return rng.choice(simple_templates)
        if not simple_templates:
            return rng.choice(complex_templates)

        if rng.random() < self.cluster_density:
            return rng.choice(complex_templates)
        else:
            return rng.choice(simple_templates)


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

    def generate_root(self, lemma: str) -> List[str]:
        lemma_lower = lemma.lower()
        if lemma_lower in self.root_registry:
            return list(self.root_registry[lemma_lower].replace("-", ""))
        rng = random.Random(self.seed + sum(ord(c) for c in lemma_lower))

        pref_initial = self.profile.get('root_generation', {}).get(
            'preferred_initial_clusters', ['str', 'st', 'br'])
        pref_final = self.profile.get('root_generation', {}).get(
            'preferred_final_clusters', ['cht', 'ft', 'nd'])
        pref_vowels = self.profile.get('root_generation', {}).get(
            'preferred_nuclei', ['a', 'o', 'u'])

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


class ConceptHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get('abstract_concepts', {})
        self.enabled = self.config.get('enabled', False)
        self.mappings = {k.lower(): v for k, v in self.config.get(
            'mappings', {}).items()}
        root_mappings = profile.get('mappings', {})
        if root_mappings:
            for k, v in root_mappings.items():
                if k.lower() not in self.mappings:
                    self.mappings[k.lower()] = v
        self.local_overrides = {k.lower(): v for k, v in self.config.get(
            'local_overrides', {}).items()}
        self.definitions = self.config.get('definitions', {})
        self.purism_level = profile.get('cultural_purism', 0.0)
        self.universal_registry = self._load_universal_registry()

    def _load_universal_registry(self) -> Dict:
        paths_to_try = [
            Path('reserved_universal.json'),
            Path('./conlangs/reserved_universal.json'),
        ]
        for p in paths_to_try:
            if p.exists():
                try:
                    with open(p, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except:
                    continue
        return {"concepts": {}, "mappings_ln": {}}

    def resolve_concept(self, lemma: str, engine_instance, word_form: str = None) -> Optional[Tuple[str, str, Dict]]:
        if not self.enabled:
            return None

        clean_lemma = lemma.lower().strip()

        if word_form:
            clean_word = word_form.lower().strip()
            if clean_word in self.mappings:
                return self.mappings[clean_word], 'direct_mapping', {'origin': 'mapping_table_surface'}

        if clean_lemma in self.mappings:
            concept_id = self.mappings[clean_lemma]
        else:
            concept_id = self.universal_registry.get(
                'mappings_ln', {}).get(clean_lemma)

        if not concept_id:
            return None

        concept_id_lower = concept_id.lower() if isinstance(
            concept_id, str) else concept_id

        if concept_id_lower in self.local_overrides:
            word = self.local_overrides[concept_id_lower]
            return word, 'override', {'origin': 'local_override', 'concept_id': concept_id}

        if clean_lemma in self.local_overrides:
            word = self.local_overrides[clean_lemma]
            return word, 'override', {'origin': 'local_override_direct'}

        if concept_id in self.definitions:
            definition = self.definitions[concept_id]
            if isinstance(definition, str):
                generated_word = engine_instance._generate_deterministic_word(
                    concept_id)
                return generated_word, 'unique', {'description': definition}

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
                    base_source_lemma, tags=None, pos=target_pos, derivation_depth=current_depth + 1)
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
                        return self.apply_affix(base_conlang_word, derivation_rule)
                if replacement and not derivation_rule:
                    source_stem = lemma[:-len(suf)]
                    base_stem_word = engine_ref._get_word_form(
                        source_stem, tags=['stem'], pos=target_pos, derivation_depth=current_depth + 1)
                    return self.apply_affix(base_stem_word, {'affix': replacement, 'position': 'suffix', 'force': True})
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


class DemonstrativeHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get(
            'determiner_system', {}).get('demonstratives', {})
        self.enabled = bool(self.config)
        self.proximal = self.config.get('proximal', {})
        self.distal = self.config.get('distal', {})
        self.mappings = self.config.get('source_mappings', {
            'proximal': ['este', 'esta', 'isto', 'esse', 'essa', 'isso', 'estes', 'estas', 'esses', 'essas'],
            'distal': ['aquele', 'aquela', 'aquilo', 'aqueles', 'aquelas']
        })
        self.heuristic_enabled = self.config.get(
            'gender_inheritance_heuristic', True)

    def is_demonstrative(self, func: Dict) -> bool:
        if func['pos'] not in {'DET', 'PRON'}:
            return False
        lemma = func.get('lemma', '').lower()
        word = func.get('word', '').lower()
        if lemma in self.mappings.get('proximal', []) or word in self.mappings.get('proximal', []):
            return True
        if lemma in self.mappings.get('distal', []) or word in self.mappings.get('distal', []):
            return True
        return False

    def get_form(self, func: Dict, all_functions: List[Dict], engine_ref) -> str:
        lemma = func.get('lemma', '').lower()
        word = func.get('word', '').lower()
        target_type = None
        if lemma in self.mappings.get('proximal', []) or word in self.mappings.get('proximal', []):
            target_type = 'proximal'
        elif lemma in self.mappings.get('distal', []) or word in self.mappings.get('distal', []):
            target_type = 'distal'
        if not target_type:
            return func.get('word', '')
        forms = self.proximal if target_type == 'proximal' else self.distal
        head_idx = func['dependencies'][0] if func['dependencies'] else -1
        gender = 'masculine'
        number = 'singular'
        source_gender_hint = 'masculine'
        source_feats = func.get('feats', '')
        if 'Gender=Fem' in source_feats:
            source_gender_hint = 'feminine'
        if head_idx != -1:
            head = next(
                (f for f in all_functions if f['index'] == head_idx), None)
            if head:
                head_lemma = head.get('lemma', head.get('word', '')).lower()
                head_conlang_word = engine_ref._get_word_form(head_lemma)
                gender = engine_ref.gender_handler.infer_gender(
                    head_conlang_word)
                if gender == engine_ref.gender_handler.default_gender and source_gender_hint == 'feminine':
                    if self.heuristic_enabled:
                        gender = 'feminine'
                feats = head.get('feats', '')
                if 'Number=Plur' in feats:
                    number = 'plural'
                elif 'Number=Sing' in feats:
                    number = 'singular'
        if 'Number=Plur' in source_feats:
            number = 'plural'
        new_word = ""
        if number == 'plural':
            new_word = forms.get('pl', '')
        else:
            key = 'sg_f' if gender == 'feminine' else 'sg_m'
            new_word = forms.get(key, '')
        if new_word:
            if func.get('word', '') and func['word'][0].isupper():
                new_word = new_word.capitalize()
            return new_word
        return func.get('word', '')


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
        self.pharyngealization_handler = PharyngealizationHandler(self.profile)
        self.gender_handler = GenderHandler(self.profile)
        self.synonym_handler = SynonymHandler(self.profile)
        self.loanword_handler = LoanwordHandler(
            self.profile, self.phonology_handler)
        self.concept_handler = ConceptHandler(self.profile)
        self.root_handler = RootSystemHandler(
            self.profile, self.phonology_handler)
        self.broken_plural_handler = BrokenPluralHandler(
            self.profile, self.phonology_handler)
        self.dual_handler = DualHandler(
            self.profile, self.phonology_handler)
        self.construct_state_handler = ConstructStateHandler(
            self.profile, self.gender_handler)
        self.sun_letter_handler = SunLetterHandler(self.profile)
        self.sandhi_handler = SandhiHandler(self.profile)
        self.negation_handler = NegationHandler(self.profile)
        self.possessive_handler = PossessiveHandler(self.profile)
        self.clitic_handler = CliticHandler(self.profile)
        self.interrogative_handler = InterrogativeHandler(self.profile)
        self.demonstrative_handler = DemonstrativeHandler(self.profile)
        self.copula_handler = CopulaHandler(self.profile)
        self.allomorphy_handler = AllomorphyHandler(
            self.profile, self.phonology_handler)
        self.compounding_handler = CompoundingHandler(self.profile)
        self.functional_config = self.profile.get('functional_particles', {})
        self.lexical_registers = self.profile.get('lexical_registers', {})
        if not self.lexical_registers and 'lexical_registers_defaults' in self.profile:
            self.lexical_registers = self.profile['lexical_registers_defaults']
        self.confluence_handler = LexicalConfluenceHandler(self.profile)
        self.word_cache: Dict[str, Union[str, Dict]] = {}
        self.source_engines: Dict[str, 'OriginalLanguageEngine'] = {}
        self.preposition_handler = PrepositionHandler(self.profile)
        self.vocabulary_override = self.profile.get('vocabulary', {})
        self.load_word_cache()
        self.processing_stack = set()

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
        if 'root_system' not in self.profile:
            family_roots = None
            for p in family_data.get('proto_languages', []):
                if 'root_system' in p:
                    family_roots = p['root_system']
            if family_roots:
                self.profile['root_system'] = family_roots
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

    def _get_word_form(self, lemma: str, tags: List[str] = None, force_word: str = None, meta: Dict = None, pos: str = None, derivation_depth: int = 0, word_form: str = None) -> str:
        lemma = lemma.lower().strip()

        if lemma in self.vocabulary_override:
            return self.vocabulary_override[lemma]
        if lemma.lower() in self.vocabulary_override:
            return self.vocabulary_override[lemma.lower()]

        if lemma in self.processing_stack:
            return self._generate_deterministic_word(lemma, depth=100)
        self.processing_stack.add(lemma)
        try:
            if word_form:
                res = self.concept_handler.resolve_concept(
                    lemma, self, word_form=word_form)
                if res and res[2].get('origin') == 'mapping_table_surface':
                    return res[0]

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

            concept_result = self.concept_handler.resolve_concept(
                lemma, self, word_form=word_form)
            if concept_result:
                word, c_type, c_meta = concept_result
                return self._get_word_form(lemma, tags=['concept'], force_word=word, meta=c_meta)

            if self.root_handler.enabled and (pos == 'VERB' or pos == 'NOUN'):
                root = self.root_handler.generate_root(lemma)
                pattern_def = self.root_handler.get_binyan_by_meaning('basic')
                if tags:
                    for tag in tags:
                        derived_binyan = self.root_handler.get_binyan_by_meaning(
                            tag)
                        if derived_binyan:
                            pattern_def = derived_binyan
                            break
                if pattern_def:
                    generated_word = self.root_handler.apply_pattern(
                        root, pattern_def)
                    entry = {
                        "lemma": lemma,
                        "default": generated_word,
                        "synsets": [{"word": generated_word, "tags": ["root_derived"], "affinity": 1.0}],
                        "origin": "triconsonantal_system",
                        "root": "".join(root)
                    }
                    self.word_cache[lemma] = entry
                    return generated_word

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
            return self._generate_deterministic_word(lemma, depth=0)
        finally:
            self.processing_stack.remove(lemma)

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
        hoistable_terminators = {'.', '!', '?'}
        all_terminators = set(self.profile.get('style', {}).get(
            'sentence_terminators', ['.', '!', '?']))
        all_terminators.update(self.profile.get('style', {}).get(
            'secondary_terminators', [':', ';']))

        last_content_word_str = None
        last_content_func = None

        for sent_idx, sent_data in enumerate(functions_info):
            ordered_functions = sent_data['functions']
            translated_words = []
            transitivity_map = self.transitivity_analyzer.analyze(
                ordered_functions)
            topic_idx = self.topicalization_handler.identify_topic(
                ordered_functions)
            sentence_terminator = None
            is_question, q_type = self.interrogative_handler.is_yes_no_question(
                sent_data['original'])
            construct_heads_indices = set()
            if self.construct_state_handler.enabled:
                for func in ordered_functions:
                    if func['pos'] in {'NOUN', 'PROPN'}:
                        if self.construct_state_handler.is_construct_head(func, ordered_functions):
                            construct_heads_indices.add(func['index'])
            absorbed_indices = set()
            clitic_map = {}
            if self.clitic_handler.enabled:
                clitic_map, clitic_absorbed = self.clitic_handler.analyze_clitics(
                    ordered_functions, self.negation_handler)
                absorbed_indices.update(clitic_absorbed)
            if self.negation_handler.enabled:
                for func in ordered_functions:
                    if func['index'] in absorbed_indices:
                        continue
                    is_negated, trigger_idx, neg_strategy = self.negation_handler.detect_negation(
                        func, ordered_functions)
                    if is_negated and trigger_idx is not None:
                        should_absorb = True
                        trigger_word = next(
                            (f['word'].lower() for f in ordered_functions if f['index'] == trigger_idx), '')
                        if neg_strategy.get('type') == 'emphatic_negation':
                            if trigger_word not in {'não', 'nao', 'not'}:
                                should_absorb = False
                        if should_absorb:
                            absorbed_indices.add(trigger_idx)
            possessive_suffixes_map = {}
            if self.possessive_handler.enabled:
                possessive_suffixes_map, possessive_indices = self.possessive_handler.analyze_possessives(
                    ordered_functions)
                absorbed_indices.update(possessive_indices)
            inflected_preps_map = {}
            if self.preposition_handler.enabled:
                inflected_preps_map, prep_absorbed = self.preposition_handler.analyze_inflections(
                    ordered_functions, self)
                absorbed_indices.update(prep_absorbed)

            compound_map = {}
            if self.compounding_handler.enabled:
                compound_map, compound_absorbed = self.compounding_handler.apply_compounding(
                    ordered_functions, self)
                absorbed_indices.update(compound_absorbed)

            for i, func in enumerate(ordered_functions):
                if func['index'] in absorbed_indices:
                    continue

                if 'mwt' in func and self.concept_handler.enabled:
                    mwt = func['mwt']
                    span_indices = set(mwt['span_indices'])
                    mapping = self.concept_handler.resolve_concept(
                        mwt['form'], self)
                    if mapping:
                        if not span_indices.intersection(absorbed_indices):
                            remaining_span = span_indices - {func['index']}
                            found_count = 0
                            if i + len(remaining_span) < len(ordered_functions):
                                for k in range(1, len(remaining_span) + 1):
                                    next_f = ordered_functions[i + k]
                                    if next_f['index'] in remaining_span:
                                        found_count += 1
                            if found_count == len(remaining_span):
                                word, _, _ = mapping
                                translated_words.append(word)
                                absorbed_indices.update(remaining_span)
                                last_content_word_str = word
                                last_content_func = func
                                continue

                orig_word = func.get("word", "")
                lemma = func.get("lemma", "")
                pos = func.get("pos", "")
                feats = func.get("feats", "")
                syntactic_func = func.get("function", "")
                deprel = func.get("deprel", "")
                is_named_entity = func.get("named_entity", False)

                if preposition_handling == 'replace' and pos == 'ADP':
                    continue

                should_drop_article = False
                if self.profile.get('drop_articles', False):
                    is_det_pos = (pos == 'DET')
                    is_det_rel = (deprel == 'det')

                    if is_det_pos or is_det_rel:
                        f_feats = func.get('feats', '_')
                        word_lower = orig_word.lower()
                        if 'Definite=Def' in f_feats or 'PronType=Art' in f_feats or word_lower in {'o', 'a', 'os', 'as'}:
                            if 'PronType=Prs' not in f_feats and 'PronType=Dem' not in f_feats:
                                should_drop_article = True

                if should_drop_article:
                    continue

                clean_word_lower = self._clean_word(orig_word).lower()
                raw_lemma = lemma if lemma else clean_word_lower
                raw_lemma = raw_lemma.lower()

                if pos == 'PUNCT':
                    mapped_punct = punctuation_map.get(orig_word, orig_word)
                    if orig_word in hoistable_terminators:
                        sentence_terminator = mapped_punct
                        continue
                    translated_words.append(mapped_punct)
                    continue

                if ignore_digits and pos == 'NUM':
                    if re.search(r'\d', orig_word):
                        translated_words.append(orig_word)
                        last_content_word_str = orig_word
                        last_content_func = func
                        continue

                if self.copula_handler.enabled and deprel == 'cop':
                    copula_form = self.copula_handler.get_copula_form(
                        func, ordered_functions, self)
                    if copula_form is None:
                        continue
                    if self.mutation_handler.enabled:
                        prev_word = last_content_word_str
                        copula_form = self.mutation_handler.apply_mutation(
                            copula_form, prev_word, last_content_func)
                    translated_words.append(copula_form)
                    last_content_word_str = copula_form
                    last_content_func = func
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
                            prev_word = last_content_word_str
                            translated_word = self.mutation_handler.apply_mutation(
                                translated_word, prev_word, last_content_func)
                        translated_words.append(translated_word)
                        last_content_word_str = translated_word
                        last_content_func = func
                        continue

                if pos == 'DET' and self.construct_state_handler.enabled and self.construct_state_handler.suppress_article:
                    head_idx = func.get('dependencies', [-1])[0]
                    if head_idx in construct_heads_indices:
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

                if self.demonstrative_handler.enabled and self.demonstrative_handler.is_demonstrative(func):
                    current_form = self.demonstrative_handler.get_form(
                        func, ordered_functions, self)
                else:
                    translated_root = self._get_word_form(
                        target_lemma, context_tags, pos=current_pos, word_form=clean_word_lower)
                    current_form = translated_root

                if func['index'] in compound_map:
                    current_form = compound_map[func['index']]

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

                if self.broken_plural_handler.enabled:
                    current_form = self.broken_plural_handler.apply_plural(
                        current_form, feats, current_pos
                    )

                if self.dual_handler.enabled:
                    current_form = self.dual_handler.apply_dual(
                        current_form, feats, deprel, current_pos
                    )

                if self.construct_state_handler.enabled and func['index'] in construct_heads_indices:
                    current_form = self.construct_state_handler.apply_construct_morphology(
                        current_form, func)

                if func['index'] in possessive_suffixes_map:
                    suffix = possessive_suffixes_map[func['index']]
                    current_form = f"{current_form}{suffix}"

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

                if apply_case and func['index'] not in compound_map:
                    is_transitive = transitivity_map.get(func['index'], False)
                    current_form = self.syntax_engine.case_morphology.apply_case(
                        current_form, syntactic_func, self.syntax_engine.word_order, deprel, clause_transitivity=is_transitive, func_data=func, all_functions=ordered_functions)

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

                is_negated, trigger_idx, neg_strategy = self.negation_handler.detect_negation(
                    func, ordered_functions)

                clitic_handled_neg = False
                if self.clitic_handler.enabled and func['index'] in clitic_map:
                    if 'neg' in self.clitic_handler.order and clitic_map[func['index']].get('neg'):
                        clitic_handled_neg = True

                if is_negated and not clitic_handled_neg:
                    current_form = self.negation_handler.apply_negation(
                        current_form, neg_strategy)

                if self.clitic_handler.enabled and func['index'] in clitic_map:
                    current_form = self.clitic_handler.apply_clitics(
                        current_form, func['index'], clitic_map)

                if self.reduplication_handler.enabled:
                    current_form = self.reduplication_handler.apply_reduplication(
                        current_form, effective_feats, pos=current_pos)

                if self.stress_handler.enabled:
                    current_form = self.stress_handler.apply_stress(
                        current_form)

                if self.pharyngealization_handler.enabled:
                    current_form = self.pharyngealization_handler.apply_effect(
                        current_form)

                if self.mutation_handler.enabled:
                    prev_word = last_content_word_str
                    current_form = self.mutation_handler.apply_mutation(
                        current_form, prev_word, last_content_func)

                if is_named_entity:
                    current_form = current_form.capitalize()

                if orig_word[0].isupper() and pos == 'PROPN':
                    current_form = current_form.capitalize()

                if func['index'] in inflected_preps_map:
                    translated_root = inflected_preps_map[func['index']]
                    current_form = translated_root

                translated_words.append(current_form)
                last_content_word_str = current_form
                last_content_func = func

                if self.sun_letter_handler.enabled and len(translated_words) > 1 and last_content_func:
                    if last_content_func.get('pos') == 'DET':
                        prev_word = translated_words[-2]
                        assimilated_prev = self.sun_letter_handler.assimilate(
                            prev_word, current_form)
                        translated_words[-2] = assimilated_prev

            if sentence_terminator:
                translated_words.append(sentence_terminator)

            if is_question and self.interrogative_handler.enabled:
                particle = self.interrogative_handler.get_particle(q_type)
                if particle:
                    translated_words.insert(0, particle)
                    meta_config = self.profile.get('interrogative_system', {}).get(
                        'particle_metadata', {})
                    particle_meta = {
                        'word': particle,
                        'lemma': particle,
                        'pos': meta_config.get('pos', 'PART'),
                        'function': meta_config.get('function', 'INT'),
                        'deprel': meta_config.get('deprel', 'discourse'),
                        'index': -1,
                        'dependencies': []
                    }
                    ordered_functions.insert(0, particle_meta)

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

            if self.allomorphy_handler.enabled:
                translated_words = self.allomorphy_handler.apply_allomorphy(
                    translated_words)

            functions_for_glue = []
            for func in ordered_functions:
                if func['index'] not in absorbed_indices:
                    functions_for_glue.append(func)

            final_sentence_tokens = self.syntax_engine._glue_tokens(
                translated_words, functions_for_glue)

            if final_sentence_tokens:
                if capitalization_enabled:
                    first = final_sentence_tokens[0]
                    if first:
                        final_sentence_tokens[0] = first[0].upper() + first[1:]

            final_str = ' '.join(final_sentence_tokens)
            if self.sandhi_handler.enabled:
                final_str = self.sandhi_handler.apply_sandhi(final_str)

            final_sentences.append(final_str)

        self.save_word_cache()
        final_output = ' '.join(final_sentences)
        final_output = polish_output(
            final_output, self.profile, text, functions_info)
        return final_output

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
        return "".join(re.findall(r"[\w]", word, re.UNICODE))

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

    def _fetch_source_word(self, source_id: str, lemma: str) -> str:
        if source_id in self.source_engines:
            engine = self.source_engines[source_id]
            return engine._get_word_form(lemma)

        possible_paths = [
            Path(f"{source_id}.json"),
            Path(f"./conlangs/{source_id}.json"),
            Path(f"../conlangs/{source_id}.json"),
            Path(f"cache/{source_id}.json")
        ]

        path_to_use = None
        for p in possible_paths:
            if p.exists():
                path_to_use = str(p)
                break

        if path_to_use:
            try:
                new_engine = OriginalLanguageEngine(path_to_use)
                self.source_engines[source_id] = new_engine
                return new_engine._get_word_form(lemma)
            except Exception:
                pass

        rng = random.Random(self.global_seed + sum(ord(c) for c in lemma))
        fallback = "".join(rng.choice(list(self.phonotactics.get(
            'consonants', 'bcdfghjklmnpqrstvwxz'))) for _ in range(5))
        return fallback

    def _generate_word_from_seed(self, clean_word: str, seed: int, is_derived: bool = False, base_conlang_word: str = "") -> str:
        random.seed(seed)
        if is_derived and base_conlang_word:
            split_idx = max(1, int(len(base_conlang_word) * 0.6))
            prefix = base_conlang_word[:split_idx]
            suffix_seed = int(hashlib.sha256(
                clean_word.encode()).hexdigest(), 16)
            random.seed(seed + suffix_seed)
            generated_word = prefix
            template = self.phonology_handler.select_template(
                random, self.templates)
            in_onset = True
            prev_consonant = None
            last_char_generated = prefix[-1] if prefix else None

            for char_type in template:
                if char_type == 'C':
                    valid_candidates = []
                    candidates = list(self.consonants)

                    if prev_consonant:
                        for cand in candidates:
                            if in_onset:
                                if self.phonology_handler.is_valid_onset_cluster(prev_consonant, cand):
                                    valid_candidates.append(cand)
                            else:
                                if self.phonology_handler.is_valid_coda_cluster(prev_consonant, cand):
                                    valid_candidates.append(cand)
                    else:
                        is_final_in_syllable = True
                        current_template_idx = template.find(char_type)

                        for j in range(current_template_idx + 1, len(template)):
                            if template[j] == 'V':
                                is_final_in_syllable = False
                                break

                        for cand in candidates:
                            if is_final_in_syllable and not self.phonology_handler.is_valid_final(cand):
                                continue
                            valid_candidates.append(cand)

                    chosen_c = None
                    if valid_candidates:
                        chosen_c = self.phonology_handler.get_weighted_choice(
                            valid_candidates, last_char_generated, random)
                    else:
                        if self.consonants:
                            chosen_c = random.choice(list(self.consonants))

                    if chosen_c:
                        generated_word += chosen_c
                        prev_consonant = chosen_c
                        last_char_generated = chosen_c

                elif char_type == 'V':
                    if self.vowels:
                        chosen_v = self.phonology_handler.get_weighted_choice(
                            list(self.vowels), last_char_generated, random)
                        generated_word += chosen_v
                        last_char_generated = chosen_v
                    in_onset = False
                    prev_consonant = None
            return generated_word

        num_syllables = self.phonology_handler.get_syllable_count(random)
        generated_word = ""
        last_char_generated = None

        for _ in range(num_syllables):
            template = self.phonology_handler.select_template(
                random, self.templates)
            in_onset = True
            prev_consonant = None

            for i, char_type in enumerate(template):
                if char_type == 'C':
                    valid_candidates = []
                    candidates = list(self.consonants)

                    if prev_consonant:
                        for cand in candidates:
                            if in_onset:
                                if self.phonology_handler.is_valid_onset_cluster(prev_consonant, cand):
                                    valid_candidates.append(cand)
                            else:
                                if self.phonology_handler.is_valid_coda_cluster(prev_consonant, cand):
                                    valid_candidates.append(cand)
                    else:
                        is_final_in_syllable = True
                        for j in range(i+1, len(template)):
                            if template[j] == 'V':
                                is_final_in_syllable = False
                                break

                        for cand in candidates:
                            if is_final_in_syllable and not self.phonology_handler.is_valid_final(cand):
                                continue
                            valid_candidates.append(cand)

                    chosen_c = None
                    if valid_candidates:
                        chosen_c = self.phonology_handler.get_weighted_choice(
                            valid_candidates, last_char_generated, random)
                    else:
                        if self.consonants:
                            chosen_c = random.choice(list(self.consonants))

                    if chosen_c:
                        generated_word += chosen_c
                        prev_consonant = chosen_c
                        last_char_generated = chosen_c

                elif char_type == 'V':
                    if self.vowels:
                        chosen_v = self.phonology_handler.get_weighted_choice(
                            list(self.vowels), last_char_generated, random)
                        generated_word += chosen_v
                        last_char_generated = chosen_v
                    in_onset = False
                    prev_consonant = None
        return generated_word

    def _generate_deterministic_word(self, word: str, depth: int = 0) -> str:
        clean_word = "".join(filter(str.isalpha, word.lower()))
        if not clean_word:
            return word
        if depth > 10:
            rng = random.Random(self.global_seed + sum(ord(c)
                                                       for c in clean_word) + depth)
            return self._generate_word_from_seed(clean_word, rng.randint(0, 1000000))
        entry = {
            "lemma": clean_word,
            "default": "",
            "synsets": []
        }

        if self.confluence_handler.enabled:
            stratum = self.confluence_handler.determine_stratum(
                clean_word, self.global_seed)
            if stratum and stratum['type'] != 'native':
                source_id = stratum.get('source_id')
                source_word = self._fetch_source_word(source_id, clean_word)
                nativized = self.phonology_handler.nativize_word(source_word)

                mutation_intensity = stratum.get('mutation_intensity', 0)
                if mutation_intensity > 0:
                    mutation_seed = int(hashlib.sha256(
                        f"{clean_word}_mutation_{self.global_seed}".encode()).hexdigest(), 16)
                    rng_mut = random.Random(mutation_seed)
                    if rng_mut.random() < mutation_intensity:
                        nativized = self._mutate_word(nativized, mutation_seed)

                entry["default"] = nativized
                entry["synsets"].append({"word": nativized, "tags": [
                                        "loanword", f"source:{source_id}"], "affinity": 1.0})
                entry["origin"] = f"confluence_{source_id}"
                self.word_cache[clean_word] = entry
                self.save_word_cache()
                return nativized

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
                base_word = self._generate_deterministic_word(
                    manual_target, depth + 1)
                if manual_target in self.word_cache:
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
                base_word = self._generate_deterministic_word(
                    phantom_base_key, depth + 1)
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
                    self._generate_deterministic_word(root_semantic, depth + 1)
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
        base_word = self.phonology_handler.apply_monophthongization(base_word)
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
                    variant_word = self.phonology_handler.apply_rules(
                        variant_word, name)
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
            "original_text": text,
            "reordered_text": reordered_text,
            "tagged_words": tagged,
            "dependencies": dependencies,
            "constituents": constituents,
            "clauses": clauses,
            "functions": functions,
            "agreement_violations": agreement_violations,
            "complexity": complexity_metrics,
            "word_order": self.syntax_engine.word_order
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
