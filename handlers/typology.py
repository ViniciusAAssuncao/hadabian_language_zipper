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


class PhonologicalDistance:
    def __init__(self, phoneme_feature_db: dict):
        self.db = phoneme_feature_db

    def _count_shared_features(self, p1: str, p2: str) -> tuple[int, int]:
        f1 = self.db.get(p1)
        f2 = self.db.get(p2)
        if not f1 or not f2:
            return (0, 0)

        shared = 0
        total = 0
        keys = set(f1.keys()).union(set(f2.keys()))

        for k in keys:
            total += 1
            if k in f1 and k in f2:
                if f1[k] == f2[k]:
                    shared += 1

        return (shared, total)

    def feature_similarity(self, p1: str, p2: str) -> float:
        if p1 == p2:
            return 1.0

        shared, total = self._count_shared_features(p1, p2)
        if total == 0:
            return 0.1

        return float(shared) / float(total)

    def substitution_cost(self, p1: str, p2: str) -> float:
        if p1 == p2:
            return 0.0

        f1 = self.db.get(p1, {})
        f2 = self.db.get(p2, {})

        is_v1 = "height" in f1 or "backness" in f1
        is_c1 = "place" in f1 or "manner" in f1
        is_v2 = "height" in f2 or "backness" in f2
        is_c2 = "place" in f2 or "manner" in f2

        if (is_v1 and is_c2) or (is_c1 and is_v2):
            return 1.5

        return 1.0 - self.feature_similarity(p1, p2)

    def weighted_edit_distance(self, s1: str, s2: str) -> float:
        m = len(s1)
        n = len(s2)
        dp = [[0.0] * (n + 1) for _ in range(m + 1)]

        for i in range(m + 1):
            dp[i][0] = float(i)
        for j in range(n + 1):
            dp[0][j] = float(j)

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                cost = self.substitution_cost(s1[i - 1], s2[j - 1])
                dp[i][j] = min(
                    dp[i - 1][j] + 1.0,
                    dp[i][j - 1] + 1.0,
                    dp[i - 1][j - 1] + cost
                )

        return dp[m][n]

    def normalized_similarity(self, s1: str, s2: str) -> float:
        if not s1 and not s2:
            return 1.0

        dist = self.weighted_edit_distance(s1, s2)
        max_possible_distance = max(len(s1), len(s2)) * 1.5

        if max_possible_distance == 0.0:
            return 1.0

        sim = 1.0 - (dist / max_possible_distance)
        return max(0.0, min(1.0, sim))


class SwadeshComparator:
    def __init__(self, swadesh_data: list, phonological_distance: PhonologicalDistance, cognate_threshold: float = 0.65):
        self.swadesh_data = swadesh_data
        self.phonological_distance = phonological_distance
        self.cognate_threshold = cognate_threshold

    def get_swadesh_concepts(self) -> list[str]:
        return self.swadesh_data

    def is_potential_cognate(self, similarity: float) -> bool:
        return similarity >= self.cognate_threshold

    def compare(self, engine_a, engine_b) -> dict:
        concepts = self.get_swadesh_concepts()
        total_concepts = len(concepts)

        found_in_a = 0
        found_in_b = 0
        compared = 0
        potential_cognate_pairs = 0
        total_similarity = 0.0
        pairs = []

        cache_a = engine_a.word_cache
        cache_b = engine_b.word_cache

        for concept in concepts:
            in_a = concept in cache_a
            in_b = concept in cache_b

            if in_a:
                found_in_a += 1
            if in_b:
                found_in_b += 1

            if in_a and in_b:
                entry_a = cache_a[concept]
                entry_b = cache_b[concept]

                word_a = entry_a.get("default", "") if isinstance(
                    entry_a, dict) else str(entry_a)
                word_b = entry_b.get("default", "") if isinstance(
                    entry_b, dict) else str(entry_b)

                if word_a and word_b:
                    similarity = self.phonological_distance.normalized_similarity(
                        word_a, word_b)
                    is_cognate = self.is_potential_cognate(similarity)

                    if is_cognate:
                        potential_cognate_pairs += 1

                    total_similarity += similarity
                    compared += 1

                    pairs.append({
                        "concept": concept,
                        "word_a": word_a,
                        "word_b": word_b,
                        "similarity": round(similarity, 2),
                        "is_potential_cognate": is_cognate
                    })

        not_found = total_concepts - compared
        avg_phonological_similarity = (
            total_similarity / compared) if compared > 0 else 0.0

        return {
            "concepts_in_swadesh": total_concepts,
            "found_in_a": found_in_a,
            "found_in_b": found_in_b,
            "compared": compared,
            "not_found": not_found,
            "avg_phonological_similarity": round(avg_phonological_similarity, 2),
            "potential_cognate_pairs": potential_cognate_pairs,
            "pairs": pairs
        }
