#!/usr/bin/env python3

import os
import sys
from pathlib import Path


def print_banner():
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "GERADOR DE IDIOMAS ORIGINAIS" + " " * 30 + "║")
    print("║" + " " * 30 + "SETUP INICIAL" + " " * 36 + "║")
    print("╚" + "=" * 78 + "╝")
    print()


def create_directory_structure():
    print("=" * 80)
    print("CRIANDO ESTRUTURA DE DIRETÓRIOS")
    print("=" * 80)
    print()
    
    directories = [
        'original_profiles',
        'original_learning',
        'output',
        'examples/input',
        'examples/output'
    ]
    
    for directory in directories:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        print(f"✓ {directory}/")
    
    print()
    return True


def create_example_files():
    print("=" * 80)
    print("CRIANDO ARQUIVOS DE EXEMPLO")
    print("=" * 80)
    print()
    
    example_text = """Hello world. This is an example text for the original language generator.
The sun rises over the mountains. Birds sing in the morning.
Water flows through the valley. Trees grow tall and strong.
People live in peace. Friends share stories by the fire.
This is the beauty of our world."""
    
    example_path = Path('examples/input/example.txt')
    with open(example_path, 'w', encoding='utf-8') as f:
        f.write(example_text)
    
    print(f"✓ {example_path}")
    
    wordlist = ['hello', 'world', 'sun', 'moon', 'water', 'fire', 'earth', 'wind',
                'tree', 'mountain', 'river', 'star', 'friend', 'family', 'love', 'peace']
    
    wordlist_path = Path('examples/input/wordlist.txt')
    with open(wordlist_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(wordlist))
    
    print(f"✓ {wordlist_path}")
    print()
    
    return True


def create_example_profiles():
    print("=" * 80)
    print("CRIANDO PERFIS DE EXEMPLO")
    print("=" * 80)
    print()
    
    from original_language_engine import OriginalLanguageProfileManager
    
    manager = OriginalLanguageProfileManager()
    
    profiles = [
        {
            'id': 'exemplo_simples',
            'name': 'Idioma Simples',
            'seed': 1000,
            'complexity': 'simple'
        },
        {
            'id': 'exemplo_medio',
            'name': 'Idioma Médio',
            'seed': 2000,
            'complexity': 'medium'
        },
        {
            'id': 'exemplo_complexo',
            'name': 'Idioma Complexo',
            'seed': 3000,
            'complexity': 'complex'
        }
    ]
    
    for profile_data in profiles:
        profile = manager.create_profile(
            profile_id=profile_data['id'],
            name=profile_data['name'],
            seed=profile_data['seed'],
            complexity=profile_data['complexity']
        )
        print(f"✓ {profile.profile_id} ({profile.name})")
    
    print()
    return True


def create_readme():
    print("=" * 80)
    print("CRIANDO ARQUIVO QUICKSTART")
    print("=" * 80)
    print()
    
    quickstart_content = """# Gerador de Idiomas Originais - Início Rápido

## Instalação Concluída ✓

Todos os diretórios e arquivos de exemplo foram criados.

## Começando Agora

### 1. Interface Gráfica (Recomendado para iniciantes)

```bash
python original_gui.py
```

### 2. Linha de Comando

#### Listar idiomas de exemplo
```bash
python original_cli.py list --verbose
```

#### Traduzir texto
```bash
python original_cli.py translate exemplo_medio --text "Hello world"
```

#### Traduzir arquivo
```bash
python original_cli.py translate exemplo_medio --input examples/input/example.txt --output examples/output/translated.txt
```

#### Gerar vocabulário
```bash
python original_cli.py vocabulary exemplo_medio --output examples/output/vocab.json --include-numbers
```

### 3. Demonstração Interativa

```bash
python demo_original_language.py
```

### 4. Criar Seu Próprio Idioma

```bash
python original_cli.py create meu_idioma --name "Meu Idioma" --seed 12345 --initialize
```

## Estrutura de Diretórios

```
.
├── original_profiles/          # Perfis de idiomas
│   ├── exemplo_simples.json
│   ├── exemplo_medio.json
│   └── exemplo_complexo.json
├── original_learning/          # Dados de aprendizado
├── examples/                   # Exemplos de entrada/saída
│   ├── input/
│   └── output/
└── output/                     # Saídas gerais
```

## Próximos Passos

1. Leia **ORIGINAL_README.md** para documentação completa
2. Execute **test_original_generator.py** para verificar a instalação
3. Experimente com os perfis de exemplo
4. Crie seus próprios idiomas!

## Ajuda

Para ver todos os comandos disponíveis:
```bash
python original_cli.py --help
```

Para ajuda com um comando específico:
```bash
python original_cli.py translate --help
```
"""
    
    quickstart_path = Path('QUICKSTART.md')
    with open(quickstart_path, 'w', encoding='utf-8') as f:
        f.write(quickstart_content)
    
    print(f"✓ {quickstart_path}")
    print()
    
    return True


