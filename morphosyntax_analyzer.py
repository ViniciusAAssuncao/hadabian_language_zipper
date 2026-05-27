from typing import List, Dict, Optional, Tuple, Set
from constants import NEGATION_TRIGGERS
from collections import defaultdict
import re

from handlers.phonology import VowelHarmonyHandler


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
        self.coordinating_conjunctions = {
            'e', 'mas', 'ou', 'porém', 'todavia', 'contudo', 'nem', 'logo', 'portanto'}
        self.subordinating_conjunctions = {
            'que', 'porque', 'quando', 'se', 'embora', 'enquanto', 'como', 'pois', 'caso', 'para'}
        self.punctuation = {'.', '!', '?', ';', ','}
        self.clause_boundaries = self.coordinating_conjunctions.union(
            self.subordinating_conjunctions).union(self.punctuation)

    def segment(self, words: List[str]) -> List[List[str]]:
        clauses = []
        current_clause = []
        for word in words:
            clean_word = word.lower().strip('.,!?;:')
            if clean_word in self.clause_boundaries or word.strip() in self.punctuation:
                if current_clause:
                    clauses.append(current_clause)
                    current_clause = []
                if clean_word not in self.punctuation:
                    current_clause.append(word)
            else:
                current_clause.append(word)
        if current_clause:
            clauses.append(current_clause)
        return clauses

    def identify_clause_type(self, clause_tokens: List[str]) -> str:
        if not clause_tokens:
            return 'unknown'
        first_token = clause_tokens[0].lower().strip('.,!?;:')
        if first_token in self.subordinating_conjunctions:
            return 'subordinate'
        return 'main'


class TransitivityAnalyzer:
    def __init__(self):
        pass

    def analyze(self, functions: List[Dict]) -> Dict[int, bool]:
        transitivity_map = {}
        verb_indices = [f['index']
                        for f in functions if f['pos'] in {'VERB', 'AUX'}]

        for v_idx in verb_indices:
            is_transitive = False
            for f in functions:
                if 'obj' in f.get('deprel', '') and v_idx in f.get('dependencies', []):
                    is_transitive = True
                    break
            transitivity_map[v_idx] = is_transitive

        final_map = {}
        for f in functions:
            head_idx = f['dependencies'][0] if f['dependencies'] else -1
            if head_idx in transitivity_map:
                final_map[f['index']] = transitivity_map[head_idx]
            else:
                final_map[f['index']] = False

        return final_map


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
            topic_index = self.identify_topic(functions)
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

    def identify_topic(self, functions: List[Dict]) -> Optional[int]:
        for func in functions:
            if func['function'] == 'SUBJECT' or func['function'] == 'S':
                return func['index']

        for func in functions:
            if func['function'] == 'OBJECT' or func['function'] == 'O':
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


class CompoundingHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get('compounding', {})
        self.enabled = self.config.get('enabled', False)
        self.head_position = self.config.get('head_position', 'final')
        self.linking_elements = self.config.get('linking_elements', {})
        vocab_raw = profile.get('vocabulary', {})
        self.vocabulary = {k.lower(): v for k, v in vocab_raw.items()}
        self.vocabulary.update(vocab_raw)

    def _smart_lookup(self, lemma: str, engine_ref) -> Optional[str]:
        if not lemma:
            return None

        lemma = lemma.lower().strip()

        if lemma in self.vocabulary:
            return self.vocabulary[lemma]

        lemma_lower = lemma.lower()
        if lemma_lower in self.vocabulary:
            return self.vocabulary[lemma_lower]

        return engine_ref._get_word_form(lemma, tags=['compound_part'])

    def construct_compound(self, parts: List[str], engine_ref) -> str:
        if not parts:
            return ""

        if len(parts) == 1:
            return parts[0]

        head_word = parts[-1] if self.head_position == 'final' else parts[0]
        modifier_words = parts[:-
                               1] if self.head_position == 'final' else parts[1:]

        current_base = modifier_words[0] if self.head_position == 'final' else head_word
        remaining = modifier_words[1:] + \
            [head_word] if self.head_position == 'final' else modifier_words

        if self.head_position == 'initial':
            current_base = head_word
            remaining = modifier_words

        full_compound = current_base

        if self.head_position == 'final':
            for i, next_part in enumerate(remaining):
                modifier = full_compound
                link = self._get_linking_element(modifier, next_part)
                full_compound = f"{modifier}{link}{next_part}"
        else:
            for i, next_part in enumerate(remaining):
                head = full_compound
                modifier = next_part
                link = self._get_linking_element(head, modifier)
                full_compound = f"{head}{link}{modifier}"

        if full_compound and parts[0][0].isupper():
            full_compound = full_compound.capitalize()

        return full_compound

    def _get_linking_element(self, element_a: str, element_b: str) -> str:
        link = ""
        element_a_lower = element_a.lower()

        for link_char, rules in self.linking_elements.items():
            suffixes = rules.get('after', [])
            exact_matches = rules.get('words', [])

            if element_a_lower in exact_matches:
                link = link_char
                break

            for suff in suffixes:
                if element_a_lower.endswith(suff):
                    link = link_char
                    break
            if link:
                break

        return link

    def apply_compounding(self, functions: List[Dict], engine_ref) -> Tuple[Dict[int, str], Set[int]]:
        if not self.enabled:
            return {}, set()

        compound_map = {}
        absorbed_indices = set()

        noun_indices = [f['index']
                        for f in functions if f['pos'] in {'NOUN', 'PROPN'}]

        for head_idx in noun_indices:
            if head_idx in absorbed_indices:
                continue

            modifier_idx = -1
            for f in functions:
                if f['index'] not in absorbed_indices and \
                   head_idx in f.get('dependencies', []) and \
                   ('nmod' in f.get('deprel', '') or f.get('deprel') == 'compound'):
                    if f['pos'] in {'NOUN', 'PROPN'}:
                        modifier_idx = f['index']
                        break

            if modifier_idx != -1:
                head_func = next(
                    f for f in functions if f['index'] == head_idx)
                mod_func = next(
                    f for f in functions if f['index'] == modifier_idx)

                head_lemma = head_func.get('lemma', head_func['word'])
                mod_lemma = mod_func.get('lemma', mod_func['word'])

                head_word = self._smart_lookup(head_lemma, engine_ref)
                mod_word = self._smart_lookup(mod_lemma, engine_ref)

                if self.head_position == 'final':
                    compound_word = self.construct_compound(
                        [mod_word, head_word], engine_ref)
                else:
                    compound_word = self.construct_compound(
                        [head_word, mod_word], engine_ref)

                compound_map[head_idx] = compound_word
                absorbed_indices.add(modifier_idx)

                for f in functions:
                    if modifier_idx in f.get('dependencies', []):
                        if f['pos'] in {'ADP', 'DET'} or f['deprel'] == 'case' or f['deprel'] == 'det':
                            absorbed_indices.add(f['index'])

        return compound_map, absorbed_indices
