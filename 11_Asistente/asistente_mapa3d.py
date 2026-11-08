import json
from pathlib import Path
import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
CONFIG = RAIZ / "01_Configuracion" / "municipios"

st.set_page_config(
    page_title="MAPA_3D - Asistente",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 MAPA_3D")
st.subheader("Asistente geoespacial automatizado")

st.write(
    "Selecciona un municipio para preparar la generación "
    "de su modelo digital de elevación y visor 3D."
)

municipios = {}

for archivo in CONFIG.glob("*.json"):
    with open(archivo, encoding="utf-8") as f:
        datos = json.load(f)
    municipios[datos["id"]] = datos

if not municipios:
    st.error("No se encontraron municipios configurados.")
    st.stop()

municipio = st.selectbox(
    "Selecciona el municipio",
    sorted(municipios.keys())
)

datos = municipios[municipio]

st.info(f"Municipio seleccionado: {municipio}")

col1, col2, col3 = st.columns(3)

col1.metric("Código DANE", datos["codigo_dane"])
col2.metric("Resolución DEM", f'{datos["resolucion_metros"]} m')
col3.metric("Sistema de referencia", "EPSG:9377")

st.write("### Etapas del procesamiento")

etapas = [
    "1. Validación del municipio",
    "2. Obtención del límite geográfico",
    "3. Descarga Copernicus GLO-30",
    "4. Procesamiento QGIS/GDAL",
    "5. Generación del modelo Blender",
    "6. Preparación de vías y lugares OSM",
    "7. Integración al visor Three.js",
    "8. Publicación mediante GitHub Actions"
]

for etapa in etapas:
    st.write("☐", etapa)

if st.button("Preparar procesamiento", type="primary"):
    st.success("Configuración municipal identificada correctamente.")
    st.json(datos)
    st.warning(
        "Modo de preparación: todavía no se ejecutan "
        "descargas ni procesos externos."
    )

st.divider()
st.caption("MAPA_3D | Asistente geoespacial - Versión 0.1")
