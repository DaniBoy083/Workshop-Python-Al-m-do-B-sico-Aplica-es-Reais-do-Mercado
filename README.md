# Pokedex Incompleta - Solucao com Clean Architecture + Kivy

Projeto que resolve o desafio da Pokedex incompleta, enriquecendo os dados do arquivo `pokemon_base.csv` com a PokeAPI e gerando:

- `pokemon_completo.csv`
- `respostas.txt`

A interface principal usa **Kivy** e permite executar tudo por botao com progresso em tempo real.

## Arquitetura

A estrutura segue separacao por responsabilidades:

- `src/domain`: entidades e regras de negocio (analises)
- `src/application`: caso de uso principal (orquestracao)
- `src/infrastructure`: API HTTP, cache e persistencia CSV/TXT
- `src/presentation`: app Kivy

## Requisitos

- Python 3.13+
- Dependencias de runtime em `requirements.txt`
- Dependencias de desenvolvimento em `requirements-dev.txt`

Instalacao:

```bash
pip install -r requirements.txt
```

Para desenvolvimento e testes:

```bash
pip install -r requirements-dev.txt
```

## Como executar

### 1) Interface grafica (Kivy)

```bash
python main.py
```

### 2) Linha de comando

```bash
python generate_pokedex.py
```

Com opcoes:

```bash
python generate_pokedex.py --base-csv pokemon_base.csv --complete-csv pokemon_completo.csv --answers respostas.txt
```

## Pontos de qualidade e seguranca aplicados

- Normalizacao e sanitizacao dos nomes antes de chamar a API
- Timeout e retry em chamadas HTTP
- Tratamento de erro para Pokemon nao encontrado sem quebrar a execucao
- Cache local JSON para evitar chamadas repetidas
- Logs e feedback de progresso
- Teste unitario para regras analiticas (`tests/test_analytics.py`)

## Testes

```bash
pytest
```

Os testes cobrem:

- Regras analiticas de dominio
- Integracao do caso de uso com mock de gateway (incluindo Pokemon nao encontrado)
- Integracao do cliente HTTP com retry, cache e tratamento de falha de rede/404

## Gerar executavel Windows

Script automatizado:

```powershell
./scripts/build_windows_exe.ps1
```

Saida esperada:

- Pasta: `dist/PokedexDataStudio/`
- Executavel: `dist/PokedexDataStudio/PokedexDataStudio.exe`

## Versionamento e changelog

Fluxo recomendado para novas versoes:

1. Commitar as alteracoes da versao
2. Subir para a branch principal
3. Criar release com notas automaticas baseadas nos commits

Exemplo de comando:

```bash
gh release create v1.0.1 --target main --generate-notes
```

## Release automatica com GitHub Actions

O projeto possui workflow em `.github/workflows/release-on-tag.yml`.

Quando uma tag no formato `v*` e enviada para o repositorio, o workflow:

1. Instala dependencias de desenvolvimento
2. Executa os testes
3. Gera o executavel Windows com PyInstaller
4. Compacta o build em ZIP
5. Cria (ou atualiza) a release com notas automaticas

Exemplo para disparar:

```bash
git tag v1.0.2
git push origin v1.0.2
```
