#!/usr/bin/env python3

import argparse
import sys
import json
from pathlib import Path
from typing import Optional

from original_language_engine import (
    OriginalLanguageEngine,
    OriginalLanguageProfile,
    OriginalLanguageProfileManager,
    BatchTranslator
)


def cmd_create_profile(args):
    print("=" * 80)
    print("CRIAR NOVO PERFIL DE IDIOMA ORIGINAL")
    print("=" * 80)
    
    manager = OriginalLanguageProfileManager()
    
    profile = manager.create_profile(
        profile_id=args.id,
        name=args.name or args.id,
        seed=args.seed,
        complexity=args.complexity
    )
    
    print(f"\n✓ Perfil '{args.id}' criado com sucesso!")
    print(f"  Nome: {profile.name}")
    print(f"  Seed: {profile.seed}")
    print(f"  Complexidade: {profile.complexity}")
    
    if args.initialize:
        print("\nInicializando fonologia...")
        engine = OriginalLanguageEngine(profile)
        
        print(f"  Vogais: {len(profile.phoneme_inventory['vowels'])}")
        print(f"  Consoantes: {len(profile.phoneme_inventory['consonants'])}")
        print(f"  Ditongos: {len(profile.phoneme_inventory.get('diphthongs', []))}")
        print(f"  Templates silábicos: {len(profile.phonotactic_constraints['syllable_templates'])}")
        
        manager.save_profile(profile)
        print("\n✓ Fonologia inicializada e salva!")
    
    return 0


def cmd_list_profiles(args):
    print("=" * 80)
    print("PERFIS DE IDIOMAS ORIGINAIS")
    print("=" * 80)
    
    manager = OriginalLanguageProfileManager()
    profiles = manager.list_profiles()
    
    if not profiles:
        print("\nNenhum perfil encontrado.")
        return 0
    
    print(f"\nTotal: {len(profiles)} perfis\n")
    
    for profile_id in sorted(profiles):
        profile = manager.load_profile(profile_id)
        if profile:
            print(f"  • {profile_id}")
            if args.verbose:
                print(f"    Nome: {profile.name}")
                print(f"    Seed: {profile.seed}")
                print(f"    Complexidade: {profile.complexity}")
                if profile.phoneme_inventory:
                    print(f"    Vogais: {len(profile.phoneme_inventory.get('vowels', []))}")
                    print(f"    Consoantes: {len(profile.phoneme_inventory.get('consonants', []))}")
                print()
    
    return 0


def cmd_show_profile(args):
    print("=" * 80)
    print(f"DETALHES DO PERFIL: {args.profile}")
    print("=" * 80)
    
    manager = OriginalLanguageProfileManager()
    profile = manager.load_profile(args.profile)
    
    if not profile:
        print(f"\n✗ Perfil '{args.profile}' não encontrado")
        return 1
    
    print(f"\nID: {profile.profile_id}")
    print(f"Nome: {profile.name}")
    print(f"Descrição: {profile.description or 'N/A'}")
    print(f"Seed: {profile.seed}")
    print(f"Complexidade: {profile.complexity}")
    
    if profile.phoneme_inventory:
        print(f"\n--- FONOLOGIA ---")
        print(f"Vogais ({len(profile.phoneme_inventory['vowels'])}): {', '.join(profile.phoneme_inventory['vowels'])}")
        print(f"Consoantes ({len(profile.phoneme_inventory['consonants'])}): {', '.join(profile.phoneme_inventory['consonants'][:20])}...")
        
        if profile.phoneme_inventory.get('diphthongs'):
            print(f"Ditongos ({len(profile.phoneme_inventory['diphthongs'])}): {', '.join(profile.phoneme_inventory['diphthongs'])}")
    
    if profile.phonotactic_constraints:
        print(f"\n--- FONOTÁTICA ---")
        print(f"Templates silábicos: {', '.join(profile.phonotactic_constraints.get('syllable_templates', []))}")
        print(f"Max. consoantes no onset: {profile.phonotactic_constraints.get('max_onset_consonants', 'N/A')}")
        print(f"Max. consoantes na coda: {profile.phonotactic_constraints.get('max_coda_consonants', 'N/A')}")
        print(f"Sílabas por palavra: {profile.phonotactic_constraints.get('min_syllables_per_word', 1)}-{profile.phonotactic_constraints.get('max_syllables_per_word', 4)}")
    
    if args.json:
        print(f"\n--- JSON COMPLETO ---")
        print(json.dumps(profile.to_dict(), indent=2, ensure_ascii=False))
    
    return 0


