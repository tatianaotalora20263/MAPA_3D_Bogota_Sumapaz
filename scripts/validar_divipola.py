"""Valida municipio y departamento contra el recurso oficial DIVIPOLA de DANE."""
import argparse
import json
import urllib.parse
import urllib.request
import unicodedata
from datetime import datetime, timezone
from pathlib import Path


def normalizar(valor):
    base = unicodedata.normalize("NFD", valor.upper())
    return "".join(c for c in base if c.isalnum() and not unicodedata.combining(c))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("configuracion", type=Path)
    parser.add_argument("--salida", type=Path, required=True)
    args = parser.parse_args()
    municipio = json.loads(args.configuracion.read_text(encoding="utf-8"))
    codigo = municipio["codigo_dane"]
    consulta = urllib.parse.urlencode({
        "$select": "dpto,nom_mpio,cod_dpto,cod_mpio,tipo_municipio",
        "$where": f"cod_mpio='{codigo}'"
    })
    url = "https://www.datos.gov.co/resource/gdxc-w37w.json?" + consulta
    with urllib.request.urlopen(url, timeout=30) as respuesta:
        registros = json.load(respuesta)
    if len(registros) != 1:
        raise RuntimeError(f"DIVIPOLA devolvio {len(registros)} registros para {codigo}.")
    registro = registros[0]
    if normalizar(registro["nom_mpio"]) != normalizar(municipio["municipio"]):
        raise RuntimeError("El municipio configurado no coincide con DIVIPOLA.")
    if normalizar(registro["dpto"]) != normalizar(municipio["departamento"]):
        raise RuntimeError("El departamento configurado no coincide con DIVIPOLA.")
    salida = {
        "validado_utc": datetime.now(timezone.utc).isoformat(),
        "fuente": "DANE DIVIPOLA - Codigos municipios",
        "url_consulta": url,
        "licencia_catalogo": "CC BY-SA 4.0",
        "registro": registro
    }
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(salida, indent=2, ensure_ascii=True), encoding="utf-8")


if __name__ == "__main__":
    main()
