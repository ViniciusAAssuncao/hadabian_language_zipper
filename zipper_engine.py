import hashlib
import json
import re
from typing import List, Dict, Tuple, Optional
import unicodedata


class ZipperEngine:
    def __init__(self, profile_path: str):
        with open(profile_path, 'r', encoding='utf-8') as f:
            self.profile = json.load(f)
        
        self.id = self.profile.get('id', 'unknown')
        self.name = self.profile.get('name', 'Unknown')
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
    
    def process_texts(self, base_texts: List[str]) -> str:
        if len(base_texts) != len(self.bases):
            raise ValueError(f"Expected {len(self.bases)} base texts, got {len(base_texts)}")
        
        normalized_texts = [self._normalize_text(text) for text in base_texts]
        word_groups = self._align_word_groups(normalized_texts)
        
        result_words = []
        for group in word_groups:
            fused_word = self._fuse_word_group(group)
            result_words.append(fused_word)
        
        result_text = ' '.join(result_words)
        result_text = self._apply_orthography(result_text)
        result_text = self._apply_capitalization(result_text, base_texts[0])
        
        return result_text
    
    def _normalize_text(self, text: str) -> str:
        text = text.strip()
        if not self.fusion_rules.get('preserve_accents', False):
            text = self._remove_accents(text)
        return text
    
    def _remove_accents(self, text: str) -> str:
        nfd = unicodedata.normalize('NFD', text)
        return ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')
    
    def _align_word_groups(self, texts: List[str]) -> List[List[str]]:
        word_lists = [text.split() for text in texts]
        max_len = max(len(wl) for wl in word_lists)
        
        aligned_groups = []
        for i in range(max_len):
            group = []
            for word_list in word_lists:
                if i < len(word_list):
                    group.append(word_list[i])
                else:
                    group.append('')
            aligned_groups.append(group)
        
        return aligned_groups
    
    def _fuse_word_group(self, word_group: List[str]) -> str:
        valid_words = [w for w in word_group if w]
        if not valid_words:
            return ''
        
        seed_str = '|'.join(word_group) + f'|{self.id}|{self.global_seed}'
        seed_hash = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16)
        
        syllable_groups = [self._syllabify(word) for word in valid_words]
        
        max_syllables = max(len(sg) for sg in syllable_groups)
        
        result_syllables = []
        for syl_idx in range(max_syllables):
            available_syllables = []
            source_indices = []
            
            for src_idx, syl_group in enumerate(syllable_groups):
                if syl_idx < len(syl_group):
                    available_syllables.append(syl_group[syl_idx])
                    source_indices.append(src_idx)
            
            if not available_syllables:
                continue
            
            position_seed = (seed_hash + syl_idx * 7919) % (2**32)
            chosen_idx = position_seed % len(available_syllables)
            source_lang_idx = source_indices[chosen_idx]
            
            weight = self.fusion_weights[source_lang_idx] if source_lang_idx < len(self.fusion_weights) else 0.5
            
            if weight > 0.5:
                chosen_syl = available_syllables[chosen_idx]
            else:
                blend_syl = self._blend_syllables(available_syllables, position_seed)
                chosen_syl = blend_syl
            
            result_syllables.append(chosen_syl)
        
        fused_word = ''.join(result_syllables)
        fused_word = self._apply_phonotactics(fused_word, seed_hash)
        
        return fused_word
    
    def _syllabify(self, word: str) -> List[str]:
        if not word:
            return []
        
        word = word.lower()
        vowels = set('aeiouàâäãåæèéêëìíîïòóôöõøùúûüýÿœ')
        
        syllables = []
        current_syl = ''
        
        i = 0
        while i < len(word):
            char = word[i]
            current_syl += char
            
            if char in vowels:
                if i + 1 < len(word) and word[i + 1] in vowels:
                    current_syl += word[i + 1]
                    i += 1
                
                if i + 1 < len(word) and word[i + 1] not in vowels:
                    consonant_cluster = ''
                    j = i + 1
                    while j < len(word) and word[j] not in vowels:
                        consonant_cluster += word[j]
                        j += 1
                    
                    if len(consonant_cluster) > 1:
                        split_point = len(consonant_cluster) // 2
                        current_syl += consonant_cluster[:split_point]
                        syllables.append(current_syl)
                        current_syl = consonant_cluster[split_point:]
                        i = j - len(consonant_cluster) + split_point
                    else:
                        current_syl += consonant_cluster
                        syllables.append(current_syl)
                        current_syl = ''
                        i = j
                    continue
                else:
                    syllables.append(current_syl)
                    current_syl = ''
            
            i += 1
        
        if current_syl:
            if syllables:
                syllables[-1] += current_syl
            else:
                syllables.append(current_syl)
        
        return syllables if syllables else [word]
    
    def _blend_syllables(self, syllables: List[str], seed: int) -> str:
        if not syllables:
            return ''
        if len(syllables) == 1:
            return syllables[0]
        
        choice = seed % 4
        
        if choice == 0:
            onset = self._extract_onset(syllables[0])
            nucleus = self._extract_nucleus(syllables[1])
            coda = self._extract_coda(syllables[0])
            return onset + nucleus + coda
        elif choice == 1:
            onset = self._extract_onset(syllables[1])
            nucleus = self._extract_nucleus(syllables[0])
            coda = self._extract_coda(syllables[1])
            return onset + nucleus + coda
        elif choice == 2:
            mid = len(syllables[0]) // 2
            return syllables[0][:mid] + syllables[1][mid:]
        else:
            return syllables[seed % len(syllables)]
    
    def _extract_onset(self, syllable: str) -> str:
        vowels = set('aeiouàâäãåæèéêëìíîïòóôöõøùúûüýÿœ')
        onset = ''
        for char in syllable:
            if char.lower() not in vowels:
                onset += char
            else:
                break
        return onset
    
    def _extract_nucleus(self, syllable: str) -> str:
        vowels = set('aeiouàâäãåæèéêëìíîïòóôöõøùúûüýÿœ')
        onset_end = 0
        for i, char in enumerate(syllable):
            if char.lower() in vowels:
                onset_end = i
                break
        
        nucleus = ''
        for i in range(onset_end, len(syllable)):
            if syllable[i].lower() in vowels:
                nucleus += syllable[i]
            else:
                break
        
        return nucleus
    
    def _extract_coda(self, syllable: str) -> str:
        vowels = set('aeiouàâäãåæèéêëìíîïòóôöõøùúûüýÿœ')
        coda_start = len(syllable)
        for i in range(len(syllable) - 1, -1, -1):
            if syllable[i].lower() not in vowels:
                coda_start = i
            else:
                break
        
        if coda_start < len(syllable):
            return syllable[coda_start:]
        return ''
    
    def _apply_phonotactics(self, word: str, seed: int) -> str:
        vowels = set(self.phonotactics.get('vowels', 'aeiouàâäãåæèéêëìíîïòóôöõøùúûüýÿœ'))
        forbidden_finals = self.phonotactics.get('forbidden_final_consonants', [])
        max_consonant_cluster = self.phonotactics.get('max_consonant_cluster', 3)
        max_vowel_cluster = self.phonotactics.get('max_vowel_cluster', 2)
        
        if word and word[-1].lower() in forbidden_finals:
            replacement_vowels = list(vowels)
            if replacement_vowels:
                vowel_idx = seed % len(replacement_vowels)
                word = word[:-1] + replacement_vowels[vowel_idx]
        
        result = []
        consonant_count = 0
        vowel_count = 0
        
        for char in word:
            is_vowel = char.lower() in vowels
            
            if is_vowel:
                if vowel_count >= max_vowel_cluster:
                    consonant_count = 1
                    vowel_count = 0
                else:
                    result.append(char)
                    vowel_count += 1
                    consonant_count = 0
            else:
                if consonant_count >= max_consonant_cluster:
                    vowel_count = 1
                    consonant_count = 0
                else:
                    result.append(char)
                    consonant_count += 1
                    vowel_count = 0
        
        return ''.join(result)
    
    def _apply_orthography(self, text: str) -> str:
        long_vowel_map = self.orthography.get('long_vowel_mapping', {})
        primary_accent = self.orthography.get('primary_accent', '')
        transform_s_cedilla = self.orthography.get('transform_s_to_cedilla', False)
        
        for original, replacement in long_vowel_map.items():
            pattern = original * 2
            text = text.replace(pattern, replacement)
        
        if primary_accent == 'acute':
            text = text.replace('ä', 'á').replace('ö', 'ó').replace('ü', 'ú')
        elif primary_accent == 'circumflex':
            text = text.replace('ä', 'â').replace('ö', 'ô').replace('ü', 'û')
        elif primary_accent == 'grave':
            text = text.replace('ä', 'à').replace('ö', 'ò').replace('ü', 'ù')
        
        if transform_s_cedilla:
            text = text.replace('s', 'ç')
        
        return text
    
    def _apply_capitalization(self, result_text: str, reference_text: str) -> str:
        if not self.fusion_rules.get('preserve_caps', False):
            return result_text
        
        result_words = result_text.split()
        reference_words = reference_text.split()
        
        for i in range(min(len(result_words), len(reference_words))):
            if reference_words[i] and reference_words[i][0].isupper():
                if result_words[i]:
                    result_words[i] = result_words[i][0].upper() + result_words[i][1:]
        
        return ' '.join(result_words)