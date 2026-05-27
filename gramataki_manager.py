import json
import hashlib
import random
import re
from pathlib import Path
from typing import Dict, List, Optional
from constants import PORTUGUESE_STOP_WORDS

class GramatakiManager:
    def __init__(self, profile: Dict, engine_ref):
        self.profile = profile
        self.engine = engine_ref
        self.profile_id = profile.get('id', 'unknown')
        self.dictionary: Dict[str, Dict] = {}
        self.storage_path = Path(
            f"./gramatakis/{self.profile_id}_gramataki.json")

        self.caches_dir = Path("./cultures/caches")
        self.caches_dir.mkdir(parents=True, exist_ok=True)
        self.unified_pools_path = self.caches_dir / \
            f"{self.profile_id}_pools_cache.json"
        self.culture_names_path = self.caches_dir / \
            f"{self.profile_id}_names.json"
        self.unified_pools = {}
        self.culture_names = {}

        self.load_dictionary()
        self.load_culture_caches()

    def load_dictionary(self):
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    self.dictionary = json.load(f)
            except Exception:
                self.dictionary = {}
        else:
            self.dictionary = {}

    def load_culture_caches(self):
        self.unified_pools = {}
        if self.unified_pools_path.exists():
            try:
                with open(self.unified_pools_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.unified_pools = data.get(self.profile_id, {})
            except:
                pass
        if self.culture_names_path.exists():
            try:
                with open(self.culture_names_path, 'r', encoding='utf-8') as f:
                    self.culture_names = json.load(f)
            except:
                pass

    def save_dictionary(self):
        if not self.storage_path.parent.exists():
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(self.dictionary, f, indent=2, ensure_ascii=False)

    def save_unified_pools(self):
        all_pools = {}
        if self.unified_pools_path.exists():
            try:
                with open(self.unified_pools_path, 'r', encoding='utf-8') as f:
                    all_pools = json.load(f)
            except:
                pass
        all_pools[self.profile_id] = self.unified_pools
        with open(self.unified_pools_path, 'w', encoding='utf-8') as f:
            json.dump(all_pools, f, indent=4, ensure_ascii=False)

    def save_culture_name(self, name: str, name_type: str):
        if name_type not in self.culture_names:
            self.culture_names[name_type] = []
        if name not in self.culture_names[name_type]:
            self.culture_names[name_type].append(name)
            with open(self.culture_names_path, 'w', encoding='utf-8') as f:
                json.dump(self.culture_names, f, indent=4, ensure_ascii=False)

    def save_entry(self, entry: Dict):
        lemma = entry.get('lemma')
        if lemma:
            self.dictionary[lemma] = entry
            self.save_dictionary()

    def _get_pool_words(self, pool_key: str, culture: Dict) -> List[str]:
        words = set()
        if pool_key in culture.get('semantic_pools', {}):
            words.update(culture['semantic_pools'][pool_key])
        if pool_key in self.unified_pools:
            words.update(self.unified_pools[pool_key])
        if pool_key in self.culture_names:
            words.update(self.culture_names[pool_key])
        return list(words)

    def generate_onomastic_name(self, culture: Dict, formula_id: str, gender: str) -> Dict:
        formula = culture.get('formulas', {}).get(formula_id, [])
        components_rules = culture.get('components_rules', {})
        filters = culture.get('phonological_filters', {})
        generated_parts = []
        etymology = []
        for comp_name in formula:
            rule = components_rules.get(comp_name)
            if not rule:
                continue
            comp_result = self._generate_component(
                comp_name, rule, culture, gender)
            if comp_result and comp_result.get('word'):
                generated_parts.append(comp_result['word'])
                etymology.append({
                    'component': comp_result['word'],
                    'meaning': comp_result.get('meaning', ''),
                    'type': comp_name
                })
        final_name = self._apply_phonological_filters(generated_parts, filters)
        return {
            'name': final_name,
            'etymology': etymology
        }

    def _generate_component(self, comp_name: str, rule: Dict, culture: Dict, gender: str) -> Dict:
        if comp_name in self.culture_names and random.random() < 0.25:
            w1 = random.choice(self.culture_names[comp_name])
            return {'word': w1, 'meaning': f"{w1} (Tradicional)"}

        strategies = rule.get('generation_strategies', [])
        if strategies:
            weights = [s.get('weight', 1.0) for s in strategies]
            strategy = random.choices(strategies, weights=weights, k=1)[0]
            stype = strategy.get('type')
            if stype == 'compound':
                p1_words = self._get_pool_words(
                    strategy.get('pool_1'), culture)
                p2_words = self._get_pool_words(
                    strategy.get('pool_2'), culture)
                if p1_words and p2_words:
                    w1 = random.choice(p1_words)
                    w2 = random.choice(p2_words)
                    cw1 = self.engine._get_word_form(w1, skip_cache=True)
                    cw2 = self.engine._get_word_form(w2, skip_cache=True)
                    if self.engine.compounding_handler.enabled:
                        final_w = self.engine.compounding_handler.construct_compound(
                            [cw1, cw2], self.engine)
                    else:
                        final_w = cw1 + cw2
                    return {'word': final_w, 'meaning': f"{w1} + {w2}"}
            elif stype == 'verbal_sentence':
                pattern = strategy.get('pattern', [])
                if len(pattern) >= 2:
                    p1_words = self._get_pool_words(pattern[0], culture)
                    p2_words = self._get_pool_words(pattern[1], culture)
                    if p1_words and p2_words:
                        w1 = random.choice(p1_words)
                        w2 = random.choice(p2_words)
                        cw1 = self.engine._get_word_form(
                            w1, pos='VERB', skip_cache=True)
                        cw2 = self.engine._get_word_form(
                            w2, pos='NOUN', skip_cache=True)
                        return {'word': cw1 + cw2, 'meaning': f"{w1} {w2}"}
            elif stype == 'abstract_derivation':
                pool_key = strategy.get('pool', 'concept_noun')
                p_words = self._get_pool_words(pool_key, culture)
                if p_words:
                    w1 = random.choice(p_words)
                    cw1 = self.engine._get_word_form(w1, skip_cache=True)
                    if self.engine.affix_handler.enabled:
                        der_rule = self.engine.affix_handler.get_derivation_rule(
                            "NOUN", "NOUN", strategy.get('derivation_type', 'abstract_noun'))
                        if der_rule:
                            cw1 = self.engine.affix_handler.apply_affix(
                                cw1, der_rule)
                    return {'word': cw1, 'meaning': f"{w1} (Abstrato)"}

        rel_type = rule.get('type')
        if rel_type == 'literal':
            val = rule.get('value', '')
            return {'word': val, 'meaning': rule.get('meaning', val)}
        if rel_type == 'relational':
            target = rule.get('target')
            connector = rule.get('connector', '')

            gender_connectors = rule.get('gender_connectors', {})
            if gender and gender in gender_connectors:
                connector = gender_connectors[gender]
            elif gender == 'Feminino' and 'connector_female' in rule:
                connector = rule.get('connector_female')

            target_rule = culture.get('components_rules', {}).get(target)
            if target_rule:
                target_res = self._generate_component(
                    target, target_rule, culture, gender)
                if target_res and target_res.get('word'):
                    final_w = f"{connector} {target_res['word']}" if connector else target_res['word']
                    meaning_str = f"{connector} ({target_res['meaning']})" if connector else target_res['meaning']
                    return {'word': final_w.strip(), 'meaning': meaning_str.strip()}

        elif rel_type == 'pool_selection':
            target_pool = rule.get('pool')
            p_words = self._get_pool_words(target_pool, culture)
            if p_words:
                w1 = random.choice(p_words)
                cw1 = self.engine._get_word_form(w1, skip_cache=True)
                return {'word': cw1, 'meaning': w1}

        elif rel_type == 'affixation':
            target_pool = rule.get('target')
            affix_rule = rule.get('affix_rule', {})
            p_words = self._get_pool_words(target_pool, culture)
            if p_words:
                w1 = random.choice(p_words)
                cw1 = self.engine._get_word_form(w1, skip_cache=True)
                final_w = cw1
                if affix_rule:
                    affix = affix_rule.get('affix', '')
                    pos = affix_rule.get('position', 'suffix')
                    if pos == 'suffix':
                        final_w = cw1 + affix.replace('-', '')
                    else:
                        final_w = affix.replace('-', '') + cw1
                return {'word': final_w, 'meaning': f"{w1} ({affix_rule.get('description', '')})"}

        elif rel_type == 'trait_derivation':
            target_pool = rule.get('target')
            degree = rule.get('degree')
            p_words = self._get_pool_words(target_pool, culture)
            if p_words:
                w1 = random.choice(p_words)
                cw1 = self.engine._get_word_form(w1, skip_cache=True)
                if self.engine.degree_handler.enabled and degree:
                    cw1 = self.engine.degree_handler.apply_degree(cw1, degree)
                return {'word': cw1, 'meaning': f"{w1} ({degree})"}

        all_words = []
        for pool_key in self.unified_pools:
            all_words.extend(self.unified_pools[pool_key])
        if 'semantic_pools' in culture:
            for p in culture['semantic_pools'].values():
                all_words.extend(p)
        if all_words:
            w1 = random.choice(all_words)
            return {'word': self.engine._get_word_form(w1, skip_cache=True), 'meaning': w1}

        return {'word': self.engine._generate_word_from_seed(comp_name, self.engine.global_seed + random.randint(1, 1000)), 'meaning': 'Desconhecido'}

    def _apply_phonological_filters(self, name_parts: List[str], filters: Dict) -> str:
        raw_name = " ".join(name_parts)
        if filters.get('apply_sandhi_between_components', False) and self.engine.sandhi_handler.enabled:
            final_name = self.engine.sandhi_handler.apply_sandhi(raw_name)
        else:
            final_name = raw_name
        if filters.get('force_capitalization', True):
            final_name = " ".join(part.capitalize()
                                  for part in final_name.split())
        return final_name

    def generate_names_from_concept(self, concept_phrase, culture=None, count=8):
        stop_words = PORTUGUESE_STOP_WORDS
        results = []
        seen = set()

        if culture and 'dynamic_patterns' in culture:
            for pat in culture['dynamic_patterns']:
                match = re.match(pat.get('pattern', ''),
                                 concept_phrase, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    fmt = pat.get('format', '')
                    for attempt in range(count * 4):
                        translated_groups = []
                        all_comp_info = []
                        for g in groups:
                            g_words = re.split(r'[\s\-_]+', g.strip())
                            g_kws = [re.sub(r'[^\w]', '', w) for w in g_words if w and re.sub(
                                r'[^\w]', '', w).lower() not in stop_words]
                            if not g_kws:
                                g_kws = [g.strip()]
                            rng = random.Random(
                                int(hashlib.sha256(f"{g}_{attempt}".encode()).hexdigest(), 16))
                            num_kw = rng.randint(
                                1, min(3, len(g_kws))) if len(g_kws) > 0 else 0
                            chosen_kw = rng.sample(g_kws, num_kw) if len(
                                g_kws) >= num_kw else g_kws[:]
                            parts = []
                            for kw in chosen_kw:
                                form = self.engine._get_word_form(
                                    kw, skip_cache=True)
                                if form:
                                    parts.append(form)
                                    all_comp_info.append(
                                        {'keyword': kw, 'form': form})
                            if self.engine.compounding_handler.enabled and len(parts) > 1:
                                g_trans = self.engine.compounding_handler.construct_compound(
                                    parts, self.engine)
                            else:
                                g_trans = "".join(parts)
                            translated_groups.append(g_trans.capitalize())
                        final_str = fmt.format(*translated_groups)
                        if self.engine.sandhi_handler.enabled:
                            final_str = self.engine.sandhi_handler.apply_sandhi(
                                final_str)
                        final_name = " ".join(p.capitalize()
                                              for p in final_str.split())
                        if final_name not in seen and len(final_name) > 1:
                            results.append({
                                'name': final_name,
                                'etymology': pat.get('description', 'Padrão Dinâmico') + " (" + " + ".join(c['keyword'] for c in all_comp_info) + ")",
                                'components': all_comp_info
                            })
                            seen.add(final_name)
                        if len(results) >= count:
                            break
                    if results:
                        return results

        words = re.split(r'[\s\-_]+', concept_phrase.lower().strip())
        keywords = [re.sub(r'[^\w]', '', w) for w in words
                    if w and re.sub(r'[^\w]', '', w) not in stop_words
                    and len(re.sub(r'[^\w]', '', w)) > 1]
        if not keywords:
            keywords = [re.sub(r'[^\w]', '', concept_phrase.lower().strip())]
        keywords = keywords[:4]

        for attempt in range(count * 4):
            rng = random.Random(int(hashlib.sha256(
                f"{concept_phrase}_concept_{attempt}".encode()).hexdigest(), 16))

            num_kw = rng.randint(1, min(3, len(keywords)))
            chosen_kw = rng.sample(keywords, num_kw) if len(
                keywords) >= num_kw else keywords[:]

            conlang_parts = []
            component_info = []
            for kw in chosen_kw:
                form = self.engine._get_word_form(kw, skip_cache=True)
                if form:
                    conlang_parts.append(form)
                    component_info.append({'keyword': kw, 'form': form})

            if not conlang_parts:
                continue

            if self.engine.compounding_handler.enabled and len(conlang_parts) > 1:
                result_word = self.engine.compounding_handler.construct_compound(
                    conlang_parts, self.engine)
            else:
                result_word = "".join(conlang_parts)

            if self.engine.sandhi_handler.enabled:
                result_word = self.engine.sandhi_handler.apply_sandhi(
                    result_word)

            result_word = result_word.capitalize()

            if result_word and result_word not in seen and len(result_word) >= 2:
                results.append({
                    'name': result_word,
                    'etymology': " + ".join(c['keyword'] for c in component_info),
                    'components': component_info
                })
                seen.add(result_word)

            if len(results) >= count:
                break

        return results

    def generate_basesuffixe_style_names(self, base_pool_key, suffix_pool_key, culture=None, count=12):
        base_words = []
        suffix_entries = []
        if culture:
            base_words = self._get_pool_words(base_pool_key, culture)
            cultural_suffixes = culture.get('cultural_suffixes', {})
            if suffix_pool_key in cultural_suffixes:
                suffix_entries = cultural_suffixes[suffix_pool_key]
            else:
                suffix_entries = self._get_pool_words(suffix_pool_key, culture)
        if not base_words:
            base_words = list(self.unified_pools.get(base_pool_key, []))
        if not suffix_entries:
            suffix_entries = list(self.unified_pools.get(suffix_pool_key, []))

        if not base_words and not suffix_entries:
            return []

        results = []
        seen = set()
        ph = self.engine.phonology_handler
        attempts = 0
        max_attempts = count * 12

        while len(results) < count and attempts < max_attempts:
            attempts += 1
            rng = random.Random(int(hashlib.sha256(
                f"ashk_{base_pool_key}_{suffix_pool_key}_{attempts}".encode()).hexdigest(), 16))

            base_word = rng.choice(base_words) if base_words else ""
            suffix_raw = rng.choice(suffix_entries) if suffix_entries else ""

            if base_word:
                conlang_base = self.engine._get_word_form(
                    base_word, skip_cache=True)
            else:
                conlang_base = ""

            if suffix_raw:
                suf_clean = suffix_raw.replace('-', '').strip()
                if len(suf_clean) <= 6 or suffix_raw.startswith('-'):
                    conlang_suffix = suf_clean
                else:
                    conlang_suffix = self.engine._get_word_form(
                        suffix_raw, skip_cache=True)
            else:
                conlang_suffix = ""

            if not conlang_base and not conlang_suffix:
                continue

            parts = [p for p in [conlang_base, conlang_suffix] if p]

            if self.engine.compounding_handler.enabled and len(parts) > 1:
                result = self.engine.compounding_handler.construct_compound(
                    parts, self.engine)
            else:
                result = "".join(parts)

            result = ph.apply_monophthongization(result)
            if self.engine.sandhi_handler.enabled:
                result = self.engine.sandhi_handler.apply_sandhi(result)
            result = result.capitalize()

            if result and result not in seen and len(result) >= 2:
                results.append(result)
                seen.add(result)

        return results

    def generate_word_blend_names(self, pool_keys, culture=None, count=12):
        all_pool_words = []
        for pk in pool_keys:
            if culture:
                words = self._get_pool_words(pk, culture)
            else:
                words = list(self.unified_pools.get(pk, []))
            all_pool_words.extend([(w, pk) for w in words])

        if not all_pool_words:
            return []

        results = []
        seen = set()
        ph = self.engine.phonology_handler
        attempts = 0
        max_attempts = count * 15

        while len(results) < count and attempts < max_attempts:
            attempts += 1
            rng = random.Random(int(hashlib.sha256(
                f"blend_{'_'.join(pool_keys)}_{attempts}".encode()).hexdigest(), 16))

            num_parts = rng.randint(2, min(3, len(all_pool_words)))
            chosen = rng.sample(all_pool_words, num_parts)

            conlang_parts = []
            meanings = []
            for word, pool in chosen:
                form = self.engine._get_word_form(word, skip_cache=True)
                if form:
                    conlang_parts.append(form)
                    meanings.append(word)

            if len(conlang_parts) < 1:
                continue

            if self.engine.compounding_handler.enabled and len(conlang_parts) > 1:
                result = self.engine.compounding_handler.construct_compound(
                    conlang_parts, self.engine)
            else:
                result = "".join(conlang_parts)

            result = ph.apply_monophthongization(result)
            if self.engine.sandhi_handler.enabled:
                result = self.engine.sandhi_handler.apply_sandhi(result)
            result = result.capitalize()

            if result and result not in seen and len(result) >= 3:
                results.append(
                    {'name': result, 'etymology': ' + '.join(meanings)})
                seen.add(result)

        return results

    def derive_gender_form(self, name, target_gender, culture=None):
        results = []
        seen = set()
        seen.add(name)
        ph = self.engine.phonology_handler
        vowels_list = list(ph.vowels) if ph.vowels else list("aeiou")
        consonants_list = list(ph.consonants) if ph.consonants else []

        gender_rules = {}
        if culture:
            gender_rules = culture.get('gender_derivation', {})

        if target_gender in gender_rules:
            rule = gender_rules[target_gender]
            affix = rule.get('affix', '')
            position = rule.get('position', 'suffix')
            strip_vowel = rule.get('strip_final_vowel', False)
            base = name
            if strip_vowel and base and base[-1].lower() in (ph.vowels or 'aeiou'):
                base = base[:-1]
            if position == 'suffix':
                candidate = base + affix
            elif position == 'prefix':
                candidate = affix + base
            else:
                candidate = base + affix
            candidate = ph.apply_monophthongization(candidate)
            if self.engine.sandhi_handler.enabled:
                candidate = self.engine.sandhi_handler.apply_sandhi(candidate)
            candidate = candidate.capitalize()
            if candidate and candidate not in seen:
                results.append(candidate)
                seen.add(candidate)

        gender_vowel_pools = {
            'Feminino': [v for v in vowels_list if v in 'aáéiíy'] or vowels_list[:max(1, len(vowels_list)//2)],
            'Masculino': [v for v in vowels_list if v in 'ouóú'] or vowels_list[max(0, len(vowels_list)//2):],
            'Neutro': vowels_list
        }
        target_vowels = gender_vowel_pools.get(target_gender, vowels_list)
        if not target_vowels:
            target_vowels = vowels_list

        gender_suffix_pools = {
            'Feminino': ['a', 'ia', 'ina', 'ina', 'elle', 'ette', 'issa'],
            'Masculino': ['os', 'us', 'or', 'an', 'on', 'ar'],
            'Neutro': ['e', 'en', 'im', 'um', 'al']
        }
        base_suffixes = gender_suffix_pools.get(target_gender, ['a'])

        phonologically_valid = [s for s in base_suffixes
                                if not s or ph.is_valid_final(s[-1])]
        if not phonologically_valid:
            phonologically_valid = base_suffixes

        strategies = [
            'replace_final_vowel',
            'add_gender_suffix',
            'replace_final_vowel',
            'strip_and_add_suffix',
            'change_internal_vowel',
            'add_gender_suffix',
            'strip_and_add_suffix',
            'replace_final_cluster',
        ]

        attempts = 0
        max_attempts = 60

        while len(results) < 12 and attempts < max_attempts:
            attempts += 1
            rng = random.Random(int(hashlib.sha256(
                f"{name}_gender_{target_gender}_{attempts}".encode()).hexdigest(), 16))

            strategy = rng.choice(strategies)
            base = name.lower().strip()
            candidate = base

            if strategy == 'replace_final_vowel' and target_vowels:
                stem = base.rstrip(
                    ''.join(ph.vowels or 'aeiou')) if base else base
                if not stem:
                    stem = base[:-1] if len(base) > 1 else base
                candidate = stem + rng.choice(target_vowels)

            elif strategy == 'add_gender_suffix' and phonologically_valid:
                suf = rng.choice(phonologically_valid)
                stem = base.rstrip(
                    ''.join(ph.vowels or 'aeiou')) if base else base
                if not stem:
                    stem = base
                candidate = stem + suf

            elif strategy == 'strip_and_add_suffix' and len(base) >= 3 and phonologically_valid:
                cut = rng.randint(max(1, len(base) - 2), len(base) - 1)
                stem = base[:cut]
                suf = rng.choice(phonologically_valid)
                candidate = stem + suf

            elif strategy == 'change_internal_vowel' and len(base) >= 3:
                vowel_idxs = [i for i, c in enumerate(
                    base) if c in (ph.vowels or 'aeiou')]
                if vowel_idxs and target_vowels:
                    idx = rng.choice(
                        vowel_idxs[:-1] if len(vowel_idxs) > 1 else vowel_idxs)
                    opts = [v for v in target_vowels if v != base[idx]]
                    if opts:
                        chars = list(base)
                        chars[idx] = rng.choice(opts)
                        candidate = "".join(chars)

            elif strategy == 'replace_final_cluster' and len(base) >= 3:
                stem = base[:-2] if len(base) > 2 else base[:-1]
                suf = rng.choice(phonologically_valid) if phonologically_valid else rng.choice(
                    target_vowels)
                candidate = stem + suf

            candidate = ph.apply_monophthongization(candidate)
            if candidate and not ph.is_valid_final(candidate[-1]):
                valid_finals = [
                    c for c in consonants_list if ph.is_valid_final(c)] + vowels_list
                if valid_finals:
                    candidate = candidate[:-1] + rng.choice(valid_finals)

            if self.engine.sandhi_handler.enabled:
                candidate = self.engine.sandhi_handler.apply_sandhi(candidate)

            candidate = candidate.capitalize() if candidate else ''

            if candidate and candidate not in seen and len(candidate) >= 2:
                results.append(candidate)
                seen.add(candidate)

        return results

    def generate_candidates(self, meaning: str, options: Dict) -> List[Dict]:
        candidates = []
        is_abstract = options.get('abstract', False)
        force_loan = options.get('force_loan', False)
        register = options.get('register', 'Neutro')

        clean_meaning = "".join(
            c for c in meaning if c.isalnum() or c.isspace()).strip()

        salt = options.get('salt', '')
        seed_str = f"{clean_meaning}_{self.engine.global_seed}_gramataki_{salt}"
        seed = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16)

        generated_word = ""
        gloss = meaning

        if force_loan:
            generated_word = self.engine.loanword_handler.nativize_reserved_term(
                clean_meaning.split()[0])
            gloss = f"Empréstimo de: {clean_meaning}"

        elif self.engine.compounding_handler.enabled and " " in clean_meaning:
            parts = clean_meaning.split()
            keywords = [w for w in parts if len(w) > 3]
            if len(keywords) < 2:
                keywords = parts[:2]

            sub_words = []
            for kw in keywords:
                sub_word = self.engine._generate_word_from_seed(
                    kw,
                    int(hashlib.sha256(
                        f"{kw}_{seed}".encode()).hexdigest(), 16)
                )
                sub_words.append(sub_word)

            generated_word = self.engine.compounding_handler.construct_compound(
                sub_words, self.engine)
            if self.engine.sandhi_handler.enabled:
                generated_word = self.engine.sandhi_handler.apply_sandhi(
                    generated_word)
            gloss = f"Composto de: {', '.join(keywords)}"

        else:
            if self.engine.root_handler.enabled:
                root = self.engine.root_handler.generate_root(clean_meaning)
                pattern = self.engine.root_handler.get_binyan_by_meaning(
                    'basic')
                generated_word = self.engine.root_handler.apply_pattern(
                    root, pattern)
                gloss = f"Raiz: {'-'.join(root)}"
            else:
                generated_word = self.engine._generate_word_from_seed(
                    clean_meaning, seed)
                gloss = "Geração fonotática simples"

        if is_abstract and self.engine.affix_handler.enabled:
            rule = self.engine.affix_handler.get_derivation_rule(
                "ADJ", "NOUN", "abstract_noun")
            if not rule:
                rule = self.engine.affix_handler.get_derivation_rule(
                    "VERB", "NOUN", "verbal_noun")

            if rule:
                generated_word = self.engine.affix_handler.apply_affix(
                    generated_word, rule)
                gloss += " + Derivação Abstrata"

        if register != "Neutro":
            generated_word = self.engine.phonology_handler.apply_rules(
                generated_word, register.lower())
            gloss += f" ({register})"

        if self.engine.special_mechanics_handler.enabled:
            generated_word = self.engine.special_mechanics_handler.apply_mechanics(
                generated_word, clean_meaning, self.engine.global_seed)

        candidates.append({
            'lemma': generated_word,
            'pos': 'NOUN' if is_abstract else 'UNK',
            'score': 100,
            'gloss': gloss
        })

        return candidates

    def nativize_external_name(self, name: str) -> str:
        if not name:
            return ""
        parts = name.split()
        nativized_parts = []
        for part in parts:
            nativized = self.engine.phonology_handler.nativize_word(part)
            if nativized:
                nativized_parts.append(nativized.capitalize())
        final_name = " ".join(nativized_parts)
        if self.engine.sandhi_handler.enabled:
            final_name = self.engine.sandhi_handler.apply_sandhi(final_name)
        return final_name

    def nativize_external_name_multiple(self, name, count=20):
        if not name:
            return []

        ph = self.engine.phonology_handler
        parts = name.strip().split()
        results = []
        seen = set()

        base = self.nativize_external_name(name)
        if base and base not in seen:
            results.append(base)
            seen.add(base)

        vowels_list = list(ph.vowels) if ph.vowels else list("aeiou")
        consonants_list = list(ph.consonants) if ph.consonants else []

        attempts = 0
        max_attempts = count * 8

        while len(results) < count and attempts < max_attempts:
            attempts += 1
            seed_val = int(hashlib.sha256(
                f"{name}_multi_{attempts}_{len(results)}".encode()
            ).hexdigest(), 16)
            rng = random.Random(seed_val)

            deviation = 0.15 + (attempts / max_attempts) * 0.55

            nativized_parts = []
            for part in parts:
                nativized_chars = []
                for char in part.lower():
                    char_norm = char
                    is_vowel = char_norm in "aeiouyäëïöü"
                    base_phoneme = ph.get_closest_phoneme(char_norm)
                    if rng.random() < deviation:
                        pool = vowels_list if is_vowel else consonants_list
                        if pool:
                            chosen = rng.choice(pool)
                        else:
                            chosen = base_phoneme
                    else:
                        chosen = base_phoneme
                    nativized_chars.append(chosen)

                raw = "".join(nativized_chars)
                raw = ph.apply_monophthongization(raw)

                if raw and not ph.is_valid_final(raw[-1]):
                    valid_finals = [
                        c for c in consonants_list if ph.is_valid_final(c)] + vowels_list
                    if valid_finals:
                        raw = raw[:-1] + rng.choice(valid_finals)

                if raw:
                    nativized_parts.append(raw.capitalize())

            candidate = " ".join(nativized_parts)
            if self.engine.sandhi_handler.enabled:
                candidate = self.engine.sandhi_handler.apply_sandhi(candidate)

            if candidate and candidate not in seen:
                results.append(candidate)
                seen.add(candidate)

        return results

    def generate_derived_forms(self, name, count=15):
        if not name:
            return []

        ph = self.engine.phonology_handler
        vowels_list = list(ph.vowels) if ph.vowels else list("aeiou")
        consonants_list = list(ph.consonants) if ph.consonants else []

        results = []
        seen = set()
        seen.add(name)

        strategies = [
            "change_suffix_vowel",
            "change_suffix_consonant",
            "swap_internal_vowel",
            "add_vowel_suffix",
            "add_consonant_suffix",
            "truncate_and_extend",
            "swap_final_consonant",
            "insert_medial_vowel",
            "change_initial_cluster",
            "double_final_vowel",
        ]

        attempts = 0
        max_attempts = count * 10

        while len(results) < count and attempts < max_attempts:
            attempts += 1
            seed_val = int(hashlib.sha256(
                f"{name}_deriv_{attempts}".encode()
            ).hexdigest(), 16)
            rng = random.Random(seed_val)

            strategy = rng.choice(strategies)
            base = name.lower().strip()
            candidate = base

            if strategy == "change_suffix_vowel" and len(base) >= 2:
                stem = base[:-1]
                if vowels_list:
                    candidate = stem + rng.choice(vowels_list)

            elif strategy == "change_suffix_consonant" and len(base) >= 2:
                if consonants_list:
                    valid = [
                        c for c in consonants_list if ph.is_valid_final(c)]
                    if valid:
                        candidate = base[:-1] + rng.choice(valid)

            elif strategy == "swap_internal_vowel" and len(base) >= 3:
                vowel_idxs = [i for i, c in enumerate(
                    base) if c in (ph.vowels or "aeiou")]
                if vowel_idxs and vowels_list and len(vowels_list) > 1:
                    idx = rng.choice(vowel_idxs)
                    current = base[idx]
                    options = [v for v in vowels_list if v != current]
                    if options:
                        chars = list(base)
                        chars[idx] = rng.choice(options)
                        candidate = "".join(chars)

            elif strategy == "add_vowel_suffix" and vowels_list:
                candidate = base + rng.choice(vowels_list)

            elif strategy == "add_consonant_suffix" and consonants_list:
                valid = [c for c in consonants_list if ph.is_valid_final(c)]
                if valid and not (base and base[-1] in (ph.consonants or "")):
                    candidate = base + rng.choice(valid)

            elif strategy == "truncate_and_extend" and len(base) >= 3:
                trunc_at = rng.randint(max(1, len(base) - 2), len(base) - 1)
                stem = base[:trunc_at]
                if vowels_list:
                    candidate = stem + rng.choice(vowels_list)
                    if consonants_list and rng.random() < 0.4:
                        valid = [
                            c for c in consonants_list if ph.is_valid_final(c)]
                        if valid:
                            candidate = candidate + rng.choice(valid)

            elif strategy == "swap_final_consonant" and len(base) >= 2:
                if base[-1] in (ph.consonants or "") and consonants_list:
                    valid = [c for c in consonants_list if ph.is_valid_final(
                        c) and c != base[-1]]
                    if valid:
                        candidate = base[:-1] + rng.choice(valid)

            elif strategy == "insert_medial_vowel" and len(base) >= 2 and vowels_list:
                insert_pos = rng.randint(1, len(base) - 1)
                candidate = base[:insert_pos] + \
                    rng.choice(vowels_list) + base[insert_pos:]

            elif strategy == "change_initial_cluster" and len(base) >= 2 and consonants_list:
                if base[0] in (ph.consonants or ""):
                    options = [c for c in consonants_list if c != base[0]]
                    if options:
                        candidate = rng.choice(options) + base[1:]

            elif strategy == "double_final_vowel" and len(base) >= 1:
                if base[-1] in (ph.vowels or "") and vowels_list:
                    candidate = base + base[-1]

            candidate = ph.apply_monophthongization(candidate)

            if candidate and not ph.is_valid_final(candidate[-1]):
                valid_finals = [
                    c for c in consonants_list if ph.is_valid_final(c)] + vowels_list
                if valid_finals:
                    candidate = candidate[:-1] + rng.choice(valid_finals)

            if candidate:
                candidate = candidate.capitalize()
                if self.engine.sandhi_handler.enabled:
                    candidate = self.engine.sandhi_handler.apply_sandhi(
                        candidate)

            if candidate and candidate not in seen and len(candidate) >= 2:
                results.append(candidate)
                seen.add(candidate)

        return results

    def generate_random_name(self) -> str:
        seed = random.randint(0, 9999999)
        word = self.engine._generate_word_from_seed(
            f"rand_{seed}", seed, is_derived=False)
        if word and self.engine.sandhi_handler.enabled:
            word = self.engine.sandhi_handler.apply_sandhi(word)
        return word.capitalize() if word else ""
