import json
import re
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

INPUT_FILE = Path("nes_games_urls.json")
DOWNLOAD_DIR = Path("nes_roms")
LOG_FILE = Path("download_log.json")
DELAY_BETWEEN_GAMES = 2.0  # segundos entre downloads para evitar bloqueios


def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]+', "_", name).strip()


def load_json(path: Path, default):
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path: Path, data):
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def download_roms():
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    games = load_json(INPUT_FILE, [])
    if not games:
        print(f"Arquivo {INPUT_FILE} não encontrado ou vazio. Rode o primeiro script antes.")
        return

    log = load_json(LOG_FILE, {"completed": {}, "failed": {}})

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            accept_downloads=True,
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        total = len(games)
        for idx, game in enumerate(games, start=1):
            url = game["url"]
            title = game.get("title") or game.get("slug") or f"game_{idx}"

            if url in log["completed"]:
                print(f"[{idx}/{total}] Já baixado, pulando: {title}")
                continue

            print(f"[{idx}/{total}] Processando: {title} ({url})")

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(1000)

                # Localiza botão/link de download na página do jogo
                download_locator = page.locator(
                    "a[href*='download'], button:has-text('Download'), a:has-text('Download')"
                ).first

                download_locator.wait_for(state="visible", timeout=15000)

                with page.expect_download(timeout=30000) as download_info:
                    download_locator.click()

                download = download_info.value
                suggested = sanitize_filename(download.suggested_filename or f"{game['slug']}.zip")
                target_path = DOWNLOAD_DIR / suggested

                # Evita sobrescrever se já existir arquivo com mesmo nome
                if target_path.exists():
                    stem = target_path.stem
                    suffix = target_path.suffix
                    target_path = DOWNLOAD_DIR / f"{stem}_{game['slug']}{suffix}"

                download.save_as(str(target_path))
                print(f"  -> Salvo em: {target_path}")

                log["completed"][url] = {
                    "title": title,
                    "file": str(target_path),
                }
                log["failed"].pop(url, None)
                save_json(LOG_FILE, log)

            except PlaywrightTimeoutError as exc:
                msg = f"Timeout ao baixar: {exc}"
                print(f"  [Erro] {msg}")
                log["failed"][url] = {"title": title, "error": msg}
                save_json(LOG_FILE, log)

            except Exception as exc:
                msg = str(exc)
                print(f"  [Erro] {msg}")
                log["failed"][url] = {"title": title, "error": msg}
                save_json(LOG_FILE, log)

            time.sleep(DELAY_BETWEEN_GAMES)

        browser.close()

    print(
        f"\nFinalizado! Sucessos: {len(log['completed'])} | Falhas: {len(log['failed'])}"
    )


if __name__ == "__main__":
    download_roms()
