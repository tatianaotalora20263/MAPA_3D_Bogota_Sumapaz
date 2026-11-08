"""Alinea una imagen RGB al rectangulo exacto del DEM y exporta una PNG liviana."""
import argparse
import json
import shutil
from pathlib import Path
from osgeo import gdal


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("imagen", type=Path)
    parser.add_argument("dem", type=Path)
    parser.add_argument("--salida", type=Path, required=True)
    parser.add_argument("--max-px", type=int, default=1536)
    parser.add_argument("--publica", type=Path)
    args = parser.parse_args()
    dem = gdal.Open(str(args.dem))
    geo = dem.GetGeoTransform()
    ancho_m, alto_m = dem.RasterXSize * geo[1], abs(dem.RasterYSize * geo[5])
    maximo = max(ancho_m, alto_m)
    ancho = max(1, round(args.max_px * ancho_m / maximo))
    alto = max(1, round(args.max_px * alto_m / maximo))
    min_x, max_y = geo[0], geo[3]
    max_x, min_y = min_x + ancho_m, max_y - alto_m
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    temporal = args.salida.with_suffix(".tif")
    opciones = gdal.WarpOptions(dstSRS="EPSG:9377", outputBounds=(min_x, min_y, max_x, max_y),
                                width=ancho, height=alto, resampleAlg="bilinear", format="GTiff")
    gdal.Warp(str(temporal), str(args.imagen), options=opciones)
    gdal.Translate(str(args.salida), str(temporal), format="PNG")
    temporal.unlink()
    if args.publica:
        args.publica.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(args.salida, args.publica)
    args.salida.with_suffix(".textura.json").write_text(json.dumps({
        "crs": "EPSG:9377", "tamano_px": [ancho, alto],
        "extension": [min_x, min_y, max_x, max_y],
        "orientacion": "norte_arriba; UV u=easting, v=northing invertida por textura WebGL"
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
