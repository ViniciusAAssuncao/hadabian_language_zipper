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


class PharyngealizationHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get('pharyngealization', {})
        self.enabled = self.config.get('enabled', False)
        self.triggers = set(self.config.get('triggers', []))
        self.affected_vowels = set(self.config.get('affected_vowels', []))
        self.lowering_effect = self.config.get('lowering_effect', False)
        self.mapping = {
            'i': 'e', 'u': 'o', 'a': 'ɑ',
            'I': 'E', 'U': 'O', 'A': 'Ɑ',
            'í': 'é', 'ú': 'ó', 'á': 'ɑ́'
        }

    def apply_effect(self, word: str) -> str:
        if not self.enabled or not self.lowering_effect or not word:
            return word

        word_list = list(word)
        length = len(word_list)

        for i, char in enumerate(word_list):
            if char.lower() in self.affected_vowels:
                triggered = False
                if i > 0:
                    prev_char = word_list[i-1].lower()
                    if prev_char in self.triggers:
                        triggered = True

                if not triggered and i < length - 1:
                    next_char = word_list[i+1].lower()
                    if next_char in self.triggers:
                        triggered = True

                if triggered:
                    word_list[i] = self.mapping.get(char, char)

        return "".join(word_list)


class ConsonantMutationHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get('consonant_mutation', {})
        self.enabled = self.config.get('enabled', False)
        self.rules = self.config.get('rules', [])

    def apply_mutation(self, current_word: str, previous_word: Optional[str], previous_func: Optional[Dict]) -> str:
        if not self.enabled or not current_word:
            return current_word

        if not previous_word and not previous_func:
            return current_word

        processed_word = current_word

        for rule in self.rules:
            triggers = rule.get('triggers', {})
            mutations = rule.get('mutations', {})
            triggered = False

            trigger_words = set(w.lower() for w in triggers.get('words', []))
            if previous_word and previous_word.lower() in trigger_words:
                triggered = True

            if not triggered and previous_func:
                trigger_pos = set(triggers.get('pos', []))
                if previous_func.get('pos') in trigger_pos:
                    triggered = True

            if not triggered and previous_word:
                trigger_ending_chars = triggers.get('ending_chars', [])
                if trigger_ending_chars:
                    for char in trigger_ending_chars:
                        if previous_word.lower().endswith(char):
                            triggered = True
                            break

            if triggered:
                first_char = processed_word[0]
                rest = processed_word[1:]

                is_upper = first_char.isupper()
                lower_char = first_char.lower()

                if lower_char in mutations:
                    new_char = mutations[lower_char]
                    if is_upper:
                        new_char = new_char.upper()
                    processed_word = new_char + rest

        return processed_word


class NegationHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get('negation_system', {})
        self.enabled = self.config.get('enabled', False)
        self.strategies = self.config.get('strategies', [])
        self.negation_triggers = {'não', 'nao', 'nem', 'jamais'}

    def detect_negation(self, func: Dict, all_functions: List[Dict]) -> Tuple[bool, Optional[int], Optional[Dict]]:
        if not self.enabled:
            return False, None, None

        my_index = func['index']
        trigger_idx = None

        for f in all_functions:
            deps = f.get('dependencies', [])
            if my_index in deps:
                lemma = f.get('lemma', '').lower()
                deprel = f.get('deprel', '').lower()
                word = f.get('word', '').lower()

                if lemma in self.negation_triggers or (deprel == 'advmod' and word in self.negation_triggers):
                    trigger_idx = f['index']
                    break

        if trigger_idx is not None:
            pos = func['pos']
            for strategy in self.strategies:
                stype = strategy.get('type')

                if pos in {'VERB', 'AUX'} and stype == 'verbal_negation':
                    return True, trigger_idx, strategy

                if pos in {'NOUN', 'ADJ', 'PRON'} and stype == 'nominal_negation':
                    return True, trigger_idx, strategy

                if stype == 'emphatic_negation':
                    trigger_word = next(
                        (x['word'].lower() for x in all_functions if x['index'] == trigger_idx), '')
                    if trigger_word in {'nunca', 'jamais', 'qatt'}:
                        return True, trigger_idx, strategy

        return False, None, None

    def apply_negation(self, word: str, strategy: Dict) -> str:
        marker = strategy.get('marker', '')
        suffix = strategy.get('suffix', '')

        res = word
        if marker:
            if suffix:
                res = f"{marker}{res}{suffix}"
            else:
                res = f"{marker} {res}"
        elif suffix:
            res = f"{res}{suffix}"

        return res


class TAMHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get('tam_system', {})
        self.enabled = self.config.get('enabled', False)
        self.rules = self.config.get('rules', [])
        self.harmony_handler = VowelHarmonyHandler(profile)
        self.infer_imperative = self.config.get(
            'infer_imperative_from_context', False)
        self.person_config = self.config.get('person_marking', {})
        self.person_prefixes = self.person_config.get('prefixes', {})
        self.person_suffixes = self.person_config.get('suffixes', {})
        self.person_marking_enabled = self.person_config.get('enabled', False)

    def _get_person_key(self, feats: Set[str]) -> str:
        person = next((f.split('=')[1]
                       for f in feats if f.startswith('Person=')), None)
        number = next((f.split('=')[1]
                       for f in feats if f.startswith('Number=')), None)
        gender = next((f.split('=')[1]
                       for f in feats if f.startswith('Gender=')), None)

        if not person or not number:
            return None

        num_map = {'Sing': 'sg', 'Plur': 'pl', 'Dual': 'du'}
        num_code = num_map.get(number, 'sg')

        base_key = f"{person}{num_code}"

        if gender:
            gen_map = {'Masc': 'm', 'Fem': 'f', 'Neut': 'n'}
            gen_code = gen_map.get(gender, '')
            if gen_code:
                complex_key = f"{base_key}_{gen_code}"
                if complex_key in self.person_prefixes or complex_key in self.person_suffixes:
                    return complex_key

        return base_key

    def apply_tam(self, word: str, feats_str: str, func: Optional[Dict] = None, all_functions: Optional[List[Dict]] = None) -> str:
        if not self.enabled or not feats_str or feats_str == '_':
            return word
        feats = set(f.strip() for f in feats_str.split('|') if f.strip())

        if self.infer_imperative and func and all_functions:
            deprel = func.get('deprel', '')
            is_clause_head = deprel in {'root', 'parataxis', 'conj', 'ccomp'}
            has_subject = False
            subject_is_after = False
            my_index = func['index']
            for f in all_functions:
                if my_index in f.get('dependencies', []) and 'nsubj' in f.get('deprel', ''):
                    has_subject = True
                    if f['index'] > my_index:
                        subject_is_after = True
                    break
            if is_clause_head and (not has_subject or subject_is_after):
                feats.add('Mood=Imp')

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

        if self.person_marking_enabled:
            key = self._get_person_key(feats)
            if key:
                prefix = self.person_prefixes.get(key, "")
                suffix = self.person_suffixes.get(key, "")

                if self.harmony_handler.enabled:
                    if suffix:
                        suffix = self.harmony_handler.apply_harmony(
                            result, suffix)

                result = f"{prefix}{result}{suffix}"

        return result


class GenderHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get('gender_system', {})
        self.enabled = self.config.get('enabled', False)
        self.inference_rules = self.config.get('inference', [])
        self.markers = self.config.get('markers', {})
        self.default_gender = self.config.get('default', 'masculine')
        self.harmony_handler = VowelHarmonyHandler(profile)

    def infer_gender(self, word: str) -> str:
        if not self.enabled or not word:
            return self.default_gender

        word_lower = word.lower()
        for rule in self.inference_rules:
            suffix = rule.get('suffix', '')
            if suffix and word_lower.endswith(suffix):
                return rule.get('gender', self.default_gender)

        return self.default_gender

    def apply_agreement(self, word: str, target_gender: str, pos: str) -> str:
        if not self.enabled or not target_gender:
            return word

        marker_config = self.markers.get(target_gender)
        if not marker_config:
            return word

        targets = marker_config.get('targets', [])
        if pos not in targets:
            return word

        marker = marker_config.get('marker', '')
        position = marker_config.get('position', 'suffix')

        if not marker:
            return word

        if self.harmony_handler.enabled and position == 'suffix':
            marker = self.harmony_handler.apply_harmony(word, marker)

        if position == 'suffix':
            return word + marker
        elif position == 'prefix':
            return marker + word

        return word


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


class AgreementChecker:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.agreement_rules = profile.get('agreement_rules', {})
        self.gender_enabled = self.agreement_rules.get(
            'gender_agreement', False)
        self.number_enabled = self.agreement_rules.get(
            'number_agreement', False)
        self.gender_handler = GenderHandler(profile)

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
        head_gender = self.gender_handler.infer_gender(head['word'])
        mod_gender = self.gender_handler.infer_gender(modifier['word'])
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


