import sys
from pathlib import Path
from zipper_engine import ZipperEngine
from language_profile_manager import LanguageProfileManager
from utilities import (
    TextAnalyzer, NameGenerator, ConsistencyChecker,
    ProfileTemplates, ExportUtilities, QuickSetup
)


def test_basic_generation():
    print("=" * 60)
    print("TEST 1: Basic Text Generation")
    print("=" * 60)
    
    profile_path = Path('profiles/cauteriano.json')
    if not profile_path.exists():
        print(f"Profile not found: {profile_path}")
        return False
    
    engine = ZipperEngine(str(profile_path))
    
    base_texts = [
        "Je marche dans la forêt",
        "Gölon in vud"
    ]
    
    result = engine.process_texts(base_texts)
    print(f"\nInput 1: {base_texts[0]}")
    print(f"Input 2: {base_texts[1]}")
    print(f"\nOutput: {result}")
    
    print("\n✓ Basic generation successful")
    return True


def test_determinism():
    print("\n" + "=" * 60)
    print("TEST 2: Determinism Check")
    print("=" * 60)
    
    profile_path = Path('profiles/cauteriano.json')
    if not profile_path.exists():
        print(f"Profile not found: {profile_path}")
        return False
    
    engine = ZipperEngine(str(profile_path))
    
    base_texts = [
        "Bonjour le monde",
        "Glidis vol"
    ]
    
    results = []
    for i in range(5):
        output = engine.process_texts(base_texts)
        results.append(output)
        print(f"Iteration {i+1}: {output}")
    
    all_same = all(r == results[0] for r in results)
    
    if all_same:
        print("\n✓ Determinism verified: All outputs identical")
        return True
    else:
        print("\n✗ Determinism failed: Outputs differ")
        return False


def test_multiple_profiles():
    print("\n" + "=" * 60)
    print("TEST 3: Multiple Profiles")
    print("=" * 60)
    
    manager = LanguageProfileManager()
    profile_ids = manager.get_all_profile_ids()
    
    print(f"\nFound {len(profile_ids)} profiles:")
    for pid in profile_ids:
        profile = manager.get_profile(pid)
        print(f"  - {pid}: {profile.get('name', 'N/A')}")
    
    print("\n✓ Profile loading successful")
    return True


def test_name_generation():
    print("\n" + "=" * 60)
    print("TEST 4: Name Generation")
    print("=" * 60)
    
    profile_path = Path('profiles/cauteriano.json')
    if not profile_path.exists():
        print(f"Profile not found: {profile_path}")
        return False
    
    engine = ZipperEngine(str(profile_path))
    name_gen = NameGenerator(engine)
    
    seed_texts = [
        "Marie Philippe Laurent Alexandre Catherine",
        "Yulit Päl Vom Jänik Pük"
    ]
    
    names = name_gen.generate_names(seed_texts, count=10)
    
    print("\nGenerated Character Names:")
    for i, name in enumerate(names, 1):
        print(f"  {i}. {name}")
    
    place_names = name_gen.generate_place_names(
        seed_texts,
        suffixes=['ia', 'ton', 'ville', 'burg'],
        count=8
    )
    
    print("\nGenerated Place Names:")
    for i, name in enumerate(place_names, 1):
        print(f"  {i}. {name}")
    
    print("\n✓ Name generation successful")
    return True


def test_text_analysis():
    print("\n" + "=" * 60)
    print("TEST 5: Text Analysis")
    print("=" * 60)
    
    original = "Je marche dans la belle forêt enchantée"
    generated = "Jö marcolön dans la belö forät enchantäd"
    
    comparison = TextAnalyzer.compare_texts(original, generated)
    
    print(f"\nOriginal text: {original}")
    print(f"Generated text: {generated}")
    print(f"\nOriginal stats: {comparison['original']}")
    print(f"Generated stats: {comparison['generated']}")
    print(f"Length preservation: {comparison['length_preservation']:.2%}")
    print(f"Vowel ratio shift: {comparison['vowel_shift']:+.3f}")
    
    print("\n✓ Text analysis successful")
    return True


