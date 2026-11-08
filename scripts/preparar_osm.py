"""Recorta OSM al limite de Bogota y ajusta alturas al DEM para Three.js."""
import argparse
import json
from pathlib import Path

import numpy as np
from osgeo import gdal, osr
from shapely.geometry import LineString, Point, shape
from shapely.prepared import prep
from shapely.ops import transform as transformar_geometria


def escribir(salida, features, nombre):
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(
        json.dumps({
            "type": "FeatureCollection",
            "name": nombre,
            "crs": {
                "type": "name",
                "properties": {"name": "MAPA_3D local Y-up"}
            },
            "features": features
        }, ensure_ascii=False),
        encoding="utf-8"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("osm", type=Path)
    parser.add_argument("dem", type=Path)
    parser.add_argument("metadata_terreno", type=Path)
    parser.add_argument("--limite", type=Path, required=True)
    parser.add_argument("--vias", type=Path, required=True)
    parser.add_argument("--lugares", type=Path, required=True)
    args = parser.parse_args()

    with args.osm.open(encoding="utf-8") as archivo:
        osm = json.load(archivo)

    with args.metadata_terreno.open(encoding="utf-8") as archivo:
        metadata = json.load(archivo)

    with args.limite.open(encoding="utf-8") as archivo:
        limite_geojson = json.load(archivo)

    geometrias = [
        shape(feature["geometry"])
        for feature in limite_geojson.get("features", [])
        if feature.get("geometry")
    ]

    if not geometrias:
        raise ValueError("El limite territorial no contiene geometria.")

    from shapely.ops import unary_union
    limite = unary_union(geometrias)

    if not limite.is_valid:
        limite = limite.buffer(0)

    if limite.is_empty:
        raise ValueError("El limite territorial esta vacio.")

    dem = gdal.Open(str(args.dem))
    if dem is None:
        raise RuntimeError("No se pudo abrir el DEM.")

    banda = dem.GetRasterBand(1)
    elevaciones = banda.ReadAsArray()
    nodata = banda.GetNoDataValue()
    inversa = gdal.InvGeoTransform(dem.GetGeoTransform())

    origen = osr.SpatialReference()
    destino = osr.SpatialReference()
    origen.ImportFromEPSG(4326)
    destino.ImportFromEPSG(9377)
    origen.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    destino.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

    conversion = osr.CoordinateTransformation(origen, destino)

    centro = metadata["centro_proyectado"]
    base = metadata["elevacion_base_m"]
    escala = metadata["escala_unidad_metros"]
    escala = 1.0 / float(escala)

    def altura(x, y):
        columna, fila = gdal.ApplyGeoTransform(inversa, x, y)
        columna = int(np.floor(columna))
        fila = int(np.floor(fila))

        if not (
            0 <= columna < dem.RasterXSize
            and 0 <= fila < dem.RasterYSize
        ):
            return None

        valor = float(elevaciones[fila, columna])

        if not np.isfinite(valor):
            return None

        if nodata is not None and np.isclose(valor, nodata):
            return None

        return (valor - base) * escala + 0.015

    def convertir_punto(lon, lat):
        x, y, _ = conversion.TransformPoint(lon, lat)
        h = altura(x, y)

        if h is None:
            return None

        return [
            (x - centro[0]) * escala,
            h,
            -(y - centro[1]) * escala
        ]

    def proyectar_geometria(x, y, z=None):
        return conversion.TransformPoint(x, y)[:2]

    limite_proyectado = transformar_geometria(
        proyectar_geometria, limite
    )

    limite_rapido = prep(limite_proyectado)
    vias = []
    lugares = []

    elementos = osm.get("elements", [])
    total = len(elementos)
    print(f"Procesando {total:,} elementos OSM...", flush=True)

    for indice, elemento in enumerate(elementos, 1):
        if indice % 5000 == 0:
            print(f"Avance: {indice:,}/{total:,} elementos | Vias: {len(vias):,} | Lugares: {len(lugares):,}", flush=True)
        etiquetas = elemento.get("tags", {})

        if (
            elemento.get("type") == "way"
            and etiquetas.get("highway")
            and elemento.get("geometry")
        ):
            puntos = [
                conversion.TransformPoint(p["lon"], p["lat"])[:2]
                for p in elemento["geometry"]
            ]

            if len(puntos) < 2:
                continue

            linea = LineString(puntos)

            if not limite_rapido.intersects(linea):
                continue

            if limite_rapido.covers(linea):
                recorte = linea
            else:
                recorte = linea.intersection(limite_proyectado)

            if recorte.is_empty:
                continue

            segmentos = []

            if recorte.geom_type == "LineString":
                segmentos = [recorte]
            elif recorte.geom_type == "MultiLineString":
                segmentos = list(recorte.geoms)
            elif recorte.geom_type == "GeometryCollection":
                segmentos = [
                    g for g in recorte.geoms
                    if g.geom_type == "LineString"
                ]

            for segmento in segmentos:
                coords = []

                for x, y in segmento.coords:
                    h = altura(x, y)
                    if h is None:
                        coords = []
                        break

                    coords.append([
                        (x - centro[0]) * escala,
                        h,
                        -(y - centro[1]) * escala
                    ])

                if len(coords) > 1:
                    vias.append({
                        "type": "Feature",
                        "properties": {
                            "nombre": etiquetas.get("name", ""),
                            "clase": etiquetas.get("highway", ""),
                            "osm_id": elemento["id"]
                        },
                        "geometry": {
                            "type": "LineString",
                            "coordinates": coords
                        }
                    })

        elif (
            elemento.get("type") == "node"
            and etiquetas.get("place")
        ):
            lon = elemento["lon"]
            lat = elemento["lat"]

            if not limite.covers(Point(lon, lat)):
                continue

            coord = convertir_punto(lon, lat)

            if coord is None:
                continue

            lugares.append({
                "type": "Feature",
                "properties": {
                    "nombre": etiquetas.get("name", ""),
                    "tipo": etiquetas.get("place", ""),
                    "osm_id": elemento["id"]
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": coord
                }
            })

    escribir(args.vias, vias, "vias")
    escribir(args.lugares, lugares, "lugares")

    print("Vias generadas:", len(vias))
    print("Lugares generados:", len(lugares))


if __name__ == "__main__":
    main()


