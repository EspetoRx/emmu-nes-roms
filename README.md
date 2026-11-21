# emmu-nes-roms

Scripts de automação em Python + **Playwright** usados para coletar ROMs de **Nintendo Entertainment System / Famicom (NES)** no catálogo de `romsgames.net`, descompactá-las e consolidá-las em `roms/`.

> Este README documenta a **proveniência real** do conteúdo e o funcionamento exato dos scripts. Leia os avisos abaixo antes de tornar o repositório público, fazer fork ou redistribuir.

---

## Avisos legais e proveniência — leia antes de publicar

### De onde vieram as ROMs deste repositório

- **Fonte:** `https://www.romsgames.net/roms/nintendo/` — catálogo **público e online**, acessado pelos scripts `script.py` e `script2.py` deste repositório. No momento da coleta o site estava no ar e oferecia download direto dos arquivos.
- **Intervalo configurado na coleta (`script.py`):** páginas **51 a 72** (`?page={page}&sort=popularity`). Os links de cada jogo eram abertos, o botão de download era clicado automaticamente e os arquivos baixados iam para `page<N>/`, sendo depois extraídos/movidos para `roms/`.
- **Intervalo configurado no pós-processamento (`script2.py`):** página **69** apenas. Os dois arquivos estão dessincronizados no estado atual; alinhe `START_PAGE`/`END_PAGE` antes de executar o fluxo completo (veja "Solução de problemas").
- **Extensões presentes em `roms/`:** predominantemente `.nes` (2506 arquivos), além de alguns `.nfo` e arquivos de documentação. Há também a pasta `docs and refs to some roms/` com arquivos de texto/HTML de referência.

### O que isso significa — e o que não significa

- O site de origem é público e estava online: isso é um **fato de proveniência**, não uma autorização de redistribuição. **Disponível publicamente não é o mesmo que domínio público**, nem implica licença de uso.
- Os direitos autorais e as marcas dos jogos pertencem aos **titulares originais** (Nintendo, Konami, Capcom, Square Enix etc.), **não** ao site de download e não a este repositório.
- As ROMs em `roms/` **não são cobertas pela GNU GPL-3.0** deste projeto. A licença em `LICENSE` aplica-se **exclusivamente ao código dos scripts** (`script.py`, `script2.py`). Declarar o contrário seria atribuir a si autoria de obras de terceiros.

### Responsabilidade do usuário

- Antes de publicar, confirme que possui base legal para cada arquivo: backup de mídia que você possui (nos termos da lei do seu país), *homebrew*, conteúdo em domínio público ou autorização expressa do titular. Em caso de dúvida, **remova as ROMs e mantenha apenas os scripts**.
- Nenhum texto deste README renuncia, limita ou transfere direitos de terceiros, e nenhum disclaimer garante imunidade jurídica. A responsabilidade pelo conteúdo publicado é do mantenedor do repositório.
- Uso pretendido: estudo de emulação, testes e preservação pessoal, sempre dentro da legalidade local.

### Automação responsável

- Os scripts interagem com um serviço de terceiros. Respeite termos de uso, limites de taxa e proteções anti-bot; reduza `MAX_CONCURRENT_DOWNLOADS` e aumente os intervalos se ocorrerem bloqueios.
- Código fornecido *"as is"*, sem garantia de funcionamento contínuo: sites mudam seletores, layout e políticas de download.

---

## Estrutura do repositório

```text
emmu-nes-roms/
├── script.py                    # Coleta os links e baixa os arquivos via Playwright
├── script2.py                   # Valida/extrai ZIPs e move os demais arquivos para roms/
├── LICENSE                      # GNU GPL-3.0 — aplicável somente aos scripts
├── README.md                    # Esta documentação
├── docs and refs to some roms/  # Arquivos de texto/HTML de referência
└── roms/                        # ROMs coletadas e extraídas
```

Diretórios `page<N>/` são temporários: criados por `script.py` e removidos por `script2.py` ao final de cada página processada.

## Pré-requisitos

- Python 3.10+ (`python --version`)
- Playwright: `pip install playwright`
- Chromium para o Playwright: `playwright install chromium`
- Opcional em Linux: `playwright install-deps chromium`

## Como as ROMs foram obtidas

### 1. Coleta — `script.py`

Configuração atual do arquivo:

| Variável | Valor |
| --- | --- |
| `URL_TEMPLATE` | `https://www.romsgames.net/roms/nintendo/?page={page}&sort=popularity` |
| `START_PAGE` / `END_PAGE` | `51` / `72` |
| `CARD_LINK_SELECTOR` | `a[href*='/nintendo-rom-'], a[href*='/roms/nintendo/']` |
| `DOWNLOAD_BTN_SELECTOR` | links/botões com `download`, `Save Game` ou `Download` |
| `MAX_CONCURRENT_DOWNLOADS` | `8` |

Fluxo executado:

1. Abre cada página da lista em Chromium (`headless=False`) com `async_playwright`.
2. Coleta os `href` dos cards via `locator(...).evaluate_all`, normaliza com `urljoin` e remove duplicatas.
3. Abre cada URL de jogo em uma aba própria, limitada por `asyncio.Semaphore`.
4. Aguarda o botão de download, usa `expect_download()` e salva o arquivo em `page<N>/`.
5. Pausa de 1 segundo entre lotes para espaçar requisições.

### 2. Pós-processamento — `script2.py`

| Variável | Valor |
| --- | --- |
| `START_PAGE` / `END_PAGE` | `69` / `69` (**diferente de `script.py`**) |
| `ROMS_DIR` | `BASE_DIR / "roms"` |
| `DELETE_ZIP_AFTER_EXTRACT` | `False` |

Para cada `page<N>/` o script:

1. Testa a integridade de cada `.zip` com `zf.testzip()` e extrai o conteúdo para `roms/`.
2. Move os arquivos que não são `.zip` para `roms/`.
3. Remove a pasta `page<N>/` somente se não houve erros; caso contrário a mantém para inspeção.

## Execução

```bash
git clone <URL-DO-REPOSITORIO> emmu-nes-roms
cd emmu-nes-roms
python -m venv .venv
source .venv/bin/activate          # Windows: .\.venv\Scripts\Activate.ps1
pip install playwright
playwright install chromium
python script.py
python script2.py
```

## Solução de problemas

- **Intervalos diferentes:** `script.py` processa 51–72, mas `script2.py` processa apenas 69. Ajuste `START_PAGE`/`END_PAGE` em `script2.py` para o mesmo intervalo antes de processar, ou as pastas `page<N>/` restantes não serão limpas.
- **Muitos timeouts / bloqueios:** reduza `MAX_CONCURRENT_DOWNLOADS` de 8 para 3 ou 4 e aumente os `asyncio.sleep`.
- **Botão ou card não encontrado:** inspecione a página no navegador (F12) — seletores mudam quando o site atualiza o layout.
- **`page<N>/` não foi excluída:** houve falha em algum ZIP ou arquivo; verifique o log antes de apagar manualmente.
- **Publicação no GitHub:** se você não tiver base legal para as ROMs, adicione os formatos ao `.gitignore` e remova os arquivos do histórico do Git antes de publicar.

## Licença

- **Scripts:** GNU General Public License v3.0 — texto completo em `LICENSE`.
- **ROMs:** não licenciadas por este repositório. Consulte a seção de avisos.
- Contribuições e correções são bem-vindas via issues ou pull requests, restritas ao código dos scripts.
