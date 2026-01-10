import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict, Counter
from datetime import datetime
import statistics


class OriginalLanguageLearningSystem:
    def __init__(self, language_id: str, learning_dir: str = "original_learning"):
        self.language_id = language_id
        self.learning_dir = Path(learning_dir)
        self.learning_dir.mkdir(exist_ok=True, parents=True)
        
        self.patterns_file = self.learning_dir / f"{language_id}_patterns.json"
        self.stats_file = self.learning_dir / f"{language_id}_stats.json"
        self.frequency_file = self.learning_dir / f"{language_id}_frequency.json"
        
        self.concept_to_word: Dict[str, str] = {}
        self.word_to_concept: Dict[str, str] = {}
        self.phoneme_frequencies: Dict[str, int] = defaultdict(int)
        self.syllable_frequencies: Dict[str, int] = defaultdict(int)
        self.word_length_distribution: List[int] = []
        self.generation_history: List[Dict] = []
        
        self.quality_scores: Dict[str, float] = {}
        self.usage_counts: Dict[str, int] = defaultdict(int)
        
        self.load_learning_data()
    
    def load_learning_data(self):
        if self.patterns_file.exists():
            try:
                with open(self.patterns_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.concept_to_word = data.get('concept_to_word', {})
                    self.word_to_concept = data.get('word_to_concept', {})
                    self.phoneme_frequencies = defaultdict(int, data.get('phoneme_frequencies', {}))
                    self.syllable_frequencies = defaultdict(int, data.get('syllable_frequencies', {}))
                    self.word_length_distribution = data.get('word_length_distribution', [])
            except:
                pass
        
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.quality_scores = data.get('quality_scores', {})
                    self.usage_counts = defaultdict(int, data.get('usage_counts', {}))
                    self.generation_history = data.get('generation_history', [])
            except:
                pass
    
    def save_learning_data(self):
        patterns_data = {
            'concept_to_word': self.concept_to_word,
            'word_to_concept': self.word_to_concept,
            'phoneme_frequencies': dict(self.phoneme_frequencies),
            'syllable_frequencies': dict(self.syllable_frequencies),
            'word_length_distribution': self.word_length_distribution,
            'last_updated': datetime.now().isoformat()
        }
        with open(self.patterns_file, 'w', encoding='utf-8') as f:
            json.dump(patterns_data, f, indent=2, ensure_ascii=False)
        
        stats_data = {
            'quality_scores': self.quality_scores,
            'usage_counts': dict(self.usage_counts),
            'generation_history': self.generation_history[-1000:],
            'last_updated': datetime.now().isoformat()
        }
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats_data, f, indent=2, ensure_ascii=False)
    
    def record_generation(self, concept: str, generated_word: str, 
                         quality_score: float, phonemes_used: List[str]):
        self.concept_to_word[concept] = generated_word
        self.word_to_concept[generated_word] = concept
        
        self.quality_scores[generated_word] = quality_score
        self.usage_counts[concept] += 1
        
        for phoneme in phonemes_used:
            self.phoneme_frequencies[phoneme] += 1
        
        self.word_length_distribution.append(len(generated_word))
        
        self.generation_history.append({
            'concept': concept,
            'word': generated_word,
            'quality': quality_score,
            'timestamp': datetime.now().isoformat()
        })
        
        if len(self.generation_history) > 1000:
            self.generation_history = self.generation_history[-800:]
    
    def get_word_for_concept(self, concept: str) -> Optional[str]:
        return self.concept_to_word.get(concept)
    
    def get_concept_for_word(self, word: str) -> Optional[str]:
        return self.word_to_concept.get(word)
    
    def get_statistics(self) -> Dict:
        total_words = len(self.concept_to_word)
        
        avg_quality = 0.0
        if self.quality_scores:
            avg_quality = statistics.mean(self.quality_scores.values())
        
        avg_length = 0.0
        if self.word_length_distribution:
            avg_length = statistics.mean(self.word_length_distribution)
        
        most_common_phonemes = Counter(self.phoneme_frequencies).most_common(10)
        
        return {
            'total_words': total_words,
            'unique_words': len(self.word_to_concept),
            'average_quality': avg_quality,
            'average_word_length': avg_length,
            'most_common_phonemes': most_common_phonemes,
            'total_generations': len(self.generation_history)
        }
    
    def export_dictionary(self, output_path: str, format: str = 'json') -> int:
        if format == 'json':
            dictionary = [
                {
                    'concept': concept,
                    'word': word,
                    'quality': self.quality_scores.get(word, 0.0),
                    'usage': self.usage_counts.get(concept, 0)
                }
                for concept, word in sorted(self.concept_to_word.items())
            ]
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(dictionary, f, indent=2, ensure_ascii=False)
            
            return len(dictionary)
        
        elif format == 'txt':
            with open(output_path, 'w', encoding='utf-8') as f:
                for concept, word in sorted(self.concept_to_word.items()):
                    f.write(f"{concept}\t{word}\n")
            
            return len(self.concept_to_word)
        
        elif format == 'csv':
            import csv
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Concept', 'Word', 'Quality', 'Usage Count'])
                
                for concept, word in sorted(self.concept_to_word.items()):
                    writer.writerow([
                        concept,
                        word,
                        self.quality_scores.get(word, 0.0),
                        self.usage_counts.get(concept, 0)
                    ])
            
            return len(self.concept_to_word)
        
        return 0


