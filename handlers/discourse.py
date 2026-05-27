from typing import Dict, List, Optional, Set, Tuple


class AllomorphyHandler:
    def __init__(self, profile: Dict, phonology_handler):
        self.profile = profile
        self.config = profile.get('allomorphy', {})
        self.enabled = self.config.get('enabled', False)
        self.rules = self.config.get('rules', [])
        self.feature_defs = self.config.get('feature_definitions', {})
        self.phonology_handler = phonology_handler

    def apply_allomorphy(self, words: List[str]) -> List[str]:
        if not self.enabled or not words:
            return words
        result = list(words)
        for i in range(len(result) - 1):
            current_word = result[i]
            next_word_raw = result[i+1]
            clean_current = "".join(x for x in current_word if x.isalpha())
            if not clean_current:
                continue
            applicable_rules = [
                r for r in self.rules if r['target_word'] == clean_current.lower()]
            if not applicable_rules:
                continue
            next_start_char = self._get_start_char(next_word_raw)
            if not next_start_char:
                continue
            for rule in applicable_rules:
                env = rule.get('environment')
                replacement = rule.get('replacement')
                match = False
                if env == 'before_vowel':
                    if next_start_char in self.phonology_handler.vowels:
                        match = True
                elif env == 'before_consonant':
                    if next_start_char in self.phonology_handler.consonants:
                        match = True
                elif env == 'before_feature':
                    feat = rule.get('feature')
                    chars = self.feature_defs.get(feat, [])
                    if next_start_char in chars:
                        match = True
                if match:
                    if current_word[0].isupper() and replacement:
                        replacement = replacement[0].upper() + replacement[1:]
                    result[i] = replacement
                    break
        return result

    def _get_start_char(self, text: str) -> Optional[str]:
        clean = "".join(x for x in text if x.isalpha())
        if not clean:
            return None
        return clean[0].lower()


class PrepositionHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get('adposition_system', {}).get(
            'inflected_prepositions', {})
        self.enabled = self.config.get('enabled', False)
        self.forms = self.config.get('forms', {})

    def _get_person_key(self, func: Dict) -> Optional[str]:
        feats_str = func.get('feats', '')
        pos = func.get('pos')
        if not feats_str or feats_str == '_':
            return None
        feat_map = {}
        for f in feats_str.split('|'):
            if '=' in f:
                k, v = f.split('=', 1)
                feat_map[k] = v

        if pos == 'PRON':
            person = feat_map.get('Person')
            number = feat_map.get('Number')
            if not person or not number:
                return None
            num_map = {'Sing': 'sg', 'Plur': 'pl', 'Dual': 'du'}
            base_key = f"{person}{num_map.get(number, 'sg')}"
            gender = feat_map.get('Gender')
            if gender:
                gen_map = {'Masc': 'm', 'Fem': 'f', 'Neut': 'n'}
                gen_code = gen_map.get(gender, '')
                if gen_code:
                    return f"{base_key}_{gen_code}"
            return base_key

        elif pos == 'DET':
            if feat_map.get('Definite') != 'Def':
                return None
            gender = feat_map.get('Gender')
            number = feat_map.get('Number')
            if not gender or not number:
                return None
            gen_map = {'Masc': 'm', 'Fem': 'f', 'Neut': 'n'}
            num_map = {'Sing': 'sg', 'Plur': 'pl'}
            return f"def_{gen_map.get(gender, 'm')}_{num_map.get(number, 'sg')}"

        return None

    def analyze_inflections(self, functions: List[Dict], engine) -> Tuple[Dict[int, str], Set[int]]:
        if not self.enabled:
            return {}, set()
        inflection_map = {}
        absorbed_indices = set()
        for f in functions:
            if f['pos'] == 'ADP':
                prep_lemma = f['lemma'].lower()
                conlang_prep = engine._get_word_form(prep_lemma)
                if conlang_prep not in self.forms:
                    continue
                prep_idx = f['index']
                target_dependent = None
                for dep in functions:
                    if dep['pos'] in {'PRON', 'DET'}:
                        if prep_idx in dep.get('dependencies', []) or dep['index'] in f.get('dependencies', []):
                            target_dependent = dep
                            break
                if target_dependent:
                    lookup_key = self._get_person_key(target_dependent)
                    if lookup_key:
                        inflected_form = self.forms[conlang_prep].get(
                            lookup_key)
                        if not inflected_form and '_' in lookup_key and target_dependent['pos'] == 'PRON':
                            base_key = lookup_key.split('_')[0]
                            inflected_form = self.forms[conlang_prep].get(
                                base_key)
                        if inflected_form:
                            inflection_map[prep_idx] = inflected_form
                            absorbed_indices.add(target_dependent['index'])
        return inflection_map, absorbed_indices


class CliticHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get(
            'pronominal_system', {}).get('clitic_ordering', {})
        self.enabled = self.config.get('enabled', False)
        self.order = self.config.get(
            'order', ['verb', 'obj_direct', 'obj_indirect'])
        self.encliticizes = self.config.get('encliticizes', False)
        self.procliticizes = self.config.get('procliticizes', False)
        self.pronouns = profile.get(
            'pronominal_system', {}).get('object_pronouns', {})

    def _get_person_key(self, feats: str) -> Optional[str]:
        if not feats or feats == '_':
            return None
        feat_map = {}
        for f in feats.split('|'):
            if '=' in f:
                k, v = f.split('=', 1)
                feat_map[k] = v
        person = feat_map.get('Person')
        number = feat_map.get('Number')
        gender = feat_map.get('Gender')
        if not person or not number:
            return None
        num_map = {'Sing': 'sg', 'Plur': 'pl', 'Dual': 'du'}
        num_code = num_map.get(number, 'sg')
        base_key = f"{person}{num_code}"
        if gender:
            gen_map = {'Masc': 'm', 'Fem': 'f', 'Neut': 'n'}
            gen_code = gen_map.get(gender, '')
            if gen_code:
                return f"{base_key}_{gen_code}"
        return base_key

    def get_pronoun_form(self, func: Dict, p_type: str) -> str:
        key = self._get_person_key(func.get('feats', ''))
        if not key:
            return ""
        forms = self.pronouns.get(p_type, {})
        if key in forms:
            return forms[key]
        base_key = key.split('_')[0]
        return forms.get(base_key, "")

    def analyze_clitics(self, functions: List[Dict], negation_handler) -> Tuple[Dict[int, Dict], Set[int]]:
        if not self.enabled:
            return {}, set()
        clitic_map = {}
        absorbed_indices = set()
        negation_in_order = 'neg' in self.order
        for func in functions:
            if func['pos'] in {'VERB', 'AUX'}:
                verb_idx = func['index']
                clitic_data = {
                    'verb': '',
                    'neg': '',
                    'obj_direct': '',
                    'obj_indirect': ''
                }
                has_clitics = False
                if negation_in_order:
                    is_negated, trig_idx, strategy = negation_handler.detect_negation(
                        func, functions)
                    if is_negated and trig_idx is not None:
                        marker = strategy.get('marker', '')
                        clitic_data['neg'] = marker
                        absorbed_indices.add(trig_idx)
                        has_clitics = True
                dependents = [
                    f for f in functions if verb_idx in f.get('dependencies', [])]
                for dep in dependents:
                    if dep['pos'] == 'PRON':
                        deprel = dep.get('deprel', '')
                        form = ""
                        if 'obj' in deprel or 'dobj' in deprel:
                            form = self.get_pronoun_form(dep, 'direct')
                            if form:
                                clitic_data['obj_direct'] = form
                                absorbed_indices.add(dep['index'])
                                has_clitics = True
                        elif 'iobj' in deprel or 'obl' in deprel:
                            form = self.get_pronoun_form(dep, 'indirect')
                            if form:
                                clitic_data['obj_indirect'] = form
                                absorbed_indices.add(dep['index'])
                                has_clitics = True
                if has_clitics:
                    clitic_map[verb_idx] = clitic_data
        return clitic_map, absorbed_indices

    def apply_clitics(self, verb_word: str, verb_idx: int, clitic_map: Dict[int, Dict]) -> str:
        if verb_idx not in clitic_map:
            return verb_word
        data = clitic_map[verb_idx]
        data['verb'] = verb_word
        parts = []
        for element in self.order:
            val = data.get(element, '')
            if val:
                parts.append(val)
        if self.encliticizes:
            return "".join(parts)
        elif self.procliticizes:
            return "".join(parts)
        return " ".join(parts)


class PossessiveHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get(
            'determiner_system', {}).get('possessives', {})
        self.enabled = self.config.get('pronominal_suffixes', False)
        self.suffixes = self.config.get('suffixes', {})
        self.possessive_map = self.config.get('possessive_lemmas', {
            'meu': '1', 'minha': '1', 'meus': '1', 'minhas': '1',
            'teu': '2', 'tua': '2', 'teus': '2', 'tuas': '2',
            'seu': '3', 'sua': '3', 'seus': '3', 'suas': '3',
            'nosso': '1', 'nossa': '1', 'nossos': '1', 'nossas': '1',
            'vosso': '2', 'vossa': '2', 'vossos': '2', 'vossas': '2'
        })

    def get_suffix(self, feats_str: str, lemma: str = '') -> str:
        if not feats_str or feats_str == '_':
            return ""
        feats = {}
        for f in feats_str.split('|'):
            if '=' in f:
                k, v = f.split('=', 1)
                feats[k] = v
        person = feats.get('Person')
        number = feats.get('Number')
        gender = feats.get('Gender')
        if not person and lemma:
            person = self.possessive_map.get(lemma.lower())
        if not person or not number:
            return ""
        key_num = 'sg' if number == 'Sing' else 'pl'
        base_key = f"{person}{key_num}"
        if gender:
            key_gen = 'm' if gender == 'Masc' else 'f'
            full_key = f"{base_key}_{key_gen}"
            if full_key in self.suffixes:
                return self.suffixes[full_key]
        if base_key in self.suffixes:
            return self.suffixes[base_key]
        return ""

    def analyze_possessives(self, functions: List[Dict]) -> Tuple[Dict[int, str], Set[int]]:
        if not self.enabled:
            return {}, set()
        suffix_map = {}
        absorbed_indices = set()
        for f in functions:
            deprel = f.get('deprel', '')
            if 'nmod:poss' in deprel or ('det' in deprel and f.get('pos') == 'DET'):
                head_idx = f['dependencies'][0] if f['dependencies'] else -1
                if head_idx == -1:
                    continue
                head_func = next(
                    (h for h in functions if h['index'] == head_idx), None)
                if not head_func or head_func['pos'] not in {'NOUN', 'PROPN'}:
                    continue
                if f.get('pos') in {'PRON', 'DET'}:
                    suffix = self.get_suffix(
                        f.get('feats', ''), lemma=f.get('lemma', ''))
                    if suffix:
                        suffix_map[head_idx] = suffix
                        absorbed_indices.add(f['index'])
        return suffix_map, absorbed_indices


class DemonstrativeHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get(
            'determiner_system', {}).get('demonstratives', {})
        self.enabled = bool(self.config)
        self.proximal = self.config.get('proximal', {})
        self.distal = self.config.get('distal', {})
        self.mappings = self.config.get('source_mappings', {
            'proximal': ['este', 'esta', 'isto', 'esse', 'essa', 'isso', 'estes', 'estas', 'esses', 'essas'],
            'distal': ['aquele', 'aquela', 'aquilo', 'aqueles', 'aquelas']
        })
        self.heuristic_enabled = self.config.get(
            'gender_inheritance_heuristic', True)

    def is_demonstrative(self, func: Dict) -> bool:
        if func['pos'] not in {'DET', 'PRON'}:
            return False
        lemma = func.get('lemma', '').lower()
        word = func.get('word', '').lower()
        if lemma in self.mappings.get('proximal', []) or word in self.mappings.get('proximal', []):
            return True
        if lemma in self.mappings.get('distal', []) or word in self.mappings.get('distal', []):
            return True
        return False

    def get_form(self, func: Dict, all_functions: List[Dict], engine_ref) -> str:
        lemma = func.get('lemma', '').lower()
        word = func.get('word', '').lower()
        target_type = None
        if lemma in self.mappings.get('proximal', []) or word in self.mappings.get('proximal', []):
            target_type = 'proximal'
        elif lemma in self.mappings.get('distal', []) or word in self.mappings.get('distal', []):
            target_type = 'distal'
        if not target_type:
            return func.get('word', '')
        forms = self.proximal if target_type == 'proximal' else self.distal
        head_idx = func['dependencies'][0] if func['dependencies'] else -1
        gender = 'masculine'
        number = 'singular'
        source_gender_hint = 'masculine'
        source_feats = func.get('feats', '')
        if 'Gender=Fem' in source_feats:
            source_gender_hint = 'feminine'
        if head_idx != -1:
            head = next(
                (f for f in all_functions if f['index'] == head_idx), None)
            if head:
                head_lemma = head.get('lemma', head.get('word', '')).lower()
                head_conlang_word = engine_ref._get_word_form(head_lemma)
                gender = engine_ref.gender_handler.infer_gender(
                    head_conlang_word)
                if gender == engine_ref.gender_handler.default_gender and source_gender_hint == 'feminine':
                    if self.heuristic_enabled:
                        gender = 'feminine'
                feats = head.get('feats', '')
                if 'Number=Plur' in feats:
                    number = 'plural'
                elif 'Number=Sing' in feats:
                    number = 'singular'
        if 'Number=Plur' in source_feats:
            number = 'plural'
        new_word = ""
        if number == 'plural':
            new_word = forms.get('pl', '')
        else:
            key = 'sg_f' if gender == 'feminine' else 'sg_m'
            new_word = forms.get(key, '')
        if new_word:
            if func.get('word', '') and func['word'][0].isupper():
                new_word = new_word.capitalize()
            return new_word
        return func.get('word', '')
