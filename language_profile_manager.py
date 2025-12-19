import json
import os
from typing import Dict, List, Optional
from pathlib import Path


class LanguageProfileManager:
    def __init__(self, profiles_dir: str = "profiles"):
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(exist_ok=True)
        self.profiles: Dict[str, Dict] = {}
        self.load_all_profiles()
    
    def load_all_profiles(self):
        self.profiles = {}
        for file_path in self.profiles_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    profile = json.load(f)
                    profile_id = profile.get('id', file_path.stem)
                    self.profiles[profile_id] = profile
            except Exception as e:
                print(f"Error loading profile {file_path}: {e}")
    
    def get_profile(self, profile_id: str) -> Optional[Dict]:
        return self.profiles.get(profile_id)
    
    def get_all_profile_ids(self) -> List[str]:
        return sorted(self.profiles.keys())
    
    def get_profile_path(self, profile_id: str) -> Optional[Path]:
        for file_path in self.profiles_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    profile = json.load(f)
                    if profile.get('id') == profile_id:
                        return file_path
            except:
                continue
        return None
    
    def create_profile(self, profile_data: Dict) -> str:
        profile_id = profile_data.get('id', 'new_lang')
        file_path = self.profiles_dir / f"{profile_id}.json"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, indent=2, ensure_ascii=False)
        
        self.profiles[profile_id] = profile_data
        return profile_id
    
    def update_profile(self, profile_id: str, profile_data: Dict):
        file_path = self.get_profile_path(profile_id)
        if not file_path:
            file_path = self.profiles_dir / f"{profile_id}.json"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, indent=2, ensure_ascii=False)
        
        self.profiles[profile_id] = profile_data
    
    def delete_profile(self, profile_id: str) -> bool:
        file_path = self.get_profile_path(profile_id)
        if file_path and file_path.exists():
            file_path.unlink()
            if profile_id in self.profiles:
                del self.profiles[profile_id]
            return True
        return False
    
    def get_profile_summary(self, profile_id: str) -> str:
        profile = self.get_profile(profile_id)
        if not profile:
            return "Profile not found"
        
        name = profile.get('name', profile_id)
        desc = profile.get('description', 'No description')
        bases = ', '.join(profile.get('bases', []))
        
        return f"{name} ({profile_id})\nBases: {bases}\n{desc}"
    
    def create_default_profile(self) -> str:
        default_profile = {
            "id": "example",
            "name": "Example Language",
            "description": "An example constructed language profile",
            "bases": ["en", "es"],
            "fusion_weights": [0.6, 0.4],
            "fusion_rules": {
                "min_cut_point": 0.4,
                "preserve_caps": True,
                "preserve_accents": False,
                "contraction_handling": "separate"
            },
            "phonotactics": {
                "vowels": "aeiouàâäèéêëìíîïòóôöùúûü",
                "forbidden_final_consonants": ["h", "w"],
                "max_consonant_cluster": 3,
                "max_vowel_cluster": 2
            },
            "orthography": {
                "long_vowel_mapping": {
                    "a": "ä",
                    "o": "ö",
                    "u": "ü"
                },
                "primary_accent": "diaeresis",
                "transform_s_to_cedilla": False
            },
            "semantic_general": "neutral",
            "global_seed": 12345
        }
        
        return self.create_profile(default_profile)


class ProfileValidator:
    @staticmethod
    def validate_profile(profile: Dict) -> tuple[bool, List[str]]:
        errors = []
        
        if 'id' not in profile:
            errors.append("Missing required field: 'id'")
        
        if 'bases' not in profile or not isinstance(profile['bases'], list):
            errors.append("Missing or invalid 'bases' field (must be a list)")
        elif len(profile['bases']) < 1:
            errors.append("At least one base language is required")
        
        if 'fusion_weights' in profile:
            weights = profile['fusion_weights']
            if not isinstance(weights, list):
                errors.append("'fusion_weights' must be a list")
            elif len(weights) != len(profile.get('bases', [])):
                errors.append("'fusion_weights' length must match 'bases' length")
            elif not all(isinstance(w, (int, float)) and w >= 0 for w in weights):
                errors.append("All fusion weights must be non-negative numbers")
        
        if 'global_seed' in profile:
            seed = profile['global_seed']
            if not isinstance(seed, int):
                errors.append("'global_seed' must be an integer")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def sanitize_profile(profile: Dict) -> Dict:
        sanitized = profile.copy()
        
        if 'id' not in sanitized:
            sanitized['id'] = 'unnamed'
        
        if 'name' not in sanitized:
            sanitized['name'] = sanitized['id'].title()
        
        if 'description' not in sanitized:
            sanitized['description'] = ''
        
        if 'bases' not in sanitized or not sanitized['bases']:
            sanitized['bases'] = ['en']
        
        if 'fusion_weights' not in sanitized:
            n = len(sanitized['bases'])
            sanitized['fusion_weights'] = [1.0 / n] * n
        
        if 'fusion_rules' not in sanitized:
            sanitized['fusion_rules'] = {}
        
        if 'phonotactics' not in sanitized:
            sanitized['phonotactics'] = {
                'vowels': 'aeiou',
                'forbidden_final_consonants': [],
                'max_consonant_cluster': 3,
                'max_vowel_cluster': 2
            }
        
        if 'orthography' not in sanitized:
            sanitized['orthography'] = {}
        
        if 'global_seed' not in sanitized:
            sanitized['global_seed'] = 12345
        
        return sanitized