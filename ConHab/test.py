# Exemplo de teste manual (pode ser executado em um shell Python ou script separado)
from engine import OriginalLanguageEngine

# Inicialize a engine
engine = OriginalLanguageEngine("./conlangs/mabadi_language.json")

# Simule a chamada interna da engine ou verifique a lógica do handler diretamente
dual_handler = engine.dual_handler

# Teste 1: Dual Nominativo (Sujeito)
# Esperado: Sufixo "āni"
word_nom = "kitab" # livro
feats_nom = "Number=Dual|Gender=Masc"
deprel_nom = "nsubj"
pos = "NOUN"
result_nom = dual_handler.apply_dual(word_nom, feats_nom, deprel_nom, pos)
print(f"Nominativo Dual: {result_nom}") # Deve imprimir: kitabāni

# Teste 2: Dual Acusativo (Objeto)
# Esperado: Sufixo "ajni"
word_acc = "kitab"
feats_acc = "Number=Dual|Gender=Masc"
deprel_acc = "obj"
result_acc = dual_handler.apply_dual(word_acc, feats_acc, deprel_acc, pos)
print(f"Acusativo Dual: {result_acc}") # Deve imprimir: kitabajni

# Teste 3: Não Dual (Singular)
# Esperado: Sem alteração pelo DualHandler
word_sg = "kitab"
feats_sg = "Number=Sing"
result_sg = dual_handler.apply_dual(word_sg, feats_sg, "nsubj", pos)
print(f"Singular: {result_sg}") # Deve imprimir: kitab