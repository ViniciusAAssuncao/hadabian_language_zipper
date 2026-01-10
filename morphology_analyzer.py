import re
from typing import List, Dict, Tuple, Optional, Set
from collections import Counter
import unicodedata


class MorphologyAnalyzer:
    def __init__(self, vowels: str = "aeiouàâäèéêëìíîïòóôöùúûü"):
        self.vowels = set(vowels.lower())
        self.common_prefixes = self._initialize_prefixes()
        self.common_suffixes = self._initialize_suffixes()
        self.morpheme_boundary_markers = set(['-', '_'])

    def _initialize_prefixes(self) -> Set[str]:
        return {
            're', 'un', 'de', 'dis', 'in', 'im', 'pre', 'post', 'anti',
            'sub', 'super', 'trans', 'inter', 'intra', 'extra', 'contra',
            'auto', 'co', 'ex', 'over', 'under', 'mis', 'non', 'pro'
        }

    def _initialize_suffixes(self) -> Set[str]:
        return {
            'ing', 'ed', 'er', 'est', 'ly', 'ness', 'ment', 'tion', 'sion',
            'ity', 'ty', 'al', 'ial', 'ous', 'ious', 'ful', 'less', 'able',
            'ible', 'ive', 'en', 's', 'es', 'ied', 'ies', 'ian', 'ist'
        }

    def detect_stacking(self, word: str) -> bool:
        if len(word) < 6:
            return False

        lower_word = word.lower()

        for i in range(3, len(word) - 2):
            prefix = lower_word[:i]
            suffix = lower_word[i:]

            if prefix == suffix:
                return True

            if len(suffix) >= 4:
                if prefix in suffix or suffix in prefix:
                    similarity = self._calculate_similarity(prefix, suffix)
                    if similarity > 0.7:
                        return True

        pattern_length = len(word) // 2
        if pattern_length >= 3:
            for start in range(len(word) - pattern_length):
                pattern = lower_word[start:start + pattern_length]
                rest = lower_word[start + pattern_length:]
                if rest.startswith(pattern[:len(rest)]):
                    return True

        return False

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        if not str1 or not str2:
            return 0.0

        max_len = max(len(str1), len(str2))
        matches = sum(1 for a, b in zip(str1, str2) if a == b)
        return matches / max_len

    def fix_stacking(self, word: str) -> str:
        if not self.detect_stacking(word):
            return word

        lower_word = word.lower()
        is_capitalized = word[0].isupper()

        for i in range(3, len(word) - 2):
            prefix = lower_word[:i]
            suffix = lower_word[i:]

            if prefix == suffix:
                fixed = prefix
                if is_capitalized:
                    fixed = fixed[0].upper() + fixed[1:]
                return fixed

        pattern_length = len(word) // 2
        if pattern_length >= 3:
            for start in range(len(word) - pattern_length):
                pattern = lower_word[start:start + pattern_length]
                rest = lower_word[start + pattern_length:]
                if rest.startswith(pattern[:len(rest)]):
                    fixed = lower_word[:start + pattern_length]
                    if is_capitalized:
                        fixed = fixed[0].upper() + fixed[1:]
                    return fixed

        mid_point = len(word) // 2
        fixed = lower_word[:mid_point]
        if is_capitalized:
            fixed = fixed[0].upper() + fixed[1:]
        return fixed

    def decompose_word(self, word: str) -> Dict[str, str]:
        lower_word = word.lower()

        prefix = ""
        for pfx in sorted(self.common_prefixes, key=len, reverse=True):
            if lower_word.startswith(pfx) and len(lower_word) > len(pfx) + 2:
                prefix = pfx
                lower_word = lower_word[len(pfx):]
                break

        suffix = ""
        for sfx in sorted(self.common_suffixes, key=len, reverse=True):
            if lower_word.endswith(sfx) and len(lower_word) > len(sfx) + 2:
                suffix = sfx
                lower_word = lower_word[:-len(sfx)]
                break

        root = lower_word

        return {
            'prefix': prefix,
            'root': root,
            'suffix': suffix,
            'original': word
        }

    def recompose_word(self, parts: Dict[str, str]) -> str:
        word = parts.get('prefix', '') + parts.get('root',
                                                   '') + parts.get('suffix', '')

        if 'original' in parts:
            if parts['original'] and parts['original'][0].isupper():
                word = word[0].upper() + word[1:] if word else word

        return word

    def detect_reduplication(self, word: str) -> Optional[Tuple[str, int]]:
        lower_word = word.lower()

        for length in range(2, len(word) // 2 + 1):
            for start in range(len(word) - length):
                segment = lower_word[start:start + length]
                remaining = lower_word[start + length:]

                count = 1
                pos = 0
                while pos < len(remaining):
                    if remaining[pos:pos + length] == segment:
                        count += 1
                        pos += length
                    else:
                        break

                if count >= 2:
                    return (segment, count)

        return None

    def fix_reduplication(self, word: str, max_repetitions: int = 2) -> str:
        reduplication = self.detect_reduplication(word)
        if not reduplication:
            return word

        segment, count = reduplication
        if count <= max_repetitions:
            return word

        is_capitalized = word[0].isupper()
        lower_word = word.lower()

        start_pos = lower_word.find(segment)
        if start_pos == -1:
            return word

        before = lower_word[:start_pos]
        repeated_part = segment * min(count, max_repetitions)
        after_pos = start_pos + len(segment) * count
        after = lower_word[after_pos:]

        fixed = before + repeated_part + after

        if is_capitalized and fixed:
            fixed = fixed[0].upper() + fixed[1:]

        return fixed

    def extract_syllables_advanced(self, word: str, diphthongs: List[str] = None) -> List[str]:
        if not word:
            return []

        if diphthongs is None:
            diphthongs = ['ai', 'ei', 'oi', 'au', 'eu',
                          'ou', 'ia', 'ie', 'io', 'ua', 'ue', 'uo']

        word = word.lower()
        syllables = []
        current = ""
        i = 0

        while i < len(word):
            char = word[i]

            if i + 1 < len(word):
                bigram = word[i:i+2]
                if bigram in diphthongs:
                    current += bigram
                    i += 2

                    if i < len(word) and word[i] not in self.vowels:
                        consonant_cluster = ""
                        while i < len(word) and word[i] not in self.vowels:
                            consonant_cluster += word[i]
                            i += 1

                        if len(consonant_cluster) > 1:
                            split_point = len(consonant_cluster) // 2
                            current += consonant_cluster[:split_point]
                            syllables.append(current)
                            current = consonant_cluster[split_point:]
                        else:
                            syllables.append(current)
                            current = consonant_cluster
                    else:
                        syllables.append(current)
                        current = ""
                    continue

            current += char

            if char in self.vowels:
                if i + 1 < len(word):
                    j = i + 1
                    consonant_cluster = ""
                    while j < len(word) and word[j] not in self.vowels:
                        consonant_cluster += word[j]
                        j += 1

                    if consonant_cluster:
                        if len(consonant_cluster) > 1 and j < len(word):
                            split_point = len(consonant_cluster) // 2
                            current += consonant_cluster[:split_point]
                            syllables.append(current)
                            current = consonant_cluster[split_point:]
                            i = j - 1
                        else:
                            syllables.append(current)
                            current = consonant_cluster if j < len(
                                word) else ""
                            i = j - 1
                    else:
                        syllables.append(current)
                        current = ""
                else:
                    syllables.append(current)
                    current = ""

            i += 1

        if current:
            if syllables:
                syllables[-1] += current
            else:
                syllables.append(current)

        return [s for s in syllables if s]

    def calculate_phonetic_distance(self, word1: str, word2: str) -> float:
        if not word1 or not word2:
            return 1.0

        word1 = word1.lower()
        word2 = word2.lower()

        max_len = max(len(word1), len(word2))
        min_len = min(len(word1), len(word2))

        length_diff = abs(len(word1) - len(word2)) / max_len

        char_matches = sum(1 for i in range(min_len) if word1[i] == word2[i])
        char_similarity = char_matches / max_len

        syll1 = self.extract_syllables_advanced(word1)
        syll2 = self.extract_syllables_advanced(word2)

        syll_diff = abs(len(syll1) - len(syll2))
        syll_similarity = 1.0 - \
            (syll_diff / max(len(syll1), len(syll2)) if syll1 or syll2 else 0)

        distance = (length_diff * 0.3 + (1 - char_similarity)
                    * 0.5 + (1 - syll_similarity) * 0.2)

        return distance

    def is_valid_word_structure(self, word: str, max_consonant_cluster: int = 3,
                                max_vowel_cluster: int = 2) -> bool:
        if not word:
            return False

        lower_word = word.lower()

        consonant_count = 0
        vowel_count = 0

        for char in lower_word:
            if not char.isalpha():
                continue

            if char in self.vowels:
                vowel_count += 1
                consonant_count = 0
                if vowel_count > max_vowel_cluster:
                    return False
            else:
                consonant_count += 1
                vowel_count = 0
                if consonant_count > max_consonant_cluster:
                    return False

        return True

    def repair_word_structure(self, word: str, epenthesis_vowel: str = 'e',
                              max_consonant_cluster: int = 3) -> str:
        if not word:
            return word

        is_capitalized = word[0].isupper()
        lower_word = word.lower()
        result = []
        consonant_count = 0

        for char in lower_word:
            if not char.isalpha():
                result.append(char)
                consonant_count = 0
                continue

            if char in self.vowels:
                result.append(char)
                consonant_count = 0
            else:
                consonant_count += 1
                if consonant_count > max_consonant_cluster:
                    result.append(epenthesis_vowel)
                    consonant_count = 1
                result.append(char)

        repaired = ''.join(result)

        if is_capitalized and repaired:
            repaired = repaired[0].upper() + repaired[1:]

        return repaired


class ConsistencyValidator:
    def __init__(self):
        self.seen_translations = {}
        self.inconsistencies = []

    def validate_translation(self, source: str, target: str) -> Tuple[bool, Optional[str]]:
        key = source.lower()

        if key in self.seen_translations:
            previous = self.seen_translations[key]
            if previous != target:
                self.inconsistencies.append({
                    'source': source,
                    'previous': previous,
                    'current': target
                })
                return False, previous
            return True, None

        self.seen_translations[key] = target
        return True, None

    def record_translation(self, source: str, target: str):
        key = source.lower()
        self.seen_translations[key] = target

    def get_inconsistencies(self) -> List[Dict]:
        return self.inconsistencies

    def get_consistency_rate(self) -> float:
        total = len(self.seen_translations) + len(self.inconsistencies)
        if total == 0:
            return 1.0
        return len(self.seen_translations) / total

    def clear_inconsistencies(self):
        self.inconsistencies = []


class WordQualityScorer:
    def __init__(self, morphology_analyzer: MorphologyAnalyzer):
        self.analyzer = morphology_analyzer

    def score_word(self, word: str, source_words: List[str] = None) -> float:
        if not word or len(word) < 2:
            return 0.0

        scores = []

        stacking_score = 0.0 if self.analyzer.detect_stacking(word) else 1.0
        scores.append(('stacking', stacking_score, 0.3))

        structure_score = 1.0 if self.analyzer.is_valid_word_structure(
            word) else 0.5
        scores.append(('structure', structure_score, 0.2))

        length_score = min(1.0, max(0.3, 1.0 - abs(len(word) - 6) / 10))
        scores.append(('length', length_score, 0.1))

        syllables = self.analyzer.extract_syllables_advanced(word)
        syllable_score = min(1.0, len(syllables) / 4) if syllables else 0.5
        scores.append(('syllables', syllable_score, 0.15))

        vowel_count = sum(1 for c in word.lower() if c in self.analyzer.vowels)
        consonant_count = sum(1 for c in word.lower()
                              if c.isalpha() and c not in self.analyzer.vowels)
        vowel_ratio = vowel_count / len(word) if word else 0
        ratio_score = 1.0 - abs(vowel_ratio - 0.4) * 2
        ratio_score = max(0.0, min(1.0, ratio_score))
        scores.append(('vowel_ratio', ratio_score, 0.15))

        if source_words:
            similarity_scores = []
            for source in source_words:
                if source:
                    distance = self.analyzer.calculate_phonetic_distance(
                        word, source)
                    similarity = 1.0 - distance
                    similarity_scores.append(similarity)

            if similarity_scores:
                avg_similarity = sum(similarity_scores) / \
                    len(similarity_scores)
                similarity_score = max(0.3, avg_similarity)
                scores.append(('similarity', similarity_score, 0.1))

        total_score = sum(score * weight for _, score, weight in scores)
        max_weight = sum(weight for _, _, weight in scores)

        return total_score / max_weight if max_weight > 0 else 0.0

    def get_best_candidate(self, candidates: List[str], source_words: List[str] = None) -> str:
        if not candidates:
            return ""

        if len(candidates) == 1:
            return candidates[0]

        scored_candidates = [(word, self.score_word(word, source_words))
                             for word in candidates]

        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        return scored_candidates[0][0]
