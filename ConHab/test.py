from engine import OriginalLanguageEngine
import json

def test_punctuation_fixes():
    engine = OriginalLanguageEngine('../conlangs/mabadi_language.json')
    
    test_cases = [
        "Mesmo que a espada trespasse o fino véu do coração e a lâmina rasgue a carne; o ódio não me cegará",
        "Não adianta dares uma mordida em cada maça, é necessário plantar uma macieira",
        "O mundo caminha para se tornar um lugar frio, não são as chuvas lá fora, é o frio. Eu sinto muito frio."
    ]
    
    print("--- Teste de Pontuação e Formatação ---")
    print(f"Estratégia de pontuação: {engine.profile['punctuation_profile']['attach_strategy']}")
    
    has_error = False
    
    for text in test_cases:
        print(f"\nOriginal: {text}")
        translation = engine.process_text(text)
        print(f"Mabádi:   {translation}")
        
        if "-,," in translation:
            print("ERRO CRÍTICO: Artefato '-,,' encontrado.")
            has_error = True
        
        if " ;" in translation:
             pass 
        
        tokens = translation.split()
        for t in tokens:
            if t.endswith("-") and len(t) > 1:
                next_idx = tokens.index(t) + 1
                if next_idx < len(tokens):
                    next_t = tokens[next_idx]
                    if next_t in [",", ";", ".", ":"]:
                        print(f"SUCESSO: Hífen '{t}' separado de pontuação '{next_t}'.")

    if not has_error:
        print("\nSUCESSO FINAL: Nenhuma anomalia crítica de pontuação detectada.")
    else:
        print("\nFALHA: Correções insuficientes.")

if __name__ == "__main__":
    test_punctuation_fixes()