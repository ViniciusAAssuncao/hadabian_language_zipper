import json
import os
import shutil
from engine import OriginalLanguageEngine

# Definição dos caminhos
PROFILE_DIR = "./conlangs"
PROFILE_NAME = "mabadi_language.json"
PROFILE_PATH = os.path.join(PROFILE_DIR, PROFILE_NAME)
BACKUP_PATH = os.path.join(PROFILE_DIR, f"{PROFILE_NAME}.bak")

def run_test():
    print("=== INICIANDO TESTE: PREPOSIÇÕES FLEXIONADAS ===")

    # 1. Backup do perfil original para não perder dados
    if os.path.exists(PROFILE_PATH):
        shutil.copy(PROFILE_PATH, BACKUP_PATH)
        print(f"[INFO] Backup criado em: {BACKUP_PATH}")
    else:
        print(f"[ERRO] Arquivo de perfil não encontrado em: {PROFILE_PATH}")
        return

    try:
        # 2. Carregar e Injetar Configuração no JSON
        with open(PROFILE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Injeção da configuração solicitada
        if "adposition_system" not in data:
            data["adposition_system"] = {}
        
        data["adposition_system"]["inflected_prepositions"] = {
            "enabled": True,
            "forms": {
                "fi": { "1sg": "fija", "2sg": "fik", "3sg": "fil" }
            }
        }

        with open(PROFILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        print("[INFO] Configuração injetada no perfil JSON.")

        # 3. Inicializar a Engine
        engine = OriginalLanguageEngine(PROFILE_PATH)
        print("[INFO] Engine inicializada.")

        # 4. Mock do Cache de Palavras
        # Força 'em' a ser traduzido como 'fi'
        engine.word_cache['em'] = {
            "lemma": "em",
            "default": "fi",
            "synsets": [{"word": "fi", "tags": ["preposition"], "affinity": 1.0}]
        }
        print("[INFO] Word Cache mockado: 'em' -> 'fi'")

        # 5. Teste Caso 1: Flexão/Absorção (em + mim -> fija)
        input_text_1 = "Eu estou em mim."
        print(f"\n--- Teste 1: '{input_text_1}' ---")
        
        output_1 = engine.process_text(input_text_1)
        print(f"Saída: '{output_1}'")

        if "fija" in output_1:
            print(">>> RESULTADO: SUCESSO (Contém 'fija')")
        else:
            print(">>> RESULTADO: FALHA (Não contém 'fija')")

        # 6. Teste Caso 2: Sem Flexão (em + casa -> fi ...)
        # Garantir que 'casa' tenha uma tradução para não gerar aleatório
        engine.word_cache['casa'] = {"default": "dar"}
        
        input_text_2 = "Eu estou em casa."
        print(f"\n--- Teste 2: '{input_text_2}' ---")
        
        output_2 = engine.process_text(input_text_2)
        print(f"Saída: '{output_2}'")

        if "fi " in output_2 and "fija" not in output_2:
            print(">>> RESULTADO: SUCESSO (Preposição separada mantida)")
        else:
            print(f">>> RESULTADO: FALHA (Esperado 'fi ...', obtido '{output_2}')")

    except Exception as e:
        print(f"[ERRO CRÍTICO] Ocorreu uma exceção durante o teste: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 7. Restaurar Backup
        if os.path.exists(BACKUP_PATH):
            shutil.copy(BACKUP_PATH, PROFILE_PATH)
            os.remove(BACKUP_PATH)
            print("\n[INFO] Perfil original restaurado e backup removido.")
        print("=== FIM DO TESTE ===")

if __name__ == "__main__":
    run_test()