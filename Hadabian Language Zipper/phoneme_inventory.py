import json
import hashlib
import random
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PhonemeClass:
    name: str
    symbols: List[str]
    features: Dict[str, any]
    frequency_weight: float = 1.0


class UniversalPhonemeInventory:
    def __init__(self):
        self.vowels = self._initialize_vowels()
        self.consonants = self._initialize_consonants()
        self.diphthongs = self._initialize_diphthongs()
        self.phoneme_features = self._initialize_features()
        
    def _initialize_vowels(self) -> Dict[str, PhonemeClass]:
        return {
            'close_front': PhonemeClass(
                name='close_front',
                symbols=['i', 'y'],
                features={'height': 'close', 'backness': 'front', 'roundness': ['unrounded', 'rounded']},
                frequency_weight=1.2
            ),
            'close_central': PhonemeClass(
                name='close_central',
                symbols=['ɨ', 'ʉ'],
                features={'height': 'close', 'backness': 'central', 'roundness': ['unrounded', 'rounded']},
                frequency_weight=0.4
            ),
            'close_back': PhonemeClass(
                name='close_back',
                symbols=['ɯ', 'u'],
                features={'height': 'close', 'backness': 'back', 'roundness': ['unrounded', 'rounded']},
                frequency_weight=1.0
            ),
            'mid_front': PhonemeClass(
                name='mid_front',
                symbols=['e', 'ø'],
                features={'height': 'mid', 'backness': 'front', 'roundness': ['unrounded', 'rounded']},
                frequency_weight=1.0
            ),
            'mid_central': PhonemeClass(
                name='mid_central',
                symbols=['ə', 'ɘ'],
                features={'height': 'mid', 'backness': 'central', 'roundness': ['unrounded', 'rounded']},
                frequency_weight=0.8
            ),
            'mid_back': PhonemeClass(
                name='mid_back',
                symbols=['ɤ', 'o'],
                features={'height': 'mid', 'backness': 'back', 'roundness': ['unrounded', 'rounded']},
                frequency_weight=0.9
            ),
            'open_front': PhonemeClass(
                name='open_front',
                symbols=['a', 'æ'],
                features={'height': 'open', 'backness': 'front', 'roundness': ['unrounded']},
                frequency_weight=1.3
            ),
            'open_back': PhonemeClass(
                name='open_back',
                symbols=['ɑ', 'ɒ'],
                features={'height': 'open', 'backness': 'back', 'roundness': ['unrounded', 'rounded']},
                frequency_weight=0.9
            )
        }
    
    def _initialize_consonants(self) -> Dict[str, PhonemeClass]:
        return {
            'plosive_bilabial': PhonemeClass(
                name='plosive_bilabial',
                symbols=['p', 'b'],
                features={'manner': 'plosive', 'place': 'bilabial', 'voice': ['voiceless', 'voiced']},
                frequency_weight=1.2
            ),
            'plosive_alveolar': PhonemeClass(
                name='plosive_alveolar',
                symbols=['t', 'd'],
                features={'manner': 'plosive', 'place': 'alveolar', 'voice': ['voiceless', 'voiced']},
                frequency_weight=1.3
            ),
            'plosive_velar': PhonemeClass(
                name='plosive_velar',
                symbols=['k', 'g'],
                features={'manner': 'plosive', 'place': 'velar', 'voice': ['voiceless', 'voiced']},
                frequency_weight=1.2
            ),
            'plosive_glottal': PhonemeClass(
                name='plosive_glottal',
                symbols=['ʔ'],
                features={'manner': 'plosive', 'place': 'glottal', 'voice': ['voiceless']},
                frequency_weight=0.3
            ),
            'fricative_labiodental': PhonemeClass(
                name='fricative_labiodental',
                symbols=['f', 'v'],
                features={'manner': 'fricative', 'place': 'labiodental', 'voice': ['voiceless', 'voiced']},
                frequency_weight=0.9
            ),
            'fricative_alveolar': PhonemeClass(
                name='fricative_alveolar',
                symbols=['s', 'z'],
                features={'manner': 'fricative', 'place': 'alveolar', 'voice': ['voiceless', 'voiced']},
                frequency_weight=1.1
            ),
            'fricative_postalveolar': PhonemeClass(
                name='fricative_postalveolar',
                symbols=['ʃ', 'ʒ'],
                features={'manner': 'fricative', 'place': 'postalveolar', 'voice': ['voiceless', 'voiced']},
                frequency_weight=0.7
            ),
            'fricative_glottal': PhonemeClass(
                name='fricative_glottal',
                symbols=['h'],
                features={'manner': 'fricative', 'place': 'glottal', 'voice': ['voiceless']},
                frequency_weight=0.8
            ),
            'nasal_bilabial': PhonemeClass(
                name='nasal_bilabial',
                symbols=['m'],
                features={'manner': 'nasal', 'place': 'bilabial', 'voice': ['voiced']},
                frequency_weight=1.1
            ),
            'nasal_alveolar': PhonemeClass(
                name='nasal_alveolar',
                symbols=['n'],
                features={'manner': 'nasal', 'place': 'alveolar', 'voice': ['voiced']},
                frequency_weight=1.2
            ),
            'nasal_velar': PhonemeClass(
                name='nasal_velar',
                symbols=['ŋ'],
                features={'manner': 'nasal', 'place': 'velar', 'voice': ['voiced']},
                frequency_weight=0.6
            ),
            'approximant_lateral': PhonemeClass(
                name='approximant_lateral',
                symbols=['l'],
                features={'manner': 'approximant', 'place': 'alveolar', 'voice': ['voiced'], 'lateral': True},
                frequency_weight=1.0
            ),
            'approximant_rhotic': PhonemeClass(
                name='approximant_rhotic',
                symbols=['r', 'ɹ'],
                features={'manner': 'approximant', 'place': 'alveolar', 'voice': ['voiced'], 'rhotic': True},
                frequency_weight=0.9
            ),
            'approximant_palatal': PhonemeClass(
                name='approximant_palatal',
                symbols=['j'],
                features={'manner': 'approximant', 'place': 'palatal', 'voice': ['voiced']},
                frequency_weight=0.7
            ),
            'approximant_labial': PhonemeClass(
                name='approximant_labial',
                symbols=['w'],
                features={'manner': 'approximant', 'place': 'labial-velar', 'voice': ['voiced']},
                frequency_weight=0.7
            ),
            'affricate_alveolar': PhonemeClass(
                name='affricate_alveolar',
                symbols=['ts', 'dz'],
                features={'manner': 'affricate', 'place': 'alveolar', 'voice': ['voiceless', 'voiced']},
                frequency_weight=0.4
            ),
            'affricate_postalveolar': PhonemeClass(
                name='affricate_postalveolar',
                symbols=['tʃ', 'dʒ'],
                features={'manner': 'affricate', 'place': 'postalveolar', 'voice': ['voiceless', 'voiced']},
                frequency_weight=0.5
            )
        }
    
    def _initialize_diphthongs(self) -> List[str]:
        return ['ai', 'au', 'ei', 'eu', 'oi', 'ou', 'ui', 'ia', 'ie', 'io', 'ua', 'ue', 'uo']
    
    def _initialize_features(self) -> Dict[str, Dict]:
        return {
            'sonority_hierarchy': {
                'vowel': 5,
                'approximant': 4,
                'nasal': 3,
                'fricative': 2,
                'plosive': 1,
                'affricate': 1
            },
            'natural_classes': {
                'obstruent': ['plosive', 'fricative', 'affricate'],
                'sonorant': ['nasal', 'approximant', 'vowel'],
                'continuant': ['fricative', 'approximant', 'vowel'],
                'sibilant': ['s', 'z', 'ʃ', 'ʒ', 'ts', 'dz', 'tʃ', 'dʒ']
            }
        }


