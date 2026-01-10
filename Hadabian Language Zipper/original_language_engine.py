import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re
import random

from phoneme_inventory import (
    UniversalPhonemeInventory,
    PhonemeSelector,
    PhonotacticConstraints,
    OrthographyMapper
)
from word_generator import (
    WordGenerator,
    SyllableGenerator,
    SemanticWordGenerator,
    CompoundWordGenerator,
    NumberWordGenerator
)
from original_learning_system import (
    OriginalLanguageLearningSystem,
    PhonemeDistributionAnalyzer,
    QualityMetrics,
    ConceptMapper
)


class OriginalLanguageProfile:
    def __init__(self, profile_id: str):
        self.profile_id = profile_id
        self.name = ""
        self.description = ""

        self.seed = 42
        self.complexity = 'medium'

        self.phoneme_inventory = {}
        self.phonotactic_constraints = {}
        self.orthography_mapping = {}

        self.vowel_count_range = (5, 9)
        self.consonant_count_range = (12, 22)
        self.allow_diphthongs = True
        self.syllable_complexity = 'medium'
        self.script_style = 'latin'

        self.derivational_morphology = True
        self.compound_words = True
        self.number_system_base = 10

        self.phonological_processes = {
            'assimilation': 0.2,
            'deletion': 0.15,
            'epenthesis': 0.1
        }

        self.syntax_profile = {
            'word_order': 'SOV',
            'primary_alignment': 'nominative_accusative',
            'adjective_position': 'pre_nominal',
            'adposition_type': 'postposition',
            'cases': {
                'nominative': {'markers': [], 'type': 'zero'},
                'accusative': {'markers': ['m', 'n'], 'type': 'suffix'},
                'genitive': {'markers': ['l', 'r'], 'type': 'suffix'},
                'dative': {'markers': ['s', 'z'], 'type': 'suffix'}
            },
            'case_application_rule': 'phonological_harmony'
        }

    def to_dict(self) -> Dict:
        return {
            'profile_id': self.profile_id,
            'name': self.name,
            'description': self.description,
            'seed': self.seed,
            'complexity': self.complexity,
            'phoneme_inventory': self.phoneme_inventory,
            'phonotactic_constraints': self.phonotactic_constraints,
            'orthography_mapping': self.orthography_mapping,
            'vowel_count_range': self.vowel_count_range,
            'consonant_count_range': self.consonant_count_range,
            'allow_diphthongs': self.allow_diphthongs,
            'syllable_complexity': self.syllable_complexity,
            'script_style': self.script_style,
            'derivational_morphology': self.derivational_morphology,
            'compound_words': self.compound_words,
            'number_system_base': self.number_system_base,
            'phonological_processes': self.phonological_processes,
            'syntax_profile': self.syntax_profile
        }

    @staticmethod
    def from_dict(data: Dict) -> 'OriginalLanguageProfile':
        profile = OriginalLanguageProfile(data['profile_id'])
        profile.name = data.get('name', '')
        profile.description = data.get('description', '')
        profile.seed = data.get('seed', 42)
        profile.complexity = data.get('complexity', 'medium')
        profile.phoneme_inventory = data.get('phoneme_inventory', {})
        profile.phonotactic_constraints = data.get(
            'phonotactic_constraints', {})
        profile.orthography_mapping = data.get('orthography_mapping', {})
        profile.vowel_count_range = tuple(
            data.get('vowel_count_range', (5, 9)))
        profile.consonant_count_range = tuple(
            data.get('consonant_count_range', (12, 22)))
        profile.allow_diphthongs = data.get('allow_diphthongs', True)
        profile.syllable_complexity = data.get('syllable_complexity', 'medium')
        profile.script_style = data.get('script_style', 'latin')
        profile.derivational_morphology = data.get(
            'derivational_morphology', True)
        profile.compound_words = data.get('compound_words', True)
        profile.number_system_base = data.get('number_system_base', 10)
        profile.phonological_processes = data.get('phonological_processes', {
            'assimilation': 0.2,
            'deletion': 0.15,
            'epenthesis': 0.1
        })
        profile.syntax_profile = data.get(
            'syntax_profile', profile.syntax_profile)
        return profile