class PhonemeDistributionAnalyzer:
    def __init__(self, learning_system: OriginalLanguageLearningSystem):
        self.learning = learning_system
    
    def analyze_distribution(self) -> Dict:
        total_phonemes = sum(self.learning.phoneme_frequencies.values())
        
        if total_phonemes == 0:
            return {
                'entropy': 0.0,
                'distribution': {},
                'uniformity_score': 0.0
            }
        
        probabilities = {
            phoneme: count / total_phonemes
            for phoneme, count in self.learning.phoneme_frequencies.items()
        }
        
        import math
        entropy = -sum(p * math.log2(p) for p in probabilities.values() if p > 0)
        
        max_entropy = math.log2(len(probabilities)) if len(probabilities) > 0 else 0
        uniformity_score = entropy / max_entropy if max_entropy > 0 else 0
        
        return {
            'entropy': entropy,
            'max_entropy': max_entropy,
            'uniformity_score': uniformity_score,
            'distribution': probabilities,
            'total_phonemes': total_phonemes
        }
    
    def detect_gaps(self, phoneme_inventory: Dict[str, List[str]]) -> List[str]:
        all_phonemes = set(phoneme_inventory['vowels'] + phoneme_inventory['consonants'])
        used_phonemes = set(self.learning.phoneme_frequencies.keys())
        
        unused = all_phonemes - used_phonemes
        return list(unused)
    
    def get_recommendations(self, phoneme_inventory: Dict[str, List[str]]) -> List[str]:
        recommendations = []
        
        gaps = self.detect_gaps(phoneme_inventory)
        if gaps:
            recommendations.append(f"Fonemas não utilizados: {', '.join(gaps[:5])}")
        
        distribution = self.analyze_distribution()
        if distribution['uniformity_score'] < 0.5:
            recommendations.append("Distribuição de fonemas desequilibrada - considere gerar mais palavras")
        
        if len(self.learning.word_length_distribution) > 10:
            avg_len = statistics.mean(self.learning.word_length_distribution)
            if avg_len < 3:
                recommendations.append("Palavras muito curtas em média - considere aumentar complexidade silábica")
            elif avg_len > 6:
                recommendations.append("Palavras muito longas em média - considere simplificar estrutura")
        
        return recommendations


class QualityMetrics:
    @staticmethod
    def calculate_word_quality(word: str, 
                              phoneme_inventory: Dict[str, List[str]],
                              constraints: Dict) -> float:
        scores = []
        
        length_score = QualityMetrics._score_length(word)
        scores.append(('length', length_score, 0.2))
        
        phoneme_score = QualityMetrics._score_phoneme_validity(word, phoneme_inventory)
        scores.append(('phoneme', phoneme_score, 0.3))
        
        structure_score = QualityMetrics._score_structure(word, phoneme_inventory, constraints)
        scores.append(('structure', structure_score, 0.3))
        
        euphony_score = QualityMetrics._score_euphony(word, phoneme_inventory)
        scores.append(('euphony', euphony_score, 0.2))
        
        total_weight = sum(weight for _, _, weight in scores)
        final_score = sum(score * weight for _, score, weight in scores) / total_weight
        
        return final_score
    
    @staticmethod
    def _score_length(word: str) -> float:
        ideal_length = 5
        length = len(word)
        
        if 3 <= length <= 7:
            return 1.0
        elif 2 <= length <= 9:
            return 0.8
        else:
            deviation = abs(length - ideal_length)
            return max(0.0, 1.0 - (deviation * 0.15))
    
    @staticmethod
    def _score_phoneme_validity(word: str, phoneme_inventory: Dict[str, List[str]]) -> float:
        all_phonemes = set(phoneme_inventory['vowels'] + phoneme_inventory['consonants'])
        
        valid_chars = 0
        total_chars = len(word)
        
        i = 0
        while i < len(word):
            found = False
            for length in [2, 1]:
                if i + length <= len(word):
                    segment = word[i:i+length]
                    if segment in all_phonemes:
                        valid_chars += length
                        i += length
                        found = True
                        break
            if not found:
                i += 1
        
        return valid_chars / total_chars if total_chars > 0 else 0.0
    
    @staticmethod
    def _score_structure(word: str, phoneme_inventory: Dict[str, List[str]], 
                        constraints: Dict) -> float:
        vowels = set(phoneme_inventory['vowels'])
        consonants = set(phoneme_inventory['consonants'])
        
        has_vowel = any(c in vowels for c in word)
        if not has_vowel:
            return 0.0
        
        vowel_count = sum(1 for c in word if c in vowels)
        consonant_count = sum(1 for c in word if c in consonants)
        total = vowel_count + consonant_count
        
        if total == 0:
            return 0.0
        
        vowel_ratio = vowel_count / total
        
        ideal_ratio = 0.4
        ratio_score = 1.0 - abs(vowel_ratio - ideal_ratio) * 2
        ratio_score = max(0.0, min(1.0, ratio_score))
        
        max_consonant_cluster = constraints.get('max_onset_consonants', 2)
        
        current_cluster = 0
        max_cluster_found = 0
        for c in word:
            if c in consonants:
                current_cluster += 1
                max_cluster_found = max(max_cluster_found, current_cluster)
            else:
                current_cluster = 0
        
        cluster_score = 1.0 if max_cluster_found <= max_consonant_cluster else 0.5
        
        return (ratio_score * 0.6 + cluster_score * 0.4)
    
    @staticmethod
    def _score_euphony(word: str, phoneme_inventory: Dict[str, List[str]]) -> float:
        vowels = set(phoneme_inventory['vowels'])
        
        if len(word) < 2:
            return 0.5
        
        alternation_score = 0.0
        alternations = 0
        total_transitions = len(word) - 1
        
        for i in range(len(word) - 1):
            curr_is_vowel = word[i] in vowels
            next_is_vowel = word[i+1] in vowels
            
            if curr_is_vowel != next_is_vowel:
                alternations += 1
        
        alternation_score = alternations / total_transitions if total_transitions > 0 else 0.5
        
        repetition_penalty = 0.0
        for i in range(len(word) - 1):
            if word[i] == word[i+1]:
                repetition_penalty += 0.1
        
        final_score = max(0.0, alternation_score - repetition_penalty)
        return min(1.0, final_score)


