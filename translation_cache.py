import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import unicodedata


class TranslationCache:
    def __init__(self, profile_id: str, cache_dir: str = "cache"):
        self.profile_id = profile_id
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.cache_file = self.cache_dir / f"{profile_id}_cache.json"
        self.mapping: Dict[str, Dict] = {}
        self.frequency: Dict[str, int] = defaultdict(int)
        self.context_map: Dict[str, List[str]] = defaultdict(list)
        
        self.load_cache()
    
    def load_cache(self):
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.mapping = data.get('mapping', {})
                    self.frequency = defaultdict(int, data.get('frequency', {}))
                    self.context_map = defaultdict(list, data.get('context_map', {}))
            except:
                self.mapping = {}
                self.frequency = defaultdict(int)
                self.context_map = defaultdict(list)
    
    def save_cache(self):
        data = {
            'mapping': self.mapping,
            'frequency': dict(self.frequency),
            'context_map': dict(self.context_map)
        }
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_cache_key(self, source_words: List[str], normalize: bool = True) -> str:
        key = "|".join(source_words)
        if normalize:
            key = key.lower()
            key = unicodedata.normalize('NFD', key)
            key = ''.join(c for c in key if unicodedata.category(c) != 'Mn')
        return key
    
    def has_translation(self, source_words: List[str]) -> bool:
        key = self.get_cache_key(source_words)
        return key in self.mapping
    
    def get_translation(self, source_words: List[str]) -> Optional[str]:
        key = self.get_cache_key(source_words)
        if key in self.mapping:
            entry = self.mapping[key]
            self.frequency[key] += 1
            return entry['target']
        return None
    
    def set_translation(self, source_words: List[str], target: str, context: Optional[List[str]] = None):
        key = self.get_cache_key(source_words)
        
        if key not in self.mapping:
            self.mapping[key] = {
                'source': source_words,
                'target': target,
                'created_count': 1,
                'variations': [target]
            }
        else:
            self.mapping[key]['created_count'] += 1
            if target not in self.mapping[key]['variations']:
                self.mapping[key]['variations'].append(target)
        
        self.frequency[key] += 1
        
        if context:
            ctx_key = self.get_cache_key(context)
            if ctx_key not in self.context_map[key]:
                self.context_map[key].append(ctx_key)
    
    def get_most_frequent_translation(self, source_words: List[str]) -> Optional[str]:
        key = self.get_cache_key(source_words)
        if key in self.mapping:
            variations = self.mapping[key]['variations']
            if len(variations) == 1:
                return variations[0]
            
            var_freq = {}
            for var in variations:
                var_key = self.get_cache_key([var])
                var_freq[var] = self.frequency.get(var_key, 0)
            
            if var_freq:
                return max(var_freq.items(), key=lambda x: x[1])[0]
        return None
    
    def merge_variations(self, source_words: List[str], preferred_target: str):
        key = self.get_cache_key(source_words)
        if key in self.mapping:
            self.mapping[key]['target'] = preferred_target
            self.mapping[key]['variations'] = [preferred_target]
    
    def get_statistics(self) -> Dict:
        total_entries = len(self.mapping)
        entries_with_variations = sum(1 for entry in self.mapping.values() 
                                     if len(entry['variations']) > 1)
        total_frequency = sum(self.frequency.values())
        
        return {
            'total_entries': total_entries,
            'entries_with_variations': entries_with_variations,
            'variation_rate': entries_with_variations / total_entries if total_entries > 0 else 0,
            'total_uses': total_frequency,
            'avg_uses_per_entry': total_frequency / total_entries if total_entries > 0 else 0
        }
    
    def consolidate_variations(self, min_frequency: int = 3):
        consolidated = 0
        for key, entry in self.mapping.items():
            if len(entry['variations']) > 1 and self.frequency[key] >= min_frequency:
                most_frequent = self.get_most_frequent_translation(entry['source'])
                if most_frequent:
                    self.merge_variations(entry['source'], most_frequent)
                    consolidated += 1
        return consolidated
    
    def export_dictionary(self, output_path: str, min_frequency: int = 1):
        dictionary = []
        for key, entry in sorted(self.mapping.items(), key=lambda x: self.frequency[x[0]], reverse=True):
            if self.frequency[key] >= min_frequency:
                dictionary.append({
                    'source': ' '.join(entry['source']),
                    'target': entry['target'],
                    'frequency': self.frequency[key],
                    'variations': entry['variations']
                })
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(dictionary, f, indent=2, ensure_ascii=False)
        
        return len(dictionary)


