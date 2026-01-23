import hashlib
import json
from typing import List, Dict, Optional, Tuple, Set
from collections import defaultdict
from pathlib import Path
import requests
import re
from morphosyntax_analyzer import CaseMorphology


class SyntacticFunction:
    SUBJECT = 'S'
    VERB = 'V'
    OBJECT = 'O'
    ADJUNCT = 'ADJ'
    COMPLEMENT = 'COMP'
    MODIFIER = 'MOD'
    PUNCT = 'PUNCT'
    UNKNOWN = 'UNK'
    QUANTIFIER = 'QUANT'
    VERB_PARTICLE = 'VPART'
    INTENSIFIER = 'INTENS'


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
        return [word[1] for word in self.words]

    def contains_index(self, index: int) -> bool:
        return index in self.dependent_indices

    def __repr__(self):
        words_str = ' '.join([w[0] for w in self.words])
        return f"Chunk({self.chunk_type}:{self.function}='{words_str}', head_idx={self.head_index})"


class WordOrderMapper:
    def __init__(self, source_order: str = 'SVO', profile: Optional[Dict] = None):
        self.source_order = source_order
        self.profile = profile or {}
        self.target_order = self.profile.get('word_order', 'SVO')
        self.subordinate_order = self.profile.get(
            'subordinate_word_order', self.target_order)
        self.order_mappings = {
            'SVO': {'S': 0, 'V': 1, 'O': 2, 'COMP': 2},
            'SOV': {'S': 0, 'O': 1, 'COMP': 1, 'V': 2},
            'VSO': {'V': 0, 'S': 1, 'O': 2, 'COMP': 2},
            'VOS': {'V': 0, 'O': 1, 'COMP': 1, 'S': 2},
            'OSV': {'O': 0, 'COMP': 0, 'S': 1, 'V': 2},
            'OVS': {'O': 0, 'COMP': 0, 'V': 1, 'S': 2}
        }
        self.function_words = {'DET', 'PREP', 'ADJ', 'ADV'}
        self.agreement_rules = self.profile.get('agreement_rules', {})
        self.adjunct_position = self.agreement_rules.get(
            'adjunct_position', 'auto')
        self.drop_articles = self.profile.get('drop_articles', False)
        self.pro_drop = self.profile.get('pro_drop', False)
        self.functional_particles = self.profile.get(
            'functional_particles', {})
        self.topicalization_config = self.profile.get('topicalization', {})

    def map_to_target_order(self, functions: List[Dict], target_order: str) -> List[int]:
        if target_order not in self.order_mappings:
            target_order = 'SVO'

        clauses_data = self._partition_into_clauses(functions)
        final_indices = []

        for clause_indices_set, is_subordinate in clauses_data:
            local_indices = sorted(list(clause_indices_set))
            clause_functions_subset = []

            for i, original_idx in enumerate(local_indices):
                f = functions[original_idx].copy()
                f['original_index'] = original_idx
                f['index'] = i
                clause_functions_subset.append(f)

            current_clause_order = self.subordinate_order if is_subordinate else target_order
            if current_clause_order not in self.order_mappings:
                current_clause_order = 'SVO'

            reordered_local_indices = self._map_single_clause(
                clause_functions_subset, current_clause_order)

            for local_idx in reordered_local_indices:
                final_indices.append(
                    clause_functions_subset[local_idx]['original_index'])

        return final_indices

    def _partition_into_clauses(self, functions: List[Dict]) -> List[Tuple[Set[int], bool]]:
        partitions = []
        current_indices = set()

        coordinating_conjunctions = {
            'e', 'mas', 'porém', 'todavia', 'contudo', 'ou', 'nem', 'logo', 'portanto'}
        subordinating_conjunctions = {
            'que', 'porque', 'quando', 'se', 'embora', 'enquanto', 'como', 'pois', 'caso', 'para'}
        subject_pronouns = {'eu', 'tu', 'ele', 'ela', 'nós', 'vós',
                            'eles', 'elas', 'você', 'vocês', 'isso', 'isto', 'aquilo'}

        is_current_subordinate = False

        for i, f in enumerate(functions):
            word = f['word'].lower()
            pos = f['pos']
            is_boundary = False
            next_is_subordinate = False

            if pos == 'PUNCT' and word in {',', ';', '.', '!', '?', ':'}:
                if i + 1 < len(functions):
                    next_f = functions[i+1]
                    next_word = next_f['word'].lower()

                    if next_word in coordinating_conjunctions:
                        is_boundary = True
                        next_is_subordinate = False
                    elif next_word in subordinating_conjunctions:
                        is_boundary = True
                        next_is_subordinate = True
                    elif next_f['function'] == SyntacticFunction.SUBJECT:
                        is_boundary = True
                    elif next_word in subject_pronouns:
                        is_boundary = True
                    elif next_f['pos'] == 'VERB' and next_f['function'] == SyntacticFunction.VERB:
                        is_boundary = True

            elif word in subordinating_conjunctions and f['pos'] in {'SCONJ', 'ADP'}:
                if i > 0:
                    is_boundary = True
                    next_is_subordinate = True

            current_indices.add(f['index'])

            if is_boundary:
                partitions.append((current_indices, is_current_subordinate))
                current_indices = set()
                is_current_subordinate = next_is_subordinate

        if current_indices:
            partitions.append((current_indices, is_current_subordinate))

        return partitions

    def _map_single_clause(self, functions: List[Dict], target_order: str) -> List[int]:
        chunks = self._build_chunks(functions)
        self._attach_orphaned_punctuation(chunks, functions)

        core_chunks = {'S': [], 'V': [], 'O': [], 'COMP': []}
        adjunct_chunks = []
        modifier_chunks = []

        for chunk in chunks:
            if chunk.function == SyntacticFunction.SUBJECT:
                core_chunks['S'].append(chunk)
            elif chunk.function == SyntacticFunction.VERB:
                core_chunks['V'].append(chunk)
            elif chunk.function == SyntacticFunction.OBJECT:
                core_chunks['O'].append(chunk)
            elif chunk.function == SyntacticFunction.COMPLEMENT:
                core_chunks['COMP'].append(chunk)
            elif chunk.function == SyntacticFunction.ADJUNCT:
                adjunct_chunks.append(chunk)
            else:
                modifier_chunks.append(chunk)

        adjunct_position = self._determine_adjunct_position(target_order)
        return self._legacy_reorder(chunks, target_order, adjunct_position, adjunct_chunks, core_chunks, modifier_chunks)

    def _legacy_reorder(self, chunks, target_order, adjunct_position, adjunct_chunks, core_chunks, modifier_chunks):
        final_closers = []
        last_chunk_idx = len(chunks) - 1

        for i, c in enumerate(chunks):
            if c.function == SyntacticFunction.PUNCT and c.words[0][0] in {'.', '!', '?'}:
                final_closers.append(c)

        ordered_chunks = []

        if adjunct_position == 'before_subject':
            ordered_chunks.extend(adjunct_chunks)

        target_map = self.order_mappings[target_order]
        placed_core = []

        if core_chunks['S']:
            placed_core.append((target_map.get('S', 0), core_chunks['S']))
        if core_chunks['V']:
            placed_core.append((target_map.get('V', 1), core_chunks['V']))
        if core_chunks['O']:
            placed_core.append((target_map.get('O', 2), core_chunks['O']))
        if core_chunks['COMP']:
            placed_core.append(
                (target_map.get('COMP', 2), core_chunks['COMP']))

        placed_core.sort(key=lambda x: x[0])

        for _, chunk_list in placed_core:
            ordered_chunks.extend(chunk_list)

        ordered_chunks.extend(modifier_chunks)

        if adjunct_position != 'before_subject':
            ordered_chunks.extend(adjunct_chunks)

        for closer in final_closers:
            if closer not in ordered_chunks:
                ordered_chunks.append(closer)

        result_indices = []
        seen = set()
        for chunk in ordered_chunks:
            indices = chunk.get_all_indices()
            for idx in indices:
                if idx not in seen:
                    result_indices.append(idx)
                    seen.add(idx)
        return result_indices

    def _should_drop(self, func: Dict, functions: List[Dict]) -> bool:
        if func['function'] in {SyntacticFunction.QUANTIFIER, SyntacticFunction.VERB_PARTICLE, SyntacticFunction.INTENSIFIER}:
            return False

        is_pro_drop = False
        pro_drop_conditions = []

        if isinstance(self.pro_drop, bool):
            is_pro_drop = self.pro_drop
        elif isinstance(self.pro_drop, dict):
            is_pro_drop = self.pro_drop.get('enabled', False)
            pro_drop_conditions = self.pro_drop.get('conditions', [])

        if is_pro_drop and func['pos'] == 'PRON' and func['function'] == SyntacticFunction.SUBJECT:
            if func['word'].isupper() and len(func['word']) > 1:
                return False

            if 'verb_agreement' in pro_drop_conditions:
                has_agreement = self.agreement_rules.get('number_agreement', False) or \
                    self.agreement_rules.get('person_agreement', False) or \
                    self.agreement_rules.get('gender_agreement', False)
                if not has_agreement:
                    return False

            head_idx = func['dependencies'][0] if func['dependencies'] else -1
            if head_idx != -1:
                head_func = next(
                    (f for f in functions if f['original_index'] == head_idx), None)
                if head_func and head_func['pos'] in {'VERB', 'AUX'}:
                    return True

        if not self.drop_articles:
            return False
        if func['pos'] != 'DET':
            return False

        if self.topicalization_config.get('reintroduce_articles', False):
            head_idx = func.get('dependencies', [-1])[0]
            if head_idx != -1:
                for f in functions:
                    if f['index'] == head_idx:
                        if f['function'] == SyntacticFunction.SUBJECT:
                            return False
                        break

        feats = func.get('feats', '_')
        return 'PronType=Art' in feats

    def _build_chunks(self, functions: List[Dict]) -> List[Chunk]:
        chunks = []
        processed_indices = set()
        i = 0
        while i < len(functions):
            if i in processed_indices:
                i += 1
                continue

            func = functions[i]

            if self._should_drop(func, functions):
                processed_indices.add(i)
                i += 1
                continue

            pos = func['pos']
            func_type = func['function']

            if func_type == SyntacticFunction.PUNCT:
                chunk = Chunk([(func['word'], func['index'])],
                              SyntacticFunction.PUNCT, 0, 'punct')
                chunks.append(chunk)
                processed_indices.add(i)
                i += 1
                continue

            chunk_built = None
            if pos == 'NOUN' and func_type in {SyntacticFunction.SUBJECT, SyntacticFunction.OBJECT, SyntacticFunction.COMPLEMENT}:
                chunk_built = self._build_noun_phrase_chunk(
                    functions, i, processed_indices)
            elif pos == 'VERB' and func_type == SyntacticFunction.VERB:
                chunk_built = self._build_verb_phrase_chunk(
                    functions, i, processed_indices)
            elif pos == 'PREP' and func_type == SyntacticFunction.ADJUNCT:
                chunk_built = self._build_prepositional_phrase_chunk(
                    functions, i, processed_indices)
            elif (pos == 'ADJ' and func_type == SyntacticFunction.COMPLEMENT) or (pos == 'ADJ' and func_type == SyntacticFunction.MODIFIER):
                chunk_built = self._build_adjective_phrase_chunk(
                    functions, i, processed_indices)

            if chunk_built:
                chunks.append(chunk_built)
                continue

            head_idx = func['dependencies'][0] if func['dependencies'] else -1
            if head_idx > i and head_idx < len(functions):
                head_pos = functions[head_idx]['pos']
                head_func = functions[head_idx]['function']
                triggers_builder = False

                if head_pos == 'NOUN' and head_func in {SyntacticFunction.SUBJECT, SyntacticFunction.OBJECT, SyntacticFunction.COMPLEMENT}:
                    if pos in {'DET', 'ADJ', 'PRON', 'ADV', 'NUM'} or func_type == SyntacticFunction.QUANTIFIER:
                        if func_type != SyntacticFunction.SUBJECT:
                            triggers_builder = True
                elif head_pos == 'VERB' and head_func == SyntacticFunction.VERB:
                    if func_type != SyntacticFunction.SUBJECT:
                        if pos in {'AUX', 'ADV', 'PRON', 'PART', 'SCONJ'} or func_type == SyntacticFunction.VERB_PARTICLE:
                            triggers_builder = True
                elif head_pos == 'ADJ' and head_func in {SyntacticFunction.COMPLEMENT, SyntacticFunction.MODIFIER}:
                    if func_type == SyntacticFunction.INTENSIFIER:
                        triggers_builder = True

                if triggers_builder:
                    i += 1
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
                        chunk.words = []
        chunks[:] = [c for c in chunks if c.words]

    def _build_noun_phrase_chunk(self, functions: List[Dict], noun_index: int,
                                 processed_indices: Set[int]) -> Optional[Chunk]:
        if noun_index >= len(functions):
            return None
        noun_func = functions[noun_index]
        np_words = [(noun_func['word'], noun_func['index'])]
        post_nominal_elements = []

        i = noun_index - 1
        while i >= 0 and i not in processed_indices:
            func = functions[i]

            if self._should_drop(func, functions):
                processed_indices.add(i)
                i -= 1
                continue

            if func['function'] in {SyntacticFunction.SUBJECT, SyntacticFunction.VERB, SyntacticFunction.PUNCT} and func['index'] != noun_index:
                break

            is_quantifier = func['function'] == SyntacticFunction.QUANTIFIER
            if is_quantifier:
                lemma = func['lemma'].lower()
                config = self.functional_particles.get(lemma, {})
                pos_rule = config.get('noun_position', 'pre_nominal')
                if pos_rule == 'post_nominal':
                    post_nominal_elements.append((func['word'], func['index']))
                    processed_indices.add(i)
                    i -= 1
                    continue

            if func['pos'] in {'DET', 'ADJ', 'PRON', 'ADV', 'NUM'} or is_quantifier:
                np_words.insert(0, (func['word'], func['index']))
                processed_indices.add(i)
                i -= 1
            else:
                break

        i = noun_index + 1
        while i < len(functions) and i not in processed_indices:
            func = functions[i]

            if func['function'] in {SyntacticFunction.SUBJECT, SyntacticFunction.VERB, SyntacticFunction.PUNCT}:
                break

            is_quantifier = func['function'] == SyntacticFunction.QUANTIFIER
            if is_quantifier:
                lemma = func['lemma'].lower()
                config = self.functional_particles.get(lemma, {})
                pos_rule = config.get('noun_position', 'pre_nominal')
                if pos_rule == 'pre_nominal':
                    np_words.insert(0, (func['word'], func['index']))
                    processed_indices.add(i)
                    i += 1
                    continue
                else:
                    post_nominal_elements.append((func['word'], func['index']))
                    processed_indices.add(i)
                    i += 1
                    continue

            if func['pos'] == 'ADJ':
                if i + 1 < len(functions) and functions[i+1]['function'] == SyntacticFunction.INTENSIFIER:
                    pass

                adj_seq = [(func['word'], func['index'])]
                prev_i = i - 1
                if prev_i >= 0 and functions[prev_i]['function'] == SyntacticFunction.INTENSIFIER and prev_i not in processed_indices:
                    intens_func = functions[prev_i]
                    lemma = intens_func['lemma'].lower()
                    config = self.functional_particles.get(lemma, {})
                    adj_pos = config.get('adj_position', 'pre_nominal')
                    if adj_pos == 'post_nominal':
                        adj_seq.append(
                            (intens_func['word'], intens_func['index']))
                    else:
                        adj_seq.insert(
                            0, (intens_func['word'], intens_func['index']))
                    processed_indices.add(prev_i)

                for w in adj_seq:
                    np_words.append(w)
                processed_indices.add(i)
                i += 1
            else:
                break

        for elem in post_nominal_elements:
            np_words.append(elem)

        processed_indices.add(noun_index)
        return Chunk(np_words, noun_func['function'], 0, 'NP')

    def _build_verb_phrase_chunk(self, functions: List[Dict], verb_index: int,
                                 processed_indices: Set[int]) -> Optional[Chunk]:
        if verb_index >= len(functions):
            return None
        verb_func = functions[verb_index]
        vp_words = [(verb_func['word'], verb_func['index'])]
        post_verbal_elements = []

        i = verb_index - 1
        while i >= 0 and i not in processed_indices:
            func = functions[i]

            if func['function'] == SyntacticFunction.VERB_PARTICLE:
                lemma = func['lemma'].lower()
                config = self.functional_particles.get(lemma, {})
                pos_rule = config.get('verb_position', 'pre_verbal')
                if pos_rule == 'post_verbal':
                    post_verbal_elements.append((func['word'], func['index']))
                else:
                    vp_words.insert(0, (func['word'], func['index']))
                processed_indices.add(i)
                i -= 1
                continue

            if func['pos'] in {'AUX', 'ADV', 'PRON', 'PART', 'SCONJ'}:
                if func['function'] == SyntacticFunction.SUBJECT:
                    break
                vp_words.insert(0, (func['word'], func['index']))
                processed_indices.add(i)
                i -= 1
            else:
                break

        i = verb_index + 1
        while i < len(functions) and i not in processed_indices:
            func = functions[i]
            if func['function'] == SyntacticFunction.VERB_PARTICLE:
                lemma = func['lemma'].lower()
                config = self.functional_particles.get(lemma, {})
                pos_rule = config.get('verb_position', 'pre_verbal')
                if pos_rule == 'pre_verbal':
                    vp_words.insert(0, (func['word'], func['index']))
                else:
                    post_verbal_elements.append((func['word'], func['index']))
                processed_indices.add(i)
                i += 1
                continue
            break

        for elem in post_verbal_elements:
            vp_words.append(elem)

        processed_indices.add(verb_index)
        return Chunk(vp_words, SyntacticFunction.VERB, 0, 'VP')

    def _build_adjective_phrase_chunk(self, functions: List[Dict], adj_index: int,
                                      processed_indices: Set[int]) -> Optional[Chunk]:
        if adj_index >= len(functions):
            return None
        adj_func = functions[adj_index]
        ap_words = [(adj_func['word'], adj_func['index'])]

        i = adj_index - 1
        if i >= 0 and i not in processed_indices and functions[i]['function'] == SyntacticFunction.INTENSIFIER:
            intens_func = functions[i]
            lemma = intens_func['lemma'].lower()
            config = self.functional_particles.get(lemma, {})
            adj_pos_rule = config.get('adj_position', 'pre_nominal')
            if adj_pos_rule == 'post_nominal':
                ap_words.append((intens_func['word'], intens_func['index']))
            else:
                ap_words.insert(0, (intens_func['word'], intens_func['index']))
            processed_indices.add(i)

        i = adj_index + 1
        if i < len(functions) and i not in processed_indices and functions[i]['function'] == SyntacticFunction.INTENSIFIER:
            intens_func = functions[i]
            lemma = intens_func['lemma'].lower()
            config = self.functional_particles.get(lemma, {})
            adj_pos_rule = config.get('adj_position', 'pre_nominal')
            if adj_pos_rule == 'pre_nominal':
                ap_words.insert(0, (intens_func['word'], intens_func['index']))
            else:
                ap_words.append((intens_func['word'], intens_func['index']))
            processed_indices.add(i)

        processed_indices.add(adj_index)
        func_label = adj_func['function']
        if func_label == SyntacticFunction.MODIFIER and adj_func.get('deprel') == 'root':
            func_label = SyntacticFunction.COMPLEMENT

        return Chunk(ap_words, func_label, 0, 'AP')

    def _build_prepositional_phrase_chunk(self, functions: List[Dict], prep_index: int,
                                          processed_indices: Set[int]) -> Optional[Chunk]:
        if prep_index >= len(functions):
            return None
        prep_func = functions[prep_index]
        pp_words = [(prep_func['word'], prep_index)]
        i = prep_index + 1
        while i < len(functions) and i not in processed_indices and functions[i]['pos'] == 'DET':
            if self._should_drop(functions[i], functions):
                processed_indices.add(i)
                i += 1
                continue

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
        use_cache = False

        if cache_key in self.sentence_cache:
            cached = self.sentence_cache[cache_key]
            if 'functions' in cached and cached['functions']:
                if 'feats' in cached['functions'][0]:
                    use_cache = True

        if use_cache:
            cached = self.sentence_cache[cache_key]
            reordered_words = []

            ordered_functions = [cached['functions'][i]
                                 for i in cached['indices']]

            for idx in cached['indices']:
                word = cached['words'][idx]
                function = cached['functions'][idx]['function']
                deprel = cached['functions'][idx].get('deprel', '')
                word_with_case = self.case_morphology.apply_case(
                    word, function, self.word_order, deprel)
                reordered_words.append(word_with_case)

            final_tokens = self._glue_tokens(
                reordered_words, ordered_functions)

            return final_tokens, ordered_functions

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
            lemma = parts[2]
            upos = parts[3]
            feats = parts[5]
            deprel = parts[7]
            head = int(parts[6]) - 1 if parts[6] != '0' else -1
            function = self._map_deprel_to_function(deprel, upos)
            functions.append({
                'word': word,
                'lemma': lemma,
                'pos': upos,
                'feats': feats,
                'deprel': deprel,
                'function': function,
                'index': i,
                'dependencies': [head] if head != -1 else [],
            })
            words.append(word)
            i += 1

        self._refine_functions(functions)

        new_indices = self.word_order_mapper.map_to_target_order(
            functions, self.word_order)
        raw_reordered_words = []
        ordered_functions = []

        for idx in new_indices:
            word = functions[idx]['word']
            function = functions[idx]['function']
            deprel = functions[idx].get('deprel', '')
            word_with_case = self.case_morphology.apply_case(
                word, function, self.word_order, deprel)
            raw_reordered_words.append(word_with_case)
            ordered_functions.append(functions[idx])

        final_tokens = self._glue_tokens(
            raw_reordered_words, ordered_functions)

        self.sentence_cache[cache_key] = {
            'indices': new_indices,
            'words': words,
            'functions': functions
        }

        return final_tokens, ordered_functions

    def _refine_functions(self, functions: List[Dict]):
        particles = self.profile.get('functional_particles', {})
        for f in functions:
            lemma = f['lemma'].lower()
            if lemma in particles:
                head_idx = f['dependencies'][0] if f['dependencies'] else -1
                if head_idx != -1 and head_idx < len(functions):
                    head = next(
                        (h for h in functions if h['index'] == head_idx), None)
                    if head:
                        head_pos = head['pos']
                        if head_pos == 'NOUN':
                            f['function'] = SyntacticFunction.QUANTIFIER
                        elif head_pos in {'VERB', 'AUX'}:
                            f['function'] = SyntacticFunction.VERB_PARTICLE
                        elif head_pos == 'ADJ':
                            f['function'] = SyntacticFunction.INTENSIFIER

    def estimate_lemma_pos(self, lemma: str) -> str:
        lemma = lemma.lower()
        if lemma.endswith(('ar', 'er', 'ir', 'or')) and len(lemma) > 2:
            return 'VERB'
        if lemma.endswith(('mente')):
            return 'ADV'
        if lemma.endswith(('o', 'a', 'e', 'os', 'as', 'es')):
            return 'NOUN'
        return 'NOUN'

    def _glue_tokens(self, words: List[str], function_objs: List[Dict]) -> List[str]:
        final_tokens = []
        conlang_terminators = set(self.profile.get('style', {}).get(
            'sentence_terminators', ['.', '!', '?']))
        secondary_terminators = set(self.profile.get(
            'style', {}).get('secondary_terminators', [':', ';']))
        punct_map = self.profile.get('style', {}).get('punctuation_map', {})
        mapped_comma = punct_map.get(',', ',')

        punct_suffix = conlang_terminators.union(secondary_terminators).union(
            {mapped_comma, '...', '…', ')', ']', '}', '”', '"', "'", '%'})
        punct_prefix = {'(', '[', '{', '«', '“', '¿', '¡'}

        for i, word in enumerate(words):
            if not final_tokens:
                final_tokens.append(word)
                continue
            last_token = final_tokens[-1]
            if word in punct_suffix:
                if word in conlang_terminators:
                    strip_chars = [mapped_comma] + list(secondary_terminators)
                    for sc in strip_chars:
                        if last_token.endswith(sc):
                            last_token = last_token[:-len(sc)]
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
            reordered_words, ordered_functions = self.process_sentence(
                sentence)
            reordered_sentences.append(' '.join(reordered_words))
            all_functions.append({
                'original': sentence,
                'reordered': ' '.join(reordered_words),
                'functions': ordered_functions
            })
        self.save_cache()
        return ' '.join(reordered_sentences), all_functions

    def _split_sentences(self, text: str) -> List[str]:
        pattern = r'([.!?]+(?:\s+|$))'
        chunks = re.split(pattern, text)

        sentences = []
        i = 0
        while i < len(chunks):
            chunk = chunks[i]
            if i + 1 < len(chunks):
                delimiter = chunks[i+1]
                full_sentence = chunk + delimiter
                if full_sentence.strip():
                    sentences.append(full_sentence)
                i += 2
            else:
                if chunk.strip():
                    sentences.append(chunk)
                i += 1

        return sentences

    def _get_cache_key(self, sentence: str) -> str:
        config_str = json.dumps(self.profile.get(
            'functional_particles', {}), sort_keys=True)
        combined = sentence.lower() + config_str + self.word_order
        return hashlib.md5(combined.encode()).hexdigest()

    def _map_deprel_to_function(self, deprel: str, upos: str) -> str:
        deprel = deprel.lower()
        if upos in {'VERB', 'AUX'}:
            if deprel in {'cop', 'aux'}:
                return SyntacticFunction.VERB
            return SyntacticFunction.VERB
        if 'nsubj' in deprel:
            return SyntacticFunction.SUBJECT
        if deprel in {'obj', 'iobj', 'ccomp'}:
            return SyntacticFunction.OBJECT
        if deprel in {'obl', 'advcl'}:
            return SyntacticFunction.ADJUNCT
        if deprel == 'root' and upos == 'ADJ':
            return SyntacticFunction.COMPLEMENT
        if upos == 'PUNCT':
            return SyntacticFunction.PUNCT
        return SyntacticFunction.MODIFIER

    def get_statistics(self) -> Dict:
        return {
            'profile_id': self.profile_id,
            'word_order': self.word_order,
            'cached_sentences': len(self.sentence_cache),
        }
