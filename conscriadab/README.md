# Conscriadab

Gerador procedural de glifos para criação de sistemas de escrita e alfabetos para conlangs.

## Arquitetura

```
conscriadab.py          Interface Tkinter principal
glyph_generator.py      Lógica de geração procedural
glyph_exporter.py       Exportação de arquivos PNG
demo.py                 Script de demonstração
```

## Funcionalidades Implementadas

### Geração Procedural
- Glifos gerados a partir de primitivas geométricas
- Algoritmo baseado em seed (mesma seed = mesmos glifos)
- 4 estilos disponíveis: geometric, curvilinear, angular, mixed
- Controle de complexidade (2-10 primitivas por glifo)
- Sistema de simetria automático (vertical, horizontal, ambos ou nenhum)

### Interface (Tkinter)
- Configuração de seed para consistência
- Seleção de estilo visual
- Campo para caracteres customizados
- Controle deslizante de complexidade
- Preview em tempo real dos glifos
- Galeria com miniaturas
- Exportação individual ou em lote

### Exportação
- PNG transparente 512x512px
- Nomenclatura: glyph_{caractere}_seed{seed}.png
- Pronto para edição com IA generativa

## Como Usar

### Com Interface Gráfica

```bash
python conscriadab.py
```

1. Digite uma seed (ex: 12345)
2. Escolha o estilo
3. Digite os caracteres desejados (ex: ABCDEFGHIJKLMNOPQRSTUVWXYZ)
4. Ajuste a complexidade
5. Clique em "Gerar Alfabeto"
6. Navegue pela galeria e clique nos glifos para preview
7. Exporte individualmente ou todos de uma vez

### Sem Interface (Demo)

```bash
python demo.py
```

## Exemplo de Uso Programático

```python
from glyph_generator import GlyphGenerator
from glyph_exporter import GlyphExporter

seed = "minha_seed_123"
style = "geometric"
chars = "ABCDEFGHIJ"

generator = GlyphGenerator(seed=seed, style=style)
glyphs = generator.generate_alphabet(chars)

exporter = GlyphExporter()
exporter.export_alphabet(glyphs, seed)
```

## Estilos Disponíveis

- **geometric**: Linhas retas, círculos, triângulos (inspirado em runas)
- **curvilinear**: Curvas Bezier fluidas (inspirado em scripts árabes)
- **angular**: Polígonos conectados (inspirado em cuneiforme)
- **mixed**: Combinação aleatória dos três estilos

## Características Técnicas

### Consistência por Seed
A mesma seed sempre gera os mesmos glifos, garantindo:
- Reprodutibilidade
- Consistência visual entre sessões
- Possibilidade de compartilhar seeds

### Separação de Responsabilidades
- GlyphGenerator: Lógica pura de geração
- GlyphExporter: Manipulação de arquivos
- ConscriadabApp: Interface e coordenação

### Escalabilidade
Arquitetura modular permite:
- Adicionar novos estilos facilmente
- Implementar novos tipos de primitivas
- Expandir opções de exportação (SVG, fontes TTF)
- Integrar processamento com IA

## Próximos Passos Possíveis

- Exportação SVG vetorial
- Geração de fontes TTF/OTF
- Mais estilos e primitivas
- Variações automáticas (bold, italic)
- Sistema de templates
- Integração com APIs de IA generativa
- Edição básica inline

## Dependências

- Python 3.x
- Pillow (PIL)
- tkinter (incluso na maioria das instalações Python)

## Instalação

```bash
pip install Pillow
```

No Ubuntu/Debian:
```bash
sudo apt-get install python3-tk
```

## Estrutura de Arquivos Gerados

```
output/
  glyph_A_seed12345.png
  glyph_B_seed12345.png
  glyph_C_seed12345.png
  ...
```

Cada arquivo é:
- PNG transparente
- 512x512 pixels
- Preto sobre fundo transparente
- Pronto para uso ou edição
