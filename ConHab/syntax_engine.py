import hashlib
import json
from typing import List, Dict, Optional, Tuple, Set
from collections import defaultdict
from pathlib import Path
import requests


class SyntacticFunction:
    SUBJECT = 'S'
    VERB = 'V'
    OBJECT = 'O'
    ADJUNCT = 'ADJ'
    COMPLEMENT = 'COMP'
    MODIFIER = 'MOD'
    PUNCT = 'PUNCT'
    UNKNOWN = 'UNK'


class Chunk:
    def __init__(self, words: List[Tuple[str, int]], function: str, head_index: int,
                 chunk_type: str = 'simple', parent_chunk: Optional['Chunk'] = None):
        self.words = words
        self.function = function
        self.head_index = head_index
        self.chunk_type = chunk_type
        self.parent_chunk = parent_chunk
        self.child_chunks: List['Chunk'] = []
        self.dependent_indices = set(word[1] for word in words)

    def get_head_word(self) -> Tuple[str, int]:
        return self.words[self.head_index] if self.words else None

    def get_all_indices(self) -> List[int]:
        return sorted([word[1] for word in self.words])

    def contains_index(self, index: int) -> bool:
        return index in self.dependent_indices

    def __repr__(self):
        words_str = ' '.join([w[0] for w in self.words])
        return f"Chunk({self.chunk_type}:{self.function}='{words_str}', head_idx={self.head_index})"


