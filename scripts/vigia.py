import os
import time
import logging
from logging.handlers import RotatingFileHandler
import httpx
from dotenv import load_dotenv

load_dotenv()
URL = os.getenv("NEXOTERRA_HEALTH_URL", "")
INTERVALO = int(os.getenv("VIGIA_INTERVALO", "60"))
LIMITE_FALHAS = int(os.getenv("VIGIA_LIMITE_FALHAS", "3"))

handler = RotatingFileHandler("logs/vigia.log", maxBytes=1_000_000, backupCount=5)
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
log = logging.getLogger("vigia")
log.setLevel(logging.INFO)
log.addHandler(handler)


def mostrar(msg, nivel=logging.INFO):
    print(msg, flush=True)
    log.log(nivel, msg)


def main():
    if not URL:
        raise SystemExit("Defina NEXOTERRA_HEALTH_URL no arquivo .env")
    falhas = 0
    caiu = False
    mostrar(f"Vigia iniciado. Checando a cada {INTERVALO}s")
    try:
        while True:
            try:
                r = httpx.get(URL, timeout=10, follow_redirects=True)
                ms = int(r.elapsed.total_seconds() * 1000)
                if r.status_code == 200:
                    if caiu:
                        mostrar("RECUPERADA: a API voltou a responder")
                        caiu = False
                    falhas = 0
                    mostrar(f"OK 200 {ms}ms")
                else:
                    falhas += 1
                    mostrar(f"FALHA status {r.status_code} ({falhas})", logging.WARNING)
            except Exception as e:
                falhas += 1
                mostrar(f"FALHA {type(e).__name__} ({falhas})", logging.WARNING)
            if falhas >= LIMITE_FALHAS and not caiu:
                caiu = True
                mostrar("ALERTA: a API está fora do ar", logging.ERROR)
            time.sleep(INTERVALO)
    except KeyboardInterrupt:
        mostrar("Vigia encerrado")


if __name__ == "__main__":
    main()