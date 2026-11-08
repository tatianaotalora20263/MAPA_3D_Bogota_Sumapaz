"""Genera un terreno GLB con Y vertical a partir de una matriz NPZ."""
import argparse
import json
import sys
from pathlib import Path

import bpy
import numpy as np


def argumentos():
    parser = argparse.ArgumentParser()
    parser.add_argument("--entrada", required=True, type=Path)
    parser.add_argument("--blend", required=True, type=Path)
    parser.add_argument("--glb", required=True, type=Path)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--nombre", required=True)
    parser.add_argument("--exageracion", type=float, default=1.0)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1:])


def main():
    args = argumentos()
    datos = np.load(args.entrada)
    elevaciones = datos["elevaciones"]
    geo = datos["geotransform"]
    filas, columnas = elevaciones.shape
    validos = np.isfinite(elevaciones)
    if not validos.any():
        raise RuntimeError("No existen elevaciones validas para Blender.")
    escala = 0.001
    base = float(np.nanmin(elevaciones))
    centro_x = geo[0] + columnas * geo[1] / 2
    centro_y = geo[3] + filas * geo[5] / 2
    indices = np.full((filas, columnas), -1, dtype=np.int32)
    vertices = []
    for fila in range(filas):
        for columna in range(columnas):
            if not validos[fila, columna]:
                continue
            x = geo[0] + (columna + 0.5) * geo[1]
            norte = geo[3] + (fila + 0.5) * geo[5]
            indices[fila, columna] = len(vertices)
            # Blender usa Z como vertical; su exportador GLB lo convierte a Y-up.
            vertices.append(((x - centro_x) * escala,
                             (norte - centro_y) * escala,
                             (float(elevaciones[fila, columna]) - base) * escala * args.exageracion))
    caras = []
    for fila in range(filas - 1):
        for columna in range(columnas - 1):
            a, b, c, d = indices[fila, columna], indices[fila, columna + 1], indices[fila + 1, columna + 1], indices[fila + 1, columna]
            if min(a, b, c, d) >= 0:
                caras.append((a, b, c, d))
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    malla = bpy.data.meshes.new(f"Malla_{args.nombre}")
    malla.from_pydata(vertices, [], caras)
    malla.update()
    objeto = bpy.data.objects.new(f"Terreno_{args.nombre}", malla)
    bpy.context.collection.objects.link(objeto)
    bpy.context.view_layer.objects.active = objeto
    objeto.select_set(True)
    material = bpy.data.materials.new("Terreno_base")
    material.diffuse_color = (0.35, 0.5, 0.25, 1.0)
    objeto.data.materials.append(material)
    for ruta in [args.blend, args.glb, args.metadata]:
        ruta.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(args.blend))
    bpy.ops.export_scene.gltf(filepath=str(args.glb), export_format="GLB", use_selection=True)
    metadata = {
        "nombre": args.nombre, "crs": "EPSG:9377", "eje_vertical": "Y",
        "escala_unidad_metros": 1000, "elevacion_base_m": base,
        "elevacion_max_m": float(np.nanmax(elevaciones)), "centro_proyectado": [float(centro_x), float(centro_y)],
        "vertices": len(vertices), "caras": len(caras), "exageracion_vertical": args.exageracion
    }
    args.metadata.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