class WordOrderMapper:
    def __init__(self, source_order: str = 'SVO', profile: Optional[Dict] = None):
        self.source_order = source_order
        self.profile = profile or {}
        self.order_mappings = {
            'SVO': {'S': 0, 'V': 1, 'O': 2},
            'SOV': {'S': 0, 'O': 1, 'V': 2},
            'VSO': {'V': 0, 'S': 1, 'O': 2},
            'VOS': {'V': 0, 'O': 1, 'S': 2},
            'OSV': {'O': 0, 'S': 1, 'V': 2},
            'OVS': {'O': 0, 'V': 1, 'S': 2}
        }
        self.function_words = {'DET', 'PREP', 'ADJ', 'ADV'}
        self.agreement_rules = self.profile.get('agreement_rules', {})
        self.adjunct_position = self.agreement_rules.get(
            'adjunct_position', 'auto')

    def map_to_target_order(self, functions: List[Dict], target_order: str) -> List[int]:
        if target_order not in self.order_mappings:
            target_order = 'SVO'

        clauses_indices = self._partition_into_clauses(functions)

        final_indices = []

        for clause_indices_set in clauses_indices:
            local_indices = sorted(list(clause_indices_set))

            clause_functions_subset = []

            for i, original_idx in enumerate(local_indices):
                f = functions[original_idx].copy()
                f['original_index'] = original_idx
                f['index'] = i
                clause_functions_subset.append(f)

            reordered_local_indices = self._map_single_clause(
                clause_functions_subset, target_order)

            for local_idx in reordered_local_indices:
                final_indices.append(
                    clause_functions_subset[local_idx]['original_index'])

        return final_indices

    def _partition_into_clauses(self, functions: List[Dict]) -> List[Set[int]]:
        partitions = []
        current_indices = set()

        clause_starters = {'e', 'mas', 'porém', 'todavia', 'contudo',
                           'ou', 'então', 'portanto', 'porque', 'pois', 'logo'}
        subject_pronouns = {'eu', 'tu', 'ele', 'ela', 'nós', 'vós',
                            'eles', 'elas', 'você', 'vocês', 'isso', 'isto', 'aquilo'}

        for i, f in enumerate(functions):
            word = f['word'].lower()
            pos = f['pos']

            is_boundary = False

            if pos == 'PUNCT' and word in {',', ';', '.', '!', '?', ':'}:
                if i + 1 < len(functions):
                    next_f = functions[i+1]
                    next_word = next_f['word'].lower()
                    if next_word in clause_starters:
                        is_boundary = True
                    elif next_f['function'] == SyntacticFunction.SUBJECT:
                        is_boundary = True
                    elif next_word in subject_pronouns:
                        is_boundary = True
                    elif next_f['pos'] == 'VERB' and next_f['function'] == SyntacticFunction.VERB:
                        is_boundary = True

            current_indices.add(f['index'])

            if is_boundary:
                partitions.append(current_indices)
                current_indices = set()

        if current_indices:
            partitions.append(current_indices)

        return partitions

    def _map_single_clause(self, functions: List[Dict], target_order: str) -> List[int]:
        chunks = self._build_chunks(functions)
        self._attach_orphaned_punctuation(chunks, functions)

        core_chunks = {'S': [], 'V': [], 'O': []}
        adjunct_chunks = []
        modifier_chunks = []

        for chunk in chunks:
            if chunk.function == SyntacticFunction.SUBJECT:
                core_chunks['S'].append(chunk)
            elif chunk.function == SyntacticFunction.VERB:
                core_chunks['V'].append(chunk)
            elif chunk.function == SyntacticFunction.OBJECT:
                core_chunks['O'].append(chunk)
            elif chunk.function == SyntacticFunction.ADJUNCT:
                adjunct_chunks.append(chunk)
            else:
                modifier_chunks.append(chunk)

        adjunct_position = self._determine_adjunct_position(target_order)

        return self._legacy_reorder(chunks, target_order, adjunct_position, adjunct_chunks, adjuncts_added=False)

    def _legacy_reorder(self, chunks, target_order, adjunct_position, adjunct_chunks, adjuncts_added):
        target_mapping = self.order_mappings[target_order]

        core_chunks = {'S': [], 'V': [], 'O': []}
        local_adjuncts = []
        local_modifiers = []
        final_closers = []

        for c in chunks:
            if c.function == SyntacticFunction.PUNCT and c.words[0][0] in {'.', '!', '?'}:
                final_closers.append(c)
            elif c.function == SyntacticFunction.SUBJECT:
                core_chunks['S'].append(c)
            elif c.function == SyntacticFunction.VERB:
                core_chunks['V'].append(c)
            elif c.function == SyntacticFunction.OBJECT:
                core_chunks['O'].append(c)
            elif c.function == SyntacticFunction.ADJUNCT:
                local_adjuncts.append(c)
            else:
                local_modifiers.append(c)

        ordered_chunks = []

        if adjunct_position == 'before_subject':
            ordered_chunks.extend(local_adjuncts)
            adjuncts_added = True

        ordered_chunks.extend(core_chunks['S'])

        ordered_chunks.extend(local_modifiers)

        ordered_chunks.extend(core_chunks['O'])

        ordered_chunks.extend(core_chunks['V'])

        if not adjuncts_added:
            ordered_chunks.extend(local_adjuncts)

        ordered_chunks.extend(final_closers)

        result_indices = []
        seen = set()
        for chunk in ordered_chunks:
            indices = chunk.get_all_indices()
            for idx in indices:
                if idx not in seen:
                    result_indices.append(idx)
                    seen.add(idx)
        return result_indices

    def _build_chunks(self, functions: List[Dict]) -> List[Chunk]:
        chunks = []
        processed_indices = set()

        i = 0
        while i < len(functions):
            if i in processed_indices:
                i += 1
                continue

            func = functions[i]
            pos = func['pos']
            func_type = func['function']

            if func_type == SyntacticFunction.PUNCT:
                chunk = Chunk([(func['word'], func['index'])],
                              SyntacticFunction.PUNCT, 0, 'punct')
                chunks.append(chunk)
                processed_indices.add(i)
                i += 1
                continue

            if pos == 'NOUN' and func_type in {SyntacticFunction.SUBJECT, SyntacticFunction.OBJECT}:
                np_chunk = self._build_noun_phrase_chunk(
                    functions, i, processed_indices)
                if np_chunk:
                    chunks.append(np_chunk)
                    continue

            elif pos == 'VERB' and func_type == SyntacticFunction.VERB:
                vp_chunk = self._build_verb_phrase_chunk(
                    functions, i, processed_indices)
                if vp_chunk:
                    chunks.append(vp_chunk)
                    continue

            elif pos == 'PREP' and func_type == SyntacticFunction.ADJUNCT:
                pp_chunk = self._build_prepositional_phrase_chunk(
                    functions, i, processed_indices)
                if pp_chunk:
                    chunks.append(pp_chunk)
                    continue

            chunk = Chunk(
                words=[(func['word'], func['index'])],
                function=func_type,
                head_index=0,
                chunk_type='simple'
            )
            chunks.append(chunk)
            processed_indices.add(i)
            i += 1

        return chunks

    def _attach_orphaned_punctuation(self, chunks: List[Chunk], functions: List[Dict]):
        index_to_chunk = {}
        processed_indices = set()

        for chunk in chunks:
            for _, idx in chunk.words:
                index_to_chunk[idx] = chunk
                processed_indices.add(idx)
        glue_punct = {',', ';', ':', ')', ']', '}', '...', '…', '%'}
        closers = {'.', '!', '?'}

        for chunk in chunks:
            if chunk.chunk_type == 'punct' and chunk.words:
                word = chunk.words[0][0]
                idx = chunk.words[0][1]

                if word in glue_punct:
                    chunk_idx = chunks.index(chunk)
                    if chunk_idx > 0:
                        prev_chunk = chunks[chunk_idx-1]
                        prev_chunk.words.append((word, idx))
                        prev_chunk.dependent_indices.add(idx)
                        prev_chunk.words.sort(key=lambda x: x[1])
                        chunk.words = []

        chunks[:] = [c for c in chunks if c.words]

    def _build_noun_phrase_chunk(self, functions: List[Dict], noun_index: int,
                                 processed_indices: Set[int]) -> Optional[Chunk]:
        if noun_index >= len(functions):
            return None
        noun_func = functions[noun_index]
        np_words = [(noun_func['word'], noun_func['index'])]

        i = noun_index - 1
        while i >= 0 and i not in processed_indices:
            func = functions[i]
            if func['pos'] in {'DET', 'ADJ', 'PRON', 'ADV', 'NUM'}:
                np_words.insert(0, (func['word'], func['index']))
                processed_indices.add(i)
                i -= 1
            else:
                break

        i = noun_index + 1
        while i < len(functions) and i not in processed_indices:
            func = functions[i]
            if func['pos'] == 'ADJ':
                np_words.append((func['word'], func['index']))
                processed_indices.add(i)
                i += 1
            else:
                break

        processed_indices.add(noun_index)
        return Chunk(np_words, noun_func['function'], 0, 'NP')

    def _build_verb_phrase_chunk(self, functions: List[Dict], verb_index: int,
                                 processed_indices: Set[int]) -> Optional[Chunk]:
        if verb_index >= len(functions):
            return None
        verb_func = functions[verb_index]
        vp_words = [(verb_func['word'], verb_func['index'])]

        i = verb_index - 1
        while i >= 0 and i not in processed_indices:
            func = functions[i]
            if func['pos'] in {'AUX', 'ADV', 'PRON', 'PART', 'SCONJ'}:
                vp_words.insert(0, (func['word'], func['index']))
                processed_indices.add(i)
                i -= 1
            else:
                break

        processed_indices.add(verb_index)
        return Chunk(vp_words, SyntacticFunction.VERB, 0, 'VP')

    def _build_prepositional_phrase_chunk(self, functions: List[Dict], prep_index: int,
                                          processed_indices: Set[int]) -> Optional[Chunk]:
        if prep_index >= len(functions):
            return None
        prep_func = functions[prep_index]
        pp_words = [(prep_func['word'], prep_index)]

        i = prep_index + 1
        while i < len(functions) and i not in processed_indices and functions[i]['pos'] == 'DET':
            pp_words.append((functions[i]['word'], functions[i]['index']))
            processed_indices.add(i)
            i += 1

        if i < len(functions) and i not in processed_indices:
            if functions[i]['pos'] in {'NOUN', 'PRON', 'PROPN'}:
                np = self._build_noun_phrase_chunk(
                    functions, i, processed_indices)
                if np:
                    for w in np.words:
                        if w[1] not in [x[1] for x in pp_words]:
                            pp_words.append(w)
                            processed_indices.add(w[1])
            elif functions[i]['pos'] == 'ADJ':
                pp_words.append((functions[i]['word'], functions[i]['index']))
                processed_indices.add(i)

        processed_indices.add(prep_index)
        return Chunk(pp_words, SyntacticFunction.ADJUNCT, 0, 'PP')

    def _determine_adjunct_position(self, target_order: str) -> str:
        if self.adjunct_position != 'auto':
            return self.adjunct_position
        if target_order == 'SOV':
            return 'after_object'
        return 'after_verb'


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
        self.ud_model = 'portuguese-bosque-ud-2.17-251125'

        self.word_order_mapper = WordOrderMapper(
            self.source_order, self.profile)
        self.case_morphology = CaseMorphology(self.profile)

        self.syntax_cache_dir = Path("./syntax_cache")
        self.syntax_cache_dir.mkdir(exist_ok=True)
        self.syntax_cache_file = self.syntax_cache_dir / \
            f"{self.profile_id}_syntax.json"

        self.sentence_cache: Dict[str, Dict] = {}
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

    def process_sentence(self, sentence: str) -> Tuple[List[str], List[Dict]]:
        cache_key = self._get_cache_key(sentence)

        if cache_key in self.sentence_cache:
            cached = self.sentence_cache[cache_key]
            reordered_words = []

            for idx in cached['indices']:
                word = cached['words'][idx]
                function = cached['functions'][idx]['function']
                word_with_case = self.case_morphology.apply_case(
                    word, function, self.word_order)
                reordered_words.append(word_with_case)

            final_tokens = self._glue_tokens(
                reordered_words, [cached['functions'][i] for i in cached['indices']])
            return final_tokens, cached['functions']

        url = "https://lindat.mff.cuni.cz/services/udpipe/api/process"
        params = {
            'data': sentence,
            'model': self.ud_model,
            'tokenizer': '',
            'tagger': '',
            'parser': '',
            'output': 'conllu'
        }
        try:
            response = requests.post(url, data=params, timeout=10)
            if not response.ok:
                return sentence.split(), []
            data = response.json()
            conllu = data['result']
        except:
            return sentence.split(), []

        functions = []
        words = []
        i = 0
        for line in conllu.splitlines():
            if not line.strip() or line.startswith('#'):
                continue
            parts = line.split('\t')
            if len(parts) != 10 or '-' in parts[0]:
                continue

            word = parts[1]
            upos = parts[3]
            deprel = parts[7]
            head = int(parts[6]) - 1 if parts[6] != '0' else -1
            function = self._map_deprel_to_function(deprel, upos)

            functions.append({
                'word': word,
                'pos': upos,
                'deprel': deprel,
                'function': function,
                'index': i,
                'dependencies': [head] if head != -1 else [],
            })
            words.append(word)
            i += 1

        new_indices = self.word_order_mapper.map_to_target_order(
            functions, self.word_order)

        raw_reordered_words = []
        ordered_functions = []

        for idx in new_indices:
            word = functions[idx]['word']
            function = functions[idx]['function']
            word_with_case = self.case_morphology.apply_case(
                word, function, self.word_order)
            raw_reordered_words.append(word_with_case)
            ordered_functions.append(functions[idx])

        final_tokens = self._glue_tokens(
            raw_reordered_words, ordered_functions)

        self.sentence_cache[cache_key] = {
            'indices': new_indices,
            'words': words,
            'functions': functions
        }

        return final_tokens, functions

    def _glue_tokens(self, words: List[str], function_objs: List[Dict]) -> List[str]:
        final_tokens = []
        punct_suffix = {'.', ',', '!', '?', ';', ':', '...',
                        '…', ')', ']', '}', '»', '”', '"', "'", '%'}
        punct_prefix = {'(', '[', '{', '«', '“', '¿', '¡'}

        for i, word in enumerate(words):
            if not final_tokens:
                final_tokens.append(word)
                continue

            last_token = final_tokens[-1]

            if word in punct_suffix:
                final_tokens[-1] = last_token + word
            elif any(last_token.startswith(p) for p in punct_prefix) and last_token in punct_prefix:
                final_tokens[-1] = last_token + word
            else:
                final_tokens.append(word)

        return final_tokens

    def process_text(self, text: str) -> Tuple[str, List[Dict]]:
        sentences = self._split_sentences(text)
        all_functions = []
        reordered_sentences = []

        for sentence in sentences:
            if not sentence.strip():
                reordered_sentences.append("")
                continue

            reordered_words, functions = self.process_sentence(sentence)
            reordered_sentences.append(' '.join(reordered_words))
            all_functions.append({
                'original': sentence,
                'reordered': ' '.join(reordered_words),
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
            if i + 1 < len(sentences) and sentences[i+1].strip():
                result.append(sentences[i] + sentences[i+1])
                i += 2
            elif sentences[i].strip():
                result.append(sentences[i])
                i += 1
            else:
                i += 1
        return result

    def _get_cache_key(self, sentence: str) -> str:
        return hashlib.md5(sentence.lower().encode()).hexdigest()

    def _map_deprel_to_function(self, deprel: str, upos: str) -> str:
        deprel = deprel.lower()
        if upos in {'VERB', 'AUX'}:
            return SyntacticFunction.VERB
        if 'nsubj' in deprel:
            return SyntacticFunction.SUBJECT
        if deprel in {'obj', 'iobj', 'ccomp'}:
            return SyntacticFunction.OBJECT
        if deprel in {'obl', 'advcl'}:
            return SyntacticFunction.ADJUNCT
        if upos == 'PUNCT':
            return SyntacticFunction.PUNCT
        return SyntacticFunction.MODIFIER

    def get_statistics(self) -> Dict:
        return {
            'profile_id': self.profile_id,
            'word_order': self.word_order,
            'cached_sentences': len(self.sentence_cache),
        }
