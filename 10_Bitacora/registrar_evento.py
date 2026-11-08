"""Registra eventos JSONL sin depender de paquetes externos."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ejecucion", required=True)
    parser.add_argument("--agente", required=True)
    parser.add_argument("--herramienta", required=True)
    parser.add_argument("--estado", required=True,
                        choices=["pendiente", "en_progreso", "completado", "bloqueado", "fallido"])
    parser.add_argument("--mensaje", required=True)
    parser.add_argument("--artefacto", action="append", default=[])
    args = parser.parse_args()
    raiz = Path(__file__).resolve().parents[1]
    destino = raiz / "10_Bitacora" / "ejecuciones" / f"{args.ejecucion}.jsonl"
    destino.parent.mkdir(parents=True, exist_ok=True)
    evento = {
        "id_ejecucion": args.ejecucion,
        "marca_utc": datetime.now(timezone.utc).isoformat(),
        "agente": args.agente,
        "herramienta": args.herramienta,
        "estado": args.estado,
        "mensaje": args.mensaje,
        "artefactos": args.artefacto
    }
    with destino.open("a", encoding="utf-8") as archivo:
        archivo.write(json.dumps(evento, ensure_ascii=True) + "\n")


if __name__ == "__main__":
    main()