class CaseMorphology:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.case_system = profile.get('case_system', {})
        self.enabled = self.case_system.get('enabled', False)
        self.preposition_handling = self.case_system.get(
            'preposition_handling', 'coexist')
        self.harmony_config = profile.get('vowel_harmony', {})
        self.harmony_enabled = self.harmony_config.get('enabled', False)
        self.vowel_harmony_handler = VowelHarmonyHandler(profile)
        self.alignment = profile.get('alignment', 'nominative-accusative')
        self.semantic_config = profile.get('semantic_fields', {})
        self.animate_domains = set(self.semantic_config.get(
            'animate_domains', ['família', 'religião', 'human']))
        self.manual_groups = self.semantic_config.get('manual_groups', {})

    def _get_marker_config(self, key: str) -> Tuple[str, str, List[str], bool]:
        case_markers = self.case_system.get('markers', {})
        config = case_markers.get(key, '')

        default_pos = self.case_system.get('marker_position', 'suffix')

        if isinstance(config, dict):
            return (config.get('marker', ''),
                    config.get('type', default_pos),
                    config.get('conditions', []),
                    config.get('shift_to_determiner', False))
        return config, default_pos, [], False

    def _is_animate(self, func_data: Dict) -> bool:
        lemma = func_data.get('lemma', '').lower()
        if lemma in self.manual_groups:
            group = self.manual_groups[lemma]
            if group in self.animate_domains:
                return True

        pos = func_data.get('pos', '')
        if pos in {'PROPN', 'PRON'}:
            return True

        feats = func_data.get('feats', '')
        if 'Animacy=Anim' in feats:
            return True

        return False

    def _is_definite(self, func_data: Dict, all_functions: List[Dict] = None) -> bool:
        feats = func_data.get('feats', '')
        if 'Definite=Def' in feats:
            return True

        pos = func_data.get('pos', '')
        if pos in {'PROPN', 'PRON'}:
            return True

        my_index = func_data.get('index')
        if all_functions:
            for f in all_functions:
                if my_index in f.get('dependencies', []) and f.get('pos') == 'DET':
                    f_feats = f.get('feats', '')
                    if 'Definite=Def' in f_feats or 'PronType=Art' in f_feats:
                        return True

        return False

    def apply_case(self, word: str, function: str, word_order: str, deprel: str = '', clause_transitivity: bool = False, func_data: Dict = None, all_functions: List[Dict] = None) -> str:
        if not self.enabled:
            return word

        if self.preposition_handling == 'none' and function not in {'SUBJECT', 'OBJECT', 'S', 'O'}:
            return word
        target_key = ''
        current_deprel = deprel
        current_function = function
        if func_data and func_data.get('pos') == 'DET' and all_functions:
            head_idx = func_data['dependencies'][0] if func_data['dependencies'] else -1
            if head_idx != -1:
                head_func = next(
                    (f for f in all_functions if f['index'] == head_idx), None)
                if head_func:
                    current_deprel = head_func.get('deprel', '')
                    current_function = head_func.get('function', '')
                    effective_func_data = head_func
                else:
                    effective_func_data = func_data
            else:
                effective_func_data = func_data
        else:
            effective_func_data = func_data

        if current_deprel:
            core_dep = current_deprel.split(':')[0]
            if core_dep == 'obj':
                target_key = 'accusative'
                if self.alignment == 'ergative-absolutive':
                    target_key = 'absolutive'
            elif core_dep == 'iobj':
                target_key = 'dative'
            elif core_dep == 'obl':
                target_key = 'locative'
                if not self.case_system.get('markers', {}).get('locative'):
                    target_key = 'dative'
            elif core_dep == 'nsubj':
                if self.alignment == 'ergative-absolutive':
                    target_key = 'ergative' if clause_transitivity else 'absolutive'
                else:
                    target_key = 'nominative'

        if not target_key:
            if current_function in {'SUBJECT', 'S'}:
                if self.alignment == 'ergative-absolutive':
                    target_key = 'ergative' if clause_transitivity else 'absolutive'
                else:
                    target_key = 'nominative'
            elif current_function in {'OBJECT', 'O'}:
                if self.alignment == 'ergative-absolutive':
                    target_key = 'absolutive'
                else:
                    target_key = 'accusative'
            elif current_function in {'ADJUNCT', 'ADJ'}:
                target_key = 'locative'
                if not self.case_system.get('markers', {}).get('locative'):
                    target_key = 'dative'

        if not target_key:
            return word

        marker_text, marker_type, conditions, shift_to_determiner = self._get_marker_config(
            target_key)

        if not marker_text:
            return word

        conditions_met = True
        if conditions and effective_func_data:
            for cond in conditions:
                if cond == 'animate':
                    if not self._is_animate(effective_func_data):
                        conditions_met = False
                        break
                elif cond == 'definite':
                    if not self._is_definite(effective_func_data, all_functions):
                        conditions_met = False
                        break

        if not conditions_met:
            return word

        is_det = func_data.get('pos') == 'DET' if func_data else False
        is_noun = func_data.get('pos') in {
            'NOUN', 'PROPN', 'PRON'} if func_data else False

        if shift_to_determiner:
            if is_noun and all_functions:
                has_det = False
                my_index = func_data.get('index')
                for f in all_functions:
                    if my_index in f.get('dependencies', []) and f.get('pos') == 'DET':
                        has_det = True
                        break
                if has_det:
                    return word

            if is_det:
                pass

            if is_noun and not has_det:
                pass
            elif is_det:
                pass
            else:
                return word

        if isinstance(marker_text, str) and marker_text.startswith('-'):
            marker_text = marker_text[1:]

        if self.harmony_enabled:
            marker_text = self.vowel_harmony_handler.apply_harmony(
                word, marker_text)

        if marker_type == 'suffix':
            return word + marker_text
        elif marker_type == 'prefix':
            is_capitalized = word and word[0].isupper()
            result = marker_text + word.lower()
            if is_capitalized:
                result = result[0].upper() + result[1:]
            return result
        elif marker_type == 'particle_before':
            return f"{marker_text} {word}"
        elif marker_type == 'particle_after':
            return f"{word} {marker_text}"

        return word + marker_text
