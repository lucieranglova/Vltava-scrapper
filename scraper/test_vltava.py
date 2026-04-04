
import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OUTPUT = Path("data/vltava.json")
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL")


def send_discord(message: str, success: bool):
    if not DISCORD_WEBHOOK:
        print("Chybí DISCORD_WEBHOOK_URL — zpráva se neodešle")
        return

    color = 3066993 if success else 15158332  # zelená / červená

    payload = json.dumps({
        "embeds": [{
            "title": "✅ Vltava scraper OK" if success else "❌ Vltava scraper CHYBA",
            "description": message,
            "color": color,
        }]
    }).encode("utf-8")

    req = urllib.request.Request(
        DISCORD_WEBHOOK,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
    urllib.request.urlopen(req, timeout=10)
    print("Discord zpráva odeslána.")
except urllib.error.HTTPError as e:
    print(f"Discord chyba {e.code}: {e.read().decode('utf-8')}")
    raise


def main():
    errors = []
    info = []

    # 1. Existuje soubor?
    if not OUTPUT.exists():
        send_discord("Soubor `data/vltava.json` neexistuje.", success=False)
        raise SystemExit(1)

    # 2. Je validní JSON?
    try:
        data = json.loads(OUTPUT.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        send_discord(f"JSON soubor je poškozený: {e}", success=False)
        raise SystemExit(1)

    # 3. Obsahuje aktuální data?
    aktualni = data.get("aktualni", {})
    datetime_str = aktualni.get("datetime", "")
    teplota = aktualni.get("teplota_c")

    # Ověř datum – formát "04.04.2026 15:20"
    try:
        dt = datetime.strptime(datetime_str, "%d.%m.%Y %H:%M")
        dnes = datetime.now(timezone.utc).date()
        if dt.date() != dnes:
            errors.append(f"Datum v JSON je {dt.date()} ale dnes je {dnes}")
        else:
            info.append(f"Datum: {dt.strftime('%d. %m. %Y %H:%M')} ✓")
    except ValueError:
        errors.append(f"Nepodařilo se přečíst datum: `{datetime_str}`")

    # 4. Ověř teplotu
    if teplota is None:
        errors.append("Teplota chybí v JSON souboru")
    else:
        teplota = float(teplota)
        if not (-5 <= teplota <= 35):
            errors.append(f"Teplota {teplota} °C je mimo očekávaný rozsah (-5 až 35 °C)")
        else:
            info.append(f"Teplota: **{teplota} °C** ✓")

    # 5. Sestav zprávu a odešli
    if errors:
        zprava = "\n".join(errors)
        send_discord(zprava, success=False)
        raise SystemExit(1)
    else:
        zprava = "\n".join(info)
        send_discord(zprava, success=True)
        print("Všechny testy prošly.")


if __name__ == "__main__":
    main()
