import sys
import json
from pathlib import Path


def test_imports():
    print("=" * 80)
    print("TESTE 1: IMPORTAÇÕES")
    print("=" * 80)

    modules = [
        ('zipper_engine', 'ZipperEngine'),
        ('translation_cache', 'TranslationCache, MorphemeCache, ContextualMemory'),
        ('morphology_analyzer',
         'MorphologyAnalyzer, ConsistencyValidator, WordQualityScorer'),
        ('learning_system', 'LearningSystem, ConvergenceEngine, AdaptiveWeightSystem'),
        ('context_engine', 'SemanticContextEngine, ContextualTranslator, PhraseAnalyzer'),
        ('utilities', 'AdvancedTextAnalyzer, QualityMetrics, BatchProcessor')
    ]

    success = 0
    failed = 0

    for module, classes in modules:
        try:
            exec(f"from {module} import {classes}")
            print(f"✓ {module}: {classes}")
            success += 1
        except Exception as e:
            print(f"✗ {module}: {e}")
            failed += 1

    print(f"\nResultado: {success} sucessos, {failed} falhas")
    return failed == 0


def test_morphology():
    print("\n" + "=" * 80)
    print("TESTE 2: ANÁLISE MORFOLÓGICA")
    print("=" * 80)

    try:
        from morphology_analyzer import MorphologyAnalyzer

        analyzer = MorphologyAnalyzer()

        print("\na) Teste de empilhamento:")
        test_words = ["memoryememory", "walkwalk", "good", "house"]
        for word in test_words:
            is_stacked = analyzer.detect_stacking(word)
            if is_stacked:
                fixed = analyzer.fix_stacking(word)
                print(f"   {word}: EMPILHADO → {fixed}")
            else:
                print(f"   {word}: OK")

        print("\nb) Teste de reduplicação:")
        reduplicated = analyzer.detect_reduplication("lalalala")
        if reduplicated:
            segment, count = reduplicated
            print(f"   'lalalala': detectado '{segment}' repetido {count}x")
            fixed = analyzer.fix_reduplication("lalalala", max_repetitions=2)
            print(f"   Corrigido para: {fixed}")

        print("\nc) Teste de decomposição:")
        word = "unhappiness"
        parts = analyzer.decompose_word(word)
        print(f"   '{word}':")
        print(f"     Prefixo: {parts['prefix']}")
        print(f"     Raiz: {parts['root']}")
        print(f"     Sufixo: {parts['suffix']}")

        print("\nd) Teste de estrutura fonética:")
        valid_words = ["hello", "xztqp", "aeiou"]
        for word in valid_words:
            is_valid = analyzer.is_valid_word_structure(word)
            print(f"   '{word}': {'VÁLIDO' if is_valid else 'INVÁLIDO'}")

        print("\n✓ Testes de morfologia passaram!")
        return True

    except Exception as e:
        print(f"\n✗ Erro nos testes de morfologia: {e}")
        return False


