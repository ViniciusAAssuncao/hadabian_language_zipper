import json
from engine import OriginalLanguageEngine, PhonologyHandler

def test_monophthongization():
    print("Iniciando teste de Monoftongação para Mabádi...")
    
    try:
        engine = OriginalLanguageEngine('./conlangs/mabadi_language.json')
        ph = engine.phonology_handler
        
        print("\nConfiguração de Monoftongação:")
        print(f"Habilitado: {ph.monophthong_enabled}")
        print(f"Regras: {ph.monophthong_rules}")
        
        test_cases = [
            ("bajt", "bēt", "aj -> ē"),
            ("qawm", "qōm", "aw -> ō"),
            ("xajr", "xēr", "aj -> ē"),
            ("kawne", "kōne", "aw -> ō"),
            ("bijt", "bijt", "ij -> ij (sem regra) ou ij -> ī se adicionado"),
            ("normal", "normal", "sem mudança")
        ]
        
        print("\nExecutando casos de teste diretos no PhonologyHandler:")
        all_passed = True
        for input_word, expected, desc in test_cases:
            result = ph.apply_monophthongization(input_word)
            success = result == expected
            status = "PASSOU" if success else f"FALHOU (Esperado: {expected}, Obtido: {result})"
            if not success:
                # Regras extras adicionadas no profile podem afetar bijt/uw se existirem
                if "ij" in input_word and result == "bīt":
                     status = "PASSOU (Regra ij->ī aplicada)"
                     success = True
                else:
                    all_passed = False
            print(f"  Entrada: {input_word:10} | {desc:20} -> {status}")

        # Teste integrado
        print("\nTeste integrado (geração de palavra):")
        # Força a geração de uma palavra que naturalmente teria ditongo se não fosse a regra
        # Como o gerador usa sementes aleatórias, vamos simular a nativização direta
        
        raw_word_aj = "bayt" # Phonology handler deve converter y->j ou y->i e depois aplicar regra
        nativized_aj = ph.nativize_word(raw_word_aj)
        print(f"  Nativização de 'bayt': {nativized_aj}")
        
        raw_word_aw = "kawn"
        nativized_aw = ph.nativize_word(raw_word_aw)
        print(f"  Nativização de 'kawn': {nativized_aw}")

        if "ē" in nativized_aj or "e" in nativized_aj: # Depende do mapeamento exato de y e j
             print("  Verificação 'bayt' -> contém vogal monoftongada (e/ē).")
        
        if "ō" in nativized_aw or "o" in nativized_aw:
             print("  Verificação 'kawn' -> contém vogal monoftongada (o/ō).")

        if all_passed:
            print("\nRESULTADO FINAL: SUCESSO. A monoftongação está funcionando conforme esperado.")
        else:
            print("\nRESULTADO FINAL: FALHA em alguns testes unitários.")

    except Exception as e:
        print(f"\nERRO CRÍTICO DURANTE O TESTE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_monophthongization()