class SyntaxMorphologyGenerator:
    def __init__(self, profile: OriginalLanguageProfile, rng: random.Random):
        self.profile = profile
        self.rng = rng
        self.vowels = set(profile.phoneme_inventory.get('vowels', []))
        self.consonants = set(profile.phoneme_inventory.get('consonants', []))
        self.constraints = profile.phonotactic_constraints

    def inflect_noun(self, word: str, case_name: str) -> str:
        case_config = self.profile.syntax_profile['cases'].get(case_name)

        if not case_config or case_config['type'] == 'zero':
            return word

        markers = case_config.get('markers', [])
        if not markers:
            return word

        marker = self._select_harmonious_marker(word, markers)

        if case_config['type'] == 'suffix':
            return self._attach_suffix(word, marker)
        elif case_config['type'] == 'prefix':
            return self._attach_prefix(word, marker)

        return word

    def _select_harmonious_marker(self, word: str, markers: List[str]) -> str:
        if len(markers) == 1:
            return markers[0]

        last_vowel = self._get_last_vowel(word)
        word_final = word[-1] if word else ''

        for marker in markers:
            if word_final in self.vowels and marker[0] in self.consonants:
                return marker
            if word_final in self.consonants and marker[0] in self.vowels:
                return marker

        return self.rng.choice(markers)

    def _attach_suffix(self, word: str, suffix: str) -> str:
        if not word or not suffix:
            return word + suffix

        word_final = word[-1]
        suffix_initial = suffix[0]

        if word_final in self.consonants and suffix_initial in self.consonants:
            epenthetic = self._get_epenthetic_vowel(word)
            return f"{word}{epenthetic}{suffix}"

        if word_final in self.vowels and suffix_initial in self.vowels:
            if not self.constraints.get('allow_hiatus', True):
                epenthetic = self.rng.choice(list(self.consonants))
                return f"{word}{epenthetic}{suffix}"

        return f"{word}{suffix}"

    def _attach_prefix(self, word: str, prefix: str) -> str:
        if not word or not prefix:
            return prefix + word

        word_initial = word[0]
        prefix_final = prefix[-1]

        if word_initial in self.consonants and prefix_final in self.consonants:
            epenthetic = self._get_epenthetic_vowel(word)
            return f"{prefix}{epenthetic}{word}"

        return f"{prefix}{word}"

    def _get_last_vowel(self, word: str) -> Optional[str]:
        for char in reversed(word):
            if char in self.vowels:
                return char
        return None

    def _get_epenthetic_vowel(self, context_word: str) -> str:
        last_vowel = self._get_last_vowel(context_word)
        if last_vowel:
            return last_vowel
        return self.rng.choice(list(self.vowels)) if self.vowels else 'a'

    def construct_sentence(self, constituents: Dict[str, str]) -> List[str]:
        order = self.profile.syntax_profile.get('word_order', 'SOV')

        subject = constituents.get('S', '')
        obj = constituents.get('O', '')
        verb = constituents.get('V', '')
        indirect = constituents.get('IO', '')

        if subject:
            subject = self.inflect_noun(subject, 'nominative')
        if obj:
            obj = self.inflect_noun(obj, 'accusative')
        if indirect:
            indirect = self.inflect_noun(indirect, 'dative')

        sentence_parts = []

        for char in order:
            if char == 'S' and subject:
                sentence_parts.append(subject)
            elif char == 'O' and obj:
                sentence_parts.append(obj)
            elif char == 'V' and verb:
                sentence_parts.append(verb)

        if indirect:
            if order.startswith('S'):
                sentence_parts.insert(1, indirect)
            else:
                sentence_parts.append(indirect)

        return sentence_parts