class PhonemeSelector:
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.inventory = UniversalPhonemeInventory()
        self._rng = random.Random(seed)
    
    def generate_inventory(self, 
                          vowel_count_range: Tuple[int, int] = (5, 9),
                          consonant_count_range: Tuple[int, int] = (12, 22),
                          allow_diphthongs: bool = True,
                          complexity: str = 'medium') -> Dict[str, List[str]]:
        vowel_count = self._rng.randint(*vowel_count_range)
        consonant_count = self._rng.randint(*consonant_count_range)
        
        vowels = self._select_vowels(vowel_count, complexity)
        consonants = self._select_consonants(consonant_count, complexity)
        diphthongs = []
        
        if allow_diphthongs:
            diphthong_count = self._rng.randint(3, 8)
            diphthongs = self._select_diphthongs(diphthong_count, vowels)
        
        return {
            'vowels': vowels,
            'consonants': consonants,
            'diphthongs': diphthongs,
            'all_phonemes': vowels + consonants
        }
    
    def _select_vowels(self, count: int, complexity: str) -> List[str]:
        vowel_classes = list(self.inventory.vowels.values())
        
        weights = [vc.frequency_weight for vc in vowel_classes]
        
        selected_classes = self._rng.choices(
            vowel_classes, 
            weights=weights, 
            k=min(count, len(vowel_classes))
        )
        
        selected_vowels = []
        for vc in selected_classes:
            if len(selected_vowels) >= count:
                break
            symbol = self._rng.choice(vc.symbols)
            selected_vowels.append(symbol)
        
        while len(selected_vowels) < count and len(selected_vowels) < count * 2:
            vc = self._rng.choice(vowel_classes)
            symbol = self._rng.choice(vc.symbols)
            if symbol not in selected_vowels:
                selected_vowels.append(symbol)
        
        return selected_vowels[:count]
    
    def _select_consonants(self, count: int, complexity: str) -> List[str]:
        consonant_classes = list(self.inventory.consonants.values())
        
        weights = [cc.frequency_weight for cc in consonant_classes]
        
        selected_classes = self._rng.choices(
            consonant_classes,
            weights=weights,
            k=min(count, len(consonant_classes))
        )
        
        selected_consonants = []
        for cc in selected_classes:
            if len(selected_consonants) >= count:
                break
            symbol = self._rng.choice(cc.symbols)
            selected_consonants.append(symbol)
        
        while len(selected_consonants) < count:
            cc = self._rng.choice(consonant_classes)
            symbol = self._rng.choice(cc.symbols)
            if symbol not in selected_consonants:
                selected_consonants.append(symbol)
        
        return selected_consonants[:count]
    
    def _select_diphthongs(self, count: int, vowels: List[str]) -> List[str]:
        base_diphthongs = self.inventory.diphthongs
        
        valid_diphthongs = []
        for diphthong in base_diphthongs:
            if all(v in vowels for v in diphthong if v in 'aeiouəɨʉɯæøɤɑɒ'):
                valid_diphthongs.append(diphthong)
        
        if len(valid_diphthongs) >= count:
            return self._rng.sample(valid_diphthongs, count)
        
        result = valid_diphthongs.copy()
        while len(result) < count:
            v1 = self._rng.choice(vowels)
            v2 = self._rng.choice(vowels)
            if v1 != v2:
                new_diph = v1 + v2
                if new_diph not in result:
                    result.append(new_diph)
        
        return result[:count]


