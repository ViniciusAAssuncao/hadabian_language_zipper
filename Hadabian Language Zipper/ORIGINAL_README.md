# Gerador de Idiomas Originais (Original Language Generator)

Sistema computacional avançado para criação determin​ística de idiomas construídos totalmente originais, sem dependência de línguas naturais como base de fusão.

## 📋 Visão Geral

Este sistema gera idiomas completamente originais usando:

- **Inventário Fonêmico Universal**: Seleção baseada em princípios fonológicos universais
- **Restrições Fonotáticas**: Regras de combinação de sons inspiradas em línguas naturais
- **Geração Determinística**: Seeds criptográficas garantem reprodutibilidade total
- **Aprendizado Incremental**: Sistema evolui e melhora com uso
- **Métricas de Qualidade**: Avaliação automática de plausibilidade linguística

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    Interface do Usuário                      │
│                  (CLI / GUI / Programática)                  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│              OriginalLanguageEngine (Motor Principal)         │
├─────────────────────────────────────────────────────────────┤
│  • Coordenação de componentes                                │
│  • Tradução de texto                                         │
│  • Geração de vocabulário                                    │
│  • Análise estatística                                       │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────────────┐   ┌─────────────────┐   ┌────────────────┐
│   Phoneme     │   │  Word           │   │   Learning     │
│   Inventory   │   │  Generator      │   │   System       │
├───────────────┤   ├─────────────────┤   ├────────────────┤
│ • Seleção de  │   │ • Geração de    │   │ • Cache de     │
│   vogais      │   │   sílabas       │   │   conceitos    │
│ • Seleção de  │   │ • Geração de    │   │ • Estatísticas │
│   consoantes  │   │   palavras      │   │ • Análise de   │
│ • Ditongos    │   │ • Processos     │   │   distribuição │
│ • Ortografia  │   │   fonológicos   │   │ • Exportação   │
└───────────────┘   └─────────────────┘   └────────────────┘
```

## 🚀 Instalação

### Requisitos

- Python 3.8+
- Tkinter (para GUI)

### Setup

```bash
# Clone ou copie os arquivos para um diretório
mkdir original_language_generator
cd original_language_generator

# Copie os seguintes arquivos:
# - phoneme_inventory.py
# - word_generator.py
# - original_learning_system.py
# - original_language_engine.py
# - original_cli.py
# - original_gui.py
# - test_original_generator.py
```

## 📖 Uso

### Interface de Linha de Comando (CLI)

#### Criar um Novo Idioma

```bash
python original_cli.py create meu_idioma --name "Meu Idioma Original" --seed 12345 --initialize
```

Parâmetros:
- `--name`: Nome descritivo do idioma
- `--seed`: Semente para geração determinística (opcional)
- `--complexity`: `simple`, `medium`, ou `complex` (padrão: `medium`)
- `--initialize`: Gera fonologia imediatamente

#### Listar Idiomas

```bash
python original_cli.py list --verbose
```

#### Traduzir Texto

```bash
# Traduzir texto direto
python original_cli.py translate meu_idioma --text "Hello world, how are you?"

# Traduzir de arquivo
python original_cli.py translate meu_idioma --input entrada.txt --output saida.txt --save-learning
```

#### Gerar Vocabulário Básico

```bash
python original_cli.py vocabulary meu_idioma --output vocabulario.json --include-numbers
```

Formatos suportados: `json`, `txt`, `csv`

#### Análise de Idioma

```bash
python original_cli.py analyze meu_idioma --export-stats estatisticas.json
```

#### Exportar Dicionário

```bash
python original_cli.py export meu_idioma dicionario.json --format json
```

#### Tradução em Lote

```bash
python original_cli.py batch meu_idioma arquivo1.txt arquivo2.txt --output-dir traducoes/
```

### Interface Gráfica (GUI)

```bash
python original_gui.py
```

A GUI oferece:
- **Aba Tradutor**: Tradução interativa de texto
- **Aba Gerenciar Perfis**: CRUD de perfis de idiomas
- **Aba Vocabulário**: Geração e exportação de vocabulário
- **Aba Análise**: Estatísticas detalhadas do idioma

### Uso Programático

```python
from original_language_engine import (
    OriginalLanguageEngine,
    OriginalLanguageProfile,
    OriginalLanguageProfileManager
)

# Criar perfil
manager = OriginalLanguageProfileManager()
profile = manager.create_profile(
    profile_id='meu_idioma',
    name='Meu Idioma',
    seed=42,
    complexity='medium'
)

# Inicializar motor
engine = OriginalLanguageEngine(profile)

# Traduzir texto
traducao = engine.translate_text("Hello world")
print(f"Tradução: {traducao}")

