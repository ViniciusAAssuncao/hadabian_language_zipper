import math


class PhonologicalDispersion:
    def __init__(self, phoneme_feature_db: dict):
        self.db = phoneme_feature_db
        self.height_map = {
            "high": 1.0,
            "near-high": 0.85,
            "high-mid": 0.7,
            "mid": 0.5,
            "low-mid": 0.35,
            "near-low": 0.15,
            "low": 0.0
        }
        self.backness_map = {
            "front": 0.0,
            "near-front": 0.25,
            "central": 0.5,
            "near-back": 0.75,
            "back": 1.0
        }
        self.place_map = {
            "bilabial": 0.0,
            "labiodental": 0.1,
            "dental": 0.2,
            "alveolar": 0.3,
            "postalveolar": 0.4,
            "retroflex": 0.5,
            "palatal": 0.6,
            "velar": 0.7,
            "uvular": 0.8,
            "pharyngeal": 0.9,
            "glottal": 1.0
        }
        self.manner_map = {
            "stop": 1.0,
            "plosive": 1.0,
            "affricate": 0.9,
            "nasal": 0.8,
            "trill": 0.6,
            "tap": 0.5,
            "flap": 0.5,
            "fricative": 0.4,
            "lateral": 0.3,
            "lateral fricative": 0.3,
            "approximant": 0.2,
            "lateral approximant": 0.1
        }

    def _get_vowel_coordinates(self, vowel: str) -> tuple[float, float]:
        features = self.db.get(vowel, {})
        h_val = self.height_map.get(features.get("height", ""), 0.5)
        b_val = self.backness_map.get(features.get("backness", ""), 0.5)
        return (h_val, b_val)

    def _get_consonant_coordinates(self, consonant: str) -> tuple[float, float]:
        features = self.db.get(consonant, {})
        p_val = self.place_map.get(features.get("place", ""), 0.5)
        m_val = self.manner_map.get(features.get("manner", ""), 0.5)
        return (p_val, m_val)

    def compute_vowel_dispersion(self, vowel_inventory: list[str]) -> float:
        if len(vowel_inventory) < 2:
            return 0.0
        coords = [self._get_vowel_coordinates(v) for v in vowel_inventory]
        return self._compute_dispersion(coords)

    def compute_consonant_dispersion(self, consonant_inventory: list[str]) -> float:
        if len(consonant_inventory) < 2:
            return 0.0
        coords = [self._get_consonant_coordinates(
            c) for c in consonant_inventory]
        return self._compute_dispersion(coords)

    def _compute_dispersion(self, coords: list[tuple[float, float]]) -> float:
        min_dists = []
        for i, c1 in enumerate(coords):
            dists = []
            for j, c2 in enumerate(coords):
                if i != j:
                    dist = math.sqrt((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2)
                    dists.append(dist)
            if dists:
                min_dists.append(min(dists))

        if not min_dists:
            return 0.0

        avg_min_dist = sum(min_dists) / len(min_dists)
        max_theoretical = 1.0 / math.sqrt(len(coords))
        score = avg_min_dist / max_theoretical
        return min(1.0, max(0.0, score))

    def analyze_inventory(self, profile: dict) -> dict:
        pt = profile.get("phonotactics", {})
        vowels_raw = pt.get("vowels", [])
        vowels = list(vowels_raw) if isinstance(
            vowels_raw, str) else vowels_raw

        consonants_raw = pt.get("consonants", [])
        consonants = list(consonants_raw) if isinstance(
            consonants_raw, str) else consonants_raw

        v_dispersion = self.compute_vowel_dispersion(vowels)
        c_dispersion = self.compute_consonant_dispersion(consonants)

        if vowels and consonants:
            overall = (v_dispersion + c_dispersion) / 2.0
        else:
            overall = v_dispersion or c_dispersion

        analysis = {
            "vowel_dispersion": round(v_dispersion, 2),
            "consonant_dispersion": round(c_dispersion, 2),
            "overall": round(overall, 2),
            "vowel_count": len(vowels),
            "consonant_count": len(consonants),
            "warnings": [],
            "suggestions": {
                "vowels": [],
                "consonants": []
            }
        }

        analysis["warnings"] = self.generate_warnings(analysis)
        analysis["suggestions"]["vowels"] = self.suggest_additions(
            vowels, "vowels", 2)
        analysis["suggestions"]["consonants"] = self.suggest_additions(
            consonants, "consonants", 2)

        return analysis

    def generate_warnings(self, analysis: dict) -> list[str]:
        warnings = []
        if analysis["vowel_dispersion"] < 0.6 and analysis["vowel_count"] >= 2:
            warnings.append(
                "Inventário vocálico possui baixa dispersão, concentrando fonemas em uma mesma região articulatória.")
        if analysis["consonant_dispersion"] < 0.6 and analysis["consonant_count"] >= 2:
            warnings.append(
                "Inventário consonantal está aglomerado na região alveolar ou possui distâncias subótimas. Considere adicionar fonemas labiais ou velares.")
        if analysis["vowel_count"] > 0 and analysis["vowel_count"] < 3:
            warnings.append(
                "Inventário de vogais muito pequeno — incomum tipologicamente.")
        if analysis["consonant_count"] > 0 and analysis["consonant_count"] < 6:
            warnings.append(
                "Inventário de consoantes muito pequeno — incomum tipologicamente.")
        return warnings

    def suggest_additions(self, inventory: list[str], type_key: str, count: int) -> list[str]:
        if type_key == "vowels":
            candidates = ["i", "e", "a", "o",
                          "u", "y", "ø", "ɛ", "ɔ", "ɯ", "ɨ"]
        else:
            candidates = ["p", "t", "k", "m", "n", "s",
                          "f", "l", "r", "w", "j", "h", "g", "b", "d"]

        best_additions = []
        current_inv = list(inventory)

        for _ in range(count):
            best_score = -1.0
            best_phoneme = None
            for cand in candidates:
                if cand not in current_inv:
                    test_inv = current_inv + [cand]
                    if type_key == "vowels":
                        score = self.compute_vowel_dispersion(test_inv)
                    else:
                        score = self.compute_consonant_dispersion(test_inv)

                    if score > best_score:
                        best_score = score
                        best_phoneme = cand

            if best_phoneme:
                current_inv.append(best_phoneme)
                best_additions.append(best_phoneme)

        return best_additions
