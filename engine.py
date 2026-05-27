from collections import defaultdict
from typing import List, Dict, Optional, Tuple, Set, Union
import json
import hashlib
from pathlib import Path
import re
import random
import unicodedata
from gramataki_manager import GramatakiManager
from handlers.morphology import AffixHandler, BrokenPluralHandler, ConstructStateHandler, DegreeHandler, DualHandler, ReduplicationHandler, RootSystemHandler
from handlers.phonology import PhonologyHandler, SandhiHandler, StressHandler, SunLetterHandler
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
from special_mechanics import SpecialMechanicsHandler
from idiom_manager import IdiomManager
from constants import PORTUGUESE_STOP_WORDS


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

    def resolve_concept(self, lemma: str, engine_instance, word_form: str = None, pos: str = None, skip_cache: bool = False) -> Optional[Tuple[str, str, Dict]]:
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
                    concept_id, skip_cache=skip_cache)
                return generated_word, 'unique', {'description': definition}

            concept_type = definition.get('type', 'unique')
            if concept_type == 'composition':
                components = definition.get('components', [])
                connector = definition.get('connector', '')
                composed_parts = []
                for comp in components:
                    translated_part = engine_instance._get_word_form(
                        comp, skip_cache=skip_cache)
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
                    concept_id, skip_cache=skip_cache)
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
        self.idiom_manager = IdiomManager(self.profile_id)
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
        self.special_mechanics_handler = SpecialMechanicsHandler(self.profile)
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

        self.gramataki_manager = GramatakiManager(self.profile, self)

    def generate_gramataki_candidates(self, meaning: str, options: Dict) -> List[Dict]:
        return self.gramataki_manager.generate_candidates(meaning, options)

    def save_gramataki_entry(self, entry: Dict):
        self.gramataki_manager.save_entry(entry)

    def get_source_engine(self, source_id: str) -> Optional['OriginalLanguageEngine']:
        if source_id in self.source_engines:
            return self.source_engines[source_id]

        possible_paths = [
            Path(f"{source_id}.json"),
            Path(f"./conlangs/{source_id}.json"),
            Path(f"../conlangs/{source_id}.json"),
            Path(f"cache/{source_id}.json")
        ]

        for p in possible_paths:
            if p.exists():
                try:
                    new_engine = OriginalLanguageEngine(str(p))
                    self.source_engines[source_id] = new_engine
                    return new_engine
                except Exception:
                    pass

        cache_path = Path(f"cache/{source_id}_words.json")
        if cache_path.exists():
            class DummyEngine:
                def __init__(self, c_path):
                    with open(c_path, 'r', encoding='utf-8') as f:
                        self.word_cache = json.load(f)

                def _get_word_form(self, lemma: str, *args, **kwargs) -> str:
                    lemma = lemma.lower().strip()
                    if lemma in self.word_cache:
                        entry = self.word_cache[lemma]
                        if isinstance(entry, dict):
                            return entry.get('default', lemma)
                        return str(entry)
                    return lemma

            return DummyEngine(cache_path)

        return None

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

    def generate_compound(self, lemmas: List[str]) -> str:
        if not lemmas:
            return ""

        words = []
        for lemma in lemmas:
            word = self._get_word_form(lemma, tags=['compound_part'])
            words.append(word)

        compound_word = self.compounding_handler.construct_compound(
            words, self)

        if self.sandhi_handler.enabled:
            compound_word = self.sandhi_handler.apply_sandhi(compound_word)

        return compound_word

    def suggest_compounds(self, lemmas: List[str]) -> List[Dict]:
        if not lemmas:
            return []

        comp_config = self.profile.get('compounding', {})
        if not comp_config.get('enabled', False):
            return []

        words = [self._get_word_form(l, tags=['compound_part'])
                 for l in lemmas]

        suggestions = []

        primary_word = ""
        linking_rules = comp_config.get('linking_elements', {})

        components_processed = []
        rule_description = []

        for i, word in enumerate(words):
            components_processed.append(word)
            if i < len(words) - 1:
                linker = ""
                used_rule = False
                for link_char, rules in linking_rules.items():
                    suffixes = rules.get('after', [])
                    for suff in suffixes:
                        if word.lower().endswith(suff.lower()):
                            linker = link_char
                            rule_description.append(f"{word}->{link_char}")
                            used_rule = True
                            break
                    if linker:
                        break
                components_processed.append(linker)

        raw_compound = "".join(components_processed)
        if self.sandhi_handler.enabled:
            processed = self.sandhi_handler.apply_sandhi(raw_compound)
        else:
            processed = raw_compound

        desc = "Regra de Ligação" if rule_description else "Concatenação Padrão"
        if rule_description:
            desc += f" ({', '.join(rule_description)})"

        suggestions.append({
            "word": processed,
            "desc": desc
        })

        raw_direct = "".join(words)
        if raw_direct != raw_compound:
            if self.sandhi_handler.enabled:
                proc_direct = self.sandhi_handler.apply_sandhi(raw_direct)
            else:
                proc_direct = raw_direct
            suggestions.append({
                "word": proc_direct,
                "desc": "Justaposição Direta"
            })

        if "s" in linking_rules and "s" not in components_processed:
            alt_components = []
            for i, word in enumerate(words):
                alt_components.append(word)
                if i < len(words) - 1:
                    alt_components.append("s")
            raw_s = "".join(alt_components)
            if self.sandhi_handler.enabled:
                proc_s = self.sandhi_handler.apply_sandhi(raw_s)
            else:
                proc_s = raw_s
            if proc_s != processed:
                suggestions.append({
                    "word": proc_s,
                    "desc": "Ligação Genitiva (-s)"
                })

        return suggestions

    def _get_word_form(self, lemma: str, tags: List[str] = None, force_word: str = None, meta: Dict = None, pos: str = None, derivation_depth: int = 0, word_form: str = None, skip_cache: bool = False) -> str:
        lemma = lemma.lower().strip()

        if lemma in self.vocabulary_override:
            return self.vocabulary_override[lemma]
        if lemma.lower() in self.vocabulary_override:
            return self.vocabulary_override[lemma.lower()]

        if lemma in self.processing_stack:
            return self._generate_deterministic_word(lemma, depth=100, skip_cache=skip_cache)
        self.processing_stack.add(lemma)
        try:
            if word_form:
                res = self.concept_handler.resolve_concept(
                    lemma, self, word_form=word_form, pos=pos, skip_cache=skip_cache)
                if res and res[2].get('origin') == 'mapping_table_surface':
                    return res[0]

            if pos == 'ADP':
                basic_preps = self.profile.get(
                    'adposition_system', {}).get('basic_prepositions', {})
                if lemma in basic_preps:
                    return basic_preps[lemma]

            if pos in {'PRON', 'DET'}:
                possessives = self.profile.get('determiner_system', {}).get(
                    'possessives', {}).get('independent_forms', {})
                pos_lemmas = self.profile.get('determiner_system', {}).get(
                    'possessives', {}).get('possessive_lemmas', {})

                target_lemma = pos_lemmas.get(lemma)
                if target_lemma and target_lemma in possessives:
                    return possessives[target_lemma]

            entry = self.word_cache.get(lemma)
            if not entry and force_word:
                entry = {
                    "lemma": lemma,
                    "default": force_word,
                    "synsets": [{"word": force_word, "tags": tags if tags else ["unique"], "affinity": 1.0}]
                }
                if meta:
                    entry.update(meta)
                if not skip_cache:
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
                lemma, self, word_form=word_form, pos=pos, skip_cache=skip_cache)
            if concept_result:
                word, c_type, c_meta = concept_result
                return self._get_word_form(lemma, tags=['concept'], force_word=word, meta=c_meta, skip_cache=skip_cache)

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
                    if self.special_mechanics_handler.enabled:
                        generated_word = self.special_mechanics_handler.apply_mechanics(
                            generated_word, lemma, self.global_seed)
                    entry = {
                        "lemma": lemma,
                        "default": generated_word,
                        "synsets": [{"word": generated_word, "tags": ["root_derived"], "affinity": 1.0}],
                        "origin": "triconsonantal_system",
                        "root": "".join(root)
                    }
                    if not skip_cache:
                        self.word_cache[lemma] = entry
                    return generated_word

            if self.affix_handler.morph_derivation_enabled:
                derived_word = self.affix_handler.try_derive_from_source(
                    lemma, pos, self, current_depth=derivation_depth, skip_cache=skip_cache)
                if derived_word:
                    if self.special_mechanics_handler.enabled:
                        derived_word = self.special_mechanics_handler.apply_mechanics(
                            derived_word, lemma, self.global_seed)
                    entry = {
                        "lemma": lemma,
                        "default": derived_word,
                        "synsets": [{"word": derived_word, "tags": ["derived", "morphology"], "affinity": 1.0}],
                        "origin": "derived"
                    }
                    if not skip_cache:
                        self.word_cache[lemma] = entry
                    return derived_word
            return self._generate_deterministic_word(lemma, depth=0, skip_cache=skip_cache)
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

            ordered_functions, idiom_absorbed_indices = self.idiom_manager.process_functions(
                ordered_functions)

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
            absorbed_indices.update(idiom_absorbed_indices)

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

                if func.get('pos') == 'IDIOM' or func.get('_fixed'):
                    translated_words.append(func['word'])
                    last_content_word_str = func['word']
                    last_content_func = func
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
                manual_tags = func.get("manual_tags", [])

                clean_word_lower = self._clean_word(orig_word).lower()
                raw_lemma = lemma if lemma else clean_word_lower
                raw_lemma = raw_lemma.lower()

                is_mapped = False
                mapping_res = None
                if self.concept_handler.enabled:
                    mapping_res = self.concept_handler.resolve_concept(
                        raw_lemma, self, word_form=clean_word_lower, pos=pos)
                    if mapping_res:
                        is_mapped = True

                if preposition_handling == 'none' and pos == 'ADP' and self.profile.get('case_system', {}).get('enabled', False):
                    continue
                elif preposition_handling == 'replace' and pos == 'ADP' and not is_mapped and self.profile.get('case_system', {}).get('enabled', False):
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

                is_copula_dep = (deprel == 'cop')
                skip_copula_handler = False
                if is_mapped and is_copula_dep:
                    if mapping_res[2].get('origin') in {'mapping_table_surface', 'local_override_direct'}:
                        skip_copula_handler = True
                    else:
                        skip_copula_handler = True

                if self.copula_handler.enabled and is_copula_dep and not skip_copula_handler:
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
                context_tags = manual_tags if manual_tags else []

                if self.lexical_registers.get('enabled', False):
                    pass

                current_form = ""

                if is_mapped and mapping_res:
                    current_form = mapping_res[0]

                if not current_form:
                    if self.demonstrative_handler.enabled and self.demonstrative_handler.is_demonstrative(func):
                        current_form = self.demonstrative_handler.get_form(
                            func, ordered_functions, self)
                    elif pos == 'DET' and ('Definite=Def' in feats or 'PronType=Art' in feats or raw_lemma in {'o', 'a', 'os', 'as'}):
                        det_config = self.profile.get(
                            'determiner_system', {}).get('definite_article', {})
                        if det_config.get('form'):
                            translated_root = det_config.get('form')
                            current_form = translated_root
                        else:
                            translated_root = self._get_word_form(
                                target_lemma, context_tags, pos=current_pos, word_form=clean_word_lower)
                            current_form = translated_root
                    elif pos == 'ADP':
                        basic_preps = self.profile.get(
                            'adposition_system', {}).get('basic_prepositions', {})
                        if raw_lemma in basic_preps:
                            current_form = basic_preps[raw_lemma]
                        else:
                            translated_root = self._get_word_form(
                                target_lemma, context_tags, pos=current_pos, word_form=clean_word_lower)
                            current_form = translated_root
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

    def _clean_word(self, word: str) -> str:
        return "".join(c for c in word if c.isalnum() or c == '-')

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

    def _fetch_source_word(self, source_id: str, lemma: str, skip_cache: bool = False) -> str:
        engine = self.get_source_engine(source_id)
        if engine:
            word = engine._get_word_form(lemma, skip_cache=skip_cache)
            if hasattr(engine, 'save_word_cache') and not skip_cache:
                engine.save_word_cache()
            return word

        rng = random.Random(self.global_seed + sum(ord(c) for c in lemma))
        fallback = "".join(rng.choice(list(self.phonotactics.get(
            'consonants', 'bcdfghjklmnpqrstvwxz'))) for _ in range(5))
        return fallback

    def _generate_word_from_seed(self, clean_word: str, seed: int, is_derived: bool = False, base_conlang_word: str = "") -> str:
        import random
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

    def _generate_deterministic_word(self, word: str, depth: int = 0, skip_cache: bool = False) -> str:
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
            stratum_type = stratum.get(
                'type', 'foreign') if stratum else 'native'
            if stratum and stratum_type != 'native':
                source_id = stratum.get('source_id')
                source_word = self._fetch_source_word(
                    source_id, clean_word, skip_cache=skip_cache)
                nativized = self.phonology_handler.nativize_word(source_word)

                mutation_intensity = stratum.get('mutation_intensity', 0)
                if mutation_intensity > 0:
                    mutation_seed = int(hashlib.sha256(
                        f"{clean_word}_mutation_{self.global_seed}".encode()).hexdigest(), 16)
                    rng_mut = random.Random(mutation_seed)
                    if rng_mut.random() < mutation_intensity:
                        nativized = self._mutate_word(nativized, mutation_seed)

                if self.special_mechanics_handler.enabled:
                    nativized = self.special_mechanics_handler.apply_mechanics(
                        nativized, clean_word, self.global_seed)

                entry["default"] = nativized
                entry["synsets"].append({"word": nativized, "tags": [
                                        "loanword", f"source:{source_id}"], "affinity": 1.0})
                entry["origin"] = f"confluence_{source_id}"
                if not skip_cache:
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
                    manual_target, depth + 1, skip_cache=skip_cache)
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
                    phantom_base_key, depth + 1, skip_cache=skip_cache)
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
                    self._generate_deterministic_word(
                        root_semantic, depth + 1, skip_cache=skip_cache)
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

        if self.special_mechanics_handler.enabled:
            base_word = self.special_mechanics_handler.apply_mechanics(
                base_word, clean_word, self.global_seed)

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
                    if self.special_mechanics_handler.enabled:
                        variant_word = self.special_mechanics_handler.apply_mechanics(
                            variant_word, clean_word, self.global_seed)
                    if variant_word != base_word:
                        entry["synsets"].append({
                            "word": variant_word,
                            "tags": [name],
                            "affinity": 0.9 - (mutation_factor * 0.1)
                        })
        if not skip_cache:
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
            'gramataki_terms': len(self.gramataki_manager.dictionary),
            'syntax': syntax_stats,
            'phonotactics': {
                'vowels': len(self.vowels),
                'consonants': len(self.consonants),
                'templates': len(self.templates)
            }
        }