# Gerar vocabulário
vocabulario = engine.generate_core_vocabulary(include_numbers=True)

# Obter estatísticas
stats = engine.get_statistics()
print(f"Total de palavras: {stats['lexicon']['total_words']}")
print(f"Qualidade média: {stats['lexicon']['average_quality']:.2f}")

# Salvar aprendizado
engine.save_learning_data()
```

## 🔬 Fundamentos Teóricos

### Inventário Fonêmico

O sistema usa um inventário universal baseado em:

- **Triângulo Vocálico**: Vogais organizadas por altura (close/mid/open) e recuo (front/central/back)
- **Lugar e Modo de Articulação**: Consoantes classificadas por ponto e modo de produção
- **Frequência Universal**: Pesos baseados em frequência cross-linguística (WALS)

**Exemplo de Seleção:**

```
Seed: 12345
Vogais (7): i, e, a, o, u, ə, æ
Consoantes (15): p, t, k, s, m, n, l, r, f, v, d, g, h, j, w
```

### Fonotática

Restrições geradas incluem:

- **Templates Silábicos**: V, CV, CVC, CCV, CCVC, etc.
- **Clusters Máximos**: Onset (1-3), Núcleo (1-2), Coda (0-2)
- **Proibições**: Clusters específicos evitados (ex: inicial #tk, final h#)

**Equação de Validação Silábica:**

```
Sílaba_Válida = (|Onset| ≤ max_onset) ∧ 
                (|Núcleo| ≥ 1) ∧ 
                (|Coda| ≤ max_coda) ∧
                (Onset ∉ Proibidos_Onset) ∧
                (Coda ∉ Proibidos_Coda)
```

### Geração Determinística

**Hash Criptográfico:**

```python
h = SHA256(conceito + seed_global)
índice_fonema = h mod |inventário_fonêmico|
```

**Garantias:**
- Mesma entrada → Mesma saída (100%)
- Distribuição uniforme de seleções
- Reprodutibilidade cross-platform

### Processos Fonológicos

Aplicados probabilisticamente:

1. **Assimilação** (20%): Consoantes adjacentes tornam-se similares
   ```
   Exemplo: /np/ → /mp/
   ```

2. **Apagamento** (15%): Vogal final removida
   ```
   Exemplo: /kata/ → /kat/
   ```

3. **Epêntese** (10%): Vogal inserida em cluster
   ```
   Exemplo: /ktr/ → /kətr/
   ```

### Métricas de Qualidade

**Função de Qualidade:**

```
Q(palavra) = Σ λᵢ · qᵢ(palavra)
```

Onde:
- q₁ = qualidade de comprimento (ideal: 3-7 chars)
- q₂ = validade fonêmica (chars no inventário)
- q₃ = estrutura (razão vogal/consoante ~0.4)
- q₄ = eufonia (alternância V-C)

**Pesos:** λ = [0.2, 0.3, 0.3, 0.2]

**Exemplo:**
```
palavra: "kata"
q₁ = 1.0   (comprimento perfeito)
q₂ = 1.0   (todos os fonemas válidos)
q₃ = 1.0   (razão 0.5, próximo de 0.4)
q₄ = 1.0   (alternância perfeita)
Q = 1.0    (qualidade máxima)
```

## 📊 Análise e Estatísticas

### Entropia Fonêmica

```
H(L) = -Σ P(f) · log₂P(f)
```

- **H > 3.5**: Alta diversidade (bom)
- **H < 2.0**: Baixa diversidade (problema)

### Uniformidade

```
Uniformidade = H / log₂|Fonemas|
```

- **>0.7**: Distribuição equilibrada
- **<0.5**: Alguns fonemas dominam

### Exemplo de Análise

```
--- DISTRIBUIÇÃO ---
Entropia: 3.82
Uniformidade: 0.75

Fonemas mais comuns:
  a: 145
  i: 132
  t: 98
  k: 87
  n: 76
```

## 🔧 Customização Avançada

### Criar Perfil Customizado

```python
from original_language_engine import OriginalLanguageProfile

profile = OriginalLanguageProfile('idioma_custom')
profile.name = "Idioma Customizado"
profile.seed = 99999

# Customizar faixas
profile.vowel_count_range = (7, 10)
profile.consonant_count_range = (18, 25)
profile.syllable_complexity = 'complex'

# Customizar processos fonológicos
profile.phonological_processes = {
    'assimilation': 0.3,  # Aumentado
    'deletion': 0.05,     # Reduzido
    'epenthesis': 0.15    # Aumentado
}

# Customizar características
profile.allow_diphthongs = True
profile.derivational_morphology = True
profile.compound_words = True
profile.number_system_base = 12  # Base duodecimal

