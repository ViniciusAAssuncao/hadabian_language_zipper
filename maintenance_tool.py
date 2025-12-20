import argparse
import json
from pathlib import Path
from zipper_engine import ZipperEngine
from utilities import ConsistencyReporter, DictionaryExporter


def consolidate_profile(profile_id, cache_freq=3, learning_usage=5, learning_conf=0.6):
    print(f"Consolidando perfil: {profile_id}")
    print("=" * 60)
    
    profile_path = Path('profiles') / f'{profile_id}.json'
    if not profile_path.exists():
        print(f"❌ Perfil não encontrado: {profile_path}")
        return
    
    engine = ZipperEngine(
        str(profile_path),
        enable_learning=True,
        enable_caching=True,
        enable_context=True
    )
    
    print("\n1. Consolidando cache...")
    consolidated_cache = engine.consolidate_cache(min_frequency=cache_freq)
    print(f"   ✓ {consolidated_cache} variações de cache consolidadas")
    
    print("\n2. Consolidando aprendizado...")
    consolidated_learning = engine.consolidate_learning(
        min_usage=learning_usage,
        min_confidence=learning_conf
    )
    print(f"   ✓ {consolidated_learning} padrões de aprendizado consolidados")
    
    print("\n3. Estatísticas atualizadas:")
    stats = engine.get_statistics()
    
    if 'cache' in stats:
        print(f"   Cache: {stats['cache']['total_entries']} entradas")
        print(f"   Variações: {stats['cache']['entries_with_variations']}")
        print(f"   Taxa de variação: {stats['cache']['variation_rate']:.1%}")
    
    if 'learning' in stats:
        print(f"   Regras aprendidas: {stats['learning']['total_rules']}")
        print(f"   Taxa de sucesso: {stats['learning']['success_rate']:.1%}")
        print(f"   Confiança média: {stats['learning']['average_confidence']:.1%}")
    
    if 'convergence' in stats:
        print(f"   Taxa de convergência: {stats['convergence']['convergence_rate']:.1%}")
        print(f"   Taxa de estabilidade: {stats['convergence']['stability_rate']:.1%}")
    
    print("\n✓ Consolidação completa!")


def export_dictionaries(profile_id, output_dir='dictionaries', min_freq=1):
    print(f"Exportando dicionários para: {profile_id}")
    print("=" * 60)
    
    profile_path = Path('profiles') / f'{profile_id}.json'
    if not profile_path.exists():
        print(f"❌ Perfil não encontrado: {profile_path}")
        return
    
    engine = ZipperEngine(
        str(profile_path),
        enable_caching=True
    )
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    exporter = DictionaryExporter(engine.translation_cache)
    
    print("\n1. Exportando formato JSON...")
    json_file = output_path / f'{profile_id}_dictionary.json'
    count_json = exporter.export_full_dictionary(
        str(json_file), format='json', min_frequency=min_freq
    )
    print(f"   ✓ {count_json} entradas → {json_file}")
    
    print("\n2. Exportando formato CSV...")
    csv_file = output_path / f'{profile_id}_dictionary.csv'
    count_csv = exporter.export_full_dictionary(
        str(csv_file), format='csv', min_frequency=min_freq
    )
    print(f"   ✓ {count_csv} entradas → {csv_file}")
    
    print("\n3. Exportando formato TXT...")
    txt_file = output_path / f'{profile_id}_dictionary.txt'
    count_txt = exporter.export_full_dictionary(
        str(txt_file), format='txt', min_frequency=min_freq
    )
    print(f"   ✓ {count_txt} entradas → {txt_file}")
    
    print("\n✓ Exportação completa!")


