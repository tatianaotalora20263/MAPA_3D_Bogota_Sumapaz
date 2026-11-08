"""Convierte un DEM a una matriz reducida para Blender. Ejecutar con Python QGIS."""
import argparse
import json
from pathlib import Path
from osgeo import gdal
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dem", type=Path)
    parser.add_argument("--salida", type=Path, required=True)
    parser.add_argument("--max-caras", type=int, default=450000)
    args = parser.parse_args()
    ds = gdal.Open(str(args.dem))
    banda = ds.GetRasterBand(1)
    datos = banda.ReadAsArray().astype(np.float32)
    nodata = banda.GetNoDataValue()
    validos = np.isfinite(datos)
    if nodata is not None:
        validos &= datos != nodata
    datos[~validos] = np.nan
    filas, columnas = datos.shape
    paso = max(1, int(np.ceil(np.sqrt(((filas - 1) * (columnas - 1)) / args.max_caras))))
    reducidos = datos[::paso, ::paso]
    geo = list(ds.GetGeoTransform())
    geo[1] *= paso
    geo[5] *= paso
    if not np.isfinite(reducidos).any():
        raise RuntimeError("La matriz preparada no contiene elevaciones.")
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.salida, elevaciones=reducidos, geotransform=np.array(geo, dtype=np.float64))
    metadata = {
        "paso_muestreo": paso, "tamano_original": [int(columnas), int(filas)],
        "tamano_blender": [int(reducidos.shape[1]), int(reducidos.shape[0])],
        "elevacion_min": float(np.nanmin(reducidos)), "elevacion_max": float(np.nanmax(reducidos))
    }
    args.salida.with_suffix(".terreno.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
