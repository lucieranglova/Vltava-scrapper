"""
Scraper teploty Vltavy z ČHMÚ – Praha Chuchle (seq=307225)
Výstup: data/vltava.json  (aktuální hodnota + posledních 24h)
"""

import json
import re
import urllib.request
from datetime import datetime
from pathlib import Path

URL = "https://hydro.chmi.cz/hppsoldv/hpps_prfdyn.php?seq=307225"
OUTPUT = Path("data/vltava.json")


def fetch_html(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; VltavaBot/1.0)"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8")


def parse_table(html: str) -> list[dict]:
    """
    Hledá tabulku s hlavičkou: Datum a čas | Stav [cm] | Průtok ... | Teplota [°C]
    Vrací seznam řádků jako dict.
    """
    # Najdi blok tabulky s měřenými hodnotami
    # Řádky vypadají: <td>03.04.2026 17:20</td><td>53</td><td>75.7</td><td>6.8</td>
    pattern = re.compile(
        r"(\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2})"   # datum čas
        r"\s*\|\s*(\d+)"                            # stav cm
        r"\s*\|\s*([\d.]+)"                         # průtok
        r"\s*\|\s*([\d.]+)"                         # teplota
    )

    # HTML tabulka – BeautifulSoup není k dispozici, parsujeme regexem
    # Struktura: | datum | stav | průtok | teplota |
    # (z markdownu víme že jsou odděleny " | ")
    rows = []
    for m in pattern.finditer(html):
        dt_str, stav, prutok, teplota = m.groups()
        rows.append({
            "datetime": dt_str.strip(),
            "stav_cm": int(stav),
            "prutok_m3s": float(prutok),
            "teplota_c": float(teplota),
        })

    # Fallback: zkus raw HTML <td> parsing bez bs4
    if not rows:
        rows = parse_html_td(html)

    return rows


def parse_html_td(html: str) -> list[dict]:
    """Záložní parser přímo z HTML <td> tagů."""
    # Odstraň HTML tagy
    clean = re.sub(r"<[^>]+>", "|", html)
    clean = re.sub(r"\|+", "|", clean)

    date_pat = re.compile(r"(\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2})")
    rows = []

    # Najdi všechny výskyty data a pak vezmi 3 hodnoty za ním
    parts = clean.split("|")
    for i, part in enumerate(parts):
        part = part.strip()
        if date_pat.match(part):
            try:
                stav = parts[i + 1].strip()
                prutok = parts[i + 2].strip()
                teplota = parts[i + 3].strip()
                if re.match(r"^\d+$", stav) and re.match(r"^[\d.]+$", prutok) and re.match(r"^[\d.]+$", teplota):
                    rows.append({
                        "datetime": part,
                        "stav_cm": int(stav),
                        "prutok_m3s": float(prutok),
                        "teplota_c": float(teplota),
                    })
            except (IndexError, ValueError):
                continue
    return rows


def main():
    print(f"[{datetime.now().isoformat()}] Stahuji data z ČHMÚ...")
    html = fetch_html(URL)
    rows = parse_table(html)

    if not rows:
        raise ValueError("Nepodařilo se parsovat žádná data z HTML!")

    # Nejnovější hodnota = první řádek (stránka je seřazena od nejnovějšího)
    latest = rows[0]

    output = {
        "zdroj": URL,
        "stanice": "Praha - Chuchle (Vltava)",
        "aktualizovano_utc": datetime.utcnow().isoformat() + "Z",
        "aktualni": latest,
        "posledních_24h": rows,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Uloženo {len(rows)} záznamů → {OUTPUT}")
    print(f"   Teplota: {latest['teplota_c']} °C  ({latest['datetime']})")


if __name__ == "__main__":
    main()
