import re
import hashlib
import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Dict, Set, Tuple
from constants import GRAMMATICAL_CONCEPT_IDS


@dataclass
class SoundChange:
    rule_id: str
    input_pattern: str
    output: str
    environment_left: str
    environment_right: str
    word_boundary_left: bool
    word_boundary_right: bool
    probability: float
    high_frequency_exceptions: List[str]
    description: str


@dataclass
class Era:
    era_id: str
    name: str
    parent_era_id: Optional[str]
    changes: List[SoundChange]
    description: str


class SoundChangeEngine:
    def __init__(self, profile: Dict, consonants: str, vowels: str):
        self.consonants = consonants
        self.vowels = vowels
        self.eras = {}

        high_freq_lemmas = self._infer_high_frequency_lemmas(profile)

        raw_eras = profile.get('diachronic_eras', [])
        for era_data in raw_eras:
            changes = []
            for c in era_data.get('changes', []):
                prob = c.get('probability', 1.0)
                hf_exceptions = set(c.get('high_frequency_exceptions', []))
                
                if prob == 1.0:
                    hf_exceptions.update(high_freq_lemmas)

                changes.append(SoundChange(
                    rule_id=c.get('rule_id', ''),
                    input_pattern=c.get('input_pattern', ''),
                    output=c.get('output', ''),
                    environment_left=c.get('environment_left', ''),
                    environment_right=c.get('environment_right', ''),
                    word_boundary_left=c.get('word_boundary_left', False),
                    word_boundary_right=c.get('word_boundary_right', False),
                    probability=prob,
                    high_frequency_exceptions=list(hf_exceptions),
                    description=c.get('description', '')
                ))

            self.eras[era_data.get('era_id')] = Era(
                era_id=era_data.get('era_id', ''),
                name=era_data.get('name', ''),
                parent_era_id=era_data.get('parent_era_id'),
                changes=changes,
                description=era_data.get('description', '')
            )

    def _infer_high_frequency_lemmas(self, profile: Dict) -> Set[str]:
        high_freq = set()

        vocab_override = profile.get('vocabulary', {})
        for lemma in vocab_override.keys():
            high_freq.add(lemma)

        abstract_concepts = profile.get('abstract_concepts', {}).get('mappings', {})
        for lemma, concept_id in abstract_concepts.items():
            if concept_id in GRAMMATICAL_CONCEPT_IDS:
                high_freq.add(lemma)

        swadesh_path = Path("data/swadesh_100.json")
        swadesh_concepts = set()
        if swadesh_path.exists():
            try:
                with open(swadesh_path, 'r', encoding='utf-8') as f:
                    swadesh_data = json.load(f)
                    if isinstance(swadesh_data, list):
                        for item in swadesh_data:
                            if isinstance(item, dict) and 'id' in item:
                                swadesh_concepts.add(item['id'])
                            elif isinstance(item, str):
                                swadesh_concepts.add(item)
                    elif isinstance(swadesh_data, dict):
                        swadesh_concepts.update(swadesh_data.keys())
            except Exception:
                pass

        for lemma, concept_id in abstract_concepts.items():
            if concept_id in swadesh_concepts:
                high_freq.add(lemma)

        return high_freq

    def is_enabled(self) -> bool:
        for era in self.eras.values():
            if len(era.changes) > 0:
                return True
        return False

    def get_era_chain(self, target_era_id: str) -> List[Era]:
        if target_era_id not in self.eras:
            raise ValueError(f"Target era '{target_era_id}' not found.")

        chain = []
        current_id = target_era_id
        while current_id:
            if current_id not in self.eras:
                raise ValueError(
                    f"Parent era '{current_id}' not found in the chain.")

            era = self.eras[current_id]
            chain.append(era)
            current_id = era.parent_era_id

        chain.reverse()
        return chain

    def _compile_environment_regex(self, pattern: str, env_left: str, env_right: str, wb_left: bool, wb_right: bool) -> re.Pattern:
        c_class = f"[{self.consonants}]" if self.consonants else "[bcdfghjklmnpqrstvwxz]"
        v_class = f"[{self.vowels}]" if self.vowels else "[aeiou]"

        def _expand(s: str) -> str:
            if not s:
                return ""
            s = s.replace('C', c_class)
            s = s.replace('V', v_class)
            return s

        pattern_exp = _expand(pattern)
        env_left_exp = _expand(env_left)
        env_right_exp = _expand(env_right)

        left_parts = []
        if wb_left:
            left_parts.append("^")
        if env_left_exp:
            left_parts.append(f"(?<={env_left_exp})")

        right_parts = []
        if env_right_exp:
            right_parts.append(f"(?={env_right_exp})")
        if wb_right:
            right_parts.append("$")

        full_pattern = "".join(left_parts) + pattern_exp + "".join(right_parts)
        return re.compile(full_pattern)

    def apply_single_change(self, word: str, change: SoundChange, lemma: str) -> str:
        if lemma in change.high_frequency_exceptions:
            return word

        if change.probability < 1.0:
            hash_input = f"{lemma}{change.rule_id}".encode()
            hash_val = int(hashlib.sha256(hash_input).hexdigest(), 16)
            if (hash_val % 1000) / 1000.0 > change.probability:
                return word

        try:
            regex = self._compile_environment_regex(
                change.input_pattern,
                change.environment_left,
                change.environment_right,
                change.word_boundary_left,
                change.word_boundary_right
            )
            return regex.sub(change.output, word)
        except Exception:
            return word

    def apply_era(self, word: str, era: Era, lemma: str) -> Tuple[str, List[str]]:
        current_word = word
        applied_rules = []
        for change in era.changes:
            new_word = self.apply_single_change(current_word, change, lemma)
            if new_word != current_word:
                applied_rules.append(change.rule_id)
                current_word = new_word
        return current_word, applied_rules

    def derive_from_proto(self, proto_form: str, target_era_id: str, lemma: str) -> Tuple[str, List[str]]:
        chain = self.get_era_chain(target_era_id)
        current_form = proto_form
        all_applied_rules = []
        for era in chain:
            current_form, applied_rules = self.apply_era(current_form, era, lemma)
            all_applied_rules.extend(applied_rules)
        return current_form, all_applied_rules