class MorphemeCache:
    def __init__(self, profile_id: str, cache_dir: str = "cache"):
        self.profile_id = profile_id
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.morpheme_file = self.cache_dir / f"{profile_id}_morphemes.json"
        self.roots: Dict[str, str] = {}
        self.prefixes: Dict[str, str] = {}
        self.suffixes: Dict[str, str] = {}
        self.patterns: Dict[str, List[Dict]] = defaultdict(list)
        
        self.load_morphemes()
    
    def load_morphemes(self):
        if self.morpheme_file.exists():
            try:
                with open(self.morpheme_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.roots = data.get('roots', {})
                    self.prefixes = data.get('prefixes', {})
                    self.suffixes = data.get('suffixes', {})
                    self.patterns = defaultdict(list, data.get('patterns', {}))
            except:
                pass
    
    def save_morphemes(self):
        data = {
            'roots': self.roots,
            'prefixes': self.prefixes,
            'suffixes': self.suffixes,
            'patterns': dict(self.patterns)
        }
        with open(self.morpheme_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def add_root(self, source_root: str, target_root: str):
        key = source_root.lower()
        if key not in self.roots:
            self.roots[key] = target_root
    
    def get_root(self, source_root: str) -> Optional[str]:
        key = source_root.lower()
        return self.roots.get(key)
    
    def add_affix(self, source_affix: str, target_affix: str, affix_type: str):
        key = source_affix.lower()
        if affix_type == 'prefix':
            if key not in self.prefixes:
                self.prefixes[key] = target_affix
        elif affix_type == 'suffix':
            if key not in self.suffixes:
                self.suffixes[key] = target_affix
    
    def get_affix(self, source_affix: str, affix_type: str) -> Optional[str]:
        key = source_affix.lower()
        if affix_type == 'prefix':
            return self.prefixes.get(key)
        elif affix_type == 'suffix':
            return self.suffixes.get(key)
        return None
    
    def record_pattern(self, source_word: str, target_word: str, decomposition: Dict):
        pattern_key = f"{len(source_word)}_{len(target_word)}"
        self.patterns[pattern_key].append({
            'source': source_word,
            'target': target_word,
            'structure': decomposition
        })
    
    def find_similar_patterns(self, source_word: str, max_results: int = 5) -> List[Dict]:
        pattern_key = f"{len(source_word)}_"
        similar = []
        
        for key, patterns in self.patterns.items():
            if key.startswith(pattern_key):
                similar.extend(patterns)
        
        return similar[:max_results]


class ContextualMemory:
    def __init__(self, profile_id: str, cache_dir: str = "cache"):
        self.profile_id = profile_id
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.memory_file = self.cache_dir / f"{profile_id}_context.json"
        self.phrase_memory: Dict[str, List[Dict]] = defaultdict(list)
        self.semantic_clusters: Dict[str, List[str]] = defaultdict(list)
        
        self.load_memory()
    
    def load_memory(self):
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.phrase_memory = defaultdict(list, data.get('phrase_memory', {}))
                    self.semantic_clusters = defaultdict(list, data.get('semantic_clusters', {}))
            except:
                pass
    
    def save_memory(self):
        data = {
            'phrase_memory': dict(self.phrase_memory),
            'semantic_clusters': dict(self.semantic_clusters)
        }
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def add_phrase_context(self, phrase: str, translation: str, surrounding_words: List[str]):
        key = self._normalize_phrase(phrase)
        context_entry = {
            'translation': translation,
            'context': surrounding_words,
            'length': len(phrase.split())
        }
        
        if context_entry not in self.phrase_memory[key]:
            self.phrase_memory[key].append(context_entry)
    
    def get_phrase_translations(self, phrase: str) -> List[Dict]:
        key = self._normalize_phrase(phrase)
        return self.phrase_memory.get(key, [])
    
    def _normalize_phrase(self, phrase: str) -> str:
        normalized = phrase.lower().strip()
        normalized = unicodedata.normalize('NFD', normalized)
        normalized = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
        return normalized
    
    def add_to_semantic_cluster(self, word: str, related_words: List[str]):
        key = word.lower()
        for related in related_words:
            if related not in self.semantic_clusters[key]:
                self.semantic_clusters[key].append(related)
    
    def get_semantic_cluster(self, word: str) -> List[str]:
        key = word.lower()
        return self.semantic_clusters.get(key, [])
    
    def find_best_translation_by_context(self, phrase: str, context_words: List[str]) -> Optional[str]:
        translations = self.get_phrase_translations(phrase)
        if not translations:
            return None
        
        if len(translations) == 1:
            return translations[0]['translation']
        
        context_set = set(w.lower() for w in context_words)
        best_match = None
        best_score = -1
        
        for trans in translations:
            trans_context = set(w.lower() for w in trans['context'])
            overlap = len(context_set & trans_context)
            if overlap > best_score:
                best_score = overlap
                best_match = trans['translation']
        
        return best_match if best_match else translations[0]['translation']