def test_profile_templates():
    print("\n" + "=" * 60)
    print("TEST 6: Profile Templates")
    print("=" * 60)
    
    templates = [
        ("Formal Aristocratic", ProfileTemplates.get_formal_aristocratic()),
        ("Trade Language", ProfileTemplates.get_trade_language()),
        ("Ancient Scholarly", ProfileTemplates.get_ancient_scholarly()),
        ("Poetic Melodic", ProfileTemplates.get_poetic_melodic())
    ]
    
    print("\nAvailable templates:")
    for name, template in templates:
        print(f"\n{name}:")
        print(f"  Bases: {', '.join(template['bases'])}")
        print(f"  Weights: {template['fusion_weights']}")
        print(f"  Style: {template['semantic_general']}")
    
    print("\n✓ Template generation successful")
    return True


def test_consistency_checker():
    print("\n" + "=" * 60)
    print("TEST 7: Consistency Checker")
    print("=" * 60)
    
    profile_path = Path('profiles/cauteriano.json')
    if not profile_path.exists():
        print(f"Profile not found: {profile_path}")
        return False
    
    test_texts = [
        "La vie est belle",
        "Lif binon jönik"
    ]
    
    result = ConsistencyChecker.test_profile_consistency(str(profile_path), test_texts)
    
    print(f"\nConsistency check results:")
    print(f"  Success: {result['success']}")
    print(f"  Deterministic: {result.get('deterministic', False)}")
    print(f"  Output sample: {result.get('output_sample', 'N/A')}")
    
    if result.get('output_stats'):
        print(f"  Output stats: {result['output_stats']}")
    
    if result['success'] and result.get('deterministic'):
        print("\n✓ Consistency check passed")
        return True
    else:
        print("\n✗ Consistency check failed")
        return False


def test_lexicon_export():
    print("\n" + "=" * 60)
    print("TEST 8: Lexicon Export")
    print("=" * 60)
    
    profile_path = Path('profiles/cauteriano.json')
    if not profile_path.exists():
        print(f"Profile not found: {profile_path}")
        return False
    
    engine = ZipperEngine(str(profile_path))
    
    base_texts = [
        "Le soleil brille dans le ciel azur. Les oiseaux chantent joyeusement.",
        "Soin blitön in sil bluf. Böds kanons yufikö."
    ]
    
    result = engine.process_texts(base_texts)
    lexicon = ExportUtilities.export_lexicon(result, min_word_length=3)
    
    print(f"\nGenerated text: {result}")
    print(f"\nLexicon ({len(lexicon)} unique words):")
    for entry in lexicon[:15]:
        print(f"  - {entry['word']} (length: {entry['length']})")
    
    output_dir = Path('outputs')
    output_dir.mkdir(exist_ok=True)
    
    json_path = output_dir / 'test_lexicon.json'
    ExportUtilities.export_to_json(lexicon, str(json_path))
    print(f"\nLexicon exported to: {json_path}")
    
    print("\n✓ Lexicon export successful")
    return True


def test_long_text():
    print("\n" + "=" * 60)
    print("TEST 9: Long Text Processing")
    print("=" * 60)
    
    profile_path = Path('profiles/cauteriano.json')
    if not profile_path.exists():
        print(f"Profile not found: {profile_path}")
        return False
    
    engine = ZipperEngine(str(profile_path))
    
    long_text_fr = """
    Dans les temps anciens, il existait un royaume magnifique.
    Les gens vivaient en harmonie avec la nature.
    Chaque jour apportait de nouvelles merveilles.
    Les sages enseignaient la sagesse aux jeunes.
    Et la paix régnait sur toute la terre.
    """
    
    long_text_vo = """
    In tims büik, palalän gretik äbinon.
    Mens libons in pämavöl ko natül.
    Dil valik brinon mäds nevik.
    Sapans tidons sapülam jenulike.
    E pif regön su topäd vätik.
    """
    
    result = engine.process_texts([long_text_fr, long_text_vo])
    
    print(f"\nInput length: {len(long_text_fr.split())} words (FR)")
    print(f"Output length: {len(result.split())} words")
    print(f"\nOutput preview:")
    lines = result.strip().split('\n')
    for line in lines[:3]:
        print(f"  {line.strip()}")
    print("  ...")
    
    print("\n✓ Long text processing successful")
    return True


