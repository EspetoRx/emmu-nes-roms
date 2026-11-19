import json
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

BASE_LIST_URL = "https://www.romsgames.net/roms/nintendo/?page={page}&sort=popularity"
START_PAGE = 1
END_PAGE = 72
OUTPUT_FILE = Path("nes_games_urls.json")


def collect_game_links():
    collected = {}
    if OUTPUT_FILE.exists():
        with OUTPUT_FILE.open("r", encoding="utf-8") as f:
            for item in json.load(f):
                collected[item["url"]] = item

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()

        for page_num in range(START_PAGE, END_PAGE + 1):
            url = BASE_LIST_URL.format(page=page_num)
            print(f"[Página {page_num}/{END_PAGE}] Acessando {url}")

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(1200)
            except Exception as exc:
                print(f"  [Aviso] Falha na página {page_num}: {exc}")
                continue

            links = page.eval_on_selector_all(
                "a[href*='/roms/nintendo/']",
                """els => els.map(el => ({
                    href: el.getAttribute('href'),
                    text: (el.innerText || '').trim()
                }))"""
            )

            added_in_page = 0
            for entry in links:
                href = entry.get("href") or ""
                full_url = urljoin(url, href).split("#")[0]

                # Filtra apenas páginas individuais de ROMs dentro de /roms/nintendo/
                if (
                    "/roms/nintendo/" in full_url
                    and "?page=" not in full_url
                    and full_url.rstrip("/") != "https://www.romsgames.net/roms/nintendo"
                ):
                    if full_url not in collected:
                        slug = full_url.rstrip("/").split("/")[-1]
                        collected[full_url] = {
                            "title": entry.get("text") or slug,
                            "slug": slug,
                            "url": full_url,
                            "page": page_num,
                        }
                        added_in_page += 1

            print(f"  +{added_in_page} novos jogos (Total acumulado: {len(collected)})")

            with OUTPUT_FILE.open("w", encoding="utf-8") as f:
                json.dump(list(collected.values()), f, ensure_ascii=False, indent=2)

        browser.close()

    print(f"\nConcluído! {len(collected)} ROMs salvas em {OUTPUT_FILE}")


if __name__ == "__main__":
    collect_game_links()
