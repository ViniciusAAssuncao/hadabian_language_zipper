import hashlib
import json
import re
import unicodedata
from typing import List, Dict, Tuple, Optional
from pathlib import Path

from translation_cache import TranslationCache, MorphemeCache, ContextualMemory
from morphology_analyzer import MorphologyAnalyzer, ConsistencyValidator, WordQualityScorer
from learning_system import LearningSystem, ConvergenceEngine, AdaptiveWeightSystem
from context_engine import SemanticContextEngine, ContextualTranslator, PhraseAnalyzer


class ZipperEngine:
    def __init__(self, profile_path: str, enable_learning: bool = True,
                 enable_caching: bool = True, enable_context: bool = True):
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

        self.enable_learning = enable_learning
        self.enable_caching = enable_caching
        self.enable_context = enable_context

        vowel_str = self.phonotactics.get('vowels', 'aeiou')
        self.morphology_analyzer = MorphologyAnalyzer(vowel_str)
        self.consistency_validator = ConsistencyValidator()
        self.word_quality_scorer = WordQualityScorer(self.morphology_analyzer)

        if self.enable_caching:
            self.translation_cache = TranslationCache(self.id)
            self.morpheme_cache = MorphemeCache(self.id)
            self.contextual_memory = ContextualMemory(self.id)

        if self.enable_learning:
            self.learning_system = LearningSystem(self.id)
            self.convergence_engine = ConvergenceEngine(self.id)
            self.adaptive_weights = AdaptiveWeightSystem(
                self.fusion_weights.copy())

        if self.enable_context:
            self.semantic_engine = SemanticContextEngine(self.id)
            self.contextual_translator = ContextualTranslator(
                self.semantic_engine)
            self.phrase_analyzer = PhraseAnalyzer()

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

            if self.enable_context:
                full_line = ' '.join(current_line_set)
                self.semantic_engine.extract_collocations(full_line)

            normalized_line_set = [self._normalize_text(
                line) for line in current_line_set]
            word_lists = [line.split() for line in normalized_line_set]
            max_words = max(len(wl) for wl in word_lists)

            line_tokens = []
            for k in range(max_words):
                group = [wl[k] if k < len(wl) else "" for wl in word_lists]

                if self.enable_caching:
                    cached_translation = self.translation_cache.get_translation(
                        group)
                    if cached_translation:
                        anchor_word = group[0] if group[0] else group[1] if len(
                            group) > 1 else ""
                        prefix, suffix = self._extract_punctuation(anchor_word)
                        is_caps = anchor_word and anchor_word[0].isupper()
                        processed_word = cached_translation.capitalize() if is_caps else cached_translation

                        line_tokens.append({
                            "word": processed_word,
                            "prefix": prefix,
                            "suffix": suffix,
                            "original": group,
                            "from_cache": True
                        })
                        continue

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

                    if self.morphology_analyzer.detect_stacking(evolved_word):
                        evolved_word = self.morphology_analyzer.fix_stacking(
                            evolved_word)

                    evolved_word = self.morphology_analyzer.fix_reduplication(
                        evolved_word)

                    if not self.morphology_analyzer.is_valid_word_structure(
                        evolved_word,
                        self.phonotactics.get('max_consonant_cluster', 3),
                        self.phonotactics.get('max_vowel_cluster', 2)
                    ):
                        evolved_word = self.morphology_analyzer.repair_word_structure(
                            evolved_word,
                            self.phonotactics.get('epenthesis_vowel', 'e'),
                            self.phonotactics.get('max_consonant_cluster', 3)
                        )

                    quality_score = self.word_quality_scorer.score_word(
                        evolved_word, clean_group)

                    if self.enable_learning and quality_score > 0.3:
                        self.learning_system.record_generation_attempt(
                            clean_group, evolved_word, quality_score, False
                        )

                    if self.enable_caching:
                        is_valid, previous = self.consistency_validator.validate_translation(
                            '|'.join(clean_group), evolved_word
                        )

                        if not is_valid and previous:
                            if self.enable_learning:
                                confidence = self.learning_system.get_confidence_for_pattern(
                                    clean_group)
                                if confidence > 0.7:
                                    evolved_word = previous

                        self.translation_cache.set_translation(
                            clean_group, evolved_word)
                        self.consistency_validator.record_translation(
                            '|'.join(clean_group), evolved_word)

                    if self.enable_learning:
                        cache_key = '|'.join(clean_group)
                        self.convergence_engine.record_translation(
                            cache_key, evolved_word)

                        converged, preferred = self.convergence_engine.check_convergence(
                            cache_key)
                        if converged and preferred:
                            evolved_word = preferred
                            if self.enable_caching:
                                self.translation_cache.merge_variations(
                                    clean_group, preferred)

                    processed_word = evolved_word.capitalize() if is_caps else evolved_word

                    line_tokens.append({
                        "word": processed_word,
                        "prefix": prefix,
                        "suffix": suffix,
                        "original": clean_group,
                        "from_cache": False
                    })

            line_tokens = self._apply_agglutination_logic(line_tokens)

            processed_words = []
            for token in line_tokens:
                w = self._apply_orthography(token["word"])
                processed_words.append(
                    f"{token['prefix']}{w}{token['suffix']}")

            final_lines.append(" ".join(processed_words))

        if self.enable_caching:
            self.translation_cache.save_cache()
            self.morpheme_cache.save_morphemes()
            self.contextual_memory.save_memory()

        if self.enable_learning:
            self.learning_system.save_learning_data()

        if self.enable_context:
            self.semantic_engine.save_context_data()

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

        if self.enable_caching:
            cached_root = self.morpheme_cache.get_root('|'.join(valid_words))
            if cached_root:
                return cached_root

        root_seed = self._get_deterministic_hash("|".join(word_group))

        syllable_pools = []
        for word in valid_words:
            syllables = self.morphology_analyzer.extract_syllables_advanced(
                word,
                self.phonotactics.get('diphthongs', [])
            )
            syllable_pools.append(syllables)

        if not any(syllable_pools):
            return ""

        target_len = 0
        for idx, weight in enumerate(self.fusion_weights):
            if idx < len(syllable_pools) and syllable_pools[idx]:
                target_len += len(syllable_pools[idx]) * weight

        max_syl = max(1, int(round(target_len)))
        root_syllables = []

        for s_idx in range(max_syl):
            candidates = []
            for p in syllable_pools:
                if p:
                    candidates.append(p[s_idx % len(p)])

            if not candidates:
                continue

            syl_hash = (root_seed + s_idx) % (2**32)
            blended = self._blend_syllables(candidates, syl_hash)
            root_syllables.append(blended)

        result = "".join(root_syllables)

        if self.enable_caching and result:
            self.morpheme_cache.add_root('|'.join(valid_words), result)

        return result

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
            result = re.sub(r'(.)\1{2,}', r'\1', result)

            if len(result) > 4 and result[-1] in vowels:
                if drift_seed % 100 < 25:
                    result = result[:-1]

            result = result.replace('th', 't').replace(
                'ph', 'f').replace('qu', 'k')

        result = self._apply_phonotactics(result, drift_seed)
        return result

    def _syllabify(self, word: str) -> List[str]:
        return self.morphology_analyzer.extract_syllables_advanced(
            word,
            self.phonotactics.get('diphthongs', [])
        )

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

        base = options[primary_idx] if primary_idx < len(
            options) else options[0]
        alt = options[secondary_idx] if secondary_idx < len(options) else base

        morpheme_retention = self.fusion_rules.get('morpheme_retention', 0.5)

        if (seed >> 4) % 100 < (morpheme_retention * 100):
            return base

        onset = self._get_onset(base)
        nucleus = self._get_nucleus(alt if (seed % 2 == 0) else base)
        coda = self._get_coda(base if (seed % 3 == 0) else alt)

        blended = onset + nucleus + coda

        if not blended:
            return base

        return blended

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

        pattern = f'([^{v_str}\\s]{{{max_c + 1},}})'
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

                    if self.morphology_analyzer.detect_stacking(combined):
                        new_tokens.append(curr)
                        i += 1
                        continue

                    if self.evolution_stage == "archaic":
                        combined = re.sub(r'([aeiou])\1+', r'\1\1', combined)

                    new_tokens.append({
                        "word": combined,
                        "prefix": curr["prefix"],
                        "suffix": nxt["suffix"],
                        "original": curr["original"] + nxt["original"],
                        "from_cache": False
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

    def consolidate_cache(self, min_frequency: int = 3):
        if not self.enable_caching:
            return 0

        consolidated = self.translation_cache.consolidate_variations(
            min_frequency)
        self.translation_cache.save_cache()
        return consolidated

    def consolidate_learning(self, min_usage: int = 5, min_confidence: float = 0.6):
        if not self.enable_learning:
            return 0

        consolidated_rules = self.learning_system.consolidate_rules(
            min_usage, min_confidence)
        cleaned_patterns = self.learning_system.cleanup_low_quality_patterns()
        self.learning_system.save_learning_data()

        return consolidated_rules + cleaned_patterns

    def get_statistics(self) -> Dict:
        stats = {
            'profile_id': self.id,
            'bases': self.bases,
            'weights': self.fusion_weights,
            'evolution_stage': self.evolution_stage
        }

        if self.enable_caching:
            stats['cache'] = self.translation_cache.get_statistics()

        if self.enable_learning:
            stats['learning'] = self.learning_system.get_learning_statistics()
            stats['convergence'] = self.convergence_engine.get_stability_report()

        if self.enable_context:
            stats['consistency'] = {
                'rate': self.consistency_validator.get_consistency_rate(),
                'inconsistencies': len(self.consistency_validator.get_inconsistencies())
            }

        return stats

    def export_dictionary(self, output_path: str, min_frequency: int = 1) -> int:
        if not self.enable_caching:
            return 0

        return self.translation_cache.export_dictionary(output_path, min_frequency)

    def optimize_weights(self):
        if not self.enable_learning:
            return self.fusion_weights

        optimal_weights = self.adaptive_weights.get_optimal_weights()
        self.fusion_weights = optimal_weights
        self._normalize_weights()

        return self.fusion_weights
