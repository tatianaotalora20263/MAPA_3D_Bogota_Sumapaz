"""Obtiene un limite municipal con procedencia verificable.

Una geometria oficial suministrada tiene prioridad. El respaldo OSM solo se usa
cuando se solicita expresamente y siempre queda etiquetado como no oficial.
"""
import argparse
import json
import shutil
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def guardar_procedencia(salida, datos):
    salida.with_name("procedencia_limite.json").write_text(
        json.dumps(datos, indent=2, ensure_ascii=True), encoding="utf-8"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("configuracion", type=Path)
    parser.add_argument("--salida", type=Path, required=True)
    parser.add_argument("--oficial", type=Path,
                        help="GeoJSON oficial DANE/IGAC previamente obtenido.")
    parser.add_argument("--permitir-osm", action="store_true")
    args = parser.parse_args()
    config = json.loads(args.configuracion.read_text(encoding="utf-8"))
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    if args.oficial:
        if not args.oficial.is_file():
            raise FileNotFoundError(args.oficial)
        geometria = json.loads(args.oficial.read_text(encoding="utf-8"))
        if geometria.get("type") not in {"Feature", "FeatureCollection"}:
            raise RuntimeError("El limite oficial debe ser GeoJSON Feature o FeatureCollection.")
        shutil.copyfile(args.oficial, args.salida)
        guardar_procedencia(args.salida, {
            "estado": "oficial_aportado",
            "archivo": str(args.oficial.resolve()),
            "municipio": config["municipio"],
            "codigo_dane": config["codigo_dane"],
            "validado_utc": datetime.now(timezone.utc).isoformat(),
            "requiere_revision_atributos_institucionales": True
        })
        return
    if not args.permitir_osm:
        raise RuntimeError("No hay limite oficial. Aporte --oficial o habilite el respaldo OSM para el piloto.")
    parametros = urllib.parse.urlencode({
        "format": "jsonv2", "country": "Colombia", "city": config["municipio"],
        "polygon_geojson": 1, "limit": 10
    })
    url = "https://nominatim.openstreetmap.org/search?" + parametros
    solicitud = urllib.request.Request(url, headers={"User-Agent": "MAPA_3D/1.0 contacto-local"})
    with urllib.request.urlopen(solicitud, timeout=60) as respuesta:
        candidatos = json.load(respuesta)
    candidato = next((item for item in candidatos
                       if item.get("geojson", {}).get("type") in {"Polygon", "MultiPolygon"}), None)
    if not candidato:
        raise RuntimeError("Nominatim no devolvio un poligono administrativo para el municipio.")
    feature = {
        "type": "Feature",
        "properties": {
            "nombre": config["municipio"], "codigo_dane": config["codigo_dane"],
            "origen": "OpenStreetMap/Nominatim", "oficial": False,
            "osm_id": candidato.get("osm_id"), "osm_type": candidato.get("osm_type")
        },
        "geometry": candidato["geojson"]
    }
    args.salida.write_text(json.dumps({"type": "FeatureCollection", "features": [feature]}, indent=2), encoding="utf-8")
    guardar_procedencia(args.salida, {
        "estado": "respaldo_no_oficial",
        "advertencia": "Usado solo porque no se proporciono una geometria oficial verificable.",
        "fuente": "OpenStreetMap Nominatim",
        "url_consulta": url,
        "atribucion": "OpenStreetMap contributors, ODbL 1.0",
        "consulta_utc": datetime.now(timezone.utc).isoformat(),
        "respuesta": {k: candidato.get(k) for k in ["display_name", "osm_type", "osm_id", "class", "type"]}
    })


if __name__ == "__main__":
    main()
