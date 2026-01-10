import hashlib
import json
from typing import List, Dict, Optional, Tuple, Set
from collections import defaultdict
from pathlib import Path


class POSTagger:
    def __init__(self, profile_id: str):
        self.profile_id = profile_id
        self.pos_cache: Dict[str, str] = {}
        self.pattern_rules: List[Dict] = []
        self.function_words = self._initialize_function_words()

    def _initialize_function_words(self) -> Dict[str, Set[str]]:
        return {
            'DET': {'o', 'a', 'os', 'as', 'um', 'uma', 'uns', 'umas', 'este', 'esse', 'aquele', 'esta', 'essa', 'aquela'},
            'PREP': {'de', 'em', 'para', 'por', 'com', 'sem', 'sobre', 'entre', 'até', 'desde', 'durante'},
            'CONJ': {'e', 'ou', 'mas', 'porém', 'que', 'se', 'porque', 'quando', 'embora'},
            'PRON': {'eu', 'tu', 'ele', 'ela', 'nós', 'vós', 'eles', 'elas', 'me', 'te', 'se', 'lhe', 'nos', 'vos', 'meu', 'teu', 'seu'},
            'AUX': {'ser', 'estar', 'ter', 'haver', 'ir', 'vir', 'poder', 'dever', 'querer', 'é', 'são', 'foi', 'está', 'tem', 'tinha'}
        }

    def tag_word(self, word: str, position: int, context: List[str]) -> str:
        clean_word = word.lower().strip('.,!?;:')

        if clean_word in self.pos_cache:
            return self.pos_cache[clean_word]

        for pos_type, words in self.function_words.items():
            if clean_word in words:
                self.pos_cache[clean_word] = pos_type
                return pos_type

        if position == 0 or (position > 0 and context[position-1].lower() in {'.', '!', '?'}):
            if clean_word not in self.function_words.get('PREP', set()):
                tag = 'NOUN'
                self.pos_cache[clean_word] = tag
                return tag

        if clean_word.endswith(('ar', 'er', 'ir', 'ou', 'ava', 'ia')):
            tag = 'VERB'
            self.pos_cache[clean_word] = tag
            return tag

        if clean_word.endswith(('mente', 'ção', 'dade', 'ismo', 'ista')):
            tag = 'NOUN'
            self.pos_cache[clean_word] = tag
            return tag

        if position > 0:
            prev = context[position-1].lower()
            if prev in self.function_words.get('DET', set()):
                tag = 'NOUN'
                self.pos_cache[clean_word] = tag
                return tag

        tag = 'NOUN'
        self.pos_cache[clean_word] = tag
        return tag

    def tag_sentence(self, words: List[str]) -> List[Tuple[str, str]]:
        tagged = []
        for i, word in enumerate(words):
            pos = self.tag_word(word, i, words)
            tagged.append((word, pos))
        return tagged


class SyntacticFunction:
    SUBJECT = 'S'
    VERB = 'V'
    OBJECT = 'O'
    ADJUNCT = 'ADJ'
    COMPLEMENT = 'COMP'
    MODIFIER = 'MOD'
    UNKNOWN = 'UNK'


