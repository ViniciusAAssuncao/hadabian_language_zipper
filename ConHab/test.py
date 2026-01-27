import json
from syntax_engine import CaseMorphology

def test_mabadi_dom():
    with open('./conlangs/mabadi_language.json', 'r', encoding='utf-8') as f:
        profile = json.load(f)
    
    cm = CaseMorphology(profile)
    
    # Caso 1: Animado e Definido (Deve marcar com "a")
    obj_animado = {
        'lemma': 'pai',
        'pos': 'NOUN',
        'feats': 'Definite=Def',
        'deprel': 'obj'
    }
    res1 = cm.apply_case("word", "OBJECT", "VSO", "obj", True, obj_animado)
    print(f"Teste 1 (Pai definido): {res1}") # Esperado: "a word"

    # Caso 2: Inanimado e Definido (Não deve marcar)
    obj_inanimado = {
        'lemma': 'pão',
        'pos': 'NOUN',
        'feats': 'Definite=Def',
        'deprel': 'obj'
    }
    res2 = cm.apply_case("word", "OBJECT", "VSO", "obj", True, obj_inanimado)
    print(f"Teste 2 (Pão definido): {res2}") # Esperado: "word"

    # Caso 3: Nome Próprio (Deve marcar por ser inerentemente animado/def)
    obj_proprio = {
        'lemma': 'Hadab',
        'pos': 'PROPN',
        'feats': '_',
        'deprel': 'obj'
    }
    
    res3 = cm.apply_case("Hadab", "OBJECT", "VSO", "obj", True, obj_proprio)
    print(f"Teste 3 (Nome Próprio): {res3}") # Esperado: "a Hadab"
    
    obj_indefinido = {
        'lemma': 'pai',
        'pos': 'NOUN',
        'feats': 'Definite=Ind', # Ou vazio, dependendo do seu parser
        'deprel': 'obj'
    }
    res4 = cm.apply_case("pai", "OBJECT", "VSO", "obj", True, obj_indefinido)
    print(f"Teste 4 (Pai indefinido): {res4}") # Esperado: "pai"

if __name__ == "__main__":
    test_mabadi_dom()