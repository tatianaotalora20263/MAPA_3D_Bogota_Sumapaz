"""Crea un compuesto RGB Sentinel-2 para usarlo como textura del terreno."""
import argparse
import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import ee


def enmascarar_nubes(imagen):
    scl = imagen.select("SCL")
    mascara = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10)).And(scl.neq(11))
    return imagen.updateMask(mascara)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("limite", type=Path)
    parser.add_argument("--salida", type=Path, required=True)
    parser.add_argument("--inicio", required=True)
    parser.add_argument("--fin", required=True)
    parser.add_argument("--nubes-maximas", type=float, default=50)
    parser.add_argument("--proyecto", default=os.environ.get("EE_PROJECT"))
    args = parser.parse_args()
    try:
        ee.Initialize(project=args.proyecto)
    except Exception as error:
        raise RuntimeError("Earth Engine no esta autenticado o no tiene proyecto configurado.") from error
    limite = json.loads(args.limite.read_text(encoding="utf-8"))
    geometria = ee.Geometry(limite["features"][0]["geometry"])
    coleccion = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(geometria)
                 .filterDate(args.inicio, args.fin)
                 .filter(ee.Filter.lte("CLOUDY_PIXEL_PERCENTAGE", args.nubes_maximas))
                 .map(enmascarar_nubes))
    cantidad = coleccion.size().getInfo()
    if cantidad == 0:
        raise RuntimeError("No hay escenas Sentinel-2 para el periodo configurado.")
    rgb = (coleccion.median().clip(geometria).select(["B4", "B3", "B2"])
           .multiply(0.0001).visualize(min=0, max=0.3, gamma=1.1))
    # El endpoint de miniaturas de Earth Engine no reconoce EPSG:9377.
    # QGIS reproyecta el producto descargado al CRS nacional en la etapa siguiente.
    url = rgb.getDownloadURL({"region": geometria, "scale": 60, "crs": "EPSG:4326", "format": "GEO_TIFF"})
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=600) as respuesta, args.salida.open("wb") as archivo:
        archivo.write(respuesta.read())
    args.salida.with_suffix(".fuente.json").write_text(json.dumps({
        "fuente": "Copernicus Sentinel-2 L2A mediante Google Earth Engine",
        "coleccion": "COPERNICUS/S2_SR_HARMONIZED", "escenas_compuestas": cantidad,
        "periodo": [args.inicio, args.fin], "nubes_maximas_por_escena": args.nubes_maximas,
        "atribucion": "Contains modified Copernicus Sentinel data 2024, processed by Google Earth Engine",
        "descargado_utc": datetime.now(timezone.utc).isoformat()
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
