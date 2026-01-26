import json
from engine import SunLetterHandler

# Perfil de teste simplificado baseado no Mabádi
test_profile = {
    "determiner_system": {
        "definite_article": {
            "form": "ta",
            "variants": ["il"],
            "sun_letter_assimilation": True,
            "sun_letters": ["d", "n", "r", "s", "t", "x", "z"]
        }
    }
}

handler = SunLetterHandler(test_profile)

# Casos de Teste
tests = [
    ("il-", "dar", "id-"),      # Esperado: id- (assimilação de consoante)
    ("il", "xemx", "ix"),       # Esperado: ix (assimilação sem hífen)
    ("ta", "dar", "tad"),       # Esperado: tad (geminação após vogal)
    ("ta-", "tifel", "tat-"),   # Esperado: tat- (geminação com hífen)
    ("il-", "qamar", "il-"),    # Esperado: il- (letra lunar, sem mudança)
]

print("--- Iniciando Testes de Assimilação ---")
for article, noun, expected in tests:
    result = handler.assimilate(article, noun)
    status = "PASS" if result == expected else f"FAIL (Got: {result})"
    print(f"Artigo: '{article}' + Nome: '{noun}' -> Resultado: '{result}' | Esperado: '{expected}' [{status}]")

print("--- Fim dos Testes ---")