# Salvar
manager = OriginalLanguageProfileManager()
manager.save_profile(profile)
```

### Gerar Números Customizados

```python
engine = OriginalLanguageEngine(profile)

for i in range(20):
    numero = engine.generate_number_word(i)
    print(f"{i}: {numero}")
```

### Palavras Compostas

```python
composto = engine.generate_compound_word('fire', 'mountain')
print(f"fire + mountain = {composto}")
```

## 🧪 Testes

Execute a suite de testes:

```bash
python test_original_generator.py
```

Testes incluídos:
1. Seleção de Fonemas
2. Restrições Fonotáticas
3. Geração de Sílabas
4. Geração de Palavras
5. Ortografia
6. Métricas de Qualidade
7. Sistema de Aprendizado
8. Motor Completo
9. Gerenciador de Perfis
10. Mapeador de Conceitos

## 📁 Estrutura de Arquivos

```
original_profiles/          # Perfis de idiomas
  ├── idioma1.json
  └── idioma2.json

original_learning/          # Dados de aprendizado
  ├── idioma1_patterns.json
  ├── idioma1_stats.json
  └── idioma1_frequency.json
```

### Formato de Perfil (JSON)

```json
{
  "profile_id": "meu_idioma",
  "name": "Meu Idioma Original",
  "seed": 12345,
  "complexity": "medium",
  "phoneme_inventory": {
    "vowels": ["i", "e", "a", "o", "u"],
    "consonants": ["p", "t", "k", "s", "m", "n", "l", "r"],
    "diphthongs": ["ai", "au", "ei"]
  },
  "phonotactic_constraints": {
    "syllable_templates": ["V", "CV", "CVC"],
    "max_onset_consonants": 2,
    "max_coda_consonants": 1,
    "max_nucleus_vowels": 2
  },
  "orthography_mapping": {
    "i": "i",
    "a": "a",
    "k": "k"
  }
}
```

## 🎯 Casos de Uso

### 1. Worldbuilding para Ficção

```python
# Criar idioma élfico
profile_elfico = manager.create_profile(
    'elfico',
    name='Élfico',
    seed=1111,
    complexity='complex'
)

engine = OriginalLanguageEngine(profile_elfico)
vocab_elfico = engine.generate_core_vocabulary()
```

### 2. Geração de Nomes

```python
nomes_personagens = [
    engine.translate_word('warrior'),
    engine.translate_word('mage'),
    engine.translate_word('hero')
]
```

### 3. Idiomas Relacionados (Família Linguística)

```python
# Proto-idioma
proto = manager.create_profile('proto_lang', seed=5000)

# Descendente 1 (seed próxima)
desc1 = manager.duplicate_profile('proto_lang', 'desc1_lang', new_seed=5100)

# Descendente 2 (seed próxima)
desc2 = manager.duplicate_profile('proto_lang', 'desc2_lang', new_seed=5200)
```

### 4. Tradução de Corpus Grande

```python
batch = BatchTranslator(engine)

arquivos = ['cap1.txt', 'cap2.txt', 'cap3.txt']
for arquivo in arquivos:
    batch.translate_file(arquivo, f"traducao_{arquivo}")
```

## ⚠️ Limitações Atuais

1. **Sintaxe**: Não gera estruturas gramaticais (apenas léxico)
2. **Semântica**: Mapeamento 1:1 conceito→palavra (sem polissemia)
3. **Morfologia Limitada**: Derivação básica (prefixos/sufixos simples)
4. **Prosódia**: Sem sistema tonal ou acento

## 🚧 Desenvolvimentos Futuros

- [ ] Módulo sintático (ordem de palavras, casos gramaticais)
- [ ] Sistema tonal (para idiomas tonais)
- [ ] Morfologia produtiva (regras complexas)
- [ ] Evolução diacrônica simulada
- [ ] Dialetos automáticos
- [ ] Análise de corpus para calibração

## 📚 Referências Teóricas

- **Fonologia**: Prince & Smolensky (1993) - Teoria da Otimalidade
- **Universais**: Greenberg (1963) - Universais Linguísticos
- **Tipologia**: Maddieson (1984) - Patterns of Sounds
- **Silabificação**: Clements (1990) - Hierarquia de Sonoridade

## 📄 Licença

Este sistema foi desenvolvido como parte do Hadabian Language Zipper para o projeto de worldbuilding Hadab.

## 🤝 Contribuições

Para contribuir ou reportar bugs, favor documentar com:
1. Seed usada
2. Input fornecido
3. Output esperado vs. obtido
4. Logs de erro (se aplicável)

---

**Desenvolvido com fundamentos de linguística computacional e teoria fonológica universal.**
