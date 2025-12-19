import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class TextAnalyzer:
    @staticmethod
    def analyze_text(text: str) -> Dict:
        words = text.split()
        chars = list(text.replace(' ', ''))

        vowels = set('aeiouàâäãåæèéêëìíîïòóôöõøùúûüýÿœ')
        vowel_count = sum(1 for c in chars if c.lower() in vowels)
        consonant_count = sum(1 for c in chars if c.isalpha()
                              and c.lower() not in vowels)

        return {
            'word_count': len(words),
            'char_count': len(chars),
            'vowel_count': vowel_count,
            'consonant_count': consonant_count,
            'vowel_ratio': vowel_count / len(chars) if chars else 0,
            'avg_word_length': sum(len(w) for w in words) / len(words) if words else 0
        }

    @staticmethod
    def compare_texts(text1: str, text2: str) -> Dict:
        stats1 = TextAnalyzer.analyze_text(text1)
        stats2 = TextAnalyzer.analyze_text(text2)

        return {
            'original': stats1,
            'generated': stats2,
            'length_preservation': stats2['word_count'] / stats1['word_count'] if stats1['word_count'] else 0,
            'vowel_shift': stats2['vowel_ratio'] - stats1['vowel_ratio']
        }


class NameGenerator:
    def __init__(self, zipper_engine):
        self.engine = zipper_engine

    def generate_names(self, seed_texts: List[str], count: int = 10) -> List[str]:
        full_text = self.engine.process_texts(seed_texts)
        words = full_text.split()

        names = []
        for word in words:
            if len(word) >= 3 and len(word) <= 12:
                capitalized = word[0].upper() + word[1:].lower()
                if capitalized not in names:
                    names.append(capitalized)
                if len(names) >= count:
                    break

        return names

    def generate_place_names(self, seed_texts: List[str], suffixes: List[str], count: int = 10) -> List[str]:
        full_text = self.engine.process_texts(seed_texts)
        words = full_text.split()

        places = []
        suffix_idx = 0

        for word in words:
            if len(word) >= 3 and len(word) <= 10:
                base = word[0].upper() + word[1:].lower()
                suffix = suffixes[suffix_idx % len(suffixes)]
                place_name = base + suffix

                if place_name not in places:
                    places.append(place_name)
                    suffix_idx += 1

                if len(places) >= count:
                    break

        return places


class ProfileTemplates:
    @staticmethod
    def get_formal_aristocratic() -> Dict:
        return {
            "id": "template_formal",
            "name": "Formal Aristocratic",
            "description": "Template for formal, aristocratic languages",
            "bases": ["fr", "la"],
            "fusion_weights": [0.65, 0.35],
            "fusion_rules": {
                "min_cut_point": 0.45,
                "preserve_caps": True,
                "preserve_accents": True,
                "contraction_handling": "expand"
            },
            "phonotactics": {
                "vowels": "aeiouàâéèêëìíîïòóôö",
                "forbidden_final_consonants": ["w", "x"],
                "max_consonant_cluster": 3,
                "max_vowel_cluster": 2
            },
            "orthography": {
                "long_vowel_mapping": {"a": "â", "e": "ê", "o": "ô"},
                "primary_accent": "circumflex",
                "transform_s_to_cedilla": False
            },
            "semantic_general": "formal",
            "global_seed": 10000
        }

    @staticmethod
    def get_trade_language() -> Dict:
        return {
            "id": "template_trade",
            "name": "Trade Language",
            "description": "Template for practical trade languages",
            "bases": ["en", "eo"],
            "fusion_weights": [0.5, 0.5],
            "fusion_rules": {
                "min_cut_point": 0.35,
                "preserve_caps": True,
                "preserve_accents": False,
                "contraction_handling": "separate"
            },
            "phonotactics": {
                "vowels": "aeiou",
                "forbidden_final_consonants": ["q", "x"],
                "max_consonant_cluster": 2,
                "max_vowel_cluster": 2
            },
            "orthography": {
                "long_vowel_mapping": {},
                "primary_accent": "none",
                "transform_s_to_cedilla": False
            },
            "semantic_general": "neutral",
            "global_seed": 20000
        }

    @staticmethod
    def get_ancient_scholarly() -> Dict:
        return {
            "id": "template_ancient",
            "name": "Ancient Scholarly",
            "description": "Template for ancient, scholarly languages",
            "bases": ["sa", "grc"],
            "fusion_weights": [0.6, 0.4],
            "fusion_rules": {
                "min_cut_point": 0.48,
                "preserve_caps": True,
                "preserve_accents": True,
                "contraction_handling": "expand"
            },
            "phonotactics": {
                "vowels": "aeiouāīū",
                "forbidden_final_consonants": [],
                "max_consonant_cluster": 4,
                "max_vowel_cluster": 1
            },
            "orthography": {
                "long_vowel_mapping": {"a": "ā", "i": "ī", "u": "ū"},
                "primary_accent": "macron",
                "transform_s_to_cedilla": False
            },
            "semantic_general": "archaic",
            "global_seed": 30000
        }

    @staticmethod
    def get_poetic_melodic() -> Dict:
        return {
            "id": "template_poetic",
            "name": "Poetic Melodic",
            "description": "Template for poetic, melodic languages",
            "bases": ["it", "pt"],
            "fusion_weights": [0.55, 0.45],
            "fusion_rules": {
                "min_cut_point": 0.38,
                "preserve_caps": True,
                "preserve_accents": True,
                "contraction_handling": "maintain"
            },
            "phonotactics": {
                "vowels": "aeiouáàâãéêíóôõú",
                "forbidden_final_consonants": ["b", "d", "g", "k", "p", "t"],
                "max_consonant_cluster": 2,
                "max_vowel_cluster": 3
            },
            "orthography": {
                "long_vowel_mapping": {},
                "primary_accent": "acute",
                "transform_s_to_cedilla": False
            },
            "semantic_general": "neutral",
            "global_seed": 40000
        }


