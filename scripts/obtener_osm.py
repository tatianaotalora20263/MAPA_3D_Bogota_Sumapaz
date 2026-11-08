"""Descarga vias y lugares OSM dentro de la caja del limite, con atribucion."""
import argparse
import json
import time
import urllib.parse
import urllib.request
from urllib.error import HTTPError, URLError
from datetime import datetime, timezone
from pathlib import Path


def coordenadas(geometria):
    if geometria["type"] == "Polygon":
        for anillo in geometria["coordinates"]:
            yield from anillo
    elif geometria["type"] == "MultiPolygon":
        for poligono in geometria["coordinates"]:
            for anillo in poligono:
                yield from anillo


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("limite", type=Path)
    parser.add_argument("--salida", type=Path, required=True)
    args = parser.parse_args()
    limite = json.loads(args.limite.read_text(encoding="utf-8"))
    puntos = list(coordenadas(limite["features"][0]["geometry"]))
    oeste, este = min(p[0] for p in puntos), max(p[0] for p in puntos)
    sur, norte = min(p[1] for p in puntos), max(p[1] for p in puntos)
    consulta = f"[out:json][timeout:180];(way[highway]({sur},{oeste},{norte},{este});node[place]({sur},{oeste},{norte},{este}););out tags geom;"
    datos = urllib.parse.urlencode({"data": consulta}).encode("utf-8")
    endpoints = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.nchc.org.tw/api/interpreter"
    ]
    osm = None
    ultimo_error = None
    endpoint_usado = None
    for endpoint in endpoints:
        solicitud = urllib.request.Request(endpoint, data=datos, headers={"User-Agent": "MAPA_3D/1.0 contacto-local"})
        try:
            with urllib.request.urlopen(solicitud, timeout=240) as respuesta:
                osm = json.load(respuesta)
            endpoint_usado = endpoint
            break
        except (HTTPError, URLError, TimeoutError) as error:
            ultimo_error = error
            time.sleep(2)
    if osm is None:
        raise RuntimeError("No fue posible obtener OSM desde los endpoints configurados.") from ultimo_error
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(osm), encoding="utf-8")
    args.salida.with_suffix(".fuente.json").write_text(json.dumps({
        "fuente": "OpenStreetMap contributors", "licencia": "ODbL 1.0", "endpoint": endpoint_usado, "consulta": consulta,
        "descargado_utc": datetime.now(timezone.utc).isoformat()
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
