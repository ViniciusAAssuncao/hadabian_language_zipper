from typing import List, Dict, Optional, Tuple, Set
from collections import defaultdict
import re


class VowelHarmonyHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get('vowel_harmony', {})
        self.enabled = self.config.get('enabled', False)
        self.groups = self.config.get('groups', {})
        self.rules = self.config.get('rules', [])

        self.vowels = "aeiouyáàâãéêíóôõúüö"
        if self.profile.get('phonotactics'):
            self.vowels = self.profile['phonotactics'].get(
                'vowels', self.vowels)

    def _get_vowel_group(self, vowel: str) -> str:
        if not self.enabled:
            return None
        for group_name, vowels in self.groups.items():
            if vowel in vowels:
                return group_name
        return None

    def _find_last_vowel(self, word: str) -> str:
        for char in reversed(word.lower()):
            if char in self.vowels:
                return char
        return None

    def apply_harmony(self, word: str, suffix: str) -> str:
        if not self.enabled or not suffix:
            return suffix

        last_vowel = self._find_last_vowel(word)
        if not last_vowel:
            return suffix

        group = self._get_vowel_group(last_vowel)
        if not group:
            return suffix

        harmonized_suffix = ""

        for char in suffix:
            replaced = False
            for rule in self.rules:
                if rule['input'] == char:
                    mapping = rule.get('map', {})
                    if group in mapping:
                        harmonized_suffix += mapping[group]
                        replaced = True
                        break
            if not replaced:
                harmonized_suffix += char

        return harmonized_suffix


class TAMHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get('tam_system', {})
        self.enabled = self.config.get('enabled', False)
        self.rules = self.config.get('rules', [])
        self.harmony_handler = VowelHarmonyHandler(profile)

    def apply_tam(self, word: str, feats_str: str) -> str:
        if not self.enabled or not feats_str or feats_str == '_':
            return word

        feats = set(f.strip() for f in feats_str.split('|') if f.strip())
        result = word

        for rule in self.rules:
            rule_feats = set(rule.get('features', []))
            if rule_feats.issubset(feats):
                marker = rule.get('marker', '')
                m_type = rule.get('type', 'suffix')

                if self.harmony_handler.enabled and m_type == 'suffix':
                    marker = self.harmony_handler.apply_harmony(result, marker)

                if m_type == 'suffix':
                    result = result + marker
                elif m_type == 'prefix':
                    result = marker + result
                elif m_type == 'particle_before':
                    result = marker + ' ' + result
                elif m_type == 'particle_after':
                    result = result + ' ' + marker

        return result


class DependencyParser:
    def __init__(self):
        self.dependency_patterns = self._initialize_patterns()

    def _initialize_patterns(self) -> List[Dict]:
        return [
            {'pattern': ['PREP', 'DET', 'NOUN'], 'head': 2,
                'relation': 'prepositional_phrase'},
            {'pattern': ['DET', 'NOUN'], 'head': 1, 'relation': 'determiner'},
            {'pattern': ['VERB', 'PREP', 'NOUN'],
                'head': 0, 'relation': 'verbal_complement'},
            {'pattern': ['NOUN', 'PREP', 'NOUN'], 'head': 0,
                'relation': 'nominal_complement'},
            {'pattern': ['ADJ', 'NOUN'], 'head': 1,
                'relation': 'adjective_modifier'},
            {'pattern': ['NOUN', 'ADJ'], 'head': 0,
                'relation': 'adjective_modifier'}
        ]

    def parse(self, tagged_words: List[Tuple[str, str]]) -> List[Dict]:
        dependencies = []

        for i in range(len(tagged_words)):
            for pattern_info in self.dependency_patterns:
                pattern = pattern_info['pattern']
                if self._matches_pattern(tagged_words, i, pattern):
                    dep = {
                        'start': i,
                        'end': i + len(pattern),
                        'head': i + pattern_info['head'],
                        'relation': pattern_info['relation'],
                        'constituents': [tagged_words[j] for j in range(i, min(i + len(pattern), len(tagged_words)))]
                    }
                    dependencies.append(dep)

        return dependencies

    def _matches_pattern(self, tagged_words: List[Tuple[str, str]], start: int, pattern: List[str]) -> bool:
        if start + len(pattern) > len(tagged_words):
            return False

        for i, pos in enumerate(pattern):
            if tagged_words[start + i][1] != pos:
                return False

        return True


