import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict, Counter
from datetime import datetime
import statistics


class LearningSystem:
    def __init__(self, profile_id: str, learning_dir: str = "learning"):
        self.profile_id = profile_id
        self.learning_dir = Path(learning_dir)
        self.learning_dir.mkdir(exist_ok=True)

        self.rules_file = self.learning_dir / f"{profile_id}_rules.json"
        self.patterns_file = self.learning_dir / f"{profile_id}_patterns.json"
        self.stats_file = self.learning_dir / f"{profile_id}_stats.json"

        self.transformation_rules: Dict[str, Dict] = {}
        self.pattern_library: Dict[str, List[Dict]] = defaultdict(list)
        self.success_metrics: Dict[str, Dict] = defaultdict(lambda: {
            'attempts': 0,
            'successes': 0,
            'failures': 0,
            'confidence': 0.5
        })
        self.generation_history: List[Dict] = []

        self.load_learning_data()

    def load_learning_data(self):
        if self.rules_file.exists():
            try:
                with open(self.rules_file, 'r', encoding='utf-8') as f:
                    self.transformation_rules = json.load(f)
            except:
                pass

        if self.patterns_file.exists():
            try:
                with open(self.patterns_file, 'r', encoding='utf-8') as f:
                    self.pattern_library = defaultdict(list, json.load(f))
            except:
                pass

        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.success_metrics = defaultdict(lambda: {
                        'attempts': 0, 'successes': 0, 'failures': 0, 'confidence': 0.5
                    }, data.get('metrics', {}))
                    self.generation_history = data.get('history', [])
            except:
                pass

    def save_learning_data(self):
        with open(self.rules_file, 'w', encoding='utf-8') as f:
            json.dump(self.transformation_rules, f,
                      indent=2, ensure_ascii=False)

        with open(self.patterns_file, 'w', encoding='utf-8') as f:
            json.dump(dict(self.pattern_library), f,
                      indent=2, ensure_ascii=False)

        stats_data = {
            'metrics': dict(self.success_metrics),
            'history': self.generation_history[-1000:],
            'last_updated': datetime.now().isoformat()
        }
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats_data, f, indent=2, ensure_ascii=False)

    def learn_transformation_rule(self, source_pattern: str, target_pattern: str,
                                  context: Optional[Dict] = None, confidence: float = 0.5):
        rule_key = self._get_rule_key(source_pattern)

        if rule_key not in self.transformation_rules:
            self.transformation_rules[rule_key] = {
                'source': source_pattern,
                'targets': [],
                'contexts': [],
                'confidence_scores': [],
                'usage_count': 0
            }

        rule = self.transformation_rules[rule_key]

        if target_pattern not in rule['targets']:
            rule['targets'].append(target_pattern)
            rule['contexts'].append(context or {})
            rule['confidence_scores'].append(confidence)
        else:
            idx = rule['targets'].index(target_pattern)
            old_confidence = rule['confidence_scores'][idx]
            rule['confidence_scores'][idx] = (old_confidence + confidence) / 2

        rule['usage_count'] += 1

    def _get_rule_key(self, pattern: str) -> str:
        return hashlib.md5(pattern.lower().encode()).hexdigest()[:16]

    def get_transformation_suggestions(self, source_pattern: str,
                                       context: Optional[Dict] = None) -> List[Tuple[str, float]]:
        rule_key = self._get_rule_key(source_pattern)

        if rule_key not in self.transformation_rules:
            return []

        rule = self.transformation_rules[rule_key]
        suggestions = []

        for target, ctx, confidence in zip(rule['targets'], rule['contexts'],
                                           rule['confidence_scores']):
            score = confidence

            if context and ctx:
                context_match = self._calculate_context_similarity(
                    context, ctx)
                score = (score + context_match) / 2

            suggestions.append((target, score))

        suggestions.sort(key=lambda x: x[1], reverse=True)
        return suggestions

    def _calculate_context_similarity(self, context1: Dict, context2: Dict) -> float:
        if not context1 or not context2:
            return 0.5

        keys1 = set(context1.keys())
        keys2 = set(context2.keys())

        if not keys1 or not keys2:
            return 0.5

        common_keys = keys1 & keys2
        if not common_keys:
            return 0.3

        matches = sum(
            1 for key in common_keys if context1[key] == context2[key])
        return matches / len(common_keys)

    def record_pattern(self, pattern_type: str, source: str, target: str,
                       features: Dict, quality_score: float = 0.5):
        pattern_entry = {
            'source': source,
            'target': target,
            'features': features,
            'quality': quality_score,
            'timestamp': datetime.now().isoformat(),
            'uses': 1
        }

        existing_patterns = self.pattern_library[pattern_type]

        for existing in existing_patterns:
            if existing['source'] == source and existing['target'] == target:
                existing['uses'] += 1
                existing['quality'] = (existing['quality'] + quality_score) / 2
                return

        self.pattern_library[pattern_type].append(pattern_entry)

        if len(self.pattern_library[pattern_type]) > 1000:
            self.pattern_library[pattern_type].sort(key=lambda x: (x['quality'], x['uses']),
                                                    reverse=True)
            self.pattern_library[pattern_type] = self.pattern_library[pattern_type][:800]

    def find_similar_patterns(self, pattern_type: str, features: Dict,
                              top_k: int = 5) -> List[Dict]:
        if pattern_type not in self.pattern_library:
            return []

        patterns = self.pattern_library[pattern_type]
        scored_patterns = []

        for pattern in patterns:
            similarity = self._calculate_feature_similarity(
                features, pattern['features'])
            quality_weight = pattern['quality'] * \
                0.6 + (pattern['uses'] / 100) * 0.4
            final_score = similarity * 0.7 + quality_weight * 0.3
            scored_patterns.append((pattern, final_score))

        scored_patterns.sort(key=lambda x: x[1], reverse=True)
        return [p for p, _ in scored_patterns[:top_k]]

    def _calculate_feature_similarity(self, features1: Dict, features2: Dict) -> float:
        if not features1 or not features2:
            return 0.0

        all_keys = set(features1.keys()) | set(features2.keys())
        if not all_keys:
            return 0.0

        matches = 0
        for key in all_keys:
            val1 = features1.get(key)
            val2 = features2.get(key)

            if val1 is None or val2 is None:
                continue

            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                if val1 == 0 and val2 == 0:
                    matches += 1
                else:
                    diff = abs(val1 - val2) / max(abs(val1), abs(val2), 1)
                    matches += max(0, 1 - diff)
            elif val1 == val2:
                matches += 1

        return matches / len(all_keys)

    def record_generation_attempt(self, source_words: List[str], generated: str,
                                  quality_score: float, was_cached: bool = False):
        self.generation_history.append({
            'source': source_words,
            'generated': generated,
            'quality': quality_score,
            'cached': was_cached,
            'timestamp': datetime.now().isoformat()
        })

        if len(self.generation_history) > 1000:
            self.generation_history = self.generation_history[-800:]

        metric_key = '|'.join(str(w) for w in source_words[:2])
        self.success_metrics[metric_key]['attempts'] += 1

        if quality_score > 0.7:
            self.success_metrics[metric_key]['successes'] += 1
        elif quality_score < 0.4:
            self.success_metrics[metric_key]['failures'] += 1

        attempts = self.success_metrics[metric_key]['attempts']
        successes = self.success_metrics[metric_key]['successes']
        self.success_metrics[metric_key]['confidence'] = successes / \
            attempts if attempts > 0 else 0.5

    def get_confidence_for_pattern(self, source_words: List[str]) -> float:
        metric_key = '|'.join(str(w) for w in source_words[:2])

        if metric_key in self.success_metrics:
            return self.success_metrics[metric_key]['confidence']

        return 0.5

    def get_learning_statistics(self) -> Dict:
        total_rules = len(self.transformation_rules)
        total_patterns = sum(len(patterns)
                             for patterns in self.pattern_library.values())

        total_attempts = sum(m['attempts']
                             for m in self.success_metrics.values())
        total_successes = sum(m['successes']
                              for m in self.success_metrics.values())

        confidence_scores = [m['confidence']
                             for m in self.success_metrics.values() if m['attempts'] > 0]
        avg_confidence = statistics.mean(
            confidence_scores) if confidence_scores else 0.5

        recent_quality = [h['quality'] for h in self.generation_history[-100:]]
        recent_avg_quality = statistics.mean(
            recent_quality) if recent_quality else 0.5

        return {
            'total_rules': total_rules,
            'total_patterns': total_patterns,
            'total_attempts': total_attempts,
            'total_successes': total_successes,
            'success_rate': total_successes / total_attempts if total_attempts > 0 else 0.0,
            'average_confidence': avg_confidence,
            'recent_quality': recent_avg_quality,
            'history_size': len(self.generation_history)
        }

    def consolidate_rules(self, min_usage: int = 5, min_confidence: float = 0.6):
        consolidated = 0
        rules_to_remove = []

        for rule_key, rule in self.transformation_rules.items():
            if rule['usage_count'] < min_usage:
                continue

            if len(rule['targets']) <= 1:
                continue

            best_idx = 0
            best_score = 0

            for i, (target, confidence) in enumerate(zip(rule['targets'], rule['confidence_scores'])):
                if confidence > best_score:
                    best_score = confidence
                    best_idx = i

            if best_score >= min_confidence:
                rule['targets'] = [rule['targets'][best_idx]]
                rule['contexts'] = [rule['contexts'][best_idx]]
                rule['confidence_scores'] = [
                    rule['confidence_scores'][best_idx]]
                consolidated += 1

        for rule_key in rules_to_remove:
            del self.transformation_rules[rule_key]

        return consolidated

    def cleanup_low_quality_patterns(self, min_quality: float = 0.3, min_uses: int = 2):
        cleaned = 0

        for pattern_type in self.pattern_library:
            original_count = len(self.pattern_library[pattern_type])

            self.pattern_library[pattern_type] = [
                p for p in self.pattern_library[pattern_type]
                if p['quality'] >= min_quality or p['uses'] >= min_uses
            ]

            cleaned += original_count - len(self.pattern_library[pattern_type])

        return cleaned


