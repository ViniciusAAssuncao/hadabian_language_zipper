from engine import OriginalLanguageEngine
import json
import os

BASE_DIR = os.path.dirname(__file__)
CONLANGS_DIR = os.path.join(BASE_DIR, "../conlangs")

def test_absorption():
    engine_derived = OriginalLanguageEngine(
        os.path.join(CONLANGS_DIR, "test_germanic_derived.json")
    )
    engine_sibling = OriginalLanguageEngine(
        os.path.join(CONLANGS_DIR, "test_germanic_sibling.json")
    )

    terms_to_test = [
        {"word": "skyscraper", "components": ["sky", "scraper"], "semantic": ["building"]},
        {"word": "mouse", "components": [], "semantic": ["animal"]},
        {"word": "download", "components": ["down", "load"], "semantic": ["transfer"]},
        {"word": "weekend", "components": ["week", "end"], "semantic": ["time"]},
        {"word": "kindergarten", "components": ["child", "garden"], "semantic": ["school"]}
    ]

    print("=== Teste de Absorção: Conlang Derivada (Prefere Calque) ===")
    for term in terms_to_test:
        result = engine_derived.absorb_term(
            term["word"],
            term["components"],
            term["semantic"]
        )
        print(f"Termo: {term['word']:<12} -> Resultado: {result['default']:<15} (Modo: {result['absorption_mode']})")

    print("\n=== Teste de Absorção: Conlang Irmã (Prefere Adaptação/Extensão) ===")
    for term in terms_to_test:
        result = engine_sibling.absorb_term(
            term["word"],
            term["components"],
            term["semantic"]
        )
        print(f"Termo: {term['word']:<12} -> Resultado: {result['default']:<15} (Modo: {result['absorption_mode']})")

if __name__ == "__main__":
    test_absorption()