class ConceptMapper:
    def __init__(self):
        self.concept_categories = self._initialize_categories()
    
    def _initialize_categories(self) -> Dict[str, List[str]]:
        return {
            'semantic_prime': [
                'exist', 'happen', 'do', 'move', 'touch', 'see', 'hear', 'know',
                'think', 'want', 'feel', 'say', 'word', 'true', 'person', 'people',
                'body', 'place', 'time', 'now', 'before', 'after', 'good', 'bad',
                'big', 'small', 'many', 'few', 'all', 'some', 'one', 'two'
            ],
            'natural_world': [
                'sun', 'moon', 'star', 'water', 'fire', 'earth', 'wind', 'rain',
                'tree', 'flower', 'animal', 'bird', 'fish', 'stone', 'mountain',
                'river', 'ocean', 'forest', 'sky', 'cloud'
            ],
            'body_parts': [
                'head', 'eye', 'ear', 'nose', 'mouth', 'hand', 'foot', 'heart',
                'blood', 'bone', 'skin', 'hair', 'tooth', 'tongue', 'arm', 'leg'
            ],
            'kinship': [
                'mother', 'father', 'child', 'son', 'daughter', 'brother', 'sister',
                'family', 'ancestor', 'descendant'
            ],
            'time': [
                'day', 'night', 'morning', 'evening', 'yesterday', 'today', 'tomorrow',
                'year', 'season', 'past', 'present', 'future'
            ],
            'space': [
                'here', 'there', 'near', 'far', 'up', 'down', 'left', 'right',
                'inside', 'outside', 'above', 'below', 'front', 'back'
            ],
            'quantity': [
                'one', 'two', 'three', 'four', 'five', 'many', 'few', 'all', 'none',
                'more', 'less', 'much', 'little'
            ],
            'quality': [
                'good', 'bad', 'beautiful', 'ugly', 'strong', 'weak', 'hot', 'cold',
                'wet', 'dry', 'hard', 'soft', 'sharp', 'dull', 'smooth', 'rough'
            ],
            'action': [
                'go', 'come', 'take', 'give', 'eat', 'drink', 'sleep', 'wake',
                'live', 'die', 'kill', 'fight', 'hunt', 'build', 'break', 'make'
            ],
            'perception': [
                'see', 'hear', 'smell', 'taste', 'touch', 'feel', 'sense', 'perceive'
            ],
            'cognition': [
                'know', 'think', 'believe', 'understand', 'remember', 'forget',
                'learn', 'teach', 'imagine', 'dream'
            ],
            'emotion': [
                'love', 'hate', 'fear', 'anger', 'joy', 'sadness', 'surprise',
                'disgust', 'shame', 'pride'
            ]
        }
    
    def get_category(self, concept: str) -> Optional[str]:
        concept_lower = concept.lower()
        for category, concepts in self.concept_categories.items():
            if concept_lower in concepts:
                return category
        return None
    
    def get_all_core_concepts(self) -> List[str]:
        all_concepts = []
        for concepts in self.concept_categories.values():
            all_concepts.extend(concepts)
        return all_concepts
    
    def suggest_related_concepts(self, concept: str, max_suggestions: int = 5) -> List[str]:
        category = self.get_category(concept)
        if not category:
            return []
        
        related = [c for c in self.concept_categories[category] if c != concept.lower()]
        return related[:max_suggestions]