class OriginalLanguageEngine:
    def __init__(self, profile: OriginalLanguageProfile):
        self.profile = profile

        self.phoneme_selector = PhonemeSelector(seed=profile.seed)
        self.phonotactic_constraints_gen = PhonotacticConstraints(
            seed=profile.seed)
        self.orthography_mapper = OrthographyMapper(seed=profile.seed)

        if not profile.phoneme_inventory:
            self._initialize_phonology()

        self.word_generator = WordGenerator(
            phoneme_inventory=profile.phoneme_inventory,
            phonotactic_constraints=profile.phonotactic_constraints,
            seed=profile.seed
        )

        self.semantic_generator = SemanticWordGenerator(
            word_generator=self.word_generator,
            seed=profile.seed
        )

        self.compound_generator = CompoundWordGenerator(
            word_generator=self.word_generator
        )

        self.number_generator = NumberWordGenerator(
            word_generator=self.word_generator,
            base=profile.number_system_base
        )

        self.syntax_generator = SyntaxMorphologyGenerator(
            profile=self.profile,
            rng=random.Random(profile.seed)
        )

        self.learning_system = OriginalLanguageLearningSystem(
            language_id=profile.profile_id
        )

        self.distribution_analyzer = PhonemeDistributionAnalyzer(
            learning_system=self.learning_system
        )

        self.concept_mapper = ConceptMapper()

    def _initialize_phonology(self):
        self.profile.phoneme_inventory = self.phoneme_selector.generate_inventory(
            vowel_count_range=self.profile.vowel_count_range,
            consonant_count_range=self.profile.consonant_count_range,
            allow_diphthongs=self.profile.allow_diphthongs,
            complexity=self.profile.complexity
        )

        self.profile.phonotactic_constraints = self.phonotactic_constraints_gen.generate_constraints(
            phoneme_inventory=self.profile.phoneme_inventory,
            syllable_complexity=self.profile.syllable_complexity
        )

        self.profile.orthography_mapping = self.orthography_mapper.generate_orthography(
            phoneme_inventory=self.profile.phoneme_inventory,
            script_style=self.profile.script_style
        )

    def translate_word(self, source_word: str, force_regenerate: bool = False) -> str:
        concept = source_word.lower().strip()

        if not force_regenerate:
            cached = self.learning_system.get_word_for_concept(concept)
            if cached:
                self.learning_system.usage_counts[concept] += 1
                return cached

        generated_phonetic = self.word_generator.generate_word(concept)

        generated_orthographic = self.orthography_mapper.apply_orthography(
            generated_phonetic)

        phonemes_used = self._extract_phonemes(generated_phonetic)

        quality = QualityMetrics.calculate_word_quality(
            generated_phonetic,
            self.profile.phoneme_inventory,
            self.profile.phonotactic_constraints
        )

        self.learning_system.record_generation(
            concept=concept,
            generated_word=generated_orthographic,
            quality_score=quality,
            phonemes_used=phonemes_used
        )

        return generated_orthographic

    def generate_sentence(self, subject: str, verb: str, obj: Optional[str] = None,
                          indirect_obj: Optional[str] = None) -> str:

        s_word = self.translate_word(subject) if subject else ''
        v_word = self.translate_word(verb) if verb else ''
        o_word = self.translate_word(obj) if obj else ''
        io_word = self.translate_word(indirect_obj) if indirect_obj else ''

        constituents = {
            'S': self._invert_orthography(s_word),
            'V': self._invert_orthography(v_word),
            'O': self._invert_orthography(o_word),
            'IO': self._invert_orthography(io_word)
        }

        ordered_parts = self.syntax_generator.construct_sentence(constituents)

        final_parts = [self.orthography_mapper.apply_orthography(
            p) for p in ordered_parts]

        return ' '.join(final_parts) + '.'

    def _invert_orthography(self, word: str) -> str:
        if not word:
            return ""
        inverted = word
        for k, v in self.profile.orthography_mapping.items():
            if v != k and v in inverted:
                inverted = inverted.replace(v, k)
        return inverted

    def translate_text(self, source_text: str) -> str:
        words = self._tokenize(source_text)

        translated_words = []
        for word_info in words:
            if word_info['is_word']:
                translated = self.translate_word(word_info['text'])

                if word_info['is_capitalized']:
                    translated = translated.capitalize()

                translated_words.append(
                    word_info['prefix'] + translated + word_info['suffix'])
            else:
                translated_words.append(word_info['text'])

        return ''.join(translated_words)

    def _tokenize(self, text: str) -> List[Dict]:
        tokens = []

        pattern = r'(\s+|[^\w\s]+|\w+)'
        matches = re.finditer(pattern, text)

        for match in matches:
            token = match.group(0)

            if re.match(r'\w+', token):
                prefix_match = re.match(r'^([^\w]*)', token)
                suffix_match = re.search(r'([^\w]*)$', token)

                prefix = prefix_match.group(1) if prefix_match else ''
                suffix = suffix_match.group(1) if suffix_match else ''

                clean_word = re.sub(r'^[^\w]*|[^\w]*$', '', token)

                is_capitalized = clean_word and clean_word[0].isupper()

                tokens.append({
                    'text': clean_word.lower(),
                    'prefix': prefix,
                    'suffix': suffix,
                    'is_word': True,
                    'is_capitalized': is_capitalized
                })
            else:
                tokens.append({
                    'text': token,
                    'is_word': False,
                    'prefix': '',
                    'suffix': '',
                    'is_capitalized': False
                })

        return tokens

    def _extract_phonemes(self, phonetic_word: str) -> List[str]:
        phonemes = []
        all_phonemes = set(
            self.profile.phoneme_inventory['vowels'] +
            self.profile.phoneme_inventory['consonants']
        )

        i = 0
        while i < len(phonetic_word):
            found = False
            for length in [2, 1]:
                if i + length <= len(phonetic_word):
                    segment = phonetic_word[i:i+length]
                    if segment in all_phonemes:
                        phonemes.append(segment)
                        i += length
                        found = True
                        break
            if not found:
                i += 1

        return phonemes

    def generate_derived_word(self, base_concept: str, derivation_type: str) -> str:
        if not self.profile.derivational_morphology:
            return self.translate_word(base_concept)

        derived = self.semantic_generator.generate_with_derivation(
            concept=base_concept,
            derivation=derivation_type
        )

        return self.orthography_mapper.apply_orthography(derived)

    def generate_compound_word(self, concept1: str, concept2: str) -> str:
        if not self.profile.compound_words:
            return self.translate_word(f"{concept1}_{concept2}")

        compound_phonetic = self.compound_generator.generate_compound(
            concept1, concept2
        )

        return self.orthography_mapper.apply_orthography(compound_phonetic)

    def generate_number_word(self, number: int) -> str:
        number_phonetic = self.number_generator.generate_number_word(number)
        return self.orthography_mapper.apply_orthography(number_phonetic)

    def get_statistics(self) -> Dict:
        learning_stats = self.learning_system.get_statistics()
        distribution_stats = self.distribution_analyzer.analyze_distribution()

        return {
            'profile': {
                'id': self.profile.profile_id,
                'name': self.profile.name,
                'seed': self.profile.seed
            },
            'phonology': {
                'vowel_count': len(self.profile.phoneme_inventory['vowels']),
                'consonant_count': len(self.profile.phoneme_inventory['consonants']),
                'diphthong_count': len(self.profile.phoneme_inventory.get('diphthongs', [])),
                'syllable_templates': len(self.profile.phonotactic_constraints.get('syllable_templates', []))
            },
            'lexicon': learning_stats,
            'distribution': {
                'entropy': distribution_stats['entropy'],
                'uniformity': distribution_stats['uniformity_score']
            },
            'recommendations': self.distribution_analyzer.get_recommendations(
                self.profile.phoneme_inventory
            )
        }

    def export_profile(self, output_path: str):
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.profile.to_dict(), f, indent=2, ensure_ascii=False)

    def save_learning_data(self):
        self.learning_system.save_learning_data()

    def export_dictionary(self, output_path: str, format: str = 'json') -> int:
        return self.learning_system.export_dictionary(output_path, format)

    def generate_core_vocabulary(self, include_numbers: bool = True) -> Dict[str, str]:
        core_concepts = self.concept_mapper.get_all_core_concepts()

        vocabulary = {}
        for concept in core_concepts:
            translated = self.translate_word(concept)
            vocabulary[concept] = translated

        if include_numbers:
            for i in range(100):
                number_word = self.generate_number_word(i)
                vocabulary[f"number_{i}"] = number_word

        return vocabulary

    def analyze_word(self, word: str) -> Dict:
        concept = self.learning_system.get_concept_for_word(word)
        quality = self.learning_system.quality_scores.get(word, 0.0)
        usage = self.learning_system.usage_counts.get(
            concept, 0) if concept else 0

        phonemes = self._extract_phonemes(word)

        syllables = self.word_generator.syllable_generator.syllable_cache
        matching_syllables = [s for s in syllables.values() if s in word]

        return {
            'word': word,
            'concept': concept,
            'quality_score': quality,
            'usage_count': usage,
            'phonemes': phonemes,
            'phoneme_count': len(phonemes),
            'length': len(word),
            'syllables': matching_syllables
        }