def cmd_translate(args):
    print("=" * 80)
    print(f"TRADUÇÃO COM PERFIL: {args.profile}")
    print("=" * 80)
    
    manager = OriginalLanguageProfileManager()
    profile = manager.load_profile(args.profile)
    
    if not profile:
        print(f"\n✗ Perfil '{args.profile}' não encontrado")
        return 1
    
    engine = OriginalLanguageEngine(profile)
    
    if args.input:
        with open(args.input, 'r', encoding='utf-8') as f:
            source_text = f.read()
        print(f"\nLendo arquivo: {args.input}")
    else:
        source_text = args.text
    
    print(f"\nTexto original:")
    print(f"  {source_text[:200]}{'...' if len(source_text) > 200 else ''}")
    
    translated_text = engine.translate_text(source_text)
    
    print(f"\nTexto traduzido:")
    print(f"  {translated_text[:200]}{'...' if len(translated_text) > 200 else ''}")
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(translated_text)
        print(f"\n✓ Tradução salva em: {args.output}")
    else:
        print(f"\n--- TRADUÇÃO COMPLETA ---")
        print(translated_text)
    
    if args.save_learning:
        engine.save_learning_data()
        print(f"\n✓ Dados de aprendizado salvos")
    
    return 0


def cmd_generate_vocabulary(args):
    print("=" * 80)
    print(f"GERAR VOCABULÁRIO BÁSICO: {args.profile}")
    print("=" * 80)
    
    manager = OriginalLanguageProfileManager()
    profile = manager.load_profile(args.profile)
    
    if not profile:
        print(f"\n✗ Perfil '{args.profile}' não encontrado")
        return 1
    
    engine = OriginalLanguageEngine(profile)
    
    print("\nGenerando vocabulário básico...")
    
    vocabulary = engine.generate_core_vocabulary(include_numbers=args.include_numbers)
    
    print(f"\n✓ {len(vocabulary)} palavras geradas")
    
    if args.output:
        output_path = Path(args.output)
        
        if args.format == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(vocabulary, f, indent=2, ensure_ascii=False)
        elif args.format == 'txt':
            with open(output_path, 'w', encoding='utf-8') as f:
                for concept, word in sorted(vocabulary.items()):
                    f.write(f"{concept}\t{word}\n")
        elif args.format == 'csv':
            import csv
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Conceito', 'Palavra'])
                for concept, word in sorted(vocabulary.items()):
                    writer.writerow([concept, word])
        
        print(f"\n✓ Vocabulário salvo em: {output_path}")
    else:
        print("\n--- PRIMEIRAS 20 PALAVRAS ---")
        for i, (concept, word) in enumerate(sorted(vocabulary.items())[:20]):
            print(f"  {concept:20} → {word}")
    
    engine.save_learning_data()
    
    return 0


def cmd_analyze(args):
    print("=" * 80)
    print(f"ANÁLISE DE IDIOMA: {args.profile}")
    print("=" * 80)
    
    manager = OriginalLanguageProfileManager()
    profile = manager.load_profile(args.profile)
    
    if not profile:
        print(f"\n✗ Perfil '{args.profile}' não encontrado")
        return 1
    
    engine = OriginalLanguageEngine(profile)
    
    stats = engine.get_statistics()
    
    print(f"\n--- INFORMAÇÕES DO PERFIL ---")
    print(f"ID: {stats['profile']['id']}")
    print(f"Nome: {stats['profile']['name']}")
    print(f"Seed: {stats['profile']['seed']}")
    
    print(f"\n--- FONOLOGIA ---")
    print(f"Vogais: {stats['phonology']['vowel_count']}")
    print(f"Consoantes: {stats['phonology']['consonant_count']}")
    print(f"Ditongos: {stats['phonology']['diphthong_count']}")
    print(f"Templates silábicos: {stats['phonology']['syllable_templates']}")
    
    print(f"\n--- LÉXICO ---")
    print(f"Total de palavras: {stats['lexicon']['total_words']}")
    print(f"Palavras únicas: {stats['lexicon']['unique_words']}")
    print(f"Qualidade média: {stats['lexicon']['average_quality']:.2f}")
    print(f"Comprimento médio: {stats['lexicon']['average_word_length']:.1f}")
    
    if stats['lexicon']['most_common_phonemes']:
        print(f"\nFonemas mais comuns:")
        for phoneme, count in stats['lexicon']['most_common_phonemes'][:10]:
            print(f"  {phoneme}: {count}")
    
    print(f"\n--- DISTRIBUIÇÃO ---")
    print(f"Entropia: {stats['distribution']['entropy']:.2f}")
    print(f"Uniformidade: {stats['distribution']['uniformity']:.2f}")
    
    if stats.get('recommendations'):
        print(f"\n--- RECOMENDAÇÕES ---")
        for rec in stats['recommendations']:
            print(f"  • {rec}")
    
    if args.export_stats:
        stats_path = args.export_stats
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Estatísticas exportadas para: {stats_path}")
    
    return 0


