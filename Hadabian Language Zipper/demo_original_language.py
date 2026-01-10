#!/usr/bin/env python3

import sys
from pathlib import Path

from original_language_engine import (
    OriginalLanguageEngine,
    OriginalLanguageProfile,
    OriginalLanguageProfileManager
)


def print_header(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def demo_create_language():
    print_header("DEMONSTRAÇÃO: Criando um Idioma Original do Zero")
    
    manager = OriginalLanguageProfileManager()
    
    print("1. Criando perfil de idioma 'Demo Langue'...")
    profile = manager.create_profile(
        profile_id='demo_langue',
        name='Demo Langue',
        seed=42,
        complexity='medium'
    )
    print(f"   ✓ Perfil criado com ID: {profile.profile_id}")
    
    print("\n2. Inicializando motor de linguagem...")
    engine = OriginalLanguageEngine(profile)
    
    print(f"\n3. Fonologia gerada:")
    print(f"   Vogais ({len(profile.phoneme_inventory['vowels'])}): {', '.join(profile.phoneme_inventory['vowels'])}")
    print(f"   Consoantes ({len(profile.phoneme_inventory['consonants'])}): {', '.join(profile.phoneme_inventory['consonants'][:20])}...")
    print(f"   Ditongos ({len(profile.phoneme_inventory.get('diphthongs', []))}): {', '.join(profile.phoneme_inventory.get('diphthongs', []))}")
    
    print(f"\n4. Restrições fonotáticas:")
    print(f"   Templates silábicos: {', '.join(profile.phonotactic_constraints['syllable_templates'])}")
    print(f"   Consoantes máximas no onset: {profile.phonotactic_constraints['max_onset_consonants']}")
    print(f"   Consoantes máximas na coda: {profile.phonotactic_constraints['max_coda_consonants']}")
    
    print("\n5. Testando tradução de palavras individuais:")
    test_words = [
        'hello', 'world', 'language', 'computer', 'friend',
        'water', 'fire', 'earth', 'wind', 'star'
    ]
    
    for word in test_words:
        translated = engine.translate_word(word)
        print(f"   {word:15} → {translated}")
    
    print("\n6. Testando tradução de texto completo:")
    source_text = "Hello world. This is a demonstration of the original language generator."
    print(f"\n   Original:")
    print(f"   {source_text}")
    
    translated_text = engine.translate_text(source_text)
    print(f"\n   Traduzido:")
    print(f"   {translated_text}")
    
    print("\n7. Verificando determinismo...")
    translated_again = engine.translate_text(source_text)
    if translated_text == translated_again:
        print(f"   ✓ Determinismo confirmado! Traduções idênticas.")
    else:
        print(f"   ✗ ERRO: Traduções diferentes!")
    
    engine.save_learning_data()
    print(f"\n   ✓ Dados de aprendizado salvos")
    
    return engine, profile


def demo_vocabulary_generation(engine):
    print_header("DEMONSTRAÇÃO: Gerando Vocabulário Básico")
    
    print("Gerando vocabulário de conceitos fundamentais...")
    
    vocab = engine.generate_core_vocabulary(include_numbers=False)
    
    print(f"\n✓ {len(vocab)} palavras geradas")
    
    print("\n--- Primitivos Semânticos ---")
    semantic_primes = ['exist', 'do', 'think', 'know', 'want', 'see', 'say', 'good', 'bad']
    for concept in semantic_primes:
        if concept in vocab:
            print(f"  {concept:15} → {vocab[concept]}")
    
    print("\n--- Mundo Natural ---")
    nature_words = ['sun', 'moon', 'water', 'fire', 'tree', 'mountain', 'river']
    for concept in nature_words:
        if concept in vocab:
            print(f"  {concept:15} → {vocab[concept]}")
    
    print("\n--- Partes do Corpo ---")
    body_parts = ['head', 'eye', 'hand', 'heart', 'blood']
    for concept in body_parts:
        if concept in vocab:
            print(f"  {concept:15} → {vocab[concept]}")
    
    print("\n--- Números (0-10) ---")
    vocab_with_numbers = engine.generate_core_vocabulary(include_numbers=True)
    for i in range(11):
        num_key = f"number_{i}"
        if num_key in vocab_with_numbers:
            print(f"  {i:2} → {vocab_with_numbers[num_key]}")
    
    engine.save_learning_data()


def demo_linguistic_analysis(engine):
    print_header("DEMONSTRAÇÃO: Análise Linguística")
    
    stats = engine.get_statistics()
    
    print("--- Informações do Perfil ---")
    print(f"ID: {stats['profile']['id']}")
    print(f"Nome: {stats['profile']['name']}")
    print(f"Seed: {stats['profile']['seed']}")
    
    print("\n--- Fonologia ---")
    print(f"Vogais: {stats['phonology']['vowel_count']}")
    print(f"Consoantes: {stats['phonology']['consonant_count']}")
    print(f"Ditongos: {stats['phonology']['diphthong_count']}")
    print(f"Templates silábicos: {stats['phonology']['syllable_templates']}")
    
    print("\n--- Léxico ---")
    print(f"Total de palavras: {stats['lexicon']['total_words']}")
    print(f"Palavras únicas: {stats['lexicon']['unique_words']}")
    print(f"Qualidade média: {stats['lexicon']['average_quality']:.2f}")
    print(f"Comprimento médio de palavra: {stats['lexicon']['average_word_length']:.1f} caracteres")
    
    if stats['lexicon']['most_common_phonemes']:
        print("\n--- Distribuição Fonêmica ---")
        print("Fonemas mais frequentes:")
        for phoneme, count in stats['lexicon']['most_common_phonemes'][:10]:
            print(f"  {phoneme:5} : {count:4} ocorrências")
    
    print("\n--- Métricas de Distribuição ---")
    print(f"Entropia: {stats['distribution']['entropy']:.2f} bits")
    print(f"Uniformidade: {stats['distribution']['uniformity']:.2f}")
    
    if stats['distribution']['uniformity'] > 0.7:
        print("  ✓ Distribuição bem equilibrada")
    elif stats['distribution']['uniformity'] > 0.5:
        print("  ⚠ Distribuição razoável, mas pode melhorar")
    else:
        print("  ✗ Distribuição desequilibrada - alguns fonemas dominam")
    
    if stats.get('recommendations'):
        print("\n--- Recomendações ---")
        for rec in stats['recommendations']:
            print(f"  • {rec}")


def demo_word_quality(engine, profile):
    print_header("DEMONSTRAÇÃO: Análise de Qualidade de Palavras")
    
    from original_learning_system import QualityMetrics
    
    test_cases = [
        ('kata', "Palavra ideal"),
        ('a', "Muito curta"),
        ('supercalifragilisticexpialidocious', "Muito longa"),
        ('prstu', "Sem vogais"),
        ('aeiou', "Só vogais"),
        ('ktprsz', "Cluster consonantal excessivo")
    ]
    
    print("Avaliando qualidade de diferentes estruturas de palavras:\n")
    
    for word, description in test_cases:
        quality = QualityMetrics.calculate_word_quality(
            word,
            profile.phoneme_inventory,
            profile.phonotactic_constraints
        )
        
        bar_length = int(quality * 40)
        bar = "█" * bar_length + "░" * (40 - bar_length)
        
        print(f"{word:40} | {bar} | {quality:.2f}")
        print(f"{'':40}   ({description})")
        print()


def demo_compound_words(engine):
    print_header("DEMONSTRAÇÃO: Palavras Compostas")
    
    print("Gerando palavras compostas por combinação de conceitos:\n")
    
    compounds = [
        ('fire', 'mountain', 'vulcão'),
        ('water', 'fall', 'cachoeira'),
        ('sun', 'light', 'luz solar'),
        ('moon', 'night', 'noite de lua'),
        ('tree', 'house', 'casa na árvore')
    ]
    
    for concept1, concept2, meaning in compounds:
        word1 = engine.translate_word(concept1)
        word2 = engine.translate_word(concept2)
        compound = engine.generate_compound_word(concept1, concept2)
        
        print(f"{concept1} + {concept2} = {meaning}")
        print(f"  {word1} + {word2} → {compound}")
        print()
    
    engine.save_learning_data()


def demo_dialectal_variation():
    print_header("DEMONSTRAÇÃO: Variação Dialetal")
    
    manager = OriginalLanguageProfileManager()
    
    print("Criando idioma base e dois dialetos derivados:\n")
    
    print("1. Idioma Base (seed: 1000)")
    base_profile = manager.create_profile('base_lang', seed=1000)
    base_engine = OriginalLanguageEngine(base_profile)
    
    print("\n2. Dialeto Norte (seed: 1100)")
    north_profile = manager.duplicate_profile('base_lang', 'north_dialect', new_seed=1100)
    north_engine = OriginalLanguageEngine(north_profile)
    
    print("\n3. Dialeto Sul (seed: 1200)")
    south_profile = manager.duplicate_profile('base_lang', 'south_dialect', new_seed=1200)
    south_engine = OriginalLanguageEngine(south_profile)
    
    print("\n\nComparando traduções nos três dialetos:\n")
    
    test_words = ['hello', 'water', 'mountain', 'friend', 'sun']
    
    print(f"{'Conceito':15} | {'Base':20} | {'Norte':20} | {'Sul':20}")
    print("-" * 80)
    
    for word in test_words:
        base_trans = base_engine.translate_word(word)
        north_trans = north_engine.translate_word(word)
        south_trans = south_engine.translate_word(word)
        
        print(f"{word:15} | {base_trans:20} | {north_trans:20} | {south_trans:20}")
    
    base_engine.save_learning_data()
    north_engine.save_learning_data()
    south_engine.save_learning_data()
    
    manager.delete_profile('base_lang')
    manager.delete_profile('north_dialect')
    manager.delete_profile('south_dialect')


def demo_number_systems(engine):
    print_header("DEMONSTRAÇÃO: Sistema Numérico")
    
    print("Sistema numérico gerado (base 10):\n")
    
    print("--- Números Básicos (0-20) ---")
    for i in range(21):
        number_word = engine.generate_number_word(i)
        print(f"  {i:3} → {number_word}")
    
    print("\n--- Números Compostos ---")
    special_numbers = [25, 50, 75, 100, 500, 1000]
    for num in special_numbers:
        number_word = engine.generate_number_word(num)
        print(f"  {num:4} → {number_word}")


def demo_text_translation(engine):
    print_header("DEMONSTRAÇÃO: Tradução de Texto Longo")
    
    source_text = """
The sun rises over the distant mountains, painting the sky in shades of orange and gold.
Birds sing their morning songs as the world awakens.
In the valley below, a river flows peacefully through ancient forests.
People begin their daily work, greeting friends and family.
This is the beauty of life in our world.
    """.strip()
    
    print("Texto Original:")
    print("-" * 80)
    print(source_text)
    print("-" * 80)
    
    print("\nTraduzindo...")
    translated = engine.translate_text(source_text)
    
    print("\nTexto Traduzido:")
    print("-" * 80)
    print(translated)
    print("-" * 80)
    
    print(f"\nEstatísticas:")
    print(f"  Palavras originais: {len(source_text.split())}")
    print(f"  Palavras traduzidas: {len(translated.split())}")
    print(f"  Caracteres originais: {len(source_text)}")
    print(f"  Caracteres traduzidos: {len(translated)}")
    
    engine.save_learning_data()


def run_full_demo():
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "DEMONSTRAÇÃO COMPLETA DO GERADOR DE IDIOMAS ORIGINAIS" + " " * 10 + "║")
    print("╚" + "=" * 78 + "╝")
    
    try:
        engine, profile = demo_create_language()
        
        input("\nPressione Enter para continuar para geração de vocabulário...")
        demo_vocabulary_generation(engine)
        
        input("\nPressione Enter para continuar para análise linguística...")
        demo_linguistic_analysis(engine)
        
        input("\nPressione Enter para continuar para análise de qualidade...")
        demo_word_quality(engine, profile)
        
        input("\nPressione Enter para continuar para palavras compostas...")
        demo_compound_words(engine)
        
        input("\nPressione Enter para continuar para variação dialetal...")
        demo_dialectal_variation()
        
        input("\nPressione Enter para continuar para sistema numérico...")
        demo_number_systems(engine)
        
        input("\nPressione Enter para continuar para tradução de texto longo...")
        demo_text_translation(engine)
        
        print_header("DEMONSTRAÇÃO CONCLUÍDA")
        
        print("✓ Todos os módulos foram demonstrados com sucesso!")
        print("\nArquivos gerados:")
        print("  • original_profiles/demo_langue.json")
        print("  • original_learning/demo_langue_patterns.json")
        print("  • original_learning/demo_langue_stats.json")
        print("  • original_learning/demo_langue_frequency.json")
        
        print("\nPróximos passos:")
        print("  1. Execute 'python original_gui.py' para interface gráfica")
        print("  2. Use 'python original_cli.py --help' para ver comandos CLI")
        print("  3. Leia ORIGINAL_README.md para documentação completa")
        
        manager = OriginalLanguageProfileManager()
        cleanup = input("\nDeseja remover o perfil de demonstração? (s/N): ")
        if cleanup.lower() == 's':
            manager.delete_profile('demo_langue')
            print("✓ Perfil de demonstração removido")
        
    except KeyboardInterrupt:
        print("\n\nDemonstração interrompida pelo usuário.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n✗ Erro durante demonstração: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    run_full_demo()
