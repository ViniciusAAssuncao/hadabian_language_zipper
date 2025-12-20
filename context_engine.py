import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict, Counter
import re


class SemanticContextEngine:
    def __init__(self, profile_id: str, context_dir: str = "context"):
        self.profile_id = profile_id
        self.context_dir = Path(context_dir)
        self.context_dir.mkdir(exist_ok=True)

        self.context_file = self.context_dir / f"{profile_id}_semantic.json"

        self.word_embeddings: Dict[str, List[str]] = defaultdict(list)
        self.collocation_pairs: Dict[str, Dict[str, int]] = defaultdict(
            lambda: defaultdict(int))
        self.semantic_fields: Dict[str, Set[str]] = defaultdict(set)
        self.phrase_patterns: Dict[str, List[Dict]] = defaultdict(list)
        self.contextual_meanings: Dict[str, Dict[str, str]] = defaultdict(dict)

        self.load_context_data()

    def load_context_data(self):
        if self.context_file.exists():
            try:
                with open(self.context_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.word_embeddings = defaultdict(
                        list, data.get('embeddings', {}))

                    collocations = data.get('collocations', {})
                    for word, pairs in collocations.items():
                        self.collocation_pairs[word] = defaultdict(int, pairs)

                    fields = data.get('semantic_fields', {})
                    for field, words in fields.items():
                        self.semantic_fields[field] = set(words)

                    self.phrase_patterns = defaultdict(
                        list, data.get('phrase_patterns', {}))
                    self.contextual_meanings = defaultdict(
                        dict, data.get('contextual_meanings', {}))
            except:
                pass

    def save_context_data(self):
        data = {
            'embeddings': dict(self.word_embeddings),
            'collocations': {k: dict(v) for k, v in self.collocation_pairs.items()},
            'semantic_fields': {k: list(v) for k, v in self.semantic_fields.items()},
            'phrase_patterns': dict(self.phrase_patterns),
            'contextual_meanings': dict(self.contextual_meanings)
        }
        with open(self.context_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def build_context_window(self, words: List[str], target_index: int,
                             window_size: int = 3) -> Dict:
        context = {
            'before': [],
            'after': [],
            'target': words[target_index] if 0 <= target_index < len(words) else "",
            'full_sentence': words
        }

        start = max(0, target_index - window_size)
        end = min(len(words), target_index + window_size + 1)

        context['before'] = words[start:target_index]
        context['after'] = words[target_index + 1:end]

        return context

    def extract_collocations(self, text: str, window: int = 2):
        words = text.lower().split()

        for i in range(len(words)):
            for j in range(max(0, i - window), min(len(words), i + window + 1)):
                if i != j:
                    self.collocation_pairs[words[i]][words[j]] += 1

    def get_collocations(self, word: str, top_k: int = 5) -> List[Tuple[str, int]]:
        word = word.lower()
        if word not in self.collocation_pairs:
            return []

        pairs = self.collocation_pairs[word]
        sorted_pairs = sorted(pairs.items(), key=lambda x: x[1], reverse=True)
        return sorted_pairs[:top_k]

    def calculate_context_similarity(self, context1: Dict, context2: Dict) -> float:
        scores = []

        words1 = set(w.lower() for w in context1.get(
            'before', []) + context1.get('after', []))
        words2 = set(w.lower() for w in context2.get(
            'before', []) + context2.get('after', []))

        if words1 or words2:
            intersection = len(words1 & words2)
            union = len(words1 | words2)
            jaccard = intersection / union if union > 0 else 0.0
            scores.append(jaccard)

        before1 = [w.lower() for w in context1.get('before', [])]
        before2 = [w.lower() for w in context2.get('before', [])]
        if before1 and before2:
            before_match = sum(1 for w in before1 if w in before2) / \
                max(len(before1), len(before2))
            scores.append(before_match)

        after1 = [w.lower() for w in context1.get('after', [])]
        after2 = [w.lower() for w in context2.get('after', [])]
        if after1 and after2:
            after_match = sum(1 for w in after1 if w in after2) / \
                max(len(after1), len(after2))
            scores.append(after_match)

        return sum(scores) / len(scores) if scores else 0.0

    def add_to_semantic_field(self, field_name: str, words: List[str]):
        for word in words:
            self.semantic_fields[field_name].add(word.lower())

    def get_semantic_field(self, word: str) -> Optional[str]:
        word = word.lower()
        for field_name, words in self.semantic_fields.items():
            if word in words:
                return field_name
        return None

    def get_words_in_field(self, field_name: str) -> List[str]:
        return list(self.semantic_fields.get(field_name, set()))

    def are_semantically_related(self, word1: str, word2: str) -> bool:
        word1 = word1.lower()
        word2 = word2.lower()

        field1 = self.get_semantic_field(word1)
        field2 = self.get_semantic_field(word2)

        if field1 and field2 and field1 == field2:
            return True

        if word1 in self.collocation_pairs and word2 in self.collocation_pairs[word1]:
            if self.collocation_pairs[word1][word2] >= 3:
                return True

        return False

    def record_phrase_pattern(self, source_phrase: str, target_phrase: str,
                              pattern_type: str = "general"):
        pattern_key = self._get_pattern_key(source_phrase)

        pattern_entry = {
            'source': source_phrase,
            'target': target_phrase,
            'type': pattern_type,
            'uses': 1
        }

        for existing in self.phrase_patterns[pattern_key]:
            if existing['source'] == source_phrase and existing['target'] == target_phrase:
                existing['uses'] += 1
                return

        self.phrase_patterns[pattern_key].append(pattern_entry)

    def _get_pattern_key(self, phrase: str) -> str:
        words = phrase.lower().split()
        length_key = len(words)
        first_word = words[0] if words else ""
        return f"{length_key}_{first_word}"

    def find_phrase_pattern(self, source_phrase: str) -> Optional[str]:
        pattern_key = self._get_pattern_key(source_phrase)

        if pattern_key not in self.phrase_patterns:
            return None

        patterns = self.phrase_patterns[pattern_key]

        for pattern in patterns:
            if pattern['source'].lower() == source_phrase.lower():
                return pattern['target']

        best_match = None
        best_similarity = 0.0

        source_words = set(source_phrase.lower().split())
        for pattern in patterns:
            pattern_words = set(pattern['source'].lower().split())
            similarity = len(source_words & pattern_words) / \
                len(source_words | pattern_words)

            if similarity > best_similarity and similarity > 0.6:
                best_similarity = similarity
                best_match = pattern['target']

        return best_match

    def add_contextual_meaning(self, word: str, context_key: str, translation: str):
        word = word.lower()
        self.contextual_meanings[word][context_key] = translation

    def get_contextual_meaning(self, word: str, context: Dict) -> Optional[str]:
        word = word.lower()

        if word not in self.contextual_meanings:
            return None

        context_key = self._create_context_key(context)

        if context_key in self.contextual_meanings[word]:
            return self.contextual_meanings[word][context_key]

        best_match = None
        best_score = 0.0

        for stored_key, translation in self.contextual_meanings[word].items():
            similarity = self._compare_context_keys(context_key, stored_key)
            if similarity > best_score:
                best_score = similarity
                best_match = translation

        return best_match if best_score > 0.5 else None

    def _create_context_key(self, context: Dict) -> str:
        before = '_'.join(context.get('before', [])[-2:])
        after = '_'.join(context.get('after', [])[:2])
        return f"{before}|{after}"

    def _compare_context_keys(self, key1: str, key2: str) -> float:
        words1 = set(key1.split('_') + key1.split('|'))
        words2 = set(key2.split('_') + key2.split('|'))

        words1 = {w for w in words1 if w}
        words2 = {w for w in words2 if w}

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0


class PhraseAnalyzer:
    def __init__(self):
        self.phrase_cache: Dict[str, Dict] = {}

    def analyze_phrase(self, phrase: str) -> Dict:
        cache_key = phrase.lower()

        if cache_key in self.phrase_cache:
            return self.phrase_cache[cache_key]

        words = phrase.split()
        analysis = {
            'word_count': len(words),
            'avg_word_length': sum(len(w) for w in words) / len(words) if words else 0,
            'has_punctuation': bool(re.search(r'[.,!?;:]', phrase)),
            'capitalized_words': sum(1 for w in words if w and w[0].isupper()),
            'unique_words': len(set(w.lower() for w in words)),
            'lexical_density': len(set(w.lower() for w in words)) / len(words) if words else 0
        }

        self.phrase_cache[cache_key] = analysis
        return analysis

    def compare_phrases(self, phrase1: str, phrase2: str) -> Dict:
        analysis1 = self.analyze_phrase(phrase1)
        analysis2 = self.analyze_phrase(phrase2)

        comparison = {
            'length_ratio': analysis2['word_count'] / analysis1['word_count'] if analysis1['word_count'] > 0 else 0,
            'word_length_diff': abs(analysis1['avg_word_length'] - analysis2['avg_word_length']),
            'density_diff': abs(analysis1['lexical_density'] - analysis2['lexical_density'])
        }

        return comparison

    def extract_noun_phrases(self, text: str) -> List[str]:
        words = text.split()
        noun_phrases = []
        current_phrase = []

        for i, word in enumerate(words):
            cleaned = re.sub(r'[^\w]', '', word)

            if cleaned and (cleaned[0].isupper() or i == 0):
                current_phrase.append(word)
            else:
                if len(current_phrase) >= 2:
                    noun_phrases.append(' '.join(current_phrase))
                current_phrase = []

        if len(current_phrase) >= 2:
            noun_phrases.append(' '.join(current_phrase))

        return noun_phrases

    def detect_phrase_type(self, phrase: str) -> str:
        words = phrase.lower().split()

        if not words:
            return "empty"

        question_words = {'what', 'where',
                          'when', 'why', 'how', 'who', 'which'}
        if words[0] in question_words or phrase.endswith('?'):
            return "question"

        imperative_markers = {'go', 'come', 'do',
                              'make', 'take', 'give', 'bring'}
        if words[0] in imperative_markers:
            return "imperative"

        if any(word in words for word in ['and', 'but', 'or', 'because', 'although']):
            return "compound"

        return "declarative"


class ContextualTranslator:
    def __init__(self, semantic_engine: SemanticContextEngine):
        self.semantic_engine = semantic_engine
        self.phrase_analyzer = PhraseAnalyzer()

    def translate_with_context(self, word: str, full_sentence: List[str],
                               word_index: int, base_translation: str) -> str:
        context = self.semantic_engine.build_context_window(
            full_sentence, word_index)

        contextual_translation = self.semantic_engine.get_contextual_meaning(
            word, context)
        if contextual_translation:
            return contextual_translation

        collocations = self.semantic_engine.get_collocations(word.lower())
        if collocations:
            before_words = [w.lower() for w in context.get('before', [])]
            after_words = [w.lower() for w in context.get('after', [])]

            for collocate, freq in collocations:
                if collocate in before_words or collocate in after_words:
                    if freq >= 5:
                        return base_translation

        return base_translation

    def translate_phrase(self, phrase: str, word_translations: Dict[str, str]) -> str:
        pattern_translation = self.semantic_engine.find_phrase_pattern(phrase)
        if pattern_translation:
            return pattern_translation

        words = phrase.split()
        translated_words = []

        for i, word in enumerate(words):
            if word.lower() in word_translations:
                translated = self.translate_with_context(
                    word, words, i, word_translations[word.lower()]
                )
                translated_words.append(translated)
            else:
                translated_words.append(word)

        return ' '.join(translated_words)

    def should_keep_phrase_together(self, phrase: str) -> bool:
        noun_phrases = self.phrase_analyzer.extract_noun_phrases(phrase)

        if phrase in noun_phrases:
            return True

        words = phrase.lower().split()
        if len(words) <= 1:
            return False

        for i in range(len(words) - 1):
            collocations = self.semantic_engine.get_collocations(words[i])
            for collocate, freq in collocations:
                if collocate == words[i + 1] and freq >= 5:
                    return True

        return False


class SemanticFieldBuilder:
    def __init__(self, semantic_engine: SemanticContextEngine):
        self.semantic_engine = semantic_engine
        self.auto_detected_fields: Dict[str, List[str]] = defaultdict(list)

    def auto_detect_semantic_fields(self, texts: List[str], min_cooccurrence: int = 3):
        word_groups: Dict[str, Set[str]] = defaultdict(set)

        for text in texts:
            words = text.lower().split()
            for i, word in enumerate(words):
                context_words = set()
                for j in range(max(0, i - 3), min(len(words), i + 4)):
                    if i != j:
                        context_words.add(words[j])
                word_groups[word].update(context_words)

        clusters: List[Set[str]] = []
        processed = set()

        for word, related in word_groups.items():
            if word in processed:
                continue

            cluster = {word}
            for other_word, other_related in word_groups.items():
                if other_word == word or other_word in processed:
                    continue

                overlap = len(related & other_related)
                if overlap >= min_cooccurrence:
                    cluster.add(other_word)
                    processed.add(other_word)

            if len(cluster) >= 3:
                clusters.append(cluster)
                processed.update(cluster)

        for i, cluster in enumerate(clusters):
            field_name = f"auto_field_{i}"
            self.auto_detected_fields[field_name] = list(cluster)
            self.semantic_engine.add_to_semantic_field(
                field_name, list(cluster))

        return self.auto_detected_fields

    def get_field_statistics(self) -> Dict:
        manual_fields = len([f for f in self.semantic_engine.semantic_fields
                             if not f.startswith('auto_field_')])
        auto_fields = len(self.auto_detected_fields)
        total_words = sum(len(words)
                          for words in self.semantic_engine.semantic_fields.values())

        return {
            'manual_fields': manual_fields,
            'auto_fields': auto_fields,
            'total_fields': manual_fields + auto_fields,
            'total_words': total_words,
            'avg_words_per_field': total_words / (manual_fields + auto_fields) if (manual_fields + auto_fields) > 0 else 0
        }
