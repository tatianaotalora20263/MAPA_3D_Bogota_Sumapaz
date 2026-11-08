"""Orquestador local de MAPA_3D. Cada etapa conserva insumos y evidencia."""
import argparse
import json
import shutil
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]


def ejecutar(comando, agente, etapa, bitacora, artefactos=()):
    evento = [sys.executable, str(RAIZ / "10_Bitacora" / "registrar_evento.py"), "--ejecucion", bitacora,
              "--agente", agente, "--herramienta", comando[0], "--estado", "en_progreso", "--mensaje", etapa]
    subprocess.run(evento, check=True)
    try:
        subprocess.run(comando, check=True)
    except subprocess.CalledProcessError as error:
        fallo = evento[:-4] + ["--estado", "fallido", "--mensaje", f"{etapa}: codigo {error.returncode}"]
        subprocess.run(fallo, check=True)
        raise
    final = evento[:-4] + ["--estado", "completado", "--mensaje", etapa]
    for artefacto in artefactos:
        final.extend(["--artefacto", str(artefacto)])
    subprocess.run(final, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("municipio", help="id de 01_Configuracion/municipios")
    parser.add_argument("--etapa", choices=["todo", "limite", "dem", "blender", "cartografia"], default="todo")
    parser.add_argument("--limite-oficial", type=Path)
    parser.add_argument("--permitir-osm", action="store_true")
    args = parser.parse_args()
    config = RAIZ / "01_Configuracion" / "municipios" / f"{args.municipio}.json"
    datos = json.loads(config.read_text(encoding="utf-8"))
    globales = json.loads((RAIZ / "01_Configuracion" / "configuracion_global.json").read_text(encoding="utf-8"))
    resultado = RAIZ / datos["resultado_relativo"]
    bruto, procesado, modelo, capas, metadatos = [resultado / parte for parte in ("01_bruto", "02_procesado", "03_modelo", "04_capas", "metadatos")]
    for carpeta in (bruto, procesado, modelo, capas, metadatos):
        carpeta.mkdir(parents=True, exist_ok=True)
    ejecucion = f"{datos['codigo_dane']}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    limite, divipola = bruto / "limite.geojson", metadatos / "divipola.json"
    if args.etapa in {"todo", "limite"}:
        ejecutar([sys.executable, str(RAIZ / "scripts" / "validar_divipola.py"), str(config), "--salida", str(divipola)], "limites", "Validacion DIVIPOLA", ejecucion, [divipola])
        comando = [sys.executable, str(RAIZ / "scripts" / "obtener_limite.py"), str(config), "--salida", str(limite)]
        if args.limite_oficial:
            comando.extend(["--oficial", str(args.limite_oficial)])
        elif args.permitir_osm:
            comando.append("--permitir-osm")
        ejecutar(comando, "limites", "Obtencion de limite", ejecucion, [limite, limite.with_name("procedencia_limite.json")])
    dem_origen, dem_9377 = bruto / "dem_copernicus_glo30.tif", procesado / "dem_9377.tif"
    if args.etapa in {"todo", "dem"}:
        comando_ee = [str(RAIZ / globales["rutas_herramientas"]["python_earth_engine"]), str(RAIZ / "scripts" / "descargar_dem_ee.py"), str(limite), "--salida", str(dem_origen), "--escala", str(datos["resolucion_metros"])]
        if os.environ.get("EE_PROJECT"):
            comando_ee.extend(["--proyecto", os.environ["EE_PROJECT"]])
        ejecutar(comando_ee, "earth_engine", "Descarga DEM Copernicus", ejecucion, [dem_origen])
        ejecutar([sys.executable, str(RAIZ / "scripts" / "procesar_dem.py"), str(dem_origen), str(limite), "--salida", str(dem_9377), "--resolucion", str(datos["resolucion_metros"]), "--gdalwarp", str(RAIZ / globales["rutas_herramientas"]["gdalwarp"])], "qgis", "Reproyeccion y recorte DEM", ejecucion, [dem_9377])
        ejecutar([str(RAIZ / globales["rutas_herramientas"]["python_qgis"]), str(RAIZ / "scripts" / "validar_dem.py"), str(dem_9377), "--salida", str(metadatos / "validacion_dem.json")], "validacion", "Validacion DEM", ejecucion, [metadatos / "validacion_dem.json"])
    terreno = procesado / "terreno.npz"
    metadata_terreno = modelo / "terreno.metadata.json"
    if args.etapa in {"todo", "blender"}:
        ejecutar([str(RAIZ / globales["rutas_herramientas"]["python_qgis"]), str(RAIZ / "scripts" / "preparar_terreno.py"), str(dem_9377), "--salida", str(terreno), "--max-caras", str(globales["presupuesto_maximo_caras"])], "qgis", "Preparacion matriz Blender", ejecucion, [terreno])
        ejecutar([str(RAIZ / globales["rutas_herramientas"]["blender"]), "--background", "--python", str(RAIZ / "scripts" / "crear_terreno_blender.py"), "--", "--entrada", str(terreno), "--blend", str(modelo / "terreno.blend"), "--glb", str(modelo / "terreno.glb"), "--metadata", str(metadata_terreno), "--nombre", datos["id"], "--exageracion", str(datos["exageracion_vertical"])], "blender", "Generacion GLB Y-up", ejecucion, [modelo / "terreno.blend", modelo / "terreno.glb", metadata_terreno])
        ejecutar([str(RAIZ / globales["rutas_herramientas"]["python_qgis"]), str(RAIZ / "scripts" / "preparar_limite.py"), str(limite), str(metadata_terreno), "--salida", str(capas / "limite.geojson")], "cartografico", "Normalizacion del limite para visor", ejecucion, [capas / "limite.geojson"])
    if args.etapa in {"todo", "cartografia"}:
        osm = bruto / "osm.json"
        if not osm.exists():
            ejecutar([sys.executable, str(RAIZ / "scripts" / "obtener_osm.py"), str(limite), "--salida", str(osm)], "cartografico", "Descarga de capas OSM", ejecucion, [osm])
        else:
            print("Reutilizando archivo OSM existente:", osm, flush=True)
        ejecutar([str(RAIZ / globales["rutas_herramientas"]["python_qgis"]), str(RAIZ / "scripts" / "preparar_osm.py"), str(osm), str(dem_9377), str(metadata_terreno), "--limite", str(limite), "--vias", str(capas / "vias.geojson"), "--lugares", str(capas / "lugares.geojson")], "cartografico", "Drape de capas OSM", ejecucion, [capas / "vias.geojson", capas / "lugares.geojson"])
        publico = RAIZ / "07_Visor_Web" / "public"
        destino_modelo = publico / "models" / datos["id"]
        destino_capas = publico / "capas" / datos["id"]
        destino_modelo.mkdir(parents=True, exist_ok=True)
        destino_capas.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(modelo / "terreno.glb", destino_modelo / "terreno.glb")
        shutil.copyfile(metadata_terreno, destino_modelo / "terreno.metadata.json")
        for nombre in ("limite.geojson", "vias.geojson", "lugares.geojson"):
            shutil.copyfile(capas / nombre, destino_capas / nombre)
    manifiesto = {"municipio": datos, "ejecucion": ejecucion, "resultado": str(resultado), "generado_utc": datetime.now(timezone.utc).isoformat()}
    (metadatos / "manifiesto.json").write_text(json.dumps(manifiesto, indent=2), encoding="utf-8")
    print(json.dumps(manifiesto, indent=2))


if __name__ == "__main__":
    main()

