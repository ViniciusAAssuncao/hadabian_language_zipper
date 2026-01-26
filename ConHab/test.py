import json
from engine import OriginalLanguageEngine

# Inicializa a engine
engine = OriginalLanguageEngine("../conlangs/mabadi_language.json")

# Simula uma palavra (verbo 'escrever' -> raiz 'ktb' -> 'kiteb' ou similar)
# E simula features que ativariam o 1sg (n-PREFIXO ... t-SUFIXO)
lemma = "escrever"
word_base = engine._get_word_form(lemma) # Deve gerar algo como 'kiteb' ou raiz triconsonantal

# Features para Eu (1ª Pessoa Singular)
features = "VerbForm=Fin|Person=1|Number=Sing|Tense=Past"

# Aplica TAM manualmente para teste unitário
result = engine.tam_handler.apply_tam(word_base, features)

print(f"Lemma: {lemma}")
print(f"Base: {word_base}")
print(f"Features: {features}")
print(f"Resultado Final: {result}")

# Esperado: n{base}t (ex: nkitebt ou nktebt)
if result.startswith("n") and result.endswith("t"):
    print("SUCESSO: Marcação descontínua aplicada!")
else:
    print("FALHA: Marcação incorreta.")