class FunctionIdentifier:
    def __init__(self, pos_tagger: POSTagger):
        self.tagger = pos_tagger

    def identify_functions(self, tagged_words: List[Tuple[str, str]]) -> List[Dict]:
        functions = []

        i = 0
        while i < len(tagged_words):
            word, pos = tagged_words[i]

            func_entry = {
                'word': word,
                'pos': pos,
                'function': SyntacticFunction.UNKNOWN,
                'index': i,
                'dependencies': []
            }

            if pos == 'VERB':
                func_entry['function'] = SyntacticFunction.VERB

            elif pos == 'NOUN':
                if i == 0 or self._is_after_punctuation(tagged_words, i):
                    func_entry['function'] = SyntacticFunction.SUBJECT
                else:
                    verb_before = self._find_verb_before(tagged_words, i)
                    if verb_before is not None:
                        func_entry['function'] = SyntacticFunction.OBJECT
                        func_entry['dependencies'].append(verb_before)
                    else:
                        func_entry['function'] = SyntacticFunction.SUBJECT

            elif pos == 'DET':
                func_entry['function'] = SyntacticFunction.MODIFIER
                if i + 1 < len(tagged_words):
                    func_entry['dependencies'].append(i + 1)

            elif pos == 'PREP':
                func_entry['function'] = SyntacticFunction.ADJUNCT
                if i + 1 < len(tagged_words):
                    func_entry['dependencies'].append(i + 1)

            else:
                func_entry['function'] = SyntacticFunction.MODIFIER

            functions.append(func_entry)
            i += 1

        return functions

    def _is_after_punctuation(self, tagged_words: List[Tuple[str, str]], index: int) -> bool:
        if index == 0:
            return True
        prev_word = tagged_words[index - 1][0]
        return prev_word.strip() in {'.', '!', '?', ';', ':'}

    def _find_verb_before(self, tagged_words: List[Tuple[str, str]], index: int) -> Optional[int]:
        for i in range(index - 1, -1, -1):
            if tagged_words[i][1] == 'VERB':
                return i
            if tagged_words[i][0].strip() in {'.', '!', '?'}:
                return None
        return None


class WordOrderMapper:
    def __init__(self, source_order: str = 'SVO'):
        self.source_order = source_order
        self.order_mappings = {
            'SVO': {'S': 0, 'V': 1, 'O': 2},
            'SOV': {'S': 0, 'O': 1, 'V': 2},
            'VSO': {'V': 0, 'S': 1, 'O': 2},
            'VOS': {'V': 0, 'O': 1, 'S': 2},
            'OSV': {'O': 0, 'S': 1, 'V': 2},
            'OVS': {'O': 0, 'V': 1, 'S': 2}
        }

    def map_to_target_order(self, functions: List[Dict], target_order: str) -> List[int]:
        if target_order not in self.order_mappings:
            target_order = 'SVO'

        core_elements = {'S': [], 'V': [], 'O': []}
        other_elements = []

        for func in functions:
            if func['function'] == SyntacticFunction.SUBJECT:
                core_elements['S'].append(func)
            elif func['function'] == SyntacticFunction.VERB:
                core_elements['V'].append(func)
            elif func['function'] == SyntacticFunction.OBJECT:
                core_elements['O'].append(func)
            else:
                other_elements.append(func)

        target_mapping = self.order_mappings[target_order]

        ordered_groups = [[], [], []]
        for key, position in target_mapping.items():
            ordered_groups[position] = core_elements[key]

        result_indices = []

        for group in ordered_groups:
            for element in group:
                modifiers = [f for f in other_elements if element['index'] in f.get(
                    'dependencies', [])]

                for mod in modifiers:
                    if mod['pos'] in {'DET', 'PREP'} and mod['index'] < element['index']:
                        result_indices.append(mod['index'])

                result_indices.append(element['index'])

                for mod in modifiers:
                    if mod['index'] > element['index']:
                        result_indices.append(mod['index'])

        remaining = [f['index']
                     for f in other_elements if f['index'] not in result_indices]
        result_indices.extend(sorted(remaining))

        return result_indices


class CaseMorphology:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.case_system = profile.get('case_system', {})
        self.enabled = self.case_system.get('enabled', False)

    def apply_case(self, word: str, function: str, word_order: str) -> str:
        if not self.enabled:
            return word

        case_markers = self.case_system.get('markers', {})

        if function == SyntacticFunction.SUBJECT:
            marker = case_markers.get('nominative', '')
        elif function == SyntacticFunction.OBJECT:
            marker = case_markers.get('accusative', '')
        elif function == SyntacticFunction.ADJUNCT:
            marker = case_markers.get('dative', '')
        else:
            marker = ''

        if not marker:
            return word

        position = self.case_system.get('marker_position', 'suffix')

        if position == 'suffix':
            return word + marker
        elif position == 'prefix':
            is_capitalized = word and word[0].isupper()
            result = marker + word.lower()
            if is_capitalized:
                result = result[0].upper() + result[1:]
            return result

        return word


