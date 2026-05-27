CONTRACTIONS = {
    'do': ['de', 'o'], 'da': ['de', 'a'], 'dos': ['de', 'os'], 'das': ['de', 'as'],
    'no': ['em', 'o'], 'na': ['em', 'a'], 'nos': ['em', 'os'], 'nas': ['em', 'as'],
    'pelo': ['por', 'o'], 'pela': ['por', 'a'], 'pelos': ['por', 'os'], 'pelas': ['por', 'as'],
    'ao': ['a', 'o'], 'aos': ['a', 'os'],
    'dum': ['de', 'um'], 'duma': ['de', 'uma'],
    'num': ['em', 'um'], 'numa': ['em', 'uma']
}

NEGATION_TRIGGERS = {'não', 'nao', 'nem', 'jamais'}

PORTUGUESE_STOP_WORDS = {
    'o', 'a', 'os', 'as', 'de', 'do', 'da', 'dos', 'das',
    'um', 'uma', 'uns', 'umas', 'em', 'no', 'na', 'nos', 'nas',
    'por', 'para', 'com', 'que', 'e', 'ou', 'the', 'of', 'and',
    'a', 'an', 'in', 'on', 'at', 'for', 'to', 'by', 'is', 'são',
    'é', 'ser', 'estar', 'se'
}

DEFAULT_PHONEME_FEATURES = {
    "vowels": ["a", "e", "i", "o", "u"],
    "consonants": ["p", "t", "k", "b", "d", "g", "f", "v", "s", "z", "m", "n", "l", "r"]
}