class ConvergenceEngine:
    def __init__(self, profile_id: str):
        self.profile_id = profile_id
        self.convergence_threshold = 0.85
        self.stability_window = 10
        self.translation_history: Dict[str, List[str]] = defaultdict(list)
        self.convergence_metrics: Dict[str, float] = {}

    def record_translation(self, source_key: str, translation: str):
        self.translation_history[source_key].append(translation)

        if len(self.translation_history[source_key]) > self.stability_window:
            self.translation_history[source_key] = self.translation_history[source_key][-self.stability_window:]

    def check_convergence(self, source_key: str) -> Tuple[bool, Optional[str]]:
        if source_key not in self.translation_history:
            return False, None

        history = self.translation_history[source_key]

        if len(history) < 3:
            return False, None

        counter = Counter(history)
        most_common = counter.most_common(1)[0]
        most_common_translation, frequency = most_common

        convergence_rate = frequency / len(history)
        self.convergence_metrics[source_key] = convergence_rate

        if convergence_rate >= self.convergence_threshold:
            return True, most_common_translation

        return False, None

    def get_preferred_translation(self, source_key: str) -> Optional[str]:
        if source_key not in self.translation_history:
            return None

        history = self.translation_history[source_key]
        if not history:
            return None

        counter = Counter(history)
        return counter.most_common(1)[0][0]

    def get_convergence_rate(self, source_key: str) -> float:
        return self.convergence_metrics.get(source_key, 0.0)

    def is_stable(self, source_key: str) -> bool:
        if source_key not in self.translation_history:
            return False

        history = self.translation_history[source_key]

        if len(history) < self.stability_window:
            return False

        recent = history[-self.stability_window:]
        return len(set(recent)) == 1

    def get_stability_report(self) -> Dict:
        total_keys = len(self.translation_history)
        converged_keys = sum(1 for key in self.translation_history
                             if self.check_convergence(key)[0])
        stable_keys = sum(1 for key in self.translation_history
                          if self.is_stable(key))

        avg_convergence = (statistics.mean(self.convergence_metrics.values())
                           if self.convergence_metrics else 0.0)

        return {
            'total_translations': total_keys,
            'converged': converged_keys,
            'stable': stable_keys,
            'convergence_rate': converged_keys / total_keys if total_keys > 0 else 0.0,
            'stability_rate': stable_keys / total_keys if total_keys > 0 else 0.0,
            'average_convergence': avg_convergence
        }


