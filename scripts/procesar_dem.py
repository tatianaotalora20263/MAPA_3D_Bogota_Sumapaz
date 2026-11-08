"""Reproyecta y recorta un DEM con GDAL, sin alterar sus insumos."""
import argparse
import json
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("origen", type=Path)
    parser.add_argument("limite", type=Path)
    parser.add_argument("--salida", type=Path, required=True)
    parser.add_argument("--resolucion", type=float, required=True)
    parser.add_argument("--gdalwarp", type=Path, required=True)
    args = parser.parse_args()
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    comando = [str(args.gdalwarp), "-overwrite", "-t_srs", "EPSG:9377", "-tr", str(args.resolucion), str(args.resolucion),
               "-r", "bilinear", "-cutline", str(args.limite), "-crop_to_cutline", "-dstnodata", "-9999",
               "-of", "GTiff", "-co", "COMPRESS=DEFLATE", "-co", "TILED=YES", str(args.origen), str(args.salida)]
    subprocess.run(comando, check=True)
    args.salida.with_suffix(".proceso.json").write_text(json.dumps({"comando": comando, "crs": "EPSG:9377"}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
