import json
import hashlib
from pathlib import Path
import re
import random
from typing import List, Dict, Optional, Tuple, Set
from syntax_engine import SyntaxEngine, SyntacticFunction
from morphosyntax_analyzer import (
    DependencyParser, ConstituentAnalyzer, ClauseSegmenter,
    AgreementChecker, SyntacticComplexityAnalyzer,
    TopicalizationHandler, FocusStructureHandler, TAMHandler,
    VowelHarmonyHandler, TransitivityAnalyzer, ConsonantMutationHandler
)


class PhonologyHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.phonotactics = profile.get('phonotactics', {})
        self.seed = profile.get('global_seed', 12345)

        self.base_consonants = self.phonotactics.get('consonants')
        if self.base_consonants is None:
            self.base_consonants = self._infer_inventory('consonants')

        self.base_vowels = self.phonotactics.get('vowels')
        if self.base_vowels is None:
            self.base_vowels = self._infer_inventory('vowels')

        self.active_style_name = self.phonotactics.get('active_style', None)
        self.styles = self.phonotactics.get('inventory_styles', {})

        if self.active_style_name and self.active_style_name in self.styles:
            style = self.styles[self.active_style_name]
            self.consonants = style.get('consonants', self.base_consonants)
            self.vowels = style.get('vowels', self.base_vowels)
        else:
            self.consonants = self.base_consonants
            self.vowels = self.base_vowels

        self.hierarchy_config = self.phonotactics.get('sonority_hierarchy', {})
        self.enabled = self.hierarchy_config.get('enabled', False)
        self.scale = self.hierarchy_config.get('scale', {})
        self.onset_rules = self.hierarchy_config.get('onset_rules', {})
        self.coda_rules = self.hierarchy_config.get('coda_rules', {})
        self.forbidden_initial = set(
            self.phonotactics.get('forbidden_initial_clusters', []))
        self.forbidden_final = set(self.phonotactics.get(
            'forbidden_final_consonants', []))

    def _infer_inventory(self, type_key: str) -> str:
        rng = random.Random(self.seed + sum(ord(c) for c in type_key))
        if type_key == 'consonants':
            pool = [chr(i) for i in range(97, 123) if chr(i) not in 'aeiou']
            count = rng.randint(5, 18)
            return "".join(sorted(rng.sample(pool, count)))
        elif type_key == 'vowels':
            pool = 'aeiouy'
            count = rng.randint(3, 6)
            return "".join(sorted(rng.sample(pool, count)))
        return ""

    def get_sonority(self, char: str) -> int:
        return self.scale.get(char.lower(), 0)

    def is_valid_onset_cluster(self, c1: str, c2: str) -> bool:
        cluster = f"{c1}{c2}".lower()
        if cluster in self.forbidden_initial:
            return False

        if not self.enabled:
            return True

        s1 = self.get_sonority(c1)
        s2 = self.get_sonority(c2)
        dist = s2 - s1
        min_dist = self.onset_rules.get('min_distance', 1)

        if dist < min_dist:
            return False
        if dist == 0 and not self.onset_rules.get('allow_plateau', False):
            return False
        if dist < 0 and not self.onset_rules.get('allow_reversal', False):
            return False

        return True

    def is_valid_coda_cluster(self, c1: str, c2: str) -> bool:
        if not self.enabled:
            return True

        s1 = self.get_sonority(c1)
        s2 = self.get_sonority(c2)
        dist = s1 - s2
        min_dist = self.coda_rules.get('min_distance', 0)

        if dist < min_dist:
            return False
        if dist == 0 and not self.coda_rules.get('allow_plateau', True):
            return False
        if dist < 0 and not self.coda_rules.get('allow_reversal', True):
            return False

        return True

    def is_valid_final(self, char: str) -> bool:
        return char.lower() not in self.forbidden_final


class StressHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get('stress_system', {})
        self.enabled = self.config.get('enabled', False)
        self.type = self.config.get('type', 'fixed')
        self.position = self.config.get('position', 'penultimate')
        self.graphic = self.config.get('graphic_accent', False)
        self.map = self.config.get(
            'accent_map', {'a': 'á', 'e': 'é', 'i': 'í', 'o': 'ó', 'u': 'ú'})
        self.phonotactics = profile.get('phonotactics', {})

        self.vowels = self.phonotactics.get('vowels')
        if not self.vowels:
            ph_handler = PhonologyHandler(profile)
            self.vowels = ph_handler.base_vowels
        self.vowels = set(self.vowels)

    def apply_stress(self, word: str) -> str:
        if not self.enabled or not word:
            return word

        vowel_indices = [i for i, char in enumerate(
            word) if char.lower() in self.vowels]
        if not vowel_indices:
            return word

        target_vowel_idx = -1

        if self.type == 'fixed':
            if self.position == 'ultimate':
                target_vowel_idx = vowel_indices[-1]
            elif self.position == 'penultimate':
                target_vowel_idx = vowel_indices[-2] if len(
                    vowel_indices) >= 2 else vowel_indices[-1]
            elif self.position == 'antepenultimate':
                target_vowel_idx = vowel_indices[-3] if len(vowel_indices) >= 3 else (
                    vowel_indices[-2] if len(vowel_indices) >= 2 else vowel_indices[-1])
            elif self.position == 'initial':
                target_vowel_idx = vowel_indices[0]

        elif self.type == 'weight':
            if len(vowel_indices) < 2:
                target_vowel_idx = vowel_indices[-1]
            else:
                penult_idx = vowel_indices[-2]
                ult_idx = vowel_indices[-1]
                inter_segment = word[penult_idx+1:ult_idx]

                is_heavy = False
                if len(inter_segment) > 1:
                    is_heavy = True

                if is_heavy:
                    target_vowel_idx = penult_idx
                else:
                    target_vowel_idx = vowel_indices[-3] if len(
                        vowel_indices) >= 3 else penult_idx

        if target_vowel_idx != -1 and self.graphic:
            chars = list(word)
            v = chars[target_vowel_idx]
            lower_v = v.lower()
            if lower_v in self.map:
                replacement = self.map[lower_v]
                if v.isupper():
                    replacement = replacement.upper()
                chars[target_vowel_idx] = replacement
                return "".join(chars)

        return word


class FalseCognateHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get('false_cognates', {})
        self.enabled = self.config.get('enabled', False)
        self.manual_pairs = self.config.get('manual_pairs', {})
        self.natural_chance = self.config.get('natural_confusion_chance', 0.0)

    def get_manual_target(self, lemma: str) -> Optional[str]:
        if not self.enabled:
            return None
        return self.manual_pairs.get(lemma)

    def should_collide_naturally(self, lemma: str, global_seed: int) -> Optional[int]:
        if not self.enabled or self.natural_chance <= 0:
            return None

        input_str = f"{lemma}_collision_check_{global_seed}"
        hash_obj = hashlib.sha256(input_str.encode())
        hash_val = int(hash_obj.hexdigest(), 16)

        if (hash_val % 1000) / 1000.0 < self.natural_chance:
            return hash_val % 100
        return None


class PolysemyHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get('polysemy_rules', {})
        self.enabled = self.config.get('enabled', False)
        self.merges = self.config.get('merges', {})
        self.splits = self.config.get('splits', {})

    def resolve_lemma(self, lemma: str, context: Dict) -> str:
        if not self.enabled:
            return lemma

        clean_lemma = lemma.lower().strip()

        if clean_lemma in self.merges:
            return self.merges[clean_lemma]

        if clean_lemma in self.splits:
            rules = self.splits[clean_lemma]
            context_feats = set(context.get('feats', '').split('|'))
            context_deprel = context.get('deprel', '')

            for rule in rules:
                rule_match = rule.get('rules', {})
                match_feats = set(rule_match.get('feats', []))
                match_deprel = rule_match.get('deprel', [])

                feats_ok = True
                if match_feats:
                    if not match_feats.issubset(context_feats):
                        feats_ok = False

                deprel_ok = True
                if match_deprel:
                    if context_deprel not in match_deprel:
                        deprel_ok = False

                if feats_ok and deprel_ok:
                    suffix = rule.get('target_suffix', '')
                    return f"{clean_lemma}{suffix}"

        return clean_lemma


class SemanticFieldHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get('semantic_fields', {})
        self.enabled = self.config.get('enabled', False)
        self.manual_groups = self.config.get('manual_groups', {})
        self.use_nltk = self.config.get('use_nltk', False)
        self.nltk_ready = False
        if self.enabled and self.use_nltk:
            try:
                import nltk
                from nltk.corpus import wordnet
                try:
                    wordnet.synsets('teste', lang='por')
                except LookupError:
                    nltk.download('wordnet')
                    nltk.download('omw-1.4')
                self.wn = wordnet
                self.nltk_ready = True
            except ImportError:
                self.nltk_ready = False

    def get_semantic_root(self, word: str) -> Optional[str]:
        if not self.enabled:
            return None

        clean_word = word.lower()

        if clean_word in self.manual_groups:
            return self.manual_groups[clean_word]

        if self.nltk_ready:
            try:
                synsets = self.wn.synsets(clean_word, lang='por')
                if not synsets:
                    return None

                synset = synsets[0]
                hypernyms = synset.hypernyms()

                if hypernyms:
                    hyper_lemma = hypernyms[0].lemmas(lang='por')
                    if hyper_lemma:
                        return hyper_lemma[0].name()

                    english_lemma = hypernyms[0].lemmas()[0].name()
                    return english_lemma
            except:
                pass

        return None


class AffixHandler:
    def __init__(self, profile: Dict, harmony_handler: Optional[VowelHarmonyHandler] = None):
        self.profile = profile
        self.affix_system = profile.get('affix_system', {})
        self.enabled = self.affix_system.get('enabled', False)
        self.derivation_rules = self.affix_system.get('derivation_rules', [])
        self.harmony_handler = harmony_handler

    def get_derivation_rule(self, from_pos: str, to_pos: str) -> Optional[Dict]:
        if not self.enabled:
            return None
        for rule in self.derivation_rules:
            if rule['from_pos'] == from_pos and rule['to_pos'] == to_pos:
                return rule
        return None

    def apply_affix(self, word: str, rule: Dict) -> str:
        affix = rule.get('affix', '')
        position = rule.get('position', 'suffix')

        if not affix:
            return word

        if position == 'suffix' and self.harmony_handler and self.harmony_handler.enabled:
            affix = self.harmony_handler.apply_harmony(word, affix)

        if position == 'prefix':
            return f"{affix}{word}"
        elif position == 'suffix':
            return f"{word}{affix}"
        elif position == 'infix':
            mid = len(word) // 2
            return f"{word[:mid]}{affix}{word[mid:]}"
        return word


class DegreeHandler:
    def __init__(self, profile: Dict, harmony_handler: Optional[VowelHarmonyHandler] = None):
        self.profile = profile
        self.config = profile.get('degree_system', {})
        self.enabled = self.config.get('enabled', False)
        self.rules = self.config.get('rules', {})
        self.source_rules = self.config.get('source_rules', [])
        self.harmony_handler = harmony_handler

    def detect_degree(self, word: str, lemma: str, feats_str: str) -> Optional[str]:
        if not self.enabled:
            return None

        if feats_str and feats_str != '_':
            feats = feats_str.split('|')
            if 'Degree=Dim' in feats:
                return 'diminutive'
            if 'Degree=Aug' in feats:
                return 'augmentative'
            if 'Degree=Abs' in feats or 'Degree=Sup' in feats:
                return 'superlative'

        w = word.lower()
        for rule in self.source_rules:
            suffix = rule.get('suffix', '')
            if suffix and w.endswith(suffix):
                return rule.get('type')

        return None

    def get_base_lemma(self, word: str, lemma: str, degree_type: str, feats_str: str) -> str:
        if not degree_type:
            return lemma

        w = word.lower()

        for rule in self.source_rules:
            if rule.get('type') == degree_type:
                suffix = rule.get('suffix', '')
                if suffix and w.endswith(suffix):
                    replacement = rule.get('replacement', '')
                    return w[:-len(suffix)] + replacement

        if feats_str and feats_str != '_':
            return lemma

        return lemma

    def apply_degree(self, word: str, degree_type: str) -> str:
        if not self.enabled or not degree_type:
            return word
        rule = self.rules.get(degree_type)
        if not rule:
            return word
        affix = rule.get('affix', '')
        position = rule.get('position', 'suffix')

        if position == 'suffix' and self.harmony_handler and self.harmony_handler.enabled:
            affix = self.harmony_handler.apply_harmony(word, affix)

        if position == 'suffix':
            return f"{word}{affix}"
        elif position == 'prefix':
            return f"{affix}{word}"
        return word


class ReduplicationHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get('reduplication', {})
        self.enabled = self.config.get('enabled', False)
        self.rules = self.config.get('rules', [])
        self.phonotactics = profile.get('phonotactics', {})

        self.vowels = self.phonotactics.get('vowels')
        self.consonants = self.phonotactics.get('consonants')

        if not self.vowels or not self.consonants:
            ph = PhonologyHandler(profile)
            if not self.vowels:
                self.vowels = ph.base_vowels
            if not self.consonants:
                self.consonants = ph.base_consonants

    def apply_reduplication(self, word: str, feats_str: str, pos: str = None) -> str:
        if not self.enabled or not word or not feats_str or feats_str == '_':
            return word

        feats = set(feats_str.split('|'))

        for rule in self.rules:
            allowed_pos = rule.get('pos')
            if allowed_pos and pos:
                if pos not in allowed_pos:
                    continue

            rule_feats = set(rule.get('features', []))
            if rule_feats.issubset(feats):
                method = rule.get('method', 'whole_word')
                separator = rule.get('separator', '')

                if method == 'whole_word':
                    return f"{word}{separator}{word}"
                elif method == 'first_syllable':
                    syllable = self._get_first_syllable(word)
                    if syllable:
                        return f"{syllable}{separator}{word}"

        return word

    def _get_first_syllable(self, word: str) -> str:
        import re
        c_set = re.escape(self.consonants)
        v_set = re.escape(self.vowels)
        match = re.match(f"^[{c_set}]*[{v_set}]+", word, re.IGNORECASE)
        if match:
            return match.group(0)
        return ""


