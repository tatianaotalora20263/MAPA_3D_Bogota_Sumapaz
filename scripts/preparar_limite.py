"""Convierte el limite EPSG:4326 al sistema local Y-up del modelo."""
import argparse
import json
from pathlib import Path
from osgeo import osr


def recorrer(geometria, convertir):
    tipo, coords = geometria["type"], geometria["coordinates"]
    if tipo == "Polygon":
        return {"type": tipo, "coordinates": [[convertir(*p[:2]) for p in anillo] for anillo in coords]}
    if tipo == "MultiPolygon":
        return {"type": tipo, "coordinates": [[[convertir(*p[:2]) for p in anillo] for anillo in poligono] for poligono in coords]}
    raise RuntimeError(f"Geometria de limite no soportada: {tipo}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("limite", type=Path)
    parser.add_argument("metadata_terreno", type=Path)
    parser.add_argument("--salida", type=Path, required=True)
    args = parser.parse_args()
    limite = json.loads(args.limite.read_text(encoding="utf-8"))
    metadata = json.loads(args.metadata_terreno.read_text(encoding="utf-8"))
    origen, destino = osr.SpatialReference(), osr.SpatialReference()
    origen.ImportFromEPSG(4326); destino.ImportFromEPSG(9377)
    origen.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    destino.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    conversion = osr.CoordinateTransformation(origen, destino)
    centro, base = metadata["centro_proyectado"], metadata["elevacion_base_m"]
    def convertir(lon, lat):
        x, y, _ = conversion.TransformPoint(lon, lat)
        return [(x - centro[0]) * 0.001, 0.025, -(y - centro[1]) * 0.001]
    features = []
    for feature in limite["features"]:
        features.append({"type": "Feature", "properties": feature.get("properties", {}), "geometry": recorrer(feature["geometry"], convertir)})
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps({"type": "FeatureCollection", "name": "limite", "features": features}), encoding="utf-8")


if __name__ == "__main__":
    main()