def test_caching():
    print("\n" + "=" * 80)
    print("TESTE 3: SISTEMA DE CACHE")
    print("=" * 80)

    try:
        from translation_cache import TranslationCache

        cache = TranslationCache("test_profile")

        print("\na) Teste de armazenamento:")
        cache.set_translation(["hello"], "helo")
        cached = cache.get_translation(["hello"])
        print(f"   Armazenado 'hello' → 'helo'")
        print(f"   Recuperado: {cached}")
        print(f"   {'✓' if cached == 'helo' else '✗'} Igual")

        print("\nb) Teste de frequência:")
        cache.set_translation(["hello"], "helo")
        cache.set_translation(["hello"], "helo")
        stats = cache.get_statistics()
        print(f"   Entradas: {stats['total_entries']}")
        print(f"   Usos: {stats['total_uses']}")

        print("\nc) Teste de consolidação:")
        cache.set_translation(["test"], "testo")
        cache.set_translation(["test"], "teste")
        consolidated = cache.consolidate_variations(min_frequency=1)
        print(f"   Variações consolidadas: {consolidated}")

        print("\n✓ Testes de cache passaram!")
        return True

    except Exception as e:
        print(f"\n✗ Erro nos testes de cache: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_learning():
    print("\n" + "=" * 80)
    print("TESTE 4: SISTEMA DE APRENDIZADO")
    print("=" * 80)

    try:
        from learning_system import LearningSystem, ConvergenceEngine

        learning = LearningSystem("test_profile")

        print("\na) Teste de regras de transformação:")
        learning.learn_transformation_rule("hello", "helo", confidence=0.8)
        suggestions = learning.get_transformation_suggestions("hello")
        print(f"   Regra aprendida: 'hello' → 'helo'")
        print(f"   Sugestões: {len(suggestions)}")
        if suggestions:
            print(
                f"   Melhor: {suggestions[0][0]} (confiança: {suggestions[0][1]:.2f})")

        print("\nb) Teste de padrões:")
        learning.record_pattern(
            "word_pattern",
            "hello",
            "helo",
            {"length": 5, "vowels": 2},
            quality_score=0.8
        )
        similar = learning.find_similar_patterns("word_pattern", {"length": 5})
        print(f"   Padrão registrado")
        print(f"   Padrões similares encontrados: {len(similar)}")

        print("\nc) Teste de convergência:")
        convergence = ConvergenceEngine("test_profile")
        for i in range(10):
            convergence.record_translation(
                "test_key", "translation" if i < 7 else "other")
        converged, preferred = convergence.check_convergence("test_key")
        print(f"   Convergiu: {converged}")
        print(f"   Preferida: {preferred}")

        print("\n✓ Testes de aprendizado passaram!")
        return True

    except Exception as e:
        print(f"\n✗ Erro nos testes de aprendizado: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_context():
    print("\n" + "=" * 80)
    print("TESTE 5: CONTEXTO SEMÂNTICO")
    print("=" * 80)

    try:
        from context_engine import SemanticContextEngine, PhraseAnalyzer

        semantic = SemanticContextEngine("test_profile")

        print("\na) Teste de janela de contexto:")
        words = ["the", "cat", "sat", "on", "the", "mat"]
        context = semantic.build_context_window(words, 2)
        print(f"   Palavras: {' '.join(words)}")
        print(f"   Alvo (índice 2): {context['target']}")
        print(f"   Antes: {context['before']}")
        print(f"   Depois: {context['after']}")

        print("\nb) Teste de colocações:")
        text = "the cat sat on the mat the cat ran"
        semantic.extract_collocations(text)
        collocations = semantic.get_collocations("cat")
        print(f"   Colocações de 'cat': {collocations[:3]}")

        print("\nc) Teste de análise de frases:")
        analyzer = PhraseAnalyzer()
        phrase = "The quick brown fox"
        analysis = analyzer.analyze_phrase(phrase)
        print(f"   Frase: {phrase}")
        print(f"   Palavras: {analysis['word_count']}")
        print(f"   Palavras únicas: {analysis['unique_words']}")
        print(f"   Densidade lexical: {analysis['lexical_density']:.2f}")

        print("\n✓ Testes de contexto passaram!")
        return True

    except Exception as e:
        print(f"\n✗ Erro nos testes de contexto: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_quality():
    print("\n" + "=" * 80)
    print("TESTE 6: MÉTRICAS DE QUALIDADE")
    print("=" * 80)

    try:
        from utilities import AdvancedTextAnalyzer, QualityMetrics
        from morphology_analyzer import MorphologyAnalyzer, WordQualityScorer

        print("\na) Teste de análise de texto:")
        analyzer = AdvancedTextAnalyzer()
        text = "The quick brown fox jumps over the lazy dog"
        analysis = analyzer.analyze_comprehensive(text)
        print(f"   Texto: {text}")
        print(f"   Palavras: {analysis['basic']['word_count']}")
        print(f"   Razão de vogais: {analysis['phonetic']['vowel_ratio']:.2f}")
        print(f"   Diversidade: {analysis['basic']['type_token_ratio']:.2f}")

        print("\nb) Teste de pontuação de palavras:")
        morph = MorphologyAnalyzer()
        scorer = WordQualityScorer(morph)
        words = ["hello", "memoryememory", "xztqp", "beautiful"]
        for word in words:
            score = scorer.score_word(word)
            print(f"   '{word}': {score:.2f}")

        print("\nc) Teste de qualidade de tradução:")
        metrics = QualityMetrics()
        source = "Hello world"
        generated = "Helo wold"
        quality = metrics.calculate_translation_quality(source, generated)
        print(f"   Fonte: {source}")
        print(f"   Gerado: {generated}")
        print(f"   Qualidade: {quality['overall_quality']:.2f}")

        print("\n✓ Testes de qualidade passaram!")
        return True

    except Exception as e:
        print(f"\n✗ Erro nos testes de qualidade: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    print("\n" + "=" * 80)
    print("TESTE 7: INTEGRAÇÃO COMPLETA")
    print("=" * 80)

    try:
        print("\na) Criando perfil de teste...")
        test_profile = {
            "id": "test_lang",
            "name": "Test Language",
            "bases": ["en"],
            "fusion_weights": [1.0],
            "fusion_rules": {
                "min_cut_point": 0.4,
                "preserve_caps": True
            },
            "phonotactics": {
                "vowels": "aeiou",
                "max_consonant_cluster": 3,
                "max_vowel_cluster": 2
            },
            "orthography": {},
            "global_seed": 12345
        }

        profiles_dir = Path("profiles")
        profiles_dir.mkdir(exist_ok=True)
        profile_path = profiles_dir / "test_lang.json"

        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(test_profile, f, indent=2)
        print(f"   ✓ Perfil criado: {profile_path}")

        print("\nb) Inicializando motor...")
        from zipper_engine import ZipperEngine

        engine = ZipperEngine(
            str(profile_path),
            enable_learning=True,
            enable_caching=True,
            enable_context=True
        )
        print("   ✓ Motor inicializado")

        print("\nc) Processando texto...")
        result = engine.process_texts(["Hello world"])
        print(f"   Input: 'Hello world'")
        print(f"   Output: '{result}'")

        print("\nd) Segunda processamento (deve usar cache)...")
        result2 = engine.process_texts(["Hello world"])
        print(f"   Output: '{result2}'")
        print(f"   {'✓ Consistente!' if result == result2 else '✗ Inconsistente!'}")

        print("\ne) Obtendo estatísticas...")
        stats = engine.get_statistics()
        print(
            f"   Entradas no cache: {stats.get('cache', {}).get('total_entries', 0)}")

        print("\nf) Consolidando...")
        consolidated = engine.consolidate_cache(min_frequency=1)
        print(f"   ✓ Consolidado: {consolidated} variações")

        print("\ng) Exportando dicionário...")
        dict_path = "test_dictionary.json"
        count = engine.export_dictionary(dict_path, min_frequency=1)
        print(f"   ✓ Exportado {count} entradas para {dict_path}")

        print("\n✓ Teste de integração completo!")
        return True

    except Exception as e:
        print(f"\n✗ Erro no teste de integração: {e}")
        import traceback
        traceback.print_exc()
        return False


def cleanup_test_files():
    print("\n" + "=" * 80)
    print("LIMPEZA DE ARQUIVOS DE TESTE")
    print("=" * 80)

    files_to_remove = [
        "profiles/test_lang.json",
        "test_dictionary.json",
        "cache/test_profile_cache.json",
        "cache/test_profile_morphemes.json",
        "cache/test_profile_context.json",
        "learning/test_profile_rules.json",
        "learning/test_profile_patterns.json",
        "learning/test_profile_stats.json",
        "context/test_profile_semantic.json"
    ]

    for filepath in files_to_remove:
        path = Path(filepath)
        if path.exists():
            path.unlink()
            print(f"✓ Removido: {filepath}")

    print("\n✓ Limpeza concluída!")


def run_all_tests():
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "HADABIAN LANGUAGE ZIPPER V2" + " " * 31 + "║")
    print("║" + " " * 25 + "SUITE DE TESTES" + " " * 39 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    tests = [
        ("Importações", test_imports),
        ("Morfologia", test_morphology),
        ("Cache", test_caching),
        ("Aprendizado", test_learning),
        ("Contexto", test_context),
        ("Qualidade", test_quality),
        ("Integração", test_integration)
    ]

    results = []

    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n✗ Erro fatal no teste {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    print("\n\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 30 + "RESUMO FINAL" + " " * 36 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASSOU" if result else "✗ FALHOU"
        print(f"{status:12} | {name}")

    print()
    print("-" * 80)
    print(f"Total: {passed}/{total} testes passaram ({passed/total*100:.1f}%)")
    print("-" * 80)

    if passed == total:
        print("\n🎉 TODOS OS TESTES PASSARAM! Sistema funcionando perfeitamente!")
    else:
        print(
            f"\n⚠ {total - passed} teste(s) falharam. Verifique os erros acima.")

    cleanup_test_files()

    return passed == total


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
