# Gerador de Idiomas Originais - Índice de Arquivos

Sistema completo para geração de idiomas construídos totalmente originais, independente do Hadabian Language Zipper existente.

## 📂 Estrutura de Arquivos

### Módulos Core

#### `phoneme_inventory.py` (19.9 KB)
**Função**: Sistema de inventário fonêmico universal e geração de restrições fonotáticas.

**Classes Principais**:
- `UniversalPhonemeInventory`: Inventário de vogais, consoantes e ditongos baseado em universais linguísticos
- `PhonemeSelector`: Seleção determinística de fonemas com pesos baseados em frequência
- `PhonotacticConstraints`: Geração de regras de combinação silábica
- `OrthographyMapper`: Mapeamento de fonemas para ortografia (Latino/Cirílico/Custom)

**Funcionalidades**:
- 8 classes de vogais (close/mid/open × front/central/back)
- 16 classes de consoantes (plosivas, fricativas, nasais, aproximantes, africadas)
- Geração de inventários com 5-9 vogais e 12-22 consoantes
- Restrições fonotáticas parametrizáveis (simple/medium/complex)
- Mapeamento ortográfico automático

---

#### `word_generator.py` (15.6 KB)
**Função**: Geração de palavras, sílabas e morfologia.

**Classes Principais**:
- `SyllableGenerator`: Geração determinística de sílabas respeitando templates
- `WordGenerator`: Geração de palavras completas com processos fonológicos
- `SemanticWordGenerator`: Geração com derivação morfológica
- `CompoundWordGenerator`: Criação de palavras compostas
- `NumberWordGenerator`: Sistema numérico posicional

**Funcionalidades**:
- Geração silábica determinística via SHA-256
- Templates silábicos: V, CV, CVC, CCV, CCVC, etc.
- Processos fonológicos: assimilação (20%), apagamento (15%), epêntese (10%)
- Derivação morfológica: prefixos e sufixos para plural, passado, comparativo, etc.
- Composição com sandhi (juntura)
- Sistema numérico (base 10 padrão, customizável)

---

#### `original_learning_system.py` (17.3 KB)
**Função**: Sistema de aprendizado, cache e análise de qualidade.

**Classes Principais**:
- `OriginalLanguageLearningSystem`: Cache persistente de conceito→palavra
- `PhonemeDistributionAnalyzer`: Análise de distribuição fonêmica
- `QualityMetrics`: Cálculo de qualidade de palavras e traduções
- `ConceptMapper`: Mapeamento de conceitos semânticos

**Funcionalidades**:
- Cache JSON com frequências e qualidade
- Análise de entropia e uniformidade fonêmica
- Métricas multidimensionais de qualidade:
  - Comprimento (peso 0.2)
  - Validade fonêmica (peso 0.3)
  - Estrutura V/C (peso 0.3)
  - Eufonia (peso 0.2)
- Biblioteca de primitivos semânticos (12 categorias)
- Detecção de lacunas no inventário
- Exportação em JSON/CSV/TXT

---

#### `original_language_engine.py` (17.2 KB)
**Função**: Motor principal de orquestração.

**Classes Principais**:
- `OriginalLanguageProfile`: Configuração de idioma
- `OriginalLanguageEngine`: Motor de tradução e geração
- `OriginalLanguageProfileManager`: CRUD de perfis
- `BatchTranslator`: Processamento em lote

**Funcionalidades**:
- Inicialização automática de fonologia
- Tradução determinística de texto
- Tokenização com preservação de pontuação e capitalização
- Geração de vocabulário básico (200+ conceitos)
- Análise estatística completa
- Exportação de perfis e dicionários
- Processamento batch de múltiplos arquivos

---

### Interfaces

#### `original_cli.py` (17.6 KB)
**Função**: Interface de linha de comando completa.

