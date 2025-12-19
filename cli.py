#!/usr/bin/env python3

import argparse
import sys
import json
from pathlib import Path
from zipper_engine import ZipperEngine
from language_profile_manager import LanguageProfileManager
from utilities import (
    NameGenerator, TextAnalyzer, ExportUtilities,
    ProfileTemplates, BatchProfileGenerator, QuickSetup
)


def cmd_generate(args):
    profile_path = Path('profiles') / f"{args.profile}.json"
    
    if not profile_path.exists():
        print(f"Error: Profile '{args.profile}' not found")
        return 1
    
    with open(profile_path, 'r', encoding='utf-8') as f:
        profile = json.load(f)
    
    num_bases = len(profile.get('bases', []))
    
    if len(args.inputs) != num_bases:
        print(f"Error: Profile requires {num_bases} input files, got {len(args.inputs)}")
        return 1
    
    base_texts = []
    for input_file in args.inputs:
        input_path = Path(input_file)
        if not input_path.exists():
            print(f"Error: Input file not found: {input_file}")
            return 1
        
        with open(input_path, 'r', encoding='utf-8') as f:
            base_texts.append(f.read())
    
    engine = ZipperEngine(str(profile_path))
    result = engine.process_texts(base_texts)
    
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result)
        print(f"Output written to: {output_path}")
    else:
        print(result)
    
    if args.stats:
        analysis = TextAnalyzer.analyze_text(result)
        print("\nStatistics:")
        print(f"  Words: {analysis['word_count']}")
        print(f"  Characters: {analysis['char_count']}")
        print(f"  Vowel ratio: {analysis['vowel_ratio']:.2%}")
        print(f"  Avg word length: {analysis['avg_word_length']:.1f}")
    
    return 0


def cmd_list_profiles(args):
    manager = LanguageProfileManager()
    profile_ids = manager.get_all_profile_ids()
    
    if not profile_ids:
        print("No profiles found")
        return 0
    
    print(f"Available profiles ({len(profile_ids)}):")
    print()
    
    for pid in profile_ids:
        profile = manager.get_profile(pid)
        name = profile.get('name', 'N/A')
        bases = ', '.join(profile.get('bases', []))
        
        print(f"  {pid}")
        print(f"    Name: {name}")
        print(f"    Bases: {bases}")
        
        if args.verbose:
            desc = profile.get('description', 'No description')
            weights = profile.get('fusion_weights', [])
            print(f"    Description: {desc}")
            print(f"    Weights: {weights}")
        
        print()
    
    return 0


def cmd_show_profile(args):
    manager = LanguageProfileManager()
    profile = manager.get_profile(args.profile)
    
    if not profile:
        print(f"Error: Profile '{args.profile}' not found")
        return 1
    
    print(json.dumps(profile, indent=2, ensure_ascii=False))
    return 0


def cmd_create_profile(args):
    manager = LanguageProfileManager()
    
    if args.template:
        templates = {
            'formal': ProfileTemplates.get_formal_aristocratic,
            'trade': ProfileTemplates.get_trade_language,
            'ancient': ProfileTemplates.get_ancient_scholarly,
            'poetic': ProfileTemplates.get_poetic_melodic
        }
        
        if args.template not in templates:
            print(f"Error: Unknown template '{args.template}'")
            print(f"Available templates: {', '.join(templates.keys())}")
            return 1
        
        profile = templates[args.template]()
        profile['id'] = args.id
        profile['name'] = args.name or args.id
    else:
        bases = args.bases.split(',')
        weights = [float(w) for w in args.weights.split(',')] if args.weights else None
        
        if not weights:
            weights = [1.0 / len(bases)] * len(bases)
        
        if len(weights) != len(bases):
            print("Error: Number of weights must match number of bases")
            return 1
        
        profile = {
            "id": args.id,
            "name": args.name or args.id,
            "description": args.description or "",
            "bases": bases,
            "fusion_weights": weights,
            "fusion_rules": {
                "min_cut_point": 0.4,
                "preserve_caps": True,
                "preserve_accents": False
            },
            "phonotactics": {
                "vowels": "aeiou",
                "forbidden_final_consonants": [],
                "max_consonant_cluster": 3,
                "max_vowel_cluster": 2
            },
            "orthography": {},
            "global_seed": args.seed or 12345
        }
    
    manager.create_profile(profile)
    print(f"Profile '{args.id}' created successfully")
    
    if args.edit:
        print(json.dumps(profile, indent=2, ensure_ascii=False))
    
    return 0


