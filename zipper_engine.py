import hashlib
import json
import re
import unicodedata
from typing import List, Dict, Tuple, Optional


class ZipperEngine:
    def __init__(self, profile_path: str):
        with open(profile_path, 'r', encoding='utf-8') as f:
            self.profile = json.load(f)

        self.id = self.profile.get('id', 'unknown')
        self.lineage_group = self.profile.get('lineage_group', 'generic')
        self.evolution_stage = self.profile.get('evolution_stage', 'modern')
        self.bases = self.profile.get('bases', [])
        self.fusion_weights = self.profile.get('fusion_weights', [0.5, 0.5])
        self.fusion_rules = self.profile.get('fusion_rules', {})
        self.phonotactics = self.profile.get('phonotactics', {})
        self.orthography = self.profile.get('orthography', {})
        self.global_seed = self.profile.get('global_seed', 12345)

        self._normalize_weights()

    def _normalize_weights(self):
        total = sum(self.fusion_weights)
        if total > 0:
            self.fusion_weights = [w / total for w in self.fusion_weights]

    def _get_deterministic_hash(self, input_str: str, salt: str = "") -> int:
        combined = f"{input_str.lower()}_{salt}_{self.lineage_group}_{self.global_seed}"
        return int(hashlib.sha256(combined.encode()).hexdigest(), 16)

    def process_texts(self, base_texts: List[str]) -> str:
        if len(base_texts) != len(self.bases):
            raise ValueError(f"Expected {len(self.bases)} base texts")

        base_lines = [text.splitlines() for text in base_texts]
        max_lines = max(len(lines) for lines in base_lines)

        final_lines = []
        for i in range(max_lines):
            current_line_set = [base_lines[j][i] if i < len(
                base_lines[j]) else "" for j in range(len(self.bases))]

            if not any(current_line_set):
                final_lines.append("")
                continue

            normalized_line_set = [self._normalize_text(
                line) for line in current_line_set]
            word_lists = [line.split() for line in normalized_line_set]
            max_words = max(len(wl) for wl in word_lists)

            line_tokens = []
            for k in range(max_words):
                group = [wl[k] if k < len(wl) else "" for wl in word_lists]
                anchor_word = group[0] if group[0] else (
                    group[1] if len(group) > 1 else "")

                prefix, suffix = self._extract_punctuation(anchor_word)
                clean_group = [re.sub(r"^[^\w]*|[^\w]*$", "", word)
                               for word in group]

                shared_root = self._generate_shared_root(clean_group)
                evolved_word = self._apply_diachronic_drift(
                    shared_root, clean_group)

                if evolved_word:
                    is_caps = anchor_word and anchor_word[0].isupper()
                    processed_word = evolved_word.capitalize() if is_caps else evolved_word

                    line_tokens.append({
                        "word": processed_word,
                        "prefix": prefix,
                        "suffix": suffix,
                        "original": clean_group
                    })

            line_tokens = self._apply_agglutination_logic(line_tokens)

            processed_words = []
            for token in line_tokens:
                w = self._apply_orthography(token["word"])
                processed_words.append(
                    f"{token['prefix']}{w}{token['suffix']}")

            final_lines.append(" ".join(processed_words))

        return "\n".join(final_lines)

    def _extract_punctuation(self, word: str) -> Tuple[str, str]:
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

    def _normalize_text(self, text: str) -> str:
        text = text.strip()
        if not self.fusion_rules.get('preserve_accents', False):
            nfd = unicodedata.normalize('NFD', text)
            text = ''.join(
                char for char in nfd if unicodedata.category(char) != 'Mn')
        return text

    def _generate_shared_root(self, word_group: List[str]) -> str:
        valid_words = [w for w in word_group if w]
        if not valid_words:
            return ""

        if self.fusion_rules.get('prefer_cognates', True):
            lowered = [w.lower() for w in valid_words]
            if len(set(lowered)) == 1:
                return lowered[0]

        root_seed = self._get_deterministic_hash("|".join(word_group))
        syllable_pools = [self._syllabify(w) for w in valid_words]

        target_len = 0
        for idx, weight in enumerate(self.fusion_weights):
            if idx < len(syllable_pools):
                target_len += len(syllable_pools[idx]) * weight

        max_syl = int(round(target_len)) if target_len > 0 else 1
        root_syllables = []

        for s_idx in range(max_syl):
            candidates = []
            for p in syllable_pools:
                if p:
                    candidates.append(p[s_idx % len(p)])

            if not candidates:
                continue

            syl_hash = (root_seed + s_idx) % (2**32)
            root_syllables.append(self._blend_syllables(candidates, syl_hash))

        return "".join(root_syllables)

    def _apply_diachronic_drift(self, root: str, original_group: List[str]) -> str:
        if not root:
            return ""
        drift_seed = self._get_deterministic_hash(root, self.id)
        result = root.lower()
        vowels = self.phonotactics.get('vowels', 'aeiou')

        if self.evolution_stage == "archaic":
            if self.orthography.get('gemination_rules', False):
                if drift_seed % 100 < 40:
                    result = re.sub(
                        r'([bcdfghjklmnpqrstvwxyz])', r'\1\1', result, count=1)
            if drift_seed % 100 < 30:
                result = re.sub(r'([aeiou])', r'\1\1', result, count=1)
            suffixes = self.orthography.get('archaic_suffixes', [])
            if suffixes and len(result) > 3 and result[-1] not in vowels:
                result += suffixes[drift_seed % len(suffixes)]
        elif self.evolution_stage == "modern":
            result = re.sub(r'(.)\1+', r'\1', result)
            if len(result) > 4 and result[-1] in vowels:
                if drift_seed % 100 < 25:
                    result = result[:-1]

            result = result.replace('th', 't').replace(
                'ph', 'f').replace('qu', 'k')

            result = re.sub(
                f'([{vowels}])([{vowels}])([{vowels}]+)', r'\1\2', result)

        result = self._apply_phonotactics(result, drift_seed)
        return result

    def _syllabify(self, word: str) -> List[str]:
        if not word:
            return []
        word = word.lower()
        v_list = self.phonotactics.get('vowels', 'aeiouyäëïöüáéíóúàèìòù')
        d_list = self.phonotactics.get('diphthongs', [])
        syllables = []
        curr = ""
        i = 0
        while i < len(word):
            is_d = i + 1 < len(word) and word[i:i+2] in d_list
            part = word[i:i+2] if is_d else word[i]
            curr += part
            is_vowel_part = any(v in part for v in v_list)
            if is_vowel_part:
                next_i = i + 2 if is_d else i + 1
                if next_i < len(word):
                    j = next_i
                    cluster = ""
                    while j < len(word) and not any(v in word[j] for v in v_list):
                        cluster += word[j]
                        j += 1
                    if j < len(word):
                        if len(cluster) > 1:
                            mid = len(cluster) // 2
                            curr += cluster[:mid]
                            syllables.append(curr)
                            curr = cluster[mid:]
                        else:
                            syllables.append(curr)
                            curr = cluster
                        i = j - 1
                else:
                    syllables.append(curr)
                    curr = ""
            i += 2 if is_d else 1
        if curr:
            if syllables:
                syllables[-1] += curr
            else:
                syllables.append(curr)
        return syllables

    def _blend_syllables(self, options: List[str], seed: int) -> str:
        if not options:
            return ""
        if len(options) == 1:
            return options[0]

        weights = self.fusion_weights
        if len(weights) < len(options):
            weights = weights + [0.5] * (len(options) - len(weights))

        pivot = (seed % 1000) / 1000.0

        primary_idx = 0
        acc = 0
        for i, w in enumerate(weights):
            acc += w
            if pivot <= acc:
                primary_idx = i
                break

        secondary_idx = (primary_idx + 1) % len(options)

        base = options[primary_idx]
        alt = options[secondary_idx]

        morpheme_retention = self.fusion_rules.get('morpheme_retention', 0.5)

        if (seed >> 4) % 100 < (morpheme_retention * 100):
            return base

        onset = self._get_onset(base)
        nucleus = self._get_nucleus(alt if (seed % 2 == 0) else base)
        coda = self._get_coda(base if (seed % 3 == 0) else alt)

        return onset + nucleus + coda

    def _get_onset(self, syl: str) -> str:
        v = self.phonotactics.get('vowels', 'aeiouyäëïöüáéíóúàèìòù')
        res = ""
        for c in syl:
            if c not in v:
                res += c
            else:
                break
        return res

    def _get_nucleus(self, syl: str) -> str:
        v = self.phonotactics.get('vowels', 'aeiouyäëïöüáéíóúàèìòù')
        res = ""
        found = False
        for c in syl:
            if c in v:
                res += c
                found = True
            elif found:
                break
        return res if res else "e"

    def _get_coda(self, syl: str) -> str:
        v = self.phonotactics.get('vowels', 'aeiouyäëïöüáéíóúàèìòù')
        last_v = -1
        for i in range(len(syl)):
            if syl[i] in v:
                last_v = i
        return syl[last_v+1:] if last_v != -1 else ""

    def _apply_phonotactics(self, word: str, seed: int) -> str:
        if not word:
            return ""
        v_str = self.phonotactics.get('vowels', 'aeiouyäëïöüáéíóúàèìòù')
        max_c = self.phonotactics.get('max_consonant_cluster', 3)
        ep_v = self.phonotactics.get('epenthesis_vowel', 'e')

        pattern = f'([^ {v_str}]{{{max_c + 1},}})'
        word = re.sub(pattern, lambda m: m.group(
            1)[:max_c] + ep_v + m.group(1)[max_c:], word)

        for cluster in self.phonotactics.get('forbidden_initial_clusters', []):
            if word.startswith(cluster):
                word = ep_v + word

        f_bad = self.phonotactics.get('forbidden_final_consonants', [])
        if word and word[-1] in f_bad:
            if seed % 2 == 0:
                word = word[:-1] + ep_v
            else:
                word = word[:-1]

        return word

    def _apply_agglutination_logic(self, tokens: List[dict]) -> List[dict]:
        factor = self.fusion_rules.get('agglutination_factor', 0.0)
        if factor <= 0 or not tokens:
            return tokens
        new_tokens = []
        i = 0
        while i < len(tokens):
            curr = tokens[i]
            if i + 1 < len(tokens):
                nxt = tokens[i+1]
                agg_seed = self._get_deterministic_hash(
                    curr["word"] + nxt["word"], "agg")
                should_agg = (agg_seed % 1000) < (factor * 1000)
                if should_agg and not curr["suffix"] and not nxt["prefix"] and len(curr["word"]) < 6:
                    combined = curr["word"] + nxt["word"].lower()
                    if self.evolution_stage == "archaic":
                        combined = re.sub(r'([aeiou])\1+', r'\1\1', combined)
                    new_tokens.append({
                        "word": combined,
                        "prefix": curr["prefix"],
                        "suffix": nxt["suffix"],
                        "original": curr["original"] + nxt["original"]
                    })
                    i += 2
                    continue
            new_tokens.append(curr)
            i += 1
        return new_tokens

    def _apply_orthography(self, text: str) -> str:
        mapping = self.orthography.get('long_vowel_mapping', {})
        sorted_keys = sorted(mapping.keys(), key=len, reverse=True)
        for k in sorted_keys:
            text = text.replace(k, mapping[k])
        if self.orthography.get('transform_s_to_cedilla', False):
            text = text.replace('s', 'ç').replace('S', 'Ç')
        return text
