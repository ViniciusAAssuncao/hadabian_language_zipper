import json
import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import Counter, defaultdict
import statistics
import hashlib
import re


class AdvancedTextAnalyzer:
    def __init__(self):
        self.vowels = set('aeiouàâäèéêëìíîïòóôöùúûüáéíóúàèìòù')

    def analyze_comprehensive(self, text: str) -> Dict:
        words = text.split()
        chars = [c for c in text if c.isalpha()]

        analysis = {
            'basic': self._basic_stats(words, chars),
            'phonetic': self._phonetic_stats(words, chars),
            'lexical': self._lexical_stats(words),
            'structural': self._structural_stats(words)
        }

        return analysis

    def _basic_stats(self, words: List[str], chars: List[str]) -> Dict:
        return {
            'word_count': len(words),
            'char_count': len(chars),
            'avg_word_length': sum(len(w) for w in words) / len(words) if words else 0,
            'unique_words': len(set(w.lower() for w in words)),
            'type_token_ratio': len(set(w.lower() for w in words)) / len(words) if words else 0
        }

    def _phonetic_stats(self, words: List[str], chars: List[str]) -> Dict:
        vowel_count = sum(1 for c in chars if c.lower() in self.vowels)
        consonant_count = len(chars) - vowel_count

        syllable_counts = []
        for word in words:
            syllables = self._estimate_syllables(word)
            syllable_counts.append(syllables)

        return {
            'vowel_count': vowel_count,
            'consonant_count': consonant_count,
            'vowel_ratio': vowel_count / len(chars) if chars else 0,
            'avg_syllables_per_word': statistics.mean(syllable_counts) if syllable_counts else 0,
            'max_syllables': max(syllable_counts) if syllable_counts else 0
        }

    def _estimate_syllables(self, word: str) -> int:
        word = word.lower()
        count = 0
        previous_was_vowel = False

        for char in word:
            is_vowel = char in self.vowels
            if is_vowel and not previous_was_vowel:
                count += 1
            previous_was_vowel = is_vowel

        return max(1, count)

    def _lexical_stats(self, words: List[str]) -> Dict:
        word_lengths = [len(w) for w in words]

        return {
            'min_word_length': min(word_lengths) if word_lengths else 0,
            'max_word_length': max(word_lengths) if word_lengths else 0,
            'median_word_length': statistics.median(word_lengths) if word_lengths else 0,
            'stdev_word_length': statistics.stdev(word_lengths) if len(word_lengths) > 1 else 0
        }

    def _structural_stats(self, words: List[str]) -> Dict:
        capitalized = sum(1 for w in words if w and w[0].isupper())
        all_caps = sum(1 for w in words if w.isupper() and len(w) > 1)

        return {
            'capitalized_words': capitalized,
            'all_caps_words': all_caps,
            'capitalization_rate': capitalized / len(words) if words else 0
        }

    def compare_texts(self, text1: str, text2: str) -> Dict:
        analysis1 = self.analyze_comprehensive(text1)
        analysis2 = self.analyze_comprehensive(text2)

        comparison = {
            'length_preservation': analysis2['basic']['word_count'] / analysis1['basic']['word_count'] if analysis1['basic']['word_count'] > 0 else 0,
            'lexical_diversity_shift': analysis2['basic']['type_token_ratio'] - analysis1['basic']['type_token_ratio'],
            'vowel_ratio_shift': analysis2['phonetic']['vowel_ratio'] - analysis1['phonetic']['vowel_ratio'],
            'avg_word_length_shift': analysis2['basic']['avg_word_length'] - analysis1['basic']['avg_word_length']
        }

        return comparison

    def detect_patterns(self, text: str) -> Dict:
        words = text.split()

        patterns = {
            'common_prefixes': self._find_common_affixes(words, 'prefix', 3),
            'common_suffixes': self._find_common_affixes(words, 'suffix', 3),
            'repeated_sequences': self._find_repeated_sequences(words),
            'word_length_distribution': self._word_length_distribution(words)
        }

        return patterns

    def _find_common_affixes(self, words: List[str], affix_type: str, min_length: int) -> List[Tuple[str, int]]:
        affixes = Counter()

        for word in words:
            if len(word) < min_length * 2:
                continue

            if affix_type == 'prefix':
                for length in range(min_length, min(len(word) // 2, 5)):
                    affixes[word[:length]] += 1
            else:
                for length in range(min_length, min(len(word) // 2, 5)):
                    affixes[word[-length:]] += 1

        return affixes.most_common(10)

    def _find_repeated_sequences(self, words: List[str]) -> List[Tuple[str, int]]:
        sequences = Counter()

        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i+1]}"
            sequences[bigram] += 1

        return sequences.most_common(10)

    def _word_length_distribution(self, words: List[str]) -> Dict[int, int]:
        distribution = Counter(len(w) for w in words)
        return dict(sorted(distribution.items()))


class QualityMetrics:
    def __init__(self):
        self.analyzer = AdvancedTextAnalyzer()

    def calculate_translation_quality(self, source_text: str, generated_text: str,
                                      expected_characteristics: Optional[Dict] = None) -> Dict:
        source_analysis = self.analyzer.analyze_comprehensive(source_text)
        generated_analysis = self.analyzer.analyze_comprehensive(
            generated_text)
        comparison = self.analyzer.compare_texts(source_text, generated_text)

        scores = {}

        length_score = self._score_length_preservation(
            comparison['length_preservation'])
        scores['length_preservation'] = length_score

        diversity_score = self._score_lexical_diversity(
            generated_analysis['basic']['type_token_ratio'],
            source_analysis['basic']['type_token_ratio']
        )
        scores['lexical_diversity'] = diversity_score

        phonetic_score = self._score_phonetic_balance(
            generated_analysis['phonetic']['vowel_ratio']
        )
        scores['phonetic_balance'] = phonetic_score

        structure_score = self._score_structure(generated_analysis)
        scores['structural_validity'] = structure_score

        if expected_characteristics:
            characteristic_score = self._score_characteristics(
                generated_analysis, expected_characteristics
            )
            scores['characteristic_match'] = characteristic_score

        overall_score = sum(scores.values()) / len(scores)

        return {
            'overall_quality': overall_score,
            'component_scores': scores,
            'details': {
                'source': source_analysis,
                'generated': generated_analysis,
                'comparison': comparison
            }
        }

    def _score_length_preservation(self, ratio: float) -> float:
        if 0.8 <= ratio <= 1.2:
            return 1.0
        elif 0.6 <= ratio <= 1.4:
            return 0.7
        elif 0.4 <= ratio <= 1.6:
            return 0.4
        else:
            return 0.1

    def _score_lexical_diversity(self, generated: float, source: float) -> float:
        if abs(generated - source) < 0.1:
            return 1.0
        elif abs(generated - source) < 0.2:
            return 0.7
        else:
            return 0.4

    def _score_phonetic_balance(self, vowel_ratio: float) -> float:
        ideal_ratio = 0.4
        deviation = abs(vowel_ratio - ideal_ratio)

        if deviation < 0.05:
            return 1.0
        elif deviation < 0.1:
            return 0.8
        elif deviation < 0.15:
            return 0.6
        else:
            return 0.3

    def _score_structure(self, analysis: Dict) -> float:
        scores = []

        avg_word_length = analysis['basic']['avg_word_length']
        if 4 <= avg_word_length <= 8:
            scores.append(1.0)
        elif 3 <= avg_word_length <= 10:
            scores.append(0.7)
        else:
            scores.append(0.4)

        type_token = analysis['basic']['type_token_ratio']
        if type_token > 0.5:
            scores.append(1.0)
        elif type_token > 0.3:
            scores.append(0.7)
        else:
            scores.append(0.5)

        return sum(scores) / len(scores)

    def _score_characteristics(self, analysis: Dict, expected: Dict) -> float:
        scores = []

        if 'target_vowel_ratio' in expected:
            target = expected['target_vowel_ratio']
            actual = analysis['phonetic']['vowel_ratio']
            deviation = abs(actual - target)
            score = max(0, 1.0 - deviation * 5)
            scores.append(score)

        if 'target_avg_word_length' in expected:
            target = expected['target_avg_word_length']
            actual = analysis['basic']['avg_word_length']
            deviation = abs(actual - target)
            score = max(0, 1.0 - deviation / 3)
            scores.append(score)

        return sum(scores) / len(scores) if scores else 0.5


class BatchProcessor:
    def __init__(self, zipper_engine):
        self.engine = zipper_engine
        self.results = []

    def process_batch(self, input_files: List[str], output_dir: str) -> List[Dict]:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        self.results = []

        for i, file_path in enumerate(input_files):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                base_texts = self._split_by_bases(content)

                if len(base_texts) != len(self.engine.bases):
                    self.results.append({
                        'file': file_path,
                        'status': 'error',
                        'message': f'Expected {len(self.engine.bases)} base texts'
                    })
                    continue

                result = self.engine.process_texts(base_texts)

                output_file = output_path / f"output_{i:03d}.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result)

                self.results.append({
                    'file': file_path,
                    'status': 'success',
                    'output': str(output_file),
                    'word_count': len(result.split())
                })

            except Exception as e:
                self.results.append({
                    'file': file_path,
                    'status': 'error',
                    'message': str(e)
                })

        return self.results

    def _split_by_bases(self, content: str) -> List[str]:
        separator = "---BASE---"
        if separator in content:
            return content.split(separator)

        return [content] * len(self.engine.bases)

    def generate_report(self, output_path: str):
        report = {
            'total_files': len(self.results),
            'successful': sum(1 for r in self.results if r['status'] == 'success'),
            'failed': sum(1 for r in self.results if r['status'] == 'error'),
            'total_words': sum(r.get('word_count', 0) for r in self.results),
            'results': self.results
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return report


class DictionaryExporter:
    def __init__(self, translation_cache):
        self.cache = translation_cache

    def export_full_dictionary(self, output_path: str, format: str = 'json',
                               min_frequency: int = 1) -> int:
        if format == 'json':
            return self._export_json(output_path, min_frequency)
        elif format == 'csv':
            return self._export_csv(output_path, min_frequency)
        elif format == 'txt':
            return self._export_txt(output_path, min_frequency)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _export_json(self, output_path: str, min_frequency: int) -> int:
        dictionary = []

        for key, entry in self.cache.mapping.items():
            freq = self.cache.frequency.get(key, 0)
            if freq >= min_frequency:
                dictionary.append({
                    'source': ' '.join(entry['source']),
                    'target': entry['target'],
                    'frequency': freq,
                    'variations': entry.get('variations', [entry['target']]),
                    'created_count': entry.get('created_count', 1)
                })

        dictionary.sort(key=lambda x: x['frequency'], reverse=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(dictionary, f, indent=2, ensure_ascii=False)

        return len(dictionary)

    def _export_csv(self, output_path: str, min_frequency: int) -> int:
        rows = []

        for key, entry in self.cache.mapping.items():
            freq = self.cache.frequency.get(key, 0)
            if freq >= min_frequency:
                rows.append({
                    'source': ' '.join(entry['source']),
                    'target': entry['target'],
                    'frequency': freq,
                    'variation_count': len(entry.get('variations', []))
                })

        rows.sort(key=lambda x: x['frequency'], reverse=True)

        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

        return len(rows)

    def _export_txt(self, output_path: str, min_frequency: int) -> int:
        entries = []

        for key, entry in self.cache.mapping.items():
            freq = self.cache.frequency.get(key, 0)
            if freq >= min_frequency:
                source = ' '.join(entry['source'])
                target = entry['target']
                entries.append((source, target, freq))

        entries.sort(key=lambda x: x[2], reverse=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            for source, target, freq in entries:
                f.write(f"{source} → {target} ({freq}x)\n")

        return len(entries)


class ProfileOptimizer:
    def __init__(self, zipper_engine):
        self.engine = zipper_engine
        self.test_results = []

    def optimize_weights(self, test_texts: List[List[str]],
                         iterations: int = 10) -> List[float]:
        best_weights = self.engine.fusion_weights.copy()
        best_score = 0.0

        for iteration in range(iterations):
            test_weights = self._generate_test_weights(best_weights, iteration)

            self.engine.fusion_weights = test_weights
            self.engine._normalize_weights()

            total_score = 0.0
            for test_set in test_texts:
                result = self.engine.process_texts(test_set)
                score = self._evaluate_result(result, test_set)
                total_score += score

            avg_score = total_score / len(test_texts)

            self.test_results.append({
                'iteration': iteration,
                'weights': test_weights,
                'score': avg_score
            })

            if avg_score > best_score:
                best_score = avg_score
                best_weights = test_weights.copy()

        self.engine.fusion_weights = best_weights
        self.engine._normalize_weights()

        return best_weights

    def _generate_test_weights(self, base_weights: List[float], iteration: int) -> List[float]:
        import random
        random.seed(iteration)

        variation = 0.1
        test_weights = []

        for weight in base_weights:
            adjusted = weight + random.uniform(-variation, variation)
            test_weights.append(max(0.05, min(0.95, adjusted)))

        return test_weights

    def _evaluate_result(self, result: str, source_texts: List[str]) -> float:
        quality_metrics = QualityMetrics()

        combined_source = ' '.join(source_texts)
        quality_report = quality_metrics.calculate_translation_quality(
            combined_source, result
        )

        return quality_report['overall_quality']

    def get_optimization_report(self) -> Dict:
        if not self.test_results:
            return {}

        best_result = max(self.test_results, key=lambda x: x['score'])

        scores = [r['score'] for r in self.test_results]

        return {
            'best_weights': best_result['weights'],
            'best_score': best_result['score'],
            'iterations': len(self.test_results),
            'avg_score': statistics.mean(scores),
            'improvement': best_result['score'] - self.test_results[0]['score'],
            'all_results': self.test_results
        }


class ConsistencyReporter:
    def __init__(self, zipper_engine):
        self.engine = zipper_engine

    def generate_consistency_report(self) -> Dict:
        report = {}

        if hasattr(self.engine, 'consistency_validator'):
            inconsistencies = self.engine.consistency_validator.get_inconsistencies()
            consistency_rate = self.engine.consistency_validator.get_consistency_rate()

            report['validation'] = {
                'consistency_rate': consistency_rate,
                'inconsistency_count': len(inconsistencies),
                'inconsistencies': inconsistencies[:10]
            }

        if hasattr(self.engine, 'convergence_engine'):
            convergence_report = self.engine.convergence_engine.get_stability_report()
            report['convergence'] = convergence_report

        if hasattr(self.engine, 'translation_cache'):
            cache_stats = self.engine.translation_cache.get_statistics()
            report['cache'] = cache_stats

        return report

    def export_inconsistencies(self, output_path: str):
        if not hasattr(self.engine, 'consistency_validator'):
            return

        inconsistencies = self.engine.consistency_validator.get_inconsistencies()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(inconsistencies, f, indent=2, ensure_ascii=False)

    def suggest_corrections(self) -> List[Dict]:
        if not hasattr(self.engine, 'consistency_validator'):
            return []

        inconsistencies = self.engine.consistency_validator.get_inconsistencies()
        suggestions = []

        for inconsistency in inconsistencies:
            source = inconsistency['source']
            previous = inconsistency['previous']
            current = inconsistency['current']

            if hasattr(self.engine, 'convergence_engine'):
                preferred = self.engine.convergence_engine.get_preferred_translation(
                    source)
                if preferred:
                    suggestions.append({
                        'source': source,
                        'conflicting_translations': [previous, current],
                        'suggested_translation': preferred,
                        'reason': 'most_frequent'
                    })
            else:
                suggestions.append({
                    'source': source,
                    'conflicting_translations': [previous, current],
                    'suggested_translation': previous,
                    'reason': 'first_occurrence'
                })

        return suggestions