**Comandos**:
```
create      - Criar novo perfil de idioma
list        - Listar perfis existentes
show        - Mostrar detalhes de um perfil
translate   - Traduzir texto ou arquivo
vocabulary  - Gerar vocabulário básico
analyze     - Análise linguística detalhada
export      - Exportar dicionário
batch       - Tradução em lote
delete      - Deletar perfil
duplicate   - Duplicar perfil com nova seed
```

**Exemplos de Uso**:
```bash
python original_cli.py create meu_idioma --seed 12345 --initialize
python original_cli.py translate meu_idioma --text "Hello world"
python original_cli.py vocabulary meu_idioma --output vocab.json
python original_cli.py analyze meu_idioma --export-stats stats.json
```

---

#### `original_gui.py` (25.8 KB)
**Função**: Interface gráfica completa com Tkinter.

**Abas**:
1. **Tradutor**: Interface de tradução interativa
   - Seleção de perfil com visualização de informações
   - Área de entrada/saída de texto
   - Carregamento e salvamento de arquivos
   - Tradução em tempo real

2. **Gerenciar Perfis**: CRUD visual de perfis
   - Lista de perfis com detalhes
   - Criação com wizard
   - Duplicação com opção de nova seed
   - Visualização JSON completa

3. **Vocabulário**: Geração e exportação
   - Geração de vocabulário básico
   - Opção de incluir números
   - Exportação JSON/CSV
   - Visualização de lista completa

4. **Análise**: Estatísticas e métricas
   - Informações de perfil
   - Distribuição fonêmica
   - Métricas de qualidade
   - Recomendações automáticas
   - Exportação de estatísticas

**Características**:
- Interface responsiva e intuitiva
- Tooltips e mensagens de ajuda
- Validação de entrada
- Feedback visual de operações
- Suporte a português

---

### Testes e Demonstrações

#### `test_original_generator.py` (15.6 KB)
**Função**: Suite completa de testes automatizados.

**10 Testes Implementados**:
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

**Verificações**:
- Determinismo (mesmo input → mesmo output)
- Validação de inventários
- Qualidade de palavras geradas
- Persistência de dados
- Integridade de cache
- Métricas estatísticas

---

#### `demo_original_language.py` (13.4 KB)
**Função**: Demonstração interativa completa.

**Demonstrações**:
1. Criação de idioma do zero
2. Geração de vocabulário básico
3. Análise linguística
4. Análise de qualidade de palavras
5. Palavras compostas
6. Variação dialetal (3 dialetos)
7. Sistema numérico
8. Tradução de texto longo

**Características**:
- Execução passo a passo com pausas
- Visualização de estatísticas
- Exemplos práticos
- Opção de limpeza ao final

---

#### `setup_original_generator.py` (9.1 KB)
**Função**: Script de instalação e configuração inicial.

**Etapas do Setup**:
1. Criar estrutura de diretórios:
   - `original_profiles/`
   - `original_learning/`
   - `output/`
   - `examples/input/`
   - `examples/output/`

2. Criar arquivos de exemplo:
   - `example.txt` (texto de exemplo)
   - `wordlist.txt` (lista de palavras)

3. Criar perfis de exemplo:
   - `exemplo_simples` (seed: 1000)
   - `exemplo_medio` (seed: 2000)
   - `exemplo_complexo` (seed: 3000)

4. Verificar instalação
5. Executar teste rápido

---

### Documentação

#### `ORIGINAL_README.md` (13.9 KB)
**Função**: Documentação completa do sistema.

**Seções**:
- Visão Geral
- Arquitetura
- Instalação
- Uso (CLI, GUI, Programático)
- Fundamentos Teóricos
  - Inventário Fonêmico
  - Fonotática
  - Geração Determinística
  - Processos Fonológicos
  - Métricas de Qualidade
- Análise e Estatísticas
- Customização Avançada
- Testes
- Estrutura de Arquivos
- Casos de Uso
- Limitações e Desenvolvimentos Futuros
- Referências Teóricas

---

## 📊 Estatísticas do Código

