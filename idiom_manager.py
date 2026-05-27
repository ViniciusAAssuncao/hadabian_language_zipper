import json
from pathlib import Path
from typing import List, Dict, Tuple, Set
from constants import CONTRACTIONS

class IdiomManager:
    def __init__(self, profile_id: str):
        self.profile_id = profile_id
        self.storage_path = Path(f"./cache/{profile_id}_idioms.json")
        self.idioms: Dict[str, Dict] = {}
        self.contractions = CONTRACTIONS
        self.load()

    def load(self):
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    self.idioms = json.load(f)
            except Exception:
                self.idioms = {}
        else:
            self.idioms = {}

    def save(self):
        if not self.storage_path.parent.exists():
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(self.idioms, f, indent=2, ensure_ascii=False)

    def add_idiom(self, expression: str, target: str, type: str = "lexical", tags: List[str] = None):
        key = expression.lower().strip()
        self.idioms[key] = {
            "target": target,
            "type": type,
            "tags": tags or []
        }
        self.save()

    def delete_idiom(self, expression: str):
        key = expression.lower().strip()
        if key in self.idioms:
            del self.idioms[key]
            self.save()

    def _expand_tokens(self, phrase: str) -> List[str]:
        tokens = phrase.lower().split()
        expanded = []
        for t in tokens:
            if t in self.contractions:
                expanded.extend(self.contractions[t])
            else:
                expanded.append(t)
        return expanded

    def process_functions(self, functions: List[Dict]) -> Tuple[List[Dict], Set[int]]:
        if not self.idioms:
            return functions, set()

        sorted_idioms = sorted(
            self.idioms.keys(), key=lambda k: len(k.split()), reverse=True)

        lemmas = [f.get('lemma', f['word']).lower().strip() for f in functions]
        words = [f['word'].lower().strip() for f in functions]
        indices_map = [f['index'] for f in functions]

        absorbed_indices = set()
        replacements = {}

        i = 0
        while i < len(functions):
            if indices_map[i] in absorbed_indices:
                i += 1
                continue

            match_found = False
            for phrase in sorted_idioms:
                phrase_parts = self._expand_tokens(phrase)
                k = len(phrase_parts)

                if i + k > len(functions):
                    continue

                current_indices = indices_map[i: i+k]
                if any(idx in absorbed_indices for idx in current_indices):
                    continue

                slice_lemmas = lemmas[i: i+k]
                slice_words = words[i: i+k]

                is_match = (slice_lemmas == phrase_parts) or (
                    slice_words == phrase_parts)

                if not is_match:
                    raw_parts = phrase.lower().split()
                    if len(raw_parts) == k:
                        is_match = (slice_lemmas == raw_parts) or (
                            slice_words == raw_parts)

                if is_match:
                    entry = self.idioms[phrase]
                    target = entry['target']

                    head_idx = indices_map[i]
                    replacements[head_idx] = {
                        'target': target,
                        'tags': entry.get('tags', []),
                        'type': entry.get('type', 'lexical')
                    }

                    for offset in range(1, k):
                        absorbed_indices.add(indices_map[i + offset])

                    i += k
                    match_found = True
                    break

            if not match_found:
                i += 1

        new_functions = []
        for func in functions:
            idx = func['index']

            if idx in absorbed_indices:
                continue

            if idx in replacements:
                data = replacements[idx]
                new_func = func.copy()
                new_func['lemma'] = data['target']
                new_func['word'] = data['target']
                new_func['pos'] = 'IDIOM'
                new_func['_fixed'] = True
                new_func['dependencies'] = []

                if data['tags']:
                    new_func['manual_tags'] = data['tags']

                new_functions.append(new_func)
            else:
                new_functions.append(func)

        return new_functions, absorbed_indices