def cmd_delete_profile(args):
    manager = LanguageProfileManager()
    
    if not args.force:
        response = input(f"Delete profile '{args.profile}'? (y/N): ")
        if response.lower() != 'y':
            print("Cancelled")
            return 0
    
    if manager.delete_profile(args.profile):
        print(f"Profile '{args.profile}' deleted")
        return 0
    else:
        print(f"Error: Profile '{args.profile}' not found")
        return 1


def cmd_generate_names(args):
    profile_path = Path('profiles') / f"{args.profile}.json"
    
    if not profile_path.exists():
        print(f"Error: Profile '{args.profile}' not found")
        return 1
    
    engine = ZipperEngine(str(profile_path))
    name_gen = NameGenerator(engine)
    
    base_texts = []
    for text in args.texts:
        base_texts.append(text)
    
    if args.type == 'character':
        names = name_gen.generate_names(base_texts, count=args.count)
    else:
        suffixes = args.suffixes.split(',') if args.suffixes else ['ia', 'ton', 'ville']
        names = name_gen.generate_place_names(base_texts, suffixes, count=args.count)
    
    print(f"Generated {len(names)} {args.type} names:\n")
    for i, name in enumerate(names, 1):
        print(f"  {i}. {name}")
    
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            for name in names:
                f.write(name + '\n')
        print(f"\nNames written to: {output_path}")
    
    return 0


def cmd_export_lexicon(args):
    input_path = Path(args.input)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input}")
        return 1
    
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    lexicon = ExportUtilities.export_lexicon(text, min_word_length=args.min_length)
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if args.format == 'json':
        ExportUtilities.export_to_json(lexicon, str(output_path))
    elif args.format == 'csv':
        ExportUtilities.export_to_csv(lexicon, str(output_path))
    else:
        with open(output_path, 'w', encoding='utf-8') as f:
            for entry in lexicon:
                f.write(f"{entry['word']}\n")
    
    print(f"Lexicon ({len(lexicon)} words) exported to: {output_path}")
    return 0


def cmd_analyze(args):
    input_path = Path(args.input)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input}")
        return 1
    
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    analysis = TextAnalyzer.analyze_text(text)
    
    print("Text Analysis:")
    print(f"  Words: {analysis['word_count']}")
    print(f"  Characters: {analysis['char_count']}")
    print(f"  Vowels: {analysis['vowel_count']}")
    print(f"  Consonants: {analysis['consonant_count']}")
    print(f"  Vowel ratio: {analysis['vowel_ratio']:.2%}")
    print(f"  Average word length: {analysis['avg_word_length']:.1f}")
    
    if args.compare:
        compare_path = Path(args.compare)
        if compare_path.exists():
            with open(compare_path, 'r', encoding='utf-8') as f:
                compare_text = f.read()
            
            comparison = TextAnalyzer.compare_texts(text, compare_text)
            print("\nComparison with reference:")
            print(f"  Length preservation: {comparison['length_preservation']:.2%}")
            print(f"  Vowel ratio shift: {comparison['vowel_shift']:+.3f}")
    
    return 0


def cmd_batch_dialects(args):
    manager = LanguageProfileManager()
    base_profile = manager.get_profile(args.profile)
    
    if not base_profile:
        print(f"Error: Profile '{args.profile}' not found")
        return 1
    
    variants = BatchProfileGenerator.generate_dialect_variations(
        base_profile,
        num_variants=args.count
    )
    
    print(f"Generating {len(variants)} dialect variations...")
    
    for variant in variants:
        manager.create_profile(variant)
        print(f"  Created: {variant['id']}")
    
    print(f"\nSuccessfully created {len(variants)} dialect profiles")
    return 0