class SyntaxEngine:
    def __init__(self, profile_path: str):
        with open(profile_path, 'r', encoding='utf-8') as f:
            self.profile = json.load(f)

        self.profile_id = self.profile.get('id', 'unknown')
        self.word_order = self.profile.get('word_order', 'SVO')
        self.source_order = self.profile.get('source_language_order', 'SVO')

        self.pos_tagger = POSTagger(self.profile_id)
        self.function_identifier = FunctionIdentifier(self.pos_tagger)
        self.word_order_mapper = WordOrderMapper(self.source_order)
        self.case_morphology = CaseMorphology(self.profile)

        self.syntax_cache_dir = Path("./syntax_cache")
        self.syntax_cache_dir.mkdir(exist_ok=True)
        self.syntax_cache_file = self.syntax_cache_dir / \
            f"{self.profile_id}_syntax.json"

        self.sentence_cache: Dict[str, List[int]] = {}
        self.load_cache()

    def load_cache(self):
        if self.syntax_cache_file.exists():
            try:
                with open(self.syntax_cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.sentence_cache = data.get('sentence_cache', {})
            except:
                pass

    def save_cache(self):
        data = {
            'sentence_cache': self.sentence_cache,
            'profile_id': self.profile_id,
            'word_order': self.word_order
        }
        with open(self.syntax_cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def process_sentence(self, words: List[str]) -> Tuple[List[str], List[Dict]]:
        cache_key = self._get_cache_key(words)

        if cache_key in self.sentence_cache:
            indices = self.sentence_cache[cache_key]
            reordered = [words[i] for i in indices if i < len(words)]
            return reordered, []

        tagged = self.pos_tagger.tag_sentence(words)

        functions = self.function_identifier.identify_functions(tagged)

        new_indices = self.word_order_mapper.map_to_target_order(
            functions, self.word_order)

        self.sentence_cache[cache_key] = new_indices

        reordered_words = []
        for idx in new_indices:
            if idx < len(words):
                word = words[idx]
                function = functions[idx]['function'] if idx < len(
                    functions) else SyntacticFunction.UNKNOWN
                word_with_case = self.case_morphology.apply_case(
                    word, function, self.word_order)
                reordered_words.append(word_with_case)

        return reordered_words, functions

    def process_text(self, text: str) -> Tuple[str, List[Dict]]:
        sentences = self._split_sentences(text)

        all_functions = []
        reordered_sentences = []

        for sentence in sentences:
            words = sentence.split()
            if not words:
                reordered_sentences.append("")
                continue

            reordered, functions = self.process_sentence(words)
            reordered_sentences.append(' '.join(reordered))
            all_functions.append({
                'original': sentence,
                'reordered': ' '.join(reordered),
                'functions': functions
            })

        self.save_cache()

        return ' '.join(reordered_sentences), all_functions

    def _split_sentences(self, text: str) -> List[str]:
        import re
        sentences = re.split(r'([.!?]+\s*)', text)

        result = []
        i = 0
        while i < len(sentences):
            if i + 1 < len(sentences) and sentences[i + 1].strip():
                result.append(sentences[i] + sentences[i + 1])
                i += 2
            elif sentences[i].strip():
                result.append(sentences[i])
                i += 1
            else:
                i += 1

        return result

    def _get_cache_key(self, words: List[str]) -> str:
        joined = '|'.join(words).lower()
        return hashlib.md5(joined.encode()).hexdigest()

    def get_statistics(self) -> Dict:
        return {
            'profile_id': self.profile_id,
            'word_order': self.word_order,
            'source_order': self.source_order,
            'cached_sentences': len(self.sentence_cache),
            'case_system_enabled': self.case_morphology.enabled
        }