def check_consistency(profile_id):
    print(f"Verificando consistência: {profile_id}")
    print("=" * 60)
    
    profile_path = Path('profiles') / f'{profile_id}.json'
    if not profile_path.exists():
        print(f"❌ Perfil não encontrado: {profile_path}")
        return
    
    engine = ZipperEngine(
        str(profile_path),
        enable_learning=True,
        enable_caching=True,
        enable_context=True
    )
    
    reporter = ConsistencyReporter(engine)
    report = reporter.generate_consistency_report()
    
    print("\n1. Relatório de Validação:")
    if 'validation' in report:
        print(f"   Taxa de consistência: {report['validation']['consistency_rate']:.1%}")
        print(f"   Inconsistências: {report['validation']['inconsistency_count']}")
        
        if report['validation']['inconsistency_count'] > 0:
            print("\n   Primeiras inconsistências:")
            for inc in report['validation']['inconsistencies'][:5]:
                print(f"     • {inc['source']}: {inc['previous']} vs {inc['current']}")
    
    print("\n2. Relatório de Convergência:")
    if 'convergence' in report:
        print(f"   Traduções totais: {report['convergence']['total_translations']}")
        print(f"   Convergidas: {report['convergence']['converged']}")
        print(f"   Estáveis: {report['convergence']['stable']}")
        print(f"   Taxa de convergência: {report['convergence']['convergence_rate']:.1%}")
        print(f"   Taxa de estabilidade: {report['convergence']['stability_rate']:.1%}")
    
    print("\n3. Relatório de Cache:")
    if 'cache' in report:
        print(f"   Entradas totais: {report['cache']['total_entries']}")
        print(f"   Com variações: {report['cache']['entries_with_variations']}")
        print(f"   Taxa de variação: {report['cache']['variation_rate']:.1%}")
        print(f"   Média de usos: {report['cache']['avg_uses_per_entry']:.1f}")
    
    print("\n4. Sugestões de Correção:")
    suggestions = reporter.suggest_corrections()
    if suggestions:
        print(f"   Total de sugestões: {len(suggestions)}")
        for i, suggestion in enumerate(suggestions[:10], 1):
            print(f"   {i}. {suggestion['source']}")
            print(f"      Conflitos: {', '.join(suggestion['conflicting_translations'])}")
            print(f"      Sugestão: {suggestion['suggested_translation']} ({suggestion['reason']})")
    else:
        print("   ✓ Nenhuma correção necessária!")
    
    print("\n✓ Verificação completa!")


def cleanup_profile(profile_id, min_quality=0.3, min_uses=2):
    print(f"Limpando dados de baixa qualidade: {profile_id}")
    print("=" * 60)
    
    profile_path = Path('profiles') / f'{profile_id}.json'
    if not profile_path.exists():
        print(f"❌ Perfil não encontrado: {profile_path}")
        return
    
    engine = ZipperEngine(
        str(profile_path),
        enable_learning=True,
        enable_caching=True
    )
    
    print("\n1. Limpando padrões de baixa qualidade...")
    if hasattr(engine, 'learning_system'):
        cleaned = engine.learning_system.cleanup_low_quality_patterns(
            min_quality=min_quality,
            min_uses=min_uses
        )
        print(f"   ✓ {cleaned} padrões removidos")
    
    print("\n2. Consolidando cache...")
    consolidated = engine.consolidate_cache(min_frequency=3)
    print(f"   ✓ {consolidated} variações consolidadas")
    
    print("\n3. Salvando dados limpos...")
    if hasattr(engine, 'translation_cache'):
        engine.translation_cache.save_cache()
    if hasattr(engine, 'learning_system'):
        engine.learning_system.save_learning_data()
    print("   ✓ Dados salvos")
    
    print("\n✓ Limpeza completa!")