class OriginalLanguageProfileManager:
    def __init__(self, profiles_dir: str = "original_profiles"):
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(exist_ok=True, parents=True)

    def create_profile(self, profile_id: str,
                       name: str = "",
                       seed: Optional[int] = None,
                       complexity: str = 'medium') -> OriginalLanguageProfile:
        profile = OriginalLanguageProfile(profile_id)
        profile.name = name or profile_id
        profile.complexity = complexity

        if seed is not None:
            profile.seed = seed

        self.save_profile(profile)
        return profile

    def save_profile(self, profile: OriginalLanguageProfile):
        profile_path = self.profiles_dir / f"{profile.profile_id}.json"
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)

    def load_profile(self, profile_id: str) -> Optional[OriginalLanguageProfile]:
        profile_path = self.profiles_dir / f"{profile_id}.json"

        if not profile_path.exists():
            return None

        with open(profile_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return OriginalLanguageProfile.from_dict(data)

    def list_profiles(self) -> List[str]:
        return [p.stem for p in self.profiles_dir.glob("*.json")]

    def delete_profile(self, profile_id: str) -> bool:
        profile_path = self.profiles_dir / f"{profile_id}.json"

        if profile_path.exists():
            profile_path.unlink()
            return True

        return False

    def duplicate_profile(self, source_id: str, new_id: str,
                          new_seed: Optional[int] = None) -> Optional[OriginalLanguageProfile]:
        source = self.load_profile(source_id)
        if not source:
            return None

        duplicate = OriginalLanguageProfile.from_dict(source.to_dict())
        duplicate.profile_id = new_id
        duplicate.name = f"{source.name} (Copy)"

        if new_seed is not None:
            duplicate.seed = new_seed
            duplicate.phoneme_inventory = {}
            duplicate.phonotactic_constraints = {}
            duplicate.orthography_mapping = {}

        self.save_profile(duplicate)
        return duplicate


class BatchTranslator:
    def __init__(self, engine: OriginalLanguageEngine):
        self.engine = engine

    def translate_file(self, input_path: str, output_path: str):
        with open(input_path, 'r', encoding='utf-8') as f:
            source_text = f.read()

        translated_text = self.engine.translate_text(source_text)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(translated_text)

    def translate_wordlist(self, words: List[str]) -> Dict[str, str]:
        translations = {}
        for word in words:
            translations[word] = self.engine.translate_word(word)
        return translations

    def generate_parallel_corpus(self, source_texts: List[str]) -> List[Tuple[str, str]]:
        corpus = []
        for source in source_texts:
            translated = self.engine.translate_text(source)
            corpus.append((source, translated))
        return corpus
