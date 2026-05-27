from typing import Dict, List, Optional, Set, Tuple

from constants import NEGATION_TRIGGERS
from handlers.phonology import VowelHarmonyHandler


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
            if 'type' not in rule:
                continue
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
                    if marker:
                        result = marker + ' ' + result
                elif m_type == 'particle_after':
                    if marker:
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


class NegationHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get('negation_system', {})
        self.enabled = self.config.get('enabled', False)
        self.strategies = self.config.get('strategies', [])
        self.negation_triggers = NEGATION_TRIGGERS

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


class CopulaHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get('copula_system', {})
        self.enabled = self.config.get('enabled', False)
        self.copulas = self.config.get('copulas', [])
        self.pronominal_forms = profile.get(
            'pronominal_system', {}).get('independent_pronouns', {})

    def get_copula_form(self, func: Dict, all_functions: List[Dict], engine_ref=None) -> Optional[str]:
        if not self.enabled:
            return func.get('word')

        feats = func.get('feats', '')
        tense = 'Pres'
        if 'Tense=Past' in feats or 'Tense=Imp' in feats:
            tense = 'Past'
        elif 'Tense=Fut' in feats:
            tense = 'Fut'

        subject_type = 'Noun'
        subject_person = '3sg_m'

        my_index = func['index']
        for f in all_functions:
            if my_index in f.get('dependencies', []) and 'nsubj' in f.get('deprel', ''):
                if f.get('pos') == 'PRON':
                    subject_type = 'Pronoun'

                s_feats = f.get('feats', '')
                person = next(
                    (x.split('=')[1] for x in s_feats.split('|') if 'Person=' in x), '3')
                number = next((x.split('=')[1] for x in s_feats.split(
                    '|') if 'Number=' in x), 'Sing')
                gender = next((x.split('=')[1] for x in s_feats.split(
                    '|') if 'Gender=' in x), 'Masc')

                num_map = {'Sing': 'sg', 'Plur': 'pl'}
                gen_map = {'Masc': 'm', 'Fem': 'f'}

                n_code = num_map.get(number, 'sg')
                g_code = gen_map.get(gender, 'm')
                subject_person = f"{person}{n_code}"
                if n_code == 'sg' or person == '3':
                    subject_person = f"{subject_person}_{g_code}"

                if subject_person.endswith('_'):
                    subject_person = subject_person[:-1]

                break

        selected_copula = None

        for cop in self.copulas:
            conditions = cop.get('conditions', [])
            score = 0
            required_score = len(conditions)

            for cond in conditions:
                if cond.startswith('Tense='):
                    req_tense = cond.split('=')[1]
                    if req_tense == tense:
                        score += 1
                elif cond.startswith('SubjectType='):
                    req_type = cond.split('=')[1]
                    if req_type == subject_type:
                        score += 1

            if score >= required_score:
                selected_copula = cop
                break

        if not selected_copula:
            default_cop = next((c for c in self.copulas if c.get(
                'type') == 'present_default'), None)
            selected_copula = default_cop

        if not selected_copula:
            return None

        form = selected_copula.get('form', '')
        if form == 'zero':
            return None

        if selected_copula.get('conjugates', False):
            if selected_copula.get('type') == 'present_pronominal':
                if subject_person in self.pronominal_forms:
                    return self.pronominal_forms[subject_person]

            if engine_ref and engine_ref.tam_handler:
                form = engine_ref.tam_handler.apply_tam(form, feats)

        return form


class InterrogativeHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get('interrogative_system', {})
        self.enabled = self.config.get('enabled', False)
        self.particles = self.config.get('question_particles', [])
        self.detection_rules = self.config.get('detection_rules', {})

    def is_yes_no_question(self, text: str) -> Tuple[bool, Optional[str]]:
        if not self.enabled or not text:
            return False, None

        clean_text = text.strip()
        if not clean_text.endswith('?'):
            return False, None

        wh_words = self.detection_rules.get('wh_words', [])
        alternative_indicators = self.detection_rules.get(
            'alternative_indicators', [])

        lower_text = clean_text.lower()

        for wh in wh_words:
            if lower_text.startswith(wh):
                return False, None

        is_alternative = any(
            ind in lower_text for ind in alternative_indicators)

        if is_alternative:
            return True, 'yes_no_alternative'

        return True, 'yes_no'

    def get_particle(self, q_type: str) -> str:
        for p in self.particles:
            if p.get('type') == q_type:
                return p.get('particle', '')
        if q_type == 'yes_no_alternative':
            for p in self.particles:
                if p.get('type') == 'yes_no':
                    return p.get('particle', '')
        return ""

    def apply_particle(self, words: List[str], q_type: str) -> List[str]:
        if not self.enabled:
            return words

        particle = self.get_particle(q_type)
        if not particle:
            return words

        result = words.copy()
        if result:
            result.insert(0, particle)

        return result