def show_statistics(profile_id):
    print(f"Estatísticas detalhadas: {profile_id}")
    print("=" * 60)
    
    profile_path = Path('profiles') / f'{profile_id}.json'
    if not profile_path.exists():
        print(f"❌ Perfil não encontrado: {profile_path}")
        return
    
    engine = ZipperEngine(
        str(profile_path),
        enable_learning=True,
        enable_caching=True,
        enable_context=True
    )
    
    stats = engine.get_statistics()
    
    print("\n📊 ESTATÍSTICAS GERAIS")
    print("-" * 60)
    print(f"Profile ID: {stats['profile_id']}")
    print(f"Bases: {', '.join(stats['bases'])}")
    print(f"Pesos: {', '.join(f'{w:.2f}' for w in stats['weights'])}")
    print(f"Estágio: {stats['evolution_stage']}")
    
    if 'cache' in stats:
        print("\n📦 CACHE")
        print("-" * 60)
        print(f"Entradas totais: {stats['cache']['total_entries']}")
        print(f"Entradas com variações: {stats['cache']['entries_with_variations']}")
        print(f"Taxa de variação: {stats['cache']['variation_rate']:.1%}")
        print(f"Usos totais: {stats['cache']['total_uses']}")
        print(f"Média de usos por entrada: {stats['cache']['avg_uses_per_entry']:.2f}")
    
    if 'learning' in stats:
        print("\n🧠 APRENDIZADO")
        print("-" * 60)
        print(f"Regras de transformação: {stats['learning']['total_rules']}")
        print(f"Padrões registrados: {stats['learning']['total_patterns']}")
        print(f"Tentativas totais: {stats['learning']['total_attempts']}")
        print(f"Sucessos: {stats['learning']['total_successes']}")
        print(f"Taxa de sucesso: {stats['learning']['success_rate']:.1%}")
        print(f"Confiança média: {stats['learning']['average_confidence']:.1%}")
        print(f"Qualidade recente: {stats['learning']['recent_quality']:.1%}")
        print(f"Tamanho do histórico: {stats['learning']['history_size']}")
    
    if 'convergence' in stats:
        print("\n🎯 CONVERGÊNCIA")
        print("-" * 60)
        print(f"Traduções únicas: {stats['convergence']['total_translations']}")
        print(f"Convergidas: {stats['convergence']['converged']}")
        print(f"Estáveis: {stats['convergence']['stable']}")
        print(f"Taxa de convergência: {stats['convergence']['convergence_rate']:.1%}")
        print(f"Taxa de estabilidade: {stats['convergence']['stability_rate']:.1%}")
        print(f"Convergência média: {stats['convergence']['average_convergence']:.1%}")
    
    if 'consistency' in stats:
        print("\n✅ CONSISTÊNCIA")
        print("-" * 60)
        print(f"Taxa de consistência: {stats['consistency']['rate']:.1%}")
        print(f"Inconsistências detectadas: {stats['consistency']['inconsistencies']}")
    
    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Ferramenta de manutenção do Hadabian Language Zipper'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponíveis')
    
    consolidate_parser = subparsers.add_parser('consolidate', help='Consolidar dados do perfil')
    consolidate_parser.add_argument('profile_id', help='ID do perfil')
    consolidate_parser.add_argument('--cache-freq', type=int, default=3, help='Frequência mínima para cache')
    consolidate_parser.add_argument('--learning-usage', type=int, default=5, help='Uso mínimo para learning')
    consolidate_parser.add_argument('--learning-conf', type=float, default=0.6, help='Confiança mínima')
    
    export_parser = subparsers.add_parser('export', help='Exportar dicionários')
    export_parser.add_argument('profile_id', help='ID do perfil')
    export_parser.add_argument('--output-dir', default='dictionaries', help='Diretório de saída')
    export_parser.add_argument('--min-freq', type=int, default=1, help='Frequência mínima')
    
    check_parser = subparsers.add_parser('check', help='Verificar consistência')
    check_parser.add_argument('profile_id', help='ID do perfil')
    
    cleanup_parser = subparsers.add_parser('cleanup', help='Limpar dados de baixa qualidade')
    cleanup_parser.add_argument('profile_id', help='ID do perfil')
    cleanup_parser.add_argument('--min-quality', type=float, default=0.3, help='Qualidade mínima')
    cleanup_parser.add_argument('--min-uses', type=int, default=2, help='Usos mínimos')
    
    stats_parser = subparsers.add_parser('stats', help='Mostrar estatísticas')
    stats_parser.add_argument('profile_id', help='ID do perfil')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'consolidate':
        consolidate_profile(
            args.profile_id,
            args.cache_freq,
            args.learning_usage,
            args.learning_conf
        )
    elif args.command == 'export':
        export_dictionaries(args.profile_id, args.output_dir, args.min_freq)
    elif args.command == 'check':
        check_consistency(args.profile_id)
    elif args.command == 'cleanup':
        cleanup_profile(args.profile_id, args.min_quality, args.min_uses)
    elif args.command == 'stats':
        show_statistics(args.profile_id)


if __name__ == '__main__':
    main()