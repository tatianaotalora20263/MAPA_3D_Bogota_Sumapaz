"""Ejecutar con el Python de QGIS para validar NoData, CRS y estadisticas."""
import argparse
import json
from pathlib import Path
from osgeo import gdal
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dem", type=Path)
    parser.add_argument("--salida", type=Path, required=True)
    args = parser.parse_args()
    gdal.UseExceptions()
    dataset = gdal.Open(str(args.dem))
    banda = dataset.GetRasterBand(1)
    datos = banda.ReadAsArray().astype(np.float64)
    nodata = banda.GetNoDataValue()
    validos = np.isfinite(datos)
    if nodata is not None:
        validos &= datos != nodata
    if not validos.any():
        raise RuntimeError("El DEM no contiene datos validos.")
    valores = datos[validos]
    salida = {
        "crs": dataset.GetSpatialRef().GetAuthorityCode(None),
        "geotransform": list(dataset.GetGeoTransform()),
        "tamano": [dataset.RasterXSize, dataset.RasterYSize],
        "nodata": nodata,
        "pixeles_validos": int(validos.sum()),
        "pixeles_nodata": int((~validos).sum()),
        "elevacion_m": {"min": float(valores.min()), "max": float(valores.max()), "media": float(valores.mean())}
    }
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(salida, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