def cmd_export_dictionary(args):
    print("=" * 80)
    print(f"EXPORTAR DICIONÁRIO: {args.profile}")
    print("=" * 80)
    
    manager = OriginalLanguageProfileManager()
    profile = manager.load_profile(args.profile)
    
    if not profile:
        print(f"\n✗ Perfil '{args.profile}' não encontrado")
        return 1
    
    engine = OriginalLanguageEngine(profile)
    
    count = engine.export_dictionary(args.output, format=args.format)
    
    print(f"\n✓ {count} entradas exportadas para: {args.output}")
    print(f"  Formato: {args.format.upper()}")
    
    return 0


def cmd_batch_translate(args):
    print("=" * 80)
    print(f"TRADUÇÃO EM LOTE: {args.profile}")
    print("=" * 80)
    
    manager = OriginalLanguageProfileManager()
    profile = manager.load_profile(args.profile)
    
    if not profile:
        print(f"\n✗ Perfil '{args.profile}' não encontrado")
        return 1
    
    engine = OriginalLanguageEngine(profile)
    batch = BatchTranslator(engine)
    
    input_files = args.inputs
    
    print(f"\nProcessando {len(input_files)} arquivo(s)...")
    
    for input_file in input_files:
        input_path = Path(input_file)
        
        if not input_path.exists():
            print(f"  ✗ Arquivo não encontrado: {input_file}")
            continue
        
        output_file = args.output_dir / f"{input_path.stem}_translated{input_path.suffix}"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"\n  Processando: {input_file}")
        batch.translate_file(str(input_path), str(output_file))
        print(f"  ✓ Salvo em: {output_file}")
    
    engine.save_learning_data()
    print(f"\n✓ Tradução em lote concluída!")
    
    return 0


def cmd_delete_profile(args):
    print("=" * 80)
    print(f"DELETAR PERFIL: {args.profile}")
    print("=" * 80)
    
    manager = OriginalLanguageProfileManager()
    
    if not args.force:
        response = input(f"\nTem certeza que deseja deletar '{args.profile}'? (s/N): ")
        if response.lower() != 's':
            print("Operação cancelada.")
            return 0
    
    if manager.delete_profile(args.profile):
        print(f"\n✓ Perfil '{args.profile}' deletado com sucesso")
        return 0
    else:
        print(f"\n✗ Perfil '{args.profile}' não encontrado")
        return 1