```
Arquivo                          Linhas    KB     Funções/Classes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
phoneme_inventory.py             ~650     19.9    4 classes principais
word_generator.py                ~550     15.6    5 classes principais
original_learning_system.py      ~600     17.3    4 classes principais
original_language_engine.py      ~600     17.2    4 classes principais
original_cli.py                  ~580     17.6    10 comandos
original_gui.py                  ~850     25.8    1 classe, 4 abas
test_original_generator.py       ~550     15.6    10 testes
demo_original_language.py        ~450     13.4    8 demonstrações
setup_original_generator.py      ~300      9.1    6 etapas
ORIGINAL_README.md               ~450     13.9    Documentação completa
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL                           ~5580    ~165    Sistema completo
```

## 🎯 Principais Características

### 1. Independência Total
- **Sem dependência** do Hadabian Language Zipper original
- Sistema autônomo e completo
- Pode coexistir com o sistema original

### 2. Base Científica
- Inventários baseados em **universais linguísticos** (WALS)
- Restrições fonotáticas **plausíveis**
- Processos fonológicos **naturais**
- Métricas de qualidade **quantitativas**

### 3. Determinismo Absoluto
- Geração via **SHA-256**
- Reprodutibilidade **100%**
- Seeds customizáveis
- Versionamento garantido

### 4. Escalabilidade
- Centenas de idiomas simultâneos
- Cache persistente eficiente
- Aprendizado incremental
- Análise estatística em tempo real

### 5. Usabilidade
- **CLI** completa com 10 comandos
- **GUI** intuitiva com 4 abas
- **API programática** documentada
- Exemplos e demos interativos

## 🔬 Fundamentos Matemáticos

### Geração Determinística
```
h = SHA256(conceito || seed_global)
fonema = inventário[h mod |inventário|]
```

### Qualidade de Palavra
```
Q(w) = Σᵢ λᵢ · qᵢ(w)
onde λ = [0.2, 0.3, 0.3, 0.2]
```

### Entropia Fonêmica
```
H(L) = -Σ P(f) · log₂P(f)
Uniformidade = H / log₂|Fonemas|
```

### Validação Silábica
```
Válida ⟺ (|Onset| ≤ max) ∧ (|Núcleo| ≥ 1) ∧ 
         (|Coda| ≤ max) ∧ (¬Proibida)
```

## 🚀 Início Rápido

### 1. Setup Inicial
```bash
python setup_original_generator.py
```

### 2. Demonstração
```bash
python demo_original_language.py
```

### 3. Interface Gráfica
```bash
python original_gui.py
```

### 4. Criar Idioma
```bash
python original_cli.py create meu_idioma --seed 12345 --initialize
python original_cli.py translate meu_idioma --text "Hello world"
```

## 📦 Dependências

- **Python**: 3.8+
- **Tkinter**: Para GUI (geralmente incluído)
- **Bibliotecas padrão**: json, hashlib, pathlib, collections, datetime, statistics

**Sem dependências externas!**

## 🎓 Conceitos Linguísticos Implementados

- **Fonologia**: Teoria da Otimalidade, Hierarquia de Sonoridade
- **Morfologia**: Derivação, Composição, Flexão
- **Tipologia**: Padrões silábicos universais
- **Fonética**: Articulação (lugar, modo, voz)
- **Ortografia**: Sistemas de escrita múltiplos

## 📈 Métricas e Análise

- Entropia fonêmica (Shannon)
- Uniformidade de distribuição
- Type-Token Ratio (TTR)
- Qualidade multidimensional
- Plausibilidade fonológica

## 🔧 Configuração

Todas as configurações via perfis JSON:
- Inventário fonêmico
- Restrições fonotáticas
- Processos fonológicos
- Morfologia derivacional
- Sistema numérico
- Ortografia

## 📝 Licença e Uso

Desenvolvido como extensão do Hadabian Language Zipper para o projeto Hadab.
Livre para uso em worldbuilding e projetos criativos.

---

**Sistema completo e independente para geração de idiomas construídos originais.**
**Total: ~5580 linhas de código | ~165 KB | 10 arquivos**
