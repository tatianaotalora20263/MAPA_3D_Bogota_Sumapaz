"""Descarga Copernicus GLO-30 recortado a un limite GeoJSON mediante Earth Engine."""
import argparse
import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import ee


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("limite", type=Path)
    parser.add_argument("--salida", type=Path, required=True)
    parser.add_argument("--escala", type=int, default=30)
    parser.add_argument("--proyecto", default=os.environ.get("EE_PROJECT"))
    args = parser.parse_args()
    limite = json.loads(args.limite.read_text(encoding="utf-8"))
    try:
        ee.Initialize(project=args.proyecto)
    except Exception as error:
        raise RuntimeError("Earth Engine no esta autenticado o no tiene proyecto configurado. Defina EE_PROJECT o use earthengine set_project.") from error
    geometria = ee.Geometry(limite["features"][0]["geometry"])
    coleccion = "COPERNICUS/DEM/GLO30_2024_1"
    imagen = ee.ImageCollection(coleccion).select("DEM").mosaic().clip(geometria)
    url = imagen.getDownloadURL({"region": geometria, "scale": args.escala, "crs": "EPSG:4326", "format": "GEO_TIFF"})
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=600) as respuesta, args.salida.open("wb") as archivo:
        archivo.write(respuesta.read())
    metadata = {
        "fuente": "Google Earth Engine",
        "coleccion": coleccion,
        "banda": "DEM",
        "escala_solicitada_m": args.escala,
        "proyecto_configurado": bool(args.proyecto),
        "descargado_utc": datetime.now(timezone.utc).isoformat(),
        "url_descarga_efimera": "No se registra para evitar almacenar URL firmada temporal."
    }
    args.salida.with_suffix(".fuente.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
