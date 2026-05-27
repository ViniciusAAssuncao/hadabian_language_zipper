from typing import List, Dict, Optional, Tuple, Set, Union
import hashlib
import re
import random
import unicodedata

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
        self.phonological_rules = self.phonotactics.get(
            'phonological_rules', [])
        self.compiled_rules = self._compile_all_rules()
        self.monophthong_config = self.phonotactics.get(
            'monophthongization', {})
        self.monophthong_enabled = self.monophthong_config.get(
            'enabled', False)
        self.monophthong_rules = self.monophthong_config.get('rules', [])
        self.transition_config = self.phonotactics.get('transition_matrix', {})
        self.transition_enabled = self.transition_config.get('enabled', False)
        self.transition_matrix = self.transition_config.get('matrix', {})
        self.transition_default_weight = self.transition_config.get(
            'default_weight', 1)
        self.aesthetic = profile.get('aesthetic_profile', {})
        self.syllable_dist = self.aesthetic.get('syllable_count_distribution')
        self.cluster_density = self.aesthetic.get('cluster_density', 0.5)

    def _compile_all_rules(self):
        compiled = []
        for rule in self.phonological_rules:
            input_pat = rule.get('input')
            output_pat = rule.get('output')
            register = rule.get('register')
            if input_pat and output_pat is not None:
                regex, repl = self._compile_rule_regex(input_pat, output_pat)
                compiled.append({
                    'regex': regex,
                    'replacement': repl,
                    'register': register
                })
        return compiled

    def _compile_rule_regex(self, input_pat: str, output_pat: str) -> Tuple[str, str]:
        c_set = "".join(
            self.consonants) if self.consonants else "bcdfghjklmnpqrstvwxz"
        v_set = "".join(self.vowels) if self.vowels else "aeiou"
        regex_parts = []
        input_map = []
        i = 0
        group_idx = 1
        while i < len(input_pat):
            char = input_pat[i]
            if char == 'C':
                regex_parts.append(f"([{c_set}])")
                input_map.append({'type': 'C', 'group': group_idx})
                group_idx += 1
            elif char == 'V':
                regex_parts.append(f"([{v_set}])")
                input_map.append({'type': 'V', 'group': group_idx})
                group_idx += 1
            elif char == '$':
                regex_parts.append("$")
            elif char == '^':
                regex_parts.append("^")
            else:
                regex_parts.append(re.escape(char))
            i += 1
        input_regex = "".join(regex_parts)
        replacement_parts = []
        c_counter = 0
        v_counter = 0
        input_cs = [x for x in input_map if x['type'] == 'C']
        input_vs = [x for x in input_map if x['type'] == 'V']
        i = 0
        while i < len(output_pat):
            char = output_pat[i]
            if char == 'C':
                if c_counter < len(input_cs):
                    g = input_cs[c_counter]['group']
                    replacement_parts.append(f"\\g<{g}>")
                    c_counter += 1
                else:
                    replacement_parts.append("C")
            elif char == 'V':
                if v_counter < len(input_vs):
                    g = input_vs[v_counter]['group']
                    replacement_parts.append(f"\\g<{g}>")
                    v_counter += 1
                else:
                    replacement_parts.append("V")
            else:
                replacement_parts.append(char)
            i += 1
        return input_regex, "".join(replacement_parts)

    def apply_monophthongization(self, word: str) -> str:
        if not self.monophthong_enabled or not word:
            return word
        current_word = word
        sorted_rules = sorted(self.monophthong_rules,
                              key=lambda x: x.get('priority', 0), reverse=True)
        for rule in sorted_rules:
            inp = rule.get('input')
            out = rule.get('output')
            if inp and out:
                current_word = current_word.replace(inp, out)
        return current_word

    def apply_rules(self, word: str, register: str) -> str:
        if not word:
            return word
        current_word = word
        for rule in self.compiled_rules:
            if rule['register'] and rule['register'] != register:
                continue
            try:
                current_word = re.sub(
                    rule['regex'], rule['replacement'], current_word)
            except:
                continue
        return current_word

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

    def is_valid_contact(self, c1: str, c2: str) -> bool:
        if c1.lower() in self.vowels:
            return True
        if c2.lower() in self.vowels:
            return True
        cluster = f"{c1}{c2}".lower()
        if cluster in self.forbidden_initial:
            return False
        if not self.enabled:
            return True
        s1 = self.get_sonority(c1)
        s2 = self.get_sonority(c2)
        contact_rules = self.hierarchy_config.get('contact_rules', {})
        dist = s1 - s2
        min_dist = contact_rules.get('min_distance', 0)
        if dist < min_dist:
            return False
        if dist == 0 and not contact_rules.get('allow_plateau', True):
            return False
        if dist < 0 and not contact_rules.get('allow_reversal', False):
            return False
        return True

    def is_valid_final(self, char: str) -> bool:
        return char.lower() not in self.forbidden_final

    def normalize_char(self, char: str) -> str:
        normalized = unicodedata.normalize('NFD', char)
        return "".join(c for c in normalized if unicodedata.category(c) != 'Mn')

    def get_closest_phoneme(self, char: str) -> str:
        char = char.lower()
        if char in self.vowels or char in self.consonants:
            return char
        normalized = self.normalize_char(char)
        if normalized in self.vowels or normalized in self.consonants:
            return normalized
        target_pool = self.vowels if char in 'aeiouyäëïöü' else self.consonants
        if not target_pool:
            target_pool = self.vowels + self.consonants
        char_hash = int(hashlib.sha256(char.encode()).hexdigest(), 16)
        return target_pool[char_hash % len(target_pool)]

    def nativize_word(self, word: str) -> str:
        if not word:
            return word
        nativized = []
        for char in word:
            nativized.append(self.get_closest_phoneme(char))
        result = "".join(nativized)
        result = self.apply_monophthongization(result)
        if result and not self.is_valid_final(result[-1]):
            valid_finals = [c for c in self.consonants if self.is_valid_final(
                c)] + list(self.vowels)
            if valid_finals:
                seed_val = sum(ord(c) for c in result)
                rng = random.Random(seed_val)
                strategy = rng.choice(['drop', 'change', 'add_vowel'])
                if strategy == 'drop':
                    result = result[:-1]
                elif strategy == 'change':
                    result = result[:-1] + rng.choice(valid_finals)
                elif strategy == 'add_vowel' and self.vowels:
                    result = result + rng.choice(list(self.vowels))
        return result

    def get_weighted_choice(self, candidates: List[str], prev_char: Optional[str], rng) -> str:
        if not self.transition_enabled or not prev_char or not candidates:
            return rng.choice(candidates)

        row = self.transition_matrix.get(prev_char.lower(), {})
        weights = []
        for c in candidates:
            weights.append(row.get(c.lower(), self.transition_default_weight))

        total = sum(weights)
        if total <= 0:
            return rng.choice(candidates)

        threshold = rng.random() * total
        current = 0
        for i, w in enumerate(weights):
            current += w
            if current >= threshold:
                return candidates[i]
        return candidates[-1]

    def get_syllable_count(self, rng) -> int:
        if self.syllable_dist:
            counts = []
            weights = []
            for k, v in self.syllable_dist.items():
                counts.append(int(k))
                weights.append(float(v))

            total = sum(weights)
            if total > 0:
                r = rng.random() * total
                upto = 0
                for c, w in zip(counts, weights):
                    if upto + w >= r:
                        return c
                    upto += w
                return counts[-1]

        return rng.randint(self.phonotactics.get('min_syllables', 1),
                           self.phonotactics.get('max_syllables', 3))

    def select_template(self, rng, templates: List[str]) -> str:
        if not templates:
            return "CV"

        if not self.aesthetic:
            return rng.choice(templates)

        complex_templates = [t for t in templates if 'CC' in t]
        simple_templates = [t for t in templates if 'CC' not in t]

        if not complex_templates:
            return rng.choice(simple_templates)
        if not simple_templates:
            return rng.choice(complex_templates)

        if rng.random() < self.cluster_density:
            return rng.choice(complex_templates)
        else:
            return rng.choice(simple_templates)


class SunLetterHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get('determiner_system', {}).get(
            'definite_article', {})
        self.enabled = self.config.get('sun_letter_assimilation', False)
        self.sun_letters = set(self.config.get('sun_letters', []))
        self.forms = set()
        if self.config.get('form'):
            self.forms.add(self.config.get('form').lower())
        if self.config.get('variants'):
            self.forms.update([v.lower()
                               for v in self.config.get('variants', [])])

    def assimilate(self, article: str, next_word: str) -> str:
        if not self.enabled or not article or not next_word:
            return article
        clean_next = "".join(filter(str.isalpha, next_word)).lower()
        if not clean_next:
            return article
        first_char = clean_next[0]
        if first_char not in self.sun_letters:
            return article
        active_form = None
        article_lower = article.lower().strip()
        base_article = article_lower.split(
        )[-1] if ' ' in article_lower else article_lower
        if base_article in self.forms:
            active_form = base_article
        if not active_form:
            for f in self.forms:
                if article_lower.endswith(f):
                    active_form = f
                    break
        if not active_form:
            return article
        match = re.search(r'([bcdfghjklmnpqrstvwxz])(\W*)$',
                          article, re.IGNORECASE)
        if match:
            consonant = match.group(1)
            separator = match.group(2)
            base = article[:match.start(1)]
            new_consonant = first_char
            if consonant.isupper():
                new_consonant = new_consonant.upper()
            return f"{base}{new_consonant}{separator}"
        return article


class SandhiHandler:
    def __init__(self, profile: Dict):
        self.profile = profile
        self.config = profile.get('phonotactics', {}).get('sandhi', {})
        self.enabled = self.config.get('enabled', False)
        self.rules = self.config.get('rules', [])

    def apply_sandhi(self, text: str) -> str:
        if not self.enabled or not text:
            return text
        processed = text
        for rule in self.rules:
            pattern = rule.get('pattern', '')
            replacement = rule.get('replacement', '')
            ignore_case = rule.get('ignore_case', False)
            flags = re.IGNORECASE if ignore_case else 0
            if pattern:
                processed = re.sub(pattern, replacement,
                                   processed, flags=flags)
        return processed


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
