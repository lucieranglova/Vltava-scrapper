# 🌊 Vltava Temperature Scraper - Braník

Automatický scraper teploty Vltavy z webu ČHMÚ. Každý den v 5:00 a 12:00 stáhne aktuální data ze stanice **Praha – Chuchle**, dopočítá předpovídanou teplotu v Braníku a uloží je jako JSON do repozitáře, odkud je lze přímo číst na webu.

## Jak to funguje

```
ČHMÚ měřák (každých ~10 min)
        ↓
hydro.chmi.cz  ← živá HTML stránka
        ↓  GitHub Actions cron
data/vltava.json  ← uloženo v repozitáři
        ↓
váš web / plugin
```

Scraper pokaždé stahuje živou stránku ČHMÚ

---

## Struktura repozitáře

```
├── scraper/
│   └── scrape_vltava.py        # scraper skript
├── data/
│   └── vltava.json             # výstup (generuje se automaticky)
└── .github/
    └── workflows/
        └── vltava.yml          # GitHub Actions cron
```

---

## Výstupní JSON

Soubor `data/vltava.json` má tuto strukturu:

```json
{
  "zdroj": "https://hydro.chmi.cz/hppsoldv/hpps_prfdyn.php?seq=307225",
  "stanice": "Praha - Chuchle (Vltava)",
  "aktualizovano_utc": "2026-04-03T15:30:00Z",
  "aktualni": {
    "datetime": "03.04.2026 17:20",
    "stav_cm": 53,
    "prutok_m3s": 75.7,
    "teplota_c": 6.8
  },
  "posledních_24h": [
    {
      "datetime": "03.04.2026 17:20",
      "stav_cm": 53,
      "prutok_m3s": 75.7,
      "teplota_c": 6.8
    },
    ...
  ]
}
```

---

## Použití na webu

```javascript
const url = 'https://raw.githubusercontent.com/vasrepozitar/Vltava-scrapper/main/data/vltava.json';

fetch(url)
  .then(r => r.json())
  .then(data => {
    const { teplota_c, datetime } = data.aktualni;
    console.log(`Teplota Vltavy: ${teplota_c} °C (${datetime})`);
  });
```

---

## Nasazení

### 1. Vytvořte repozitář na GitHubu

Nahrajte soubory podle struktury výše.

### 2. Povolte GitHub Actions zápis do repozitáře

`Settings → Actions → General → Workflow permissions → Read and write permissions`

### 3. Hotovo

GitHub Actions se spustí automaticky podle cronu. První spuštění lze vyvolat ručně přes `Actions → Scrape teplota Vltavy → Run workflow`.

---

## Ruční spuštění lokálně

Skript nevyžaduje žádné externí závislosti — stačí Python 3.9+.

```bash
python scraper/scrape_vltava.py
# → data/vltava.json
```

---

## Změna intervalu aktualizace

V souboru `.github/workflows/vltava.yml` upravte cron výraz:

| Interval | Cron |
|---|---|
| každé 2 hodiny | `0 */2 * * *` |
| každou hodinu | `0 * * * *` |
| každých 30 minut | `*/30 * * * *` |
| 2× denně (6:00 a 18:00 CEST) | `0 4,16 * * *` |

> **Pozor:** GitHub Actions cron běží vždy v UTC. Pro české letní časy (CEST = UTC+2) odečtěte 2 hodiny.

---

## Zdroj dat

Data pochází ze stanice **Praha – Chuchle** provozované [ČHMÚ](https://www.chmi.cz). Stanice měří přibližně 2 km od Braníku. Data jsou aktualizována přibližně každých 10 minut a jsou poskytována bez právní záruky.

- Stanice: [Praha – Chuchle (seq=307225)](https://hydro.chmi.cz/hppsoldv/hpps_prfdyn.php?seq=307225)
- Licence dat: [Creative Commons BY-NC-ND 3.0 CZ](http://creativecommons.org/licenses/by-nc-nd/3.0/cz/)
