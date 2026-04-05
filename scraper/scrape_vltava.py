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

# Korekce teploty pro Braník (rozdíl oproti stanici Chuchle)
KOREKCE = {
    1: +0.5, 2: +0.5, 3: +0.5,
    4: 0,    5: 0,
    6: -0.5,
    7: -1.0, 8: -1.0,
    9: -0.5, 10: -0.5,
    11: 0,
    12: +0.5,
}

def korekce_teploty(teplota_c: float, datum_str: str) -> float:
    """Vrátí opravenou teplotu podle měsíce."""
    mesic = int(datum_str.split(".")[1])
    return round(teplota_c + KOREKCE.get(mesic, 0), 1)

def fetch_html(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; VltavaBot/1.0)"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8")

def parse_table(html: str) -> list[dict]:
    """
    Parsuje raw HTML – hledá <td> tagy a seskupuje je po 4:
    datum+čas | stav cm | průtok m3s | teplota °C
    """
    date_pat = re.compile(r'^\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}$')
    td_values = re.findall(r'<td[^>]*>\s*([^<]+?)\s*</td>', html)
    rows = []
    i = 0
    while i < len(td_values):
        val = td_values[i].strip()
        if date_pat.match(val):
            try:
                stav   = td_values[i + 1].strip()
                prutok = td_values[i + 2].strip()
                teplo  = td_values[i + 3].strip()
                if (re.match(r'^\d+$', stav)
                        and re.match(r'^[\d.]+$', prutok)
                        and re.match(r'^[\d.]+$', teplo)):
                    teplota_raw = float(teplo)
                    teplota_opravena = korekce_teploty(teplota_raw, val)
                    rows.append({
                        "datetime":      val,
                        "stav_cm":       int(stav),
                        "prutok_m3s":    float(prutok),
                        "teplota_c":     teplota_opravena,
                        "teplota_raw_c": teplota_raw,
                    })
                    i += 4
                    continue
            except IndexError:
                pass
        i += 1
    return rows

def main():
    print(f"[{datetime.now().isoformat()}] Stahuji data z ČHMÚ...")
    html = fetch_html(URL)
    rows = parse_table(html)
    if not rows:
        raise ValueError("Nepodařilo se parsovat žádná data z HTML!")

    latest = rows[0]
    output = {
        "zdroj": URL,
        "stanice": "Praha - Chuchle (Vltava)",
        "aktualizovano_utc": datetime.utcnow().isoformat() + "Z",
        "aktualni": latest,
        "poslednich_24h": rows,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Uloženo {len(rows)} záznamů → {OUTPUT}")
    print(f"   Teplota (raw):     {latest['teplota_raw_c']} °C")
    print(f"   Teplota (Braník):  {latest['teplota_c']} °C  ({latest['datetime']})")

if __name__ == "__main__":
    main()
