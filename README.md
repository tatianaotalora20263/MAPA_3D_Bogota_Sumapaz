# MAPA_3D

Sistema local y reutilizable para producir terreno 3D y un visor cartografico de
municipios colombianos. Los insumos y resultados de cada municipio se separan por
codigo DANE en `09_Resultados`.

## Solicitud en lenguaje natural

Ejemplo operativo: `Genera el mapa 3D de Chia, Cundinamarca`.

El coordinador debe resolver el nombre, pedir confirmacion ante homonimos y lanzar:

```powershell
python .\scripts\orquestar.py chia-cundinamarca --permitir-osm
```

Para un limite oficial suministrado y verificable, que siempre tiene prioridad:

```powershell
python .\scripts\orquestar.py chia-cundinamarca --limite-oficial C:\datos\limite_oficial.geojson
```

Antes de procesar un municipio se valida su codigo contra DIVIPOLA. Si no existe
geometria oficial descargable, el respaldo OSM queda marcado como no oficial en la
procedencia y no debe presentarse como limite institucional.

## Requisitos locales

- Autenticar Earth Engine fuera del repositorio: `& .\.venv\Scripts\earthengine.exe authenticate`.
- Configurar un proyecto de Google Cloud autorizado para Earth Engine: `& .\.venv\Scripts\earthengine.exe set_project <ID_PROYECTO>`.
  Como alternativa temporal, definir `$env:EE_PROJECT = "<ID_PROYECTO>"` antes de ejecutar el orquestador.
- QGIS, GDAL, Blender y Node se configuran en `01_Configuracion/configuracion_global.json`.

No almacene credenciales, tokens ni URL firmadas de Earth Engine en el repositorio.
