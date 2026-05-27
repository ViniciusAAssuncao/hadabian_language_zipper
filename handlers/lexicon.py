import hashlib
import json
from pathlib import Path
import random
from typing import Dict, List, Optional, Tuple

from .phonology import PhonologyHandler


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
            Path('../conlangs/reserved_universal.json'),
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


class LoanwordHandler:
    def __init__(self, profile: Dict, phonology_handler: Optional[PhonologyHandler] = None):
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