def test_multi_base_language():
    print("\n" + "=" * 60)
    print("TEST 10: Multiple Base Languages (3+)")
    print("=" * 60)
    
    print("\nCreating temporary 3-base profile...")
    
    temp_profile = {
        "id": "test_triple",
        "name": "Triple Base Test",
        "description": "Test with 3 base languages",
        "bases": ["en", "fr", "de"],
        "fusion_weights": [0.4, 0.35, 0.25],
        "fusion_rules": {
            "min_cut_point": 0.4,
            "preserve_caps": True,
            "preserve_accents": False
        },
        "phonotactics": {
            "vowels": "aeiouäöü",
            "forbidden_final_consonants": [],
            "max_consonant_cluster": 3,
            "max_vowel_cluster": 2
        },
        "orthography": {},
        "global_seed": 99999
    }
    
    profile_path = Path('profiles/test_triple.json')
    import json
    with open(profile_path, 'w', encoding='utf-8') as f:
        json.dump(temp_profile, f, indent=2)
    
    engine = ZipperEngine(str(profile_path))
    
    base_texts = [
        "Hello beautiful world",
        "Bonjour beau monde",
        "Hallo schöne Welt"
    ]
    
    result = engine.process_texts(base_texts)
    
    print(f"\nInput 1 (EN): {base_texts[0]}")
    print(f"Input 2 (FR): {base_texts[1]}")
    print(f"Input 3 (DE): {base_texts[2]}")
    print(f"\nOutput: {result}")
    
    profile_path.unlink()
    print("\n✓ Multi-base generation successful")
    return True


def run_all_tests():
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "HADABIAN LANGUAGE ZIPPER" + " " * 19 + "║")
    print("║" + " " * 20 + "TEST SUITE v1.0" + " " * 23 + "║")
    print("╚" + "=" * 58 + "╝")
    
    QuickSetup.create_default_structure()
    
    tests = [
        ("Basic Generation", test_basic_generation),
        ("Determinism", test_determinism),
        ("Multiple Profiles", test_multiple_profiles),
        ("Name Generation", test_name_generation),
        ("Text Analysis", test_text_analysis),
        ("Profile Templates", test_profile_templates),
        ("Consistency Checker", test_consistency_checker),
        ("Lexicon Export", test_lexicon_export),
        ("Long Text", test_long_text),
        ("Multi-Base Language", test_multi_base_language)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} failed with exception: {str(e)}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("=" * 60)
    
    return passed == total


def demo_workflow():
    print("\n" + "=" * 60)
    print("DEMO: Complete Workflow Example")
    print("=" * 60)
    
    print("\n[Step 1] Setting up environment...")
    dirs = QuickSetup.create_default_structure()
    print(f"Created directories: {list(dirs.keys())}")
    
    print("\n[Step 2] Loading Cauteriano profile...")
    profile_path = Path('profiles/cauteriano.json')
    if not profile_path.exists():
        print("Profile not found!")
        return
    
    engine = ZipperEngine(str(profile_path))
    print(f"Loaded profile: Cauteriano")
    
    print("\n[Step 3] Preparing source texts...")
    source_fr = "La magie ancienne demeure dans les montagnes"
    source_vo = "Magiv büik städon in bels"
    
    print(f"French: {source_fr}")
    print(f"Völapük: {source_vo}")
    
    print("\n[Step 4] Generating Cauteriano text...")
    result = engine.process_texts([source_fr, source_vo])
    print(f"Result: {result}")
    
    print("\n[Step 5] Extracting character names...")
    name_gen = NameGenerator(engine)
    names = name_gen.generate_names([
        "Alexandre Marie Philippe Catherine Laurent",
        "Yulit Pük Flent Katän Lödön"
    ], count=5)
    
    print("Character names:")
    for name in names:
        print(f"  - {name}")
    
    print("\n[Step 6] Analyzing output...")
    analysis = TextAnalyzer.analyze_text(result)
    print(f"Words: {analysis['word_count']}")
    print(f"Vowel ratio: {analysis['vowel_ratio']:.2%}")
    print(f"Avg word length: {analysis['avg_word_length']:.1f}")
    
    print("\n[Step 7] Exporting lexicon...")
    lexicon = ExportUtilities.export_lexicon(result)
    output_path = Path('outputs/demo_lexicon.json')
    ExportUtilities.export_to_json(lexicon, str(output_path))
    print(f"Exported to: {output_path}")
    
    print("\n" + "=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo_workflow()
    else:
        success = run_all_tests()
        sys.exit(0 if success else 1)