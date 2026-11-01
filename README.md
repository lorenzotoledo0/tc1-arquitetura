# TC1 - Arquitetura e Urbanismo

Resumos das aulas de orientação de TC1, organizados por data.

- `CLAUDE.md`: contexto do projeto, método e fluxo de trabalho (lido automaticamente pelo Claude Code).
- `aulas/`: um arquivo por aula, com cinco seções fixas (visão geral, principais orientações, prazos e entregas, dúvidas da turma, observações).
- `pranchas/`: código das três pranchas A1 (canvas de design do Claude) e os mapas e diagramas em SVG que elas usam, em `pranchas/mapas/`.
- `scripts/`: scripts Python que geram os mapas e diagramas.
- `dados/`: dados abertos baixados para os mapas (OpenStreetMap, Overture Maps, SRTM, IBGE).

## Pranchas

Os arquivos `.dc.html` são a fonte das pranchas e só renderizam dentro do canvas do Claude; para ver ou imprimir, use Share › Export no canvas (PDF ou imagem). Os SVGs em `pranchas/mapas/` abrem em qualquer navegador e podem ir direto para o CAD ou o Illustrator.

| Prancha | Mapas e diagramas |
|---|---|
| 01 · Tema e local | Brasil/Goiás, Luziânia, uso do solo, insolação, cheios e vazios, hierarquia viária, equipamentos, hipsometria, diagnóstico, diretrizes |
| 02 · Estudos de caso e partido | 6 diagramas do partido (`partido-*.svg`) e volumetria do conjunto |
| 03 · Projeto | ainda sem desenhos |

## Como regerar os mapas

Centro: ponto do terreno (-16.2202211, -47.933783), raio de 1.000 m.

```
python scripts/gerar_mapas.py dados saida        # hierarquia viária, cheios e vazios (v1), equipamentos, hipsometria
python scripts/gerar_sintese.py dados saida      # uso do solo, cheios e vazios, diagnóstico, diretrizes (usa saida/equipamentos.json)
python scripts/gerar_localizacao.py dados saida  # Brasil/Goiás e Luziânia
python scripts/gerar_insolacao.py dados saida    # carta solar
python scripts/gerar_partido.py saida            # diagramas do partido e volumetria
```

Fontes: OpenStreetMap (ODbL), Microsoft e Google Open Buildings via Overture Maps, Overture Maps Places, SRTM 30 m (NASA, via OpenTopoData), malhas do IBGE. O uso do solo é estimado; gabarito não tem dado aberto e precisa de levantamento.

Repositório privado. Não subir senhas, tokens nem links com login.