class ConstituentAnalyzer:
    def __init__(self):
        self.constituent_types = {
            'NP': ['DET', 'NOUN'],
            'VP': ['VERB'],
            'PP': ['PREP', 'DET', 'NOUN'],
            'ADVP': ['ADV']
        }

    def identify_constituents(self, tagged_words: List[Tuple[str, str]]) -> List[Dict]:
        constituents = []
        i = 0

        while i < len(tagged_words):
            found = False

            for constituent_type, patterns in self.constituent_types.items():
                for pattern_length in range(len(patterns), 0, -1):
                    if i + pattern_length <= len(tagged_words):
                        candidate = [tagged_words[j][1]
                                     for j in range(i, i + pattern_length)]

                        if self._matches_constituent(candidate, patterns[:pattern_length]):
                            constituents.append({
                                'type': constituent_type,
                                'start': i,
                                'end': i + pattern_length,
                                'words': [tagged_words[j][0] for j in range(i, i + pattern_length)],
                                'head': self._find_head(tagged_words[i:i + pattern_length], constituent_type)
                            })
                            i += pattern_length
                            found = True
                            break

                if found:
                    break

            if not found:
                i += 1

        return constituents

    def _matches_constituent(self, candidate: List[str], pattern: List[str]) -> bool:
        if len(candidate) != len(pattern):
            return False

        for i, pos in enumerate(pattern):
            if candidate[i] != pos:
                return False

        return True

    def _find_head(self, constituent: List[Tuple[str, str]], const_type: str) -> int:
        if const_type == 'NP':
            for i, (word, pos) in enumerate(constituent):
                if pos == 'NOUN':
                    return i
        elif const_type == 'VP':
            for i, (word, pos) in enumerate(constituent):
                if pos == 'VERB':
                    return i
        elif const_type == 'PP':
            for i, (word, pos) in enumerate(constituent):
                if pos == 'PREP':
                    return i

        return 0


class ClauseSegmenter:
    def __init__(self):
        self.clause_boundaries = {'.', '!', '?', ';', ',',
                                  'e', 'mas', 'ou', 'que', 'porque', 'quando'}

    def segment(self, words: List[str]) -> List[List[str]]:
        clauses = []
        current_clause = []

        for word in words:
            clean_word = word.lower().strip('.,!?;:')

            if clean_word in self.clause_boundaries or word.strip() in {',', ';'}:
                if current_clause:
                    clauses.append(current_clause)
                    current_clause = []

                if clean_word not in {',', ';', '.', '!', '?'}:
                    current_clause.append(word)
            else:
                current_clause.append(word)

        if current_clause:
            clauses.append(current_clause)

        return clauses


class AgreementChecker:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.agreement_rules = profile.get('agreement_rules', {})
        self.gender_enabled = self.agreement_rules.get(
            'gender_agreement', False)
        self.number_enabled = self.agreement_rules.get(
            'number_agreement', False)

    def check_agreement(self, functions: List[Dict]) -> List[Dict]:
        violations = []

        for i, func in enumerate(functions):
            if func['function'] == 'NOUN' and func['pos'] == 'NOUN':
                modifiers = [f for f in functions if i in f.get(
                    'dependencies', [])]

                for mod in modifiers:
                    if self.gender_enabled:
                        violation = self._check_gender_agreement(func, mod)
                        if violation:
                            violations.append(violation)

                    if self.number_enabled:
                        violation = self._check_number_agreement(func, mod)
                        if violation:
                            violations.append(violation)

        return violations

    def _check_gender_agreement(self, head: Dict, modifier: Dict) -> Optional[Dict]:
        head_gender = self._infer_gender(head['word'])
        mod_gender = self._infer_gender(modifier['word'])

        if head_gender != mod_gender:
            return {
                'type': 'gender_mismatch',
                'head': head['word'],
                'modifier': modifier['word'],
                'head_gender': head_gender,
                'modifier_gender': mod_gender
            }

        return None

    def _check_number_agreement(self, head: Dict, modifier: Dict) -> Optional[Dict]:
        head_number = self._infer_number(head['word'])
        mod_number = self._infer_number(modifier['word'])

        if head_number != mod_number:
            return {
                'type': 'number_mismatch',
                'head': head['word'],
                'modifier': modifier['word'],
                'head_number': head_number,
                'modifier_number': mod_number
            }

        return None

    def _infer_gender(self, word: str) -> str:
        word_lower = word.lower()
        if word_lower.endswith('a'):
            return 'feminine'
        elif word_lower.endswith('o'):
            return 'masculine'
        return 'neutral'

    def _infer_number(self, word: str) -> str:
        word_lower = word.lower()
        if word_lower.endswith('s'):
            return 'plural'
        return 'singular'