class PhonotacticConstraints:
    def __init__(self, seed: int = 42):
        self.seed = seed
        self._rng = random.Random(seed)
        self.constraints = {}
    
    def generate_constraints(self, 
                           phoneme_inventory: Dict[str, List[str]],
                           syllable_complexity: str = 'medium') -> Dict:
        vowels = set(phoneme_inventory['vowels'])
        consonants = set(phoneme_inventory['consonants'])
        
        if syllable_complexity == 'simple':
            templates = ['V', 'CV', 'VC', 'CVC']
            max_onset = 1
            max_coda = 1
            max_nucleus = 1
        elif syllable_complexity == 'medium':
            templates = ['V', 'CV', 'CVC', 'CCV', 'CCVC', 'CVCC']
            max_onset = 2
            max_coda = 2
            max_nucleus = 2
        else:
            templates = ['V', 'CV', 'CVC', 'CCV', 'CCVC', 'CVCC', 'CCCV', 'CCCVC', 'CVCC', 'CVCCC']
            max_onset = 3
            max_coda = 3
            max_nucleus = 2
        
        selected_templates = self._rng.sample(templates, k=min(len(templates), self._rng.randint(4, len(templates))))
        
        forbidden_onsets = self._generate_forbidden_clusters(consonants, 'onset')
        forbidden_codas = self._generate_forbidden_clusters(consonants, 'coda')
        forbidden_nuclei = self._generate_forbidden_clusters(vowels, 'nucleus')
        
        return {
            'syllable_templates': selected_templates,
            'max_onset_consonants': max_onset,
            'max_coda_consonants': max_coda,
            'max_nucleus_vowels': max_nucleus,
            'forbidden_onsets': forbidden_onsets,
            'forbidden_codas': forbidden_codas,
            'forbidden_nuclei': forbidden_nuclei,
            'allow_hiatus': self._rng.choice([True, False]),
            'max_syllables_per_word': self._rng.randint(3, 5),
            'min_syllables_per_word': 1,
            'word_final_constraints': self._generate_word_final_constraints(consonants),
            'word_initial_constraints': self._generate_word_initial_constraints(consonants)
        }
    
    def _generate_forbidden_clusters(self, phonemes: Set[str], position: str) -> List[str]:
        forbidden = []
        phoneme_list = list(phonemes)
        
        if position == 'coda':
            problematic = ['h', 'j', 'w']
            for p in problematic:
                if p in phonemes:
                    forbidden.append(p)
        
        if len(phoneme_list) > 3:
            sample_size = self._rng.randint(0, min(5, len(phoneme_list) // 3))
            forbidden.extend(self._rng.sample(phoneme_list, sample_size))
        
        return list(set(forbidden))
    
    def _generate_word_final_constraints(self, consonants: Set[str]) -> Dict:
        return {
            'allowed_final_consonants': self._rng.sample(
                list(consonants), 
                k=self._rng.randint(len(consonants) // 2, len(consonants))
            ),
            'prefer_open_syllables': self._rng.choice([True, False])
        }
    
    def _generate_word_initial_constraints(self, consonants: Set[str]) -> Dict:
        return {
            'allowed_initial_consonants': list(consonants),
            'require_onset': self._rng.choice([True, False])
        }


class OrthographyMapper:
    def __init__(self, seed: int = 42):
        self.seed = seed
        self._rng = random.Random(seed)
        self.mapping = {}
    
    def generate_orthography(self, 
                            phoneme_inventory: Dict[str, List[str]],
                            script_style: str = 'latin') -> Dict[str, str]:
        all_phonemes = phoneme_inventory['vowels'] + phoneme_inventory['consonants']
        
        if script_style == 'latin':
            mapping = self._latin_based_mapping(all_phonemes)
        elif script_style == 'cyrillic':
            mapping = self._cyrillic_based_mapping(all_phonemes)
        elif script_style == 'custom':
            mapping = self._custom_mapping(all_phonemes)
        else:
            mapping = self._latin_based_mapping(all_phonemes)
        
        self.mapping = mapping
        return mapping
    
    def _latin_based_mapping(self, phonemes: List[str]) -> Dict[str, str]:
        mapping = {}
        
        simple_map = {
            'i': 'i', 'e': 'e', 'a': 'a', 'o': 'o', 'u': 'u',
            'p': 'p', 'b': 'b', 't': 't', 'd': 'd', 'k': 'k', 'g': 'g',
            'f': 'f', 'v': 'v', 's': 's', 'z': 'z', 'h': 'h',
            'm': 'm', 'n': 'n', 'l': 'l', 'r': 'r', 'j': 'j', 'w': 'w'
        }
        
        digraph_map = {
            'ʃ': self._rng.choice(['sh', 'ş', 'š']),
            'ʒ': self._rng.choice(['zh', 'ž']),
            'tʃ': self._rng.choice(['ch', 'č']),
            'dʒ': self._rng.choice(['j', 'ǧ']),
            'ŋ': self._rng.choice(['ng', 'ŋ']),
            'ɹ': 'r',
            'ə': self._rng.choice(['e', 'ə', 'â']),
            'ɨ': self._rng.choice(['î', 'y']),
            'ʉ': self._rng.choice(['ü', 'û']),
            'ɯ': self._rng.choice(['ï', 'ı']),
            'æ': self._rng.choice(['ä', 'ae', 'æ']),
            'ø': self._rng.choice(['ö', 'ø']),
            'ɤ': self._rng.choice(['ö', 'ô']),
            'ɑ': self._rng.choice(['a', 'á']),
            'ɒ': self._rng.choice(['o', 'ó']),
            'ʔ': self._rng.choice(["'", 'q', '']),
            'y': self._rng.choice(['ü', 'y']),
            'ts': 'ts',
            'dz': 'dz'
        }
        
        for phoneme in phonemes:
            if phoneme in simple_map:
                mapping[phoneme] = simple_map[phoneme]
            elif phoneme in digraph_map:
                mapping[phoneme] = digraph_map[phoneme]
            else:
                mapping[phoneme] = phoneme
        
        return mapping
    
    def _cyrillic_based_mapping(self, phonemes: List[str]) -> Dict[str, str]:
        mapping = {}
        cyrillic_vowels = ['а', 'е', 'и', 'о', 'у', 'ы', 'э', 'ю', 'я']
        cyrillic_consonants = ['б', 'в', 'г', 'д', 'ж', 'з', 'к', 'л', 'м', 'н', 'п', 'р', 'с', 'т', 'ф', 'х', 'ц', 'ч', 'ш', 'щ']
        
        vowel_idx = 0
        consonant_idx = 0
        
        for phoneme in phonemes:
            if phoneme in 'aeiouəɨʉɯæøɤɑɒy':
                if vowel_idx < len(cyrillic_vowels):
                    mapping[phoneme] = cyrillic_vowels[vowel_idx]
                    vowel_idx += 1
                else:
                    mapping[phoneme] = phoneme
            else:
                if consonant_idx < len(cyrillic_consonants):
                    mapping[phoneme] = cyrillic_consonants[consonant_idx]
                    consonant_idx += 1
                else:
                    mapping[phoneme] = phoneme
        
        return mapping
    
    def _custom_mapping(self, phonemes: List[str]) -> Dict[str, str]:
        return {p: p for p in phonemes}
    
    def apply_orthography(self, phonetic_word: str) -> str:
        result = []
        i = 0
        while i < len(phonetic_word):
            matched = False
            for length in [3, 2, 1]:
                if i + length <= len(phonetic_word):
                    segment = phonetic_word[i:i+length]
                    if segment in self.mapping:
                        result.append(self.mapping[segment])
                        i += length
                        matched = True
                        break
            if not matched:
                result.append(phonetic_word[i])
                i += 1
        return ''.join(result)
