# Agentes de MAPA_3D

Los contratos en `contratos.json` son operativos: cada agente debe dejar un evento
en `10_Bitacora` antes y despues de actuar. Los agentes no pueden sustituir una
fuente oficial por una alternativa sin registrar el cambio de procedencia.

El agente coordinador ejecuta los scripts con un manifiesto por municipio. Los
agentes Earth Engine, QGIS, Blender y cartografico producen artefactos separados.
El agente de validacion revisa esos artefactos y el agente de publicacion no puede
ejecutar `git push` ni publicar sin una autorizacion registrada.

El MCP de Blender y Chrome DevTools se usa para inspeccion y evidencia cuando las
instancias estan conectadas. El procesamiento reproducible se ejecuta por scripts
locales para no depender de una sesion interactiva.