class SyntacticComplexityAnalyzer:
    def __init__(self):
        self.complexity_metrics = {}

    def analyze(self, functions: List[Dict], dependencies: List[Dict]) -> Dict:
        metrics = {}

        metrics['depth'] = self._calculate_depth(dependencies)
        metrics['branching_factor'] = self._calculate_branching(functions)
        metrics['clause_count'] = self._estimate_clauses(functions)
        metrics['embedding_level'] = self._calculate_embedding(dependencies)

        return metrics

    def _calculate_depth(self, dependencies: List[Dict]) -> int:
        if not dependencies:
            return 0

        max_depth = 0
        for dep in dependencies:
            depth = 1
            current = dep

            for other in dependencies:
                if other['start'] >= current['start'] and other['end'] <= current['end']:
                    if other != current:
                        depth += 1

            max_depth = max(max_depth, depth)

        return max_depth

    def _calculate_branching(self, functions: List[Dict]) -> float:
        if not functions:
            return 0.0

        total_deps = sum(len(f.get('dependencies', [])) for f in functions)
        return total_deps / len(functions)

    def _estimate_clauses(self, functions: List[Dict]) -> int:
        verb_count = sum(
            1 for f in functions if f['function'] == 'VERB' or f['pos'] == 'VERB')
        return max(1, verb_count)

    def _calculate_embedding(self, dependencies: List[Dict]) -> int:
        if not dependencies:
            return 0

        max_embedding = 0

        for i, dep1 in enumerate(dependencies):
            embedding = 0
            for dep2 in dependencies:
                if dep2['start'] > dep1['start'] and dep2['end'] < dep1['end']:
                    embedding += 1
            max_embedding = max(max_embedding, embedding)

        return max_embedding


class TopicalizationHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.topicalization_rules = profile.get('topicalization', {})
        self.enabled = self.topicalization_rules.get('enabled', False)
        self.marker = self.topicalization_rules.get('topic_marker', '')

    def apply_topicalization(self, words: List[str], functions: List[Dict], topic_index: Optional[int] = None) -> List[str]:
        if not self.enabled:
            return words

        if topic_index is None:
            topic_index = self._identify_topic(functions)

        if topic_index is None or topic_index >= len(words):
            return words

        result = words.copy()

        if self.marker:
            result[topic_index] = self.marker + ' ' + result[topic_index]

        topic_position = self.topicalization_rules.get('position', 'initial')

        if topic_position == 'initial' and topic_index != 0:
            topic_word = result.pop(topic_index)
            result.insert(0, topic_word)
        elif topic_position == 'final' and topic_index != len(result) - 1:
            topic_word = result.pop(topic_index)
            result.append(topic_word)

        return result

    def _identify_topic(self, functions: List[Dict]) -> Optional[int]:
        for func in functions:
            if func['function'] == 'SUBJECT' or func['function'] == 'S':
                return func['index']

        return None


class FocusStructureHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.focus_rules = profile.get('focus_structure', {})
        self.enabled = self.focus_rules.get('enabled', False)

    def apply_focus(self, words: List[str], functions: List[Dict], focus_type: str = 'neutral') -> List[str]:
        if not self.enabled:
            return words

        if focus_type == 'object_focus':
            return self._apply_object_focus(words, functions)
        elif focus_type == 'verb_focus':
            return self._apply_verb_focus(words, functions)

        return words

    def _apply_object_focus(self, words: List[str], functions: List[Dict]) -> List[str]:
        object_index = None
        for func in functions:
            if func['function'] == 'OBJECT' or func['function'] == 'O':
                object_index = func['index']
                break

        if object_index is None or object_index >= len(words):
            return words

        result = words.copy()
        focus_marker = self.focus_rules.get('object_focus_marker', '')

        if focus_marker:
            result[object_index] = focus_marker + ' ' + result[object_index]

        return result

    def _apply_verb_focus(self, words: List[str], functions: List[Dict]) -> List[str]:
        verb_index = None
        for func in functions:
            if func['function'] == 'VERB' or func['function'] == 'V':
                verb_index = func['index']
                break

        if verb_index is None or verb_index >= len(words):
            return words

        result = words.copy()
        focus_marker = self.focus_rules.get('verb_focus_marker', '')

        if focus_marker:
            result[verb_index] = focus_marker + ' ' + result[verb_index]

        return result