class BatchProfileGenerator:
    @staticmethod
    def generate_dialect_variations(base_profile: Dict, num_variants: int = 5) -> List[Dict]:
        variants = []
        base_seed = base_profile.get('global_seed', 12345)

        for i in range(num_variants):
            variant = base_profile.copy()
            variant['id'] = f"{base_profile['id']}_dialect_{i+1}"
            variant['name'] = f"{base_profile.get('name', 'Unknown')} - Dialect {i+1}"
            variant['global_seed'] = base_seed + (i * 1000)

            weights = variant.get('fusion_weights', [0.5, 0.5])
            shift = (i - num_variants // 2) * 0.05
            new_weights = [max(0.1, min(0.9, w + shift)) for w in weights]
            total = sum(new_weights)
            variant['fusion_weights'] = [w / total for w in new_weights]

            variants.append(variant)

        return variants

    @staticmethod
    def generate_regional_variants(base_profile: Dict, regions: List[str]) -> List[Dict]:
        variants = []
        base_seed = base_profile.get('global_seed', 12345)

        for i, region in enumerate(regions):
            variant = base_profile.copy()
            variant['id'] = f"{base_profile['id']}_{region.lower()}"
            variant['name'] = f"{base_profile.get('name', 'Unknown')} - {region}"
            variant['description'] = f"Regional variant from {region}"
            variant['global_seed'] = base_seed + hash(region) % 10000

            variants.append(variant)

        return variants


class ConsistencyChecker:
    @staticmethod
    def check_determinism(zipper_engine, test_texts: List[str], iterations: int = 3) -> bool:
        results = []

        for _ in range(iterations):
            output = zipper_engine.process_texts(test_texts)
            results.append(output)

        return all(r == results[0] for r in results)

    @staticmethod
    def test_profile_consistency(profile_path: str, test_texts: List[str]) -> Dict:
        from zipper_engine import ZipperEngine

        try:
            engine = ZipperEngine(profile_path)
            is_deterministic = ConsistencyChecker.check_determinism(
                engine, test_texts)

            output = engine.process_texts(test_texts)
            analysis = TextAnalyzer.analyze_text(output)

            return {
                'success': True,
                'deterministic': is_deterministic,
                'output_stats': analysis,
                'output_sample': output[:200] + '...' if len(output) > 200 else output
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


class ExportUtilities:
    @staticmethod
    def export_lexicon(generated_text: str, min_word_length: int = 3) -> List[Dict]:
        words = generated_text.split()
        unique_words = sorted(set(words))

        lexicon = []
        for word in unique_words:
            if len(word) >= min_word_length:
                entry = {
                    'word': word,
                    'length': len(word),
                    'capitalized': word[0].isupper()
                }
                lexicon.append(entry)

        return lexicon

    @staticmethod
    def export_to_json(data: any, filepath: str):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def export_to_csv(lexicon: List[Dict], filepath: str):
        import csv

        if not lexicon:
            return

        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=lexicon[0].keys())
            writer.writeheader()
            writer.writerows(lexicon)


class QuickSetup:
    @staticmethod
    def create_default_structure():
        Path('profiles').mkdir(exist_ok=True)
        Path('outputs').mkdir(exist_ok=True)
        Path('inputs').mkdir(exist_ok=True)

        return {
            'profiles': Path('profiles').absolute(),
            'outputs': Path('outputs').absolute(),
            'inputs': Path('inputs').absolute()
        }

    @staticmethod
    def create_example_inputs():
        examples = {
            'french_sample.txt': "Je marche dans la forêt ancienne. Les arbres murmurent des secrets oubliés.",
            'volapuk_sample.txt': "Gölon in vud büik. Böms sagons sekretis püfadöl.",
            'portuguese_sample.txt': "Eu caminho pela floresta antiga. As árvores sussurram segredos esquecidos.",
            'chinese_sample.txt': "我走在古老的森林里。树木低语着被遗忘的秘密。"
        }

        inputs_dir = Path('inputs')
        inputs_dir.mkdir(exist_ok=True)

        for filename, content in examples.items():
            filepath = inputs_dir / filename
            if not filepath.exists():
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

        return list(examples.keys())