def cmd_duplicate_profile(args):
    print("=" * 80)
    print(f"DUPLICAR PERFIL: {args.source} → {args.new_id}")
    print("=" * 80)
    
    manager = OriginalLanguageProfileManager()
    
    duplicate = manager.duplicate_profile(
        source_id=args.source,
        new_id=args.new_id,
        new_seed=args.new_seed
    )
    
    if duplicate:
        print(f"\n✓ Perfil duplicado com sucesso!")
        print(f"  ID original: {args.source}")
        print(f"  Novo ID: {args.new_id}")
        if args.new_seed:
            print(f"  Nova seed: {args.new_seed}")
            print(f"  (Fonologia será regenerada)")
        return 0
    else:
        print(f"\n✗ Perfil '{args.source}' não encontrado")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description='Gerador de Idiomas Originais - Original Language Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  
  Criar novo perfil:
    %(prog)s create minha_lingua --name "Meu Idioma" --seed 12345 --initialize
  
  Listar perfis:
    %(prog)s list --verbose
  
  Traduzir texto:
    %(prog)s translate minha_lingua --text "Hello world" --output saida.txt
  
  Gerar vocabulário:
    %(prog)s vocabulary minha_lingua --output vocabulario.json --include-numbers
  
  Analisar idioma:
    %(prog)s analyze minha_lingua --export-stats estatisticas.json
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponíveis')
    
    create_parser = subparsers.add_parser('create', help='Criar novo perfil de idioma')
    create_parser.add_argument('id', help='ID do perfil')
    create_parser.add_argument('--name', help='Nome do idioma')
    create_parser.add_argument('--seed', type=int, help='Seed para geração determinística')
    create_parser.add_argument('--complexity', choices=['simple', 'medium', 'complex'], 
                              default='medium', help='Complexidade fonológica')
    create_parser.add_argument('--initialize', action='store_true', 
                              help='Inicializar fonologia imediatamente')
    
    list_parser = subparsers.add_parser('list', help='Listar perfis existentes')
    list_parser.add_argument('-v', '--verbose', action='store_true', 
                            help='Mostrar detalhes')
    
    show_parser = subparsers.add_parser('show', help='Mostrar detalhes de um perfil')
    show_parser.add_argument('profile', help='ID do perfil')
    show_parser.add_argument('--json', action='store_true', 
                            help='Mostrar JSON completo')
    
    translate_parser = subparsers.add_parser('translate', help='Traduzir texto')
    translate_parser.add_argument('profile', help='ID do perfil')
    translate_parser.add_argument('--text', help='Texto para traduzir')
    translate_parser.add_argument('--input', help='Arquivo de entrada')
    translate_parser.add_argument('--output', help='Arquivo de saída')
    translate_parser.add_argument('--save-learning', action='store_true',
                                 help='Salvar dados de aprendizado')
    
    vocab_parser = subparsers.add_parser('vocabulary', help='Gerar vocabulário básico')
    vocab_parser.add_argument('profile', help='ID do perfil')
    vocab_parser.add_argument('--output', help='Arquivo de saída')
    vocab_parser.add_argument('--format', choices=['json', 'txt', 'csv'],
                             default='json', help='Formato de saída')
    vocab_parser.add_argument('--include-numbers', action='store_true',
                             help='Incluir números 0-99')
    
    analyze_parser = subparsers.add_parser('analyze', help='Analisar idioma')
    analyze_parser.add_argument('profile', help='ID do perfil')
    analyze_parser.add_argument('--export-stats', help='Exportar estatísticas para arquivo JSON')
    
    export_parser = subparsers.add_parser('export', help='Exportar dicionário')
    export_parser.add_argument('profile', help='ID do perfil')
    export_parser.add_argument('output', help='Arquivo de saída')
    export_parser.add_argument('--format', choices=['json', 'txt', 'csv'],
                              default='json', help='Formato de saída')
    
    batch_parser = subparsers.add_parser('batch', help='Tradução em lote')
    batch_parser.add_argument('profile', help='ID do perfil')
    batch_parser.add_argument('inputs', nargs='+', help='Arquivos de entrada')
    batch_parser.add_argument('--output-dir', type=Path, default=Path('output'),
                             help='Diretório de saída')
    
    delete_parser = subparsers.add_parser('delete', help='Deletar perfil')
    delete_parser.add_argument('profile', help='ID do perfil')
    delete_parser.add_argument('-f', '--force', action='store_true',
                              help='Não pedir confirmação')
    
    dup_parser = subparsers.add_parser('duplicate', help='Duplicar perfil')
    dup_parser.add_argument('source', help='ID do perfil original')
    dup_parser.add_argument('new_id', help='ID do novo perfil')
    dup_parser.add_argument('--new-seed', type=int,
                           help='Nova seed (regerará fonologia)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    commands = {
        'create': cmd_create_profile,
        'list': cmd_list_profiles,
        'show': cmd_show_profile,
        'translate': cmd_translate,
        'vocabulary': cmd_generate_vocabulary,
        'analyze': cmd_analyze,
        'export': cmd_export_dictionary,
        'batch': cmd_batch_translate,
        'delete': cmd_delete_profile,
        'duplicate': cmd_duplicate_profile
    }
    
    try:
        return commands[args.command](args)
    except Exception as e:
        print(f"\n✗ Erro: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