class AdaptiveWeightSystem:
    def __init__(self, base_weights: List[float]):
        self.base_weights = base_weights
        self.weight_history: List[List[float]] = [base_weights.copy()]
        self.performance_scores: List[float] = []
        self.learning_rate = 0.05
        self.momentum = 0.9
        self.velocity = [0.0] * len(base_weights)

    def adjust_weights(self, performance_score: float, gradient: Optional[List[float]] = None):
        self.performance_scores.append(performance_score)

        if gradient is None:
            if len(self.performance_scores) >= 2:
                gradient = self._estimate_gradient()
            else:
                return self.base_weights

        for i in range(len(self.base_weights)):
            self.velocity[i] = self.momentum * \
                self.velocity[i] + self.learning_rate * gradient[i]
            self.base_weights[i] += self.velocity[i]

        self.base_weights = self._normalize_weights(self.base_weights)
        self.weight_history.append(self.base_weights.copy())

        if len(self.weight_history) > 100:
            self.weight_history = self.weight_history[-80:]

        return self.base_weights

    def _estimate_gradient(self) -> List[float]:
        if len(self.performance_scores) < 2:
            return [0.0] * len(self.base_weights)

        recent_performance = self.performance_scores[-5:]
        avg_recent = statistics.mean(recent_performance)

        gradient = []
        for i in range(len(self.base_weights)):
            if len(self.weight_history) >= 2:
                weight_change = self.weight_history[-1][i] - \
                    self.weight_history[-2][i]
                if weight_change != 0:
                    grad = (avg_recent - 0.5) * \
                        weight_change / abs(weight_change)
                else:
                    grad = 0.0
            else:
                grad = 0.0
            gradient.append(grad)

        return gradient

    def _normalize_weights(self, weights: List[float]) -> List[float]:
        weights = [max(0.05, min(0.95, w)) for w in weights]
        total = sum(weights)
        return [w / total for w in weights] if total > 0 else weights

    def get_optimal_weights(self) -> List[float]:
        if len(self.performance_scores) < 5:
            return self.base_weights

        best_idx = 0
        best_score = 0.0

        for i in range(max(0, len(self.performance_scores) - 20), len(self.performance_scores)):
            if self.performance_scores[i] > best_score:
                best_score = self.performance_scores[i]
                best_idx = i

        if best_idx < len(self.weight_history):
            return self.weight_history[best_idx]

        return self.base_weights

    def reset_to_optimal(self):
        optimal = self.get_optimal_weights()
        self.base_weights = optimal
        self.velocity = [0.0] * len(self.base_weights)
