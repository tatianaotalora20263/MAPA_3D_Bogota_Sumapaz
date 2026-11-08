# MAPA 3D - Sistema automatizado de cartografia tridimensional

## Objetivo
Desarrollar un sistema reutilizable para generar visores geograficos
tridimensionales de ciudades y municipios de Colombia.

## Herramientas
- OpenCode y modelos de OpenAI para coordinar el proceso.
- Google Earth Engine para obtener datos de elevacion.
- QGIS para procesar informacion geografica.
- Blender para construir modelos tridimensionales.
- Three.js para desarrollar el visor web.
- GitHub Actions para construir y publicar en GitHub Pages.

## Reglas generales
1. Trabajar exclusivamente dentro de MAPA_3D.
2. No modificar el proyecto anterior Bogota_3D_Agentes.
3. Utilizar herramientas y programas ya instalados.
4. Solicitar autorizacion antes de instalar dependencias.
5. No eliminar ni sobrescribir archivos sin autorizacion.
6. Explicar cada etapa en espanol.
7. Verificar resultados antes de continuar.
8. Registrar las operaciones en 10_Bitacora.
9. Priorizar datos geograficos oficiales y abiertos.
10. No inventar coordenadas, elevaciones ni resultados.

## Flujo de trabajo
1. Recibir el nombre del municipio o ciudad.
2. Identificar y validar su limite geografico.
3. Seleccionar y descargar el DEM mediante Google Earth Engine.
4. Procesar el DEM y las capas geograficas con QGIS.
5. Construir y exportar el terreno 3D mediante Blender.
6. Generar el visor web con Three.js.
7. Incorporar calles, nombres y limites administrativos.
8. Ejecutar verificaciones tecnicas.
9. Preparar la publicacion mediante GitHub Actions.
10. Registrar resultados, fuentes y evidencias.

## Restricciones
- No utilizar datos del proyecto anterior sin autorizacion.
- No publicar informacion sin verificar los resultados.
- No incluir credenciales ni claves API en GitHub.
- Mantener QGIS y Blender en puertos independientes.
- No asumir que GitHub Actions puede acceder a servicios locales.
- Solicitar confirmacion antes de publicar repositorios.

## Metodologia
Trabajar mediante el ciclo:
PLANIFICAR -> EJECUTAR -> VERIFICAR -> DOCUMENTAR.

Priorizar instrucciones pequenas, comprobables y reversibles.
