import json
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]


def main():
    configuracion = json.loads((RAIZ / "01_Configuracion" / "configuracion_global.json").read_text())
    municipio = json.loads((RAIZ / "01_Configuracion" / "municipios" / "chia-cundinamarca.json").read_text())
    contratos = json.loads((RAIZ / "02_Agentes" / "contratos.json").read_text())
    assert configuracion["crs_procesamiento"] == "EPSG:9377"
    assert municipio["codigo_dane"] == "25175"
    assert municipio["limite"]["fuente_preferida"] == "DANE/IGAC"
    for agente in ("coordinador", "earth_engine", "qgis", "blender", "cartografico", "visor", "validacion", "publicacion"):
        assert agente in contratos["agentes"]
    print("Configuracion y contratos validos")


if __name__ == "__main__":
    main()
