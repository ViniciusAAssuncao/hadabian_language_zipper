from engine import OriginalLanguageEngine

def test_accusative_elision():
    engine = OriginalLanguageEngine("./conlangs/mabadi_language.json")
    
    # Frase exemplo: "Eu vejo o pai"
    # "Eu" (1sg) -> "Jiena" (ou sujeito oculto)
    # "vejo" (ver) -> raiz gerada, ex: "nara"
    # "o" (artigo definido) -> "ta"
    # "pai" (animado, definido) -> trigger acusativo "a"
    # Ordem VSO esperada
    
    input_text = "Eu amo o pai."
    output_text = engine.process_text(input_text)
    
    print(f"Input: {input_text}")
    print(f"Output: {output_text}")
    
    # Verificação
    if "ata" in output_text.lower() and "a ta" not in output_text.lower():
        print("SUCESSO: Elisão 'a ta' -> 'ata' aplicada corretamente.")
    elif "a ta" in output_text.lower():
        print("FALHA: Sequência 'a ta' encontrada sem elisão.")
    else:
        print("INCONCLUSIVO: Termos esperados não encontrados (verificar geração de léxico).")

if __name__ == "__main__":
    test_accusative_elision()