def verify_installation():
    print("=" * 80)
    print("VERIFICANDO INSTALAÇÃO")
    print("=" * 80)
    print()
    
    required_files = [
        'phoneme_inventory.py',
        'word_generator.py',
        'original_learning_system.py',
        'original_language_engine.py',
        'original_cli.py',
        'original_gui.py',
        'test_original_generator.py',
        'demo_original_language.py'
    ]
    
    all_present = True
    for filename in required_files:
        if Path(filename).exists():
            print(f"✓ {filename}")
        else:
            print(f"✗ {filename} - FALTANDO!")
            all_present = False
    
    print()
    
    if all_present:
        print("✓ Todos os arquivos necessários estão presentes")
    else:
        print("✗ Alguns arquivos estão faltando. Verifique a instalação.")
    
    print()
    return all_present


def run_quick_test():
    print("=" * 80)
    print("TESTE RÁPIDO")
    print("=" * 80)
    print()
    
    try:
        print("Importando módulos...")
        from original_language_engine import (
            OriginalLanguageEngine,
            OriginalLanguageProfile,
            OriginalLanguageProfileManager
        )
        print("✓ Importação bem-sucedida")
        
        print("\nCriando perfil de teste...")
        manager = OriginalLanguageProfileManager()
        profile = manager.create_profile(
            'teste_setup',
            name='Teste Setup',
            seed=99999,
            complexity='simple'
        )
        print("✓ Perfil criado")
        
        print("\nInicializando motor...")
        engine = OriginalLanguageEngine(profile)
        print("✓ Motor inicializado")
        
        print("\nTestando tradução...")
        traducao = engine.translate_word('hello')
        print(f"✓ 'hello' → '{traducao}'")
        
        print("\nRemovendo perfil de teste...")
        manager.delete_profile('teste_setup')
        print("✓ Limpeza concluída")
        
        print()
        print("✓ TESTE RÁPIDO PASSOU!")
        print()
        
        return True
        
    except Exception as e:
        print(f"\n✗ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print_banner()
    
    steps = [
        ("Criar Estrutura de Diretórios", create_directory_structure),
        ("Criar Arquivos de Exemplo", create_example_files),
        ("Criar Perfis de Exemplo", create_example_profiles),
        ("Criar Quickstart Guide", create_readme),
        ("Verificar Instalação", verify_installation),
        ("Executar Teste Rápido", run_quick_test)
    ]
    
    results = []
    
    for step_name, step_func in steps:
        print(f"Executando: {step_name}...")
        try:
            result = step_func()
            results.append((step_name, result))
        except Exception as e:
            print(f"\n✗ Erro em '{step_name}': {e}")
            import traceback
            traceback.print_exc()
            results.append((step_name, False))
    
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 30 + "RESUMO DO SETUP" + " " * 33 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    
    for step_name, result in results:
        status = "✓ OK" if result else "✗ FALHOU"
        print(f"{status:10} | {step_name}")
    
    print()
    
    all_ok = all(result for _, result in results)
    
    if all_ok:
        print("🎉 SETUP CONCLUÍDO COM SUCESSO!")
        print()
        print("Próximos passos:")
        print("  1. Leia QUICKSTART.md para começar")
        print("  2. Execute: python demo_original_language.py")
        print("  3. Ou execute: python original_gui.py")
        print()
        return 0
    else:
        print("⚠ Setup concluído com alguns erros.")
        print("Verifique os erros acima e tente novamente.")
        print()
        return 1


if __name__ == '__main__':
    sys.exit(main())
