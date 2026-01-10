#!/usr/bin/env python3

import sys
import json
from pathlib import Path

from phoneme_inventory import PhonemeSelector, PhonotacticConstraints, OrthographyMapper
from word_generator import WordGenerator, SyllableGenerator
from original_learning_system import (
    OriginalLanguageLearningSystem,
    QualityMetrics,
    ConceptMapper
)
from original_language_engine import (
    OriginalLanguageEngine,
    OriginalLanguageProfile,
    OriginalLanguageProfileManager
)


def test_phoneme_selection():
    print("=" * 80)
    print("TESTE 1: SELEÇÃO DE FONEMAS")
    print("=" * 80)
    
    try:
        selector = PhonemeSelector(seed=42)
        
        inventory = selector.generate_inventory(
            vowel_count_range=(5, 7),
            consonant_count_range=(12, 18),
            allow_diphthongs=True,
            complexity='medium'
        )
        
        print(f"\n✓ Inventário gerado:")
        print(f"  Vogais ({len(inventory['vowels'])}): {', '.join(inventory['vowels'])}")
        print(f"  Consoantes ({len(inventory['consonants'])}): {', '.join(inventory['consonants'][:15])}...")
        print(f"  Ditongos ({len(inventory['diphthongs'])}): {', '.join(inventory['diphthongs'])}")
        
        assert len(inventory['vowels']) >= 5
        assert len(inventory['consonants']) >= 12
        
        print("\n✓ Teste de seleção de fonemas passou!")
        return True
        
    except Exception as e:
        print(f"\n✗ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_phonotactic_constraints():
    print("\n" + "=" * 80)
    print("TESTE 2: RESTRIÇÕES FONOTÁTICAS")
    print("=" * 80)
    
    try:
        selector = PhonemeSelector(seed=42)
        inventory = selector.generate_inventory()
        
        constraints_gen = PhonotacticConstraints(seed=42)
        constraints = constraints_gen.generate_constraints(
            phoneme_inventory=inventory,
            syllable_complexity='medium'
        )
        
        print(f"\n✓ Restrições geradas:")
        print(f"  Templates: {', '.join(constraints['syllable_templates'])}")
        print(f"  Max onset: {constraints['max_onset_consonants']}")
        print(f"  Max coda: {constraints['max_coda_consonants']}")
        print(f"  Max núcleo: {constraints['max_nucleus_vowels']}")
        print(f"  Sílabas/palavra: {constraints['min_syllables_per_word']}-{constraints['max_syllables_per_word']}")
        
        assert len(constraints['syllable_templates']) > 0
        assert constraints['max_onset_consonants'] > 0
        
        print("\n✓ Teste de restrições fonotáticas passou!")
        return True
        
    except Exception as e:
        print(f"\n✗ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_syllable_generation():
    print("\n" + "=" * 80)
    print("TESTE 3: GERAÇÃO DE SÍLABAS")
    print("=" * 80)
    
    try:
        selector = PhonemeSelector(seed=42)
        inventory = selector.generate_inventory()
        
        constraints_gen = PhonotacticConstraints(seed=42)
        constraints = constraints_gen.generate_constraints(inventory)
        
        syl_gen = SyllableGenerator(inventory, constraints, seed=42)
        
        print("\n✓ Gerando sílabas determinísticas:")
        for i in range(5):
            syllable = syl_gen.generate_syllable(
                word_position='medial',
                concept_seed='test',
                syllable_index=i
            )
            print(f"  Sílaba {i+1}: {syllable}")
        
        syl1 = syl_gen.generate_syllable('medial', 'test', 0)
        syl2 = syl_gen.generate_syllable('medial', 'test', 0)
        
        assert syl1 == syl2, "Sílabas devem ser determinísticas"
        print(f"\n✓ Determinismo confirmado: '{syl1}' == '{syl2}'")
        
        print("\n✓ Teste de geração de sílabas passou!")
        return True
        
    except Exception as e:
        print(f"\n✗ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_word_generation():
    print("\n" + "=" * 80)
    print("TESTE 4: GERAÇÃO DE PALAVRAS")
    print("=" * 80)
    
    try:
        selector = PhonemeSelector(seed=42)
        inventory = selector.generate_inventory()
        
        constraints_gen = PhonotacticConstraints(seed=42)
        constraints = constraints_gen.generate_constraints(inventory)
        
        word_gen = WordGenerator(inventory, constraints, seed=42)
        
        print("\n✓ Gerando palavras:")
        test_concepts = ['hello', 'world', 'language', 'computer', 'friend']
        
        for concept in test_concepts:
            word = word_gen.generate_word(concept)
            print(f"  {concept:15} → {word}")
        
        word1 = word_gen.generate_word('hello')
        word2 = word_gen.generate_word('hello')
        
        assert word1 == word2, "Palavras devem ser determinísticas"
        print(f"\n✓ Determinismo confirmado: '{word1}' == '{word2}'")
        
        print("\n✓ Teste de geração de palavras passou!")
        return True
        
    except Exception as e:
        print(f"\n✗ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_orthography():
    print("\n" + "=" * 80)
    print("TESTE 5: ORTOGRAFIA")
    print("=" * 80)
    
    try:
        selector = PhonemeSelector(seed=42)
        inventory = selector.generate_inventory()
        
        ortho_mapper = OrthographyMapper(seed=42)
        mapping = ortho_mapper.generate_orthography(inventory, script_style='latin')
        
        print(f"\n✓ Mapeamento ortográfico gerado:")
        print(f"  Total de mapeamentos: {len(mapping)}")
        
        for phoneme, grapheme in list(mapping.items())[:10]:
            print(f"  /{phoneme}/ → <{grapheme}>")
        
        test_phonetic = 'hello'
        orthographic = ortho_mapper.apply_orthography(test_phonetic)
        print(f"\n✓ Teste de aplicação: /{test_phonetic}/ → <{orthographic}>")
        
        print("\n✓ Teste de ortografia passou!")
        return True
        
    except Exception as e:
        print(f"\n✗ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_quality_metrics():
    print("\n" + "=" * 80)
    print("TESTE 6: MÉTRICAS DE QUALIDADE")
    print("=" * 80)
    
    try:
        selector = PhonemeSelector(seed=42)
        inventory = selector.generate_inventory()
        
        constraints_gen = PhonotacticConstraints(seed=42)
        constraints = constraints_gen.generate_constraints(inventory)
        
        test_words = [
            'kata',
            'prstu',
            'a',
            'supercalifragilisticexpialidocious'
        ]
        
        print("\n✓ Avaliando qualidade de palavras:")
        for word in test_words:
            quality = QualityMetrics.calculate_word_quality(word, inventory, constraints)
            print(f"  {word:40} → {quality:.2f}")
        
        print("\n✓ Teste de métricas de qualidade passou!")
        return True
        
    except Exception as e:
        print(f"\n✗ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_learning_system():
    print("\n" + "=" * 80)
    print("TESTE 7: SISTEMA DE APRENDIZADO")
    print("=" * 80)
    
    try:
        learning = OriginalLanguageLearningSystem('test_lang')
        
        test_data = [
            ('hello', 'kata', 0.8, ['k', 'a', 't', 'a']),
            ('world', 'munda', 0.7, ['m', 'u', 'n', 'd', 'a']),
            ('language', 'lingua', 0.9, ['l', 'i', 'n', 'g', 'u', 'a'])
        ]
        
        print("\n✓ Registrando gerações:")
        for concept, word, quality, phonemes in test_data:
            learning.record_generation(concept, word, quality, phonemes)
            print(f"  {concept} → {word} (qualidade: {quality:.2f})")
        
        retrieved = learning.get_word_for_concept('hello')
        assert retrieved == 'kata', "Palavra recuperada deve ser 'kata'"
        print(f"\n✓ Recuperação: 'hello' → '{retrieved}'")
        
        stats = learning.get_statistics()
        print(f"\n✓ Estatísticas:")
        print(f"  Total de palavras: {stats['total_words']}")
        print(f"  Qualidade média: {stats['average_quality']:.2f}")
        
        print("\n✓ Teste de sistema de aprendizado passou!")
        return True
        
    except Exception as e:
        print(f"\n✗ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_complete_engine():
    print("\n" + "=" * 80)
    print("TESTE 8: MOTOR COMPLETO")
    print("=" * 80)
    
    try:
        profile = OriginalLanguageProfile('test_complete')
        profile.name = "Idioma de Teste"
        profile.seed = 12345
        profile.complexity = 'medium'
        
        print("\n✓ Criando perfil de teste...")
        
        engine = OriginalLanguageEngine(profile)
        
        print(f"  Vogais: {len(profile.phoneme_inventory['vowels'])}")
        print(f"  Consoantes: {len(profile.phoneme_inventory['consonants'])}")
        
        test_text = "Hello world. This is a test of the language generator."
        
        print(f"\n✓ Traduzindo texto:")
        print(f"  Original: {test_text}")
        
        translated = engine.translate_text(test_text)
        print(f"  Traduzido: {translated}")
        
        translated2 = engine.translate_text(test_text)
        assert translated == translated2, "Tradução deve ser determinística"
        print(f"\n✓ Determinismo confirmado")
        
        print("\n✓ Gerando vocabulário básico...")
        vocab = engine.generate_core_vocabulary(include_numbers=False)
        print(f"  {len(vocab)} palavras geradas")
        
        print("\n  Primeiras 10 palavras:")
        for i, (concept, word) in enumerate(list(vocab.items())[:10]):
            print(f"    {concept:15} → {word}")
        
        stats = engine.get_statistics()
        print(f"\n✓ Estatísticas:")
        print(f"  Total de palavras: {stats['lexicon']['total_words']}")
        print(f"  Qualidade média: {stats['lexicon']['average_quality']:.2f}")
        print(f"  Entropia: {stats['distribution']['entropy']:.2f}")
        
        print("\n✓ Teste do motor completo passou!")
        return True
        
    except Exception as e:
        print(f"\n✗ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_profile_manager():
    print("\n" + "=" * 80)
    print("TESTE 9: GERENCIADOR DE PERFIS")
    print("=" * 80)
    
    try:
        manager = OriginalLanguageProfileManager()
        
        print("\n✓ Criando perfil de teste...")
        profile = manager.create_profile(
            profile_id='test_manager',
            name='Idioma de Teste Manager',
            seed=99999,
            complexity='simple'
        )
        
        print(f"  ID: {profile.profile_id}")
        print(f"  Nome: {profile.name}")
        print(f"  Seed: {profile.seed}")
        
        loaded = manager.load_profile('test_manager')
        assert loaded is not None, "Perfil deve ser carregado"
        assert loaded.profile_id == 'test_manager', "ID deve corresponder"
        print(f"\n✓ Perfil carregado com sucesso")
        
        profiles = manager.list_profiles()
        assert 'test_manager' in profiles, "Perfil deve estar na lista"
        print(f"\n✓ Total de perfis: {len(profiles)}")
        
        duplicate = manager.duplicate_profile('test_manager', 'test_manager_copy', new_seed=88888)
        assert duplicate is not None, "Duplicação deve funcionar"
        assert duplicate.seed == 88888, "Nova seed deve ser aplicada"
        print(f"\n✓ Perfil duplicado com nova seed")
        
        manager.delete_profile('test_manager')
        manager.delete_profile('test_manager_copy')
        print(f"\n✓ Perfis de teste removidos")
        
        print("\n✓ Teste de gerenciador de perfis passou!")
        return True
        
    except Exception as e:
        print(f"\n✗ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_concept_mapper():
    print("\n" + "=" * 80)
    print("TESTE 10: MAPEADOR DE CONCEITOS")
    print("=" * 80)
    
    try:
        mapper = ConceptMapper()
        
        print("\n✓ Categorias disponíveis:")
        categories = mapper.concept_categories.keys()
        print(f"  Total: {len(categories)}")
        for cat in list(categories)[:5]:
            print(f"    - {cat}")
        
        test_concept = 'mother'
        category = mapper.get_category(test_concept)
        print(f"\n✓ Categoria de '{test_concept}': {category}")
        
        related = mapper.suggest_related_concepts(test_concept, max_suggestions=3)
        print(f"\n✓ Conceitos relacionados:")
        for rel in related:
            print(f"    - {rel}")
        
        core_concepts = mapper.get_all_core_concepts()
        print(f"\n✓ Total de conceitos básicos: {len(core_concepts)}")
        
        print("\n✓ Teste de mapeador de conceitos passou!")
        return True
        
    except Exception as e:
        print(f"\n✗ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "GERADOR DE IDIOMAS ORIGINAIS" + " " * 30 + "║")
    print("║" + " " * 30 + "SUITE DE TESTES" + " " * 34 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    tests = [
        ("Seleção de Fonemas", test_phoneme_selection),
        ("Restrições Fonotáticas", test_phonotactic_constraints),
        ("Geração de Sílabas", test_syllable_generation),
        ("Geração de Palavras", test_word_generation),
        ("Ortografia", test_orthography),
        ("Métricas de Qualidade", test_quality_metrics),
        ("Sistema de Aprendizado", test_learning_system),
        ("Motor Completo", test_complete_engine),
        ("Gerenciador de Perfis", test_profile_manager),
        ("Mapeador de Conceitos", test_concept_mapper)
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
        print(f"\n⚠ {total - passed} teste(s) falharam. Verifique os erros acima.")
    
    return passed == total


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