class OriginalLanguageEngine:
    def __init__(self, profile_path: str):
        with open(profile_path, 'r', encoding='utf-8') as f:
            self.profile = json.load(f)
        self.profile_id = self.profile.get('id', 'unknown')
        self.global_seed = self.profile.get('global_seed', 12345)

        self.phonology_handler = PhonologyHandler(self.profile)
        self.phonotactics = self.profile.get('phonotactics', {})

        self.vowels = self.phonology_handler.vowels
        self.consonants = self.phonology_handler.consonants

        self.templates = self.phonotactics.get('syllable_templates')
        if not self.templates:
            self.templates = self._infer_templates()

        self.syntax_engine = SyntaxEngine(profile_path)
        self.dependency_parser = DependencyParser()
        self.constituent_analyzer = ConstituentAnalyzer()
        self.clause_segmenter = ClauseSegmenter()
        self.agreement_checker = AgreementChecker(self.profile)
        self.complexity_analyzer = SyntacticComplexityAnalyzer()
        self.topicalization_handler = TopicalizationHandler(self.profile)
        self.focus_handler = FocusStructureHandler(self.profile)
        self.vowel_harmony_handler = VowelHarmonyHandler(self.profile)
        self.affix_handler = AffixHandler(
            self.profile, self.vowel_harmony_handler)
        self.degree_handler = DegreeHandler(
            self.profile, self.vowel_harmony_handler)
        self.tam_handler = TAMHandler(self.profile)
        self.reduplication_handler = ReduplicationHandler(self.profile)
        self.semantic_handler = SemanticFieldHandler(self.profile)
        self.polysemy_handler = PolysemyHandler(self.profile)
        self.false_cognate_handler = FalseCognateHandler(self.profile)
        self.stress_handler = StressHandler(self.profile)
        self.transitivity_analyzer = TransitivityAnalyzer()
        self.mutation_handler = ConsonantMutationHandler(self.profile)
        self.functional_config = self.profile.get('functional_particles', {})
        self.word_cache: Dict[str, str] = {}
        self.load_word_cache()

    def _infer_templates(self) -> List[str]:
        rng = random.Random(self.global_seed + 999)
        options = ['CV', 'CVC', 'V', 'VC', 'CCV', 'CCVC', 'CVCC']
        count = rng.randint(2, 4)
        return sorted(rng.sample(options, count))

    def load_word_cache(self):
        cache_dir = Path("./cache")
        if not cache_dir.exists():
            cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f"{self.profile_id}_words.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    self.word_cache = json.load(f)
            except:
                self.word_cache = {}
        else:
            self.word_cache = {}

    def save_word_cache(self):
        cache_dir = Path("./cache")
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f"{self.profile_id}_words.json"
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.word_cache, f, indent=2, ensure_ascii=False)

    def process_text(self, text: str) -> str:
        reordered_text, functions_info = self.syntax_engine.process_text(text)
        final_sentences = []

        case_system = self.profile.get('case_system', {})
        preposition_handling = case_system.get(
            'preposition_handling', 'coexist')

        topicalization_config = self.profile.get('topicalization', {})
        topic_enabled = topicalization_config.get('enabled', False)
        topic_marker = topicalization_config.get('topic_marker', 'wa')

        focus_config = self.profile.get('focus_structure', {})
        focus_enabled = focus_config.get('enabled', False)
        object_focus_marker = focus_config.get('object_focus_marker', 'ko')
        suppress_case_on_focus = focus_config.get('suppress_case', False)

        for sent_data in functions_info:
            ordered_functions = sent_data['functions']
            translated_words = []

            last_func = None

            transitivity_map = self.transitivity_analyzer.analyze(
                ordered_functions)

            topic_idx = self.topicalization_handler.identify_topic(
                ordered_functions)

            for func in ordered_functions:
                orig_word = func.get("word", "")
                lemma = func.get("lemma", "")
                pos = func.get("pos", "")
                feats = func.get("feats", "")
                syntactic_func = func.get("function", "")
                deprel = func.get("deprel", "")
                is_named_entity = func.get("named_entity", False)

                if preposition_handling == 'replace' and pos == 'ADP':
                    continue

                clean_word_lower = self._clean_word(orig_word).lower()
                raw_lemma = lemma if lemma else clean_word_lower
                raw_lemma = raw_lemma.lower()

                if pos == 'PUNCT':
                    translated_words.append(orig_word)
                    last_func = func
                    continue

                if syntactic_func in {SyntacticFunction.QUANTIFIER, SyntacticFunction.VERB_PARTICLE, SyntacticFunction.INTENSIFIER}:
                    mapping = self.functional_config.get(raw_lemma, {})
                    translated_word = ""
                    if syntactic_func == SyntacticFunction.QUANTIFIER:
                        translated_word = mapping.get(
                            'noun_word', self._generate_deterministic_word(f'{raw_lemma}_quant'))
                    elif syntactic_func == SyntacticFunction.VERB_PARTICLE:
                        translated_word = mapping.get(
                            'verb_word', self._generate_deterministic_word(f'{raw_lemma}_verb'))
                    elif syntactic_func == SyntacticFunction.INTENSIFIER:
                        translated_word = mapping.get(
                            'adj_word', self._generate_deterministic_word(f'{raw_lemma}_intens'))

                    if translated_word:
                        if self.mutation_handler.enabled:
                            prev_word = translated_words[-1] if translated_words else None
                            translated_word = self.mutation_handler.apply_mutation(
                                translated_word, prev_word, last_func)

                        translated_words.append(translated_word)
                        last_func = func
                        continue

                degree_type = None
                if self.degree_handler.enabled:
                    degree_type = self.degree_handler.detect_degree(
                        clean_word_lower, raw_lemma, feats)

                base_lemma_for_translation = raw_lemma

                if degree_type:
                    base_lemma_for_translation = self.degree_handler.get_base_lemma(
                        clean_word_lower, raw_lemma, degree_type, feats)

                if self.polysemy_handler.enabled:
                    base_lemma_for_translation = self.polysemy_handler.resolve_lemma(
                        base_lemma_for_translation, func
                    )

                target_lemma = base_lemma_for_translation
                current_pos = pos
                applied_derivation_rule = None

                if self.affix_handler.enabled and not degree_type:
                    source_suffixes = self.profile.get(
                        'affix_system', {}).get('source_suffixes', [])
                    for suffix_rule in source_suffixes:
                        suf_str = suffix_rule.get('suffix', '')
                        input_pos = suffix_rule.get('input_pos', 'NOUN')

                        if current_pos == input_pos and base_lemma_for_translation.endswith(suf_str):
                            replacement = suffix_rule.get('replacement', '')
                            possible_stem = base_lemma_for_translation[:-len(
                                suf_str)] + replacement
                            target_pos_req = suffix_rule.get(
                                'target_pos', 'VERB')

                            target_lemma = possible_stem

                            lemma_pos = self.syntax_engine.estimate_lemma_pos(
                                target_lemma)
                            applied_derivation_rule = self.affix_handler.get_derivation_rule(
                                lemma_pos, current_pos)
                            break

                translated_root = None

                if target_lemma not in self.word_cache:
                    self.word_cache[target_lemma] = self._generate_deterministic_word(
                        target_lemma)

                translated_root = self.word_cache[target_lemma]

                current_form = translated_root

                if applied_derivation_rule:
                    current_form = self.affix_handler.apply_affix(
                        current_form, applied_derivation_rule)

                if degree_type:
                    current_form = self.degree_handler.apply_degree(
                        current_form, degree_type)

                is_topic = False
                if topic_enabled and topic_idx is not None:
                    if func['index'] == topic_idx:
                        is_topic = True

                is_focus = False
                if focus_enabled:
                    if syntactic_func == SyntacticFunction.OBJECT:
                        is_focus = True

                apply_case = True
                if is_focus and suppress_case_on_focus:
                    apply_case = False

                if apply_case:
                    is_transitive = transitivity_map.get(func['index'], False)
                    current_form = self.syntax_engine.case_morphology.apply_case(
                        current_form,
                        syntactic_func,
                        self.syntax_engine.word_order,
                        deprel,
                        clause_transitivity=is_transitive
                    )

                if is_topic and topic_marker:
                    current_form = f"{current_form} {topic_marker}"

                if is_focus and object_focus_marker:
                    current_form = f"{current_form} {object_focus_marker}"

                if self.tam_handler.enabled and (pos in {'VERB', 'AUX'} or 'Tense=' in feats or 'Mood=' in feats or 'Aspect=' in feats or 'VerbForm=' in feats):
                    tam_feats = feats
                    if is_focus:
                        tam_feats = f"{tam_feats}|Focus=Yes"

                    current_form = self.tam_handler.apply_tam(
                        current_form, tam_feats, func, ordered_functions)

                if self.reduplication_handler.enabled:
                    current_form = self.reduplication_handler.apply_reduplication(
                        current_form, feats, pos=current_pos)

                if self.stress_handler.enabled:
                    current_form = self.stress_handler.apply_stress(
                        current_form)

                if self.mutation_handler.enabled:
                    prev_word = translated_words[-1] if translated_words else None
                    current_form = self.mutation_handler.apply_mutation(
                        current_form, prev_word, last_func)

                if is_named_entity:
                    current_form = current_form.capitalize()

                if orig_word[0].isupper() and pos == 'PROPN':
                    current_form = current_form.capitalize()

                translated_words.append(current_form)
                last_func = func

            final_sentence_tokens = self.syntax_engine._glue_tokens(
                translated_words, ordered_functions)

            if final_sentence_tokens:
                first = final_sentence_tokens[0]
                if first:
                    final_sentence_tokens[0] = first[0].upper() + first[1:]

            final_sentences.append(' '.join(final_sentence_tokens))

        self.save_word_cache()
        return ' '.join(final_sentences)

    def process_with_analysis(self, text: str) -> Dict:
        reordered_text, functions_info = self.syntax_engine.process_text(text)
        return {
            'original': text,
            'reordered': reordered_text,
            'translated': self.process_text(text),
            'syntax_info': functions_info,
            'word_order': self.syntax_engine.word_order,
            'cache_size': len(self.word_cache)
        }

    def _clean_word(self, word: str) -> str:
        import re
        return re.sub(r'[^\w]', '', word)

    def _extract_punctuation(self, word: str) -> Tuple[str, str]:
        import re
        prefix = ""
        suffix = ""
        if word:
            m_start = re.match(r"^([^\w]*)", word)
            if m_start:
                prefix = m_start.group(1)
            m_end = re.search(r"([^\w]*)$", word)
            if m_end:
                suffix = m_end.group(1)
        return prefix, suffix

    def _mutate_word(self, word: str, seed: int) -> str:
        if not word or len(word) < 2:
            return word

        import random
        random.seed(seed)

        chars = list(word)
        mutable_indices = [i for i, c in enumerate(chars) if c.isalpha()]
        if not mutable_indices:
            return word

        idx_to_mutate = random.choice(mutable_indices)
        original_char = chars[idx_to_mutate]

        is_vowel = original_char.lower() in self.vowels

        if is_vowel:
            if len(self.vowels) > 1:
                options = [v for v in self.vowels if v !=
                           original_char.lower()]
                if options:
                    new_char = random.choice(options)
                    chars[idx_to_mutate] = new_char
        else:
            if len(self.consonants) > 1:
                options = [c for c in self.consonants if c !=
                           original_char.lower()]
                if options:
                    new_char = random.choice(options)
                    chars[idx_to_mutate] = new_char

        return "".join(chars)

    def _generate_deterministic_word(self, word: str) -> str:
        clean_word = "".join(filter(str.isalpha, word.lower()))
        if not clean_word:
            return word

        manual_target = self.false_cognate_handler.get_manual_target(
            clean_word)
        collision_bucket = self.false_cognate_handler.should_collide_naturally(
            clean_word, self.global_seed)

        if manual_target:
            if manual_target in self.word_cache:
                base_word = self.word_cache[manual_target]
            else:
                base_word = self._generate_deterministic_word(manual_target)

            mutation_seed = int(hashlib.sha256(
                f"{clean_word}_manual_mut_{self.global_seed}".encode()).hexdigest(), 16)
            return self._mutate_word(base_word, mutation_seed)

        elif collision_bucket is not None:
            phantom_base_key = f"PHANTOM_BUCKET_{collision_bucket}"
            if phantom_base_key in self.word_cache:
                base_word = self.word_cache[phantom_base_key]
            else:
                base_word = self._generate_deterministic_word(phantom_base_key)
                self.word_cache[phantom_base_key] = base_word

            mutation_seed = int(hashlib.sha256(
                f"{clean_word}_nat_mut_{self.global_seed}".encode()).hexdigest(), 16)
            return self._mutate_word(base_word, mutation_seed)

        root_semantic = self.semantic_handler.get_semantic_root(clean_word)
        base_word_str = clean_word
        is_derived = False

        if root_semantic and root_semantic != clean_word:
            if root_semantic in self.word_cache:
                base_conlang_word = self.word_cache[root_semantic]
            else:
                base_conlang_word = self._generate_deterministic_word(
                    root_semantic)
                self.word_cache[root_semantic] = base_conlang_word

            base_word_str = base_conlang_word
            is_derived = True

        input_str = f"{base_word_str}_{self.global_seed}_{self.profile_id}"
        if not is_derived:
            input_str = f"{clean_word}_{self.global_seed}_{self.profile_id}"

        hash_obj = hashlib.sha256(input_str.encode())
        hash_int = int(hash_obj.hexdigest(), 16)
        import random
        random.seed(hash_int)

        if is_derived:
            split_idx = max(1, int(len(base_conlang_word) * 0.6))
            prefix = base_conlang_word[:split_idx]

            suffix_seed = int(hashlib.sha256(
                clean_word.encode()).hexdigest(), 16)
            random.seed(hash_int + suffix_seed)

            generated_word = prefix
            template = random.choice(self.templates)

            in_onset = True
            prev_consonant = None

            for char_type in template:
                if char_type == 'C':
                    if self.consonants:
                        candidates = list(self.consonants)
                        random.shuffle(candidates)

                        chosen_c = None

                        if prev_consonant:
                            for cand in candidates:
                                if in_onset:
                                    if self.phonology_handler.is_valid_onset_cluster(prev_consonant, cand):
                                        chosen_c = cand
                                        break
                                else:
                                    if self.phonology_handler.is_valid_coda_cluster(prev_consonant, cand):
                                        chosen_c = cand
                                        break

                            if not chosen_c:
                                chosen_c = candidates[0]
                        else:
                            for cand in candidates:
                                if not in_onset and not self.phonology_handler.is_valid_final(cand):
                                    continue
                                chosen_c = cand
                                break
                            if not chosen_c:
                                chosen_c = candidates[0]

                        generated_word += chosen_c
                        prev_consonant = chosen_c
                elif char_type == 'V':
                    if self.vowels:
                        generated_word += random.choice(list(self.vowels))
                    in_onset = False
                    prev_consonant = None

            return generated_word

        num_syllables = random.randint(
            self.phonotactics.get('min_syllables', 1),
            self.phonotactics.get('max_syllables', 3)
        )

        generated_word = ""
        for _ in range(num_syllables):
            template = random.choice(self.templates)

            in_onset = True
            prev_consonant = None

            for i, char_type in enumerate(template):
                if char_type == 'C':
                    if self.consonants:
                        candidates = list(self.consonants)
                        random.shuffle(candidates)

                        chosen_c = None

                        if prev_consonant:
                            for cand in candidates:
                                if in_onset:
                                    if self.phonology_handler.is_valid_onset_cluster(prev_consonant, cand):
                                        chosen_c = cand
                                        break
                                else:
                                    if self.phonology_handler.is_valid_coda_cluster(prev_consonant, cand):
                                        chosen_c = cand
                                        break

                            if not chosen_c:
                                chosen_c = candidates[0]
                        else:
                            is_final_in_syllable = True
                            for j in range(i+1, len(template)):
                                if template[j] == 'V':
                                    is_final_in_syllable = False
                                    break

                            for cand in candidates:
                                if is_final_in_syllable and not self.phonology_handler.is_valid_final(cand):
                                    continue
                                chosen_c = cand
                                break

                            if not chosen_c:
                                chosen_c = candidates[0]

                        generated_word += chosen_c
                        prev_consonant = chosen_c
                elif char_type == 'V':
                    if self.vowels:
                        generated_word += random.choice(list(self.vowels))
                    in_onset = False
                    prev_consonant = None

        return generated_word if generated_word else word

    def analyze_sentence_structure(self, text: str) -> Dict:
        reordered_text, functions_info = self.syntax_engine.process_text(text)
        words = reordered_text.split()
        tagged = self.syntax_engine.pos_tagger.tag_sentence(
            words) if hasattr(self.syntax_engine, 'pos_tagger') else []
        dependencies = self.dependency_parser.parse(tagged)
        constituents = self.constituent_analyzer.identify_constituents(tagged)
        clauses = self.clause_segmenter.segment(words)
        functions = []
        if functions_info:
            for info in functions_info:
                if 'functions' in info:
                    functions.extend(info['functions'])
        agreement_violations = self.agreement_checker.check_agreement(
            functions)
        complexity_metrics = self.complexity_analyzer.analyze(
            functions, dependencies)
        return {
            'original_text': text,
            'reordered_text': reordered_text,
            'tagged_words': tagged,
            'dependencies': dependencies,
            'constituents': constituents,
            'clauses': clauses,
            'functions': functions,
            'agreement_violations': agreement_violations,
            'complexity': complexity_metrics,
            'word_order': self.syntax_engine.word_order
        }

    def get_statistics(self) -> Dict:
        syntax_stats = self.syntax_engine.get_statistics()
        return {
            'profile_id': self.profile_id,
            'word_order': self.syntax_engine.word_order,
            'cached_words': len(self.word_cache),
            'syntax': syntax_stats,
            'phonotactics': {
                'vowels': len(self.vowels),
                'consonants': len(self.consonants),
                'templates': len(self.templates)
            }
        }