def cmd_setup(args):
    print("Setting up Hadabian Language Zipper...")
    
    dirs = QuickSetup.create_default_structure()
    print("\nCreated directories:")
    for name, path in dirs.items():
        print(f"  {name}: {path}")
    
    if args.examples:
        print("\nCreating example input files...")
        files = QuickSetup.create_example_inputs()
        for filename in files:
            print(f"  Created: inputs/{filename}")
    
    if args.templates:
        print("\nCreating template profiles...")
        manager = LanguageProfileManager()
        
        templates = [
            ('template_formal', ProfileTemplates.get_formal_aristocratic()),
            ('template_trade', ProfileTemplates.get_trade_language()),
            ('template_ancient', ProfileTemplates.get_ancient_scholarly()),
            ('template_poetic', ProfileTemplates.get_poetic_melodic())
        ]
        
        for profile_id, template in templates:
            template['id'] = profile_id
            manager.create_profile(template)
            print(f"  Created: {profile_id}")
    
    print("\nSetup complete!")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description='Hadabian Language Zipper - CLI Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    gen_parser = subparsers.add_parser('generate', help='Generate text')
    gen_parser.add_argument('profile', help='Profile ID')
    gen_parser.add_argument('inputs', nargs='+', help='Input files (one per base language)')
    gen_parser.add_argument('-o', '--output', help='Output file')
    gen_parser.add_argument('-s', '--stats', action='store_true', help='Show statistics')
    
    list_parser = subparsers.add_parser('list', help='List profiles')
    list_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    show_parser = subparsers.add_parser('show', help='Show profile details')
    show_parser.add_argument('profile', help='Profile ID')
    
    create_parser = subparsers.add_parser('create', help='Create new profile')
    create_parser.add_argument('id', help='Profile ID')
    create_parser.add_argument('-n', '--name', help='Profile name')
    create_parser.add_argument('-d', '--description', help='Description')
    create_parser.add_argument('-b', '--bases', help='Base languages (comma-separated)')
    create_parser.add_argument('-w', '--weights', help='Fusion weights (comma-separated)')
    create_parser.add_argument('-s', '--seed', type=int, help='Global seed')
    create_parser.add_argument('-t', '--template', choices=['formal', 'trade', 'ancient', 'poetic'], help='Use template')
    create_parser.add_argument('-e', '--edit', action='store_true', help='Show created profile')
    
    delete_parser = subparsers.add_parser('delete', help='Delete profile')
    delete_parser.add_argument('profile', help='Profile ID')
    delete_parser.add_argument('-f', '--force', action='store_true', help='Skip confirmation')
    
    names_parser = subparsers.add_parser('names', help='Generate names')
    names_parser.add_argument('profile', help='Profile ID')
    names_parser.add_argument('texts', nargs='+', help='Seed texts')
    names_parser.add_argument('-t', '--type', choices=['character', 'place'], default='character', help='Name type')
    names_parser.add_argument('-c', '--count', type=int, default=10, help='Number of names')
    names_parser.add_argument('-s', '--suffixes', help='Place name suffixes (comma-separated)')
    names_parser.add_argument('-o', '--output', help='Output file')
    
    export_parser = subparsers.add_parser('export', help='Export lexicon')
    export_parser.add_argument('input', help='Input file')
    export_parser.add_argument('output', help='Output file')
    export_parser.add_argument('-f', '--format', choices=['json', 'csv', 'txt'], default='json', help='Output format')
    export_parser.add_argument('-m', '--min-length', type=int, default=3, help='Minimum word length')
    
    analyze_parser = subparsers.add_parser('analyze', help='Analyze text')
    analyze_parser.add_argument('input', help='Input file')
    analyze_parser.add_argument('-c', '--compare', help='Compare with reference file')
    
    batch_parser = subparsers.add_parser('dialects', help='Generate dialect variations')
    batch_parser.add_argument('profile', help='Base profile ID')
    batch_parser.add_argument('-c', '--count', type=int, default=5, help='Number of dialects')
    
    setup_parser = subparsers.add_parser('setup', help='Setup project structure')
    setup_parser.add_argument('-e', '--examples', action='store_true', help='Create example inputs')
    setup_parser.add_argument('-t', '--templates', action='store_true', help='Create template profiles')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    commands = {
        'generate': cmd_generate,
        'list': cmd_list_profiles,
        'show': cmd_show_profile,
        'create': cmd_create_profile,
        'delete': cmd_delete_profile,
        'names': cmd_generate_names,
        'export': cmd_export_lexicon,
        'analyze': cmd_analyze,
        'dialects': cmd_batch_dialects,
        'setup': cmd_setup
    }
    
    return commands[args.command](args)


if __name__ == '__main__':
    sys.exit(main())