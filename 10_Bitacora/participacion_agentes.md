# Evidencia de participacion de agentes

## Límite y DIVIPOLA

- Agente: cartografico especializado.
- Resultado: confirmo `25175` para Chia, Cundinamarca mediante el recurso oficial
  DANE DIVIPOLA `gdxc-w37w`.
- Limite: localizo el catalogo oficial MGN DANE para Cundinamarca, pero no una
  descarga geometrica vigente utilizable. El piloto usa una geometria de respaldo
  OSM, rotulada como no oficial en `procedencia_limite.json`.

## Visor

- Agente: validacion web especializado.
- Resultado: comprobo que la geometria GLB de Bogota tiene Y como eje vertical y
  que el visor previo la interpretaba como Z. El visor reutilizable aplica Y-up.

## MCP

- Blender MCP: verificado; no habia una instancia de Blender con el complemento
  conectado. La generacion reproducible queda preparada para Blender en segundo
  plano; el intento MCP queda como evidencia de conexion bloqueada.
- Chrome DevTools MCP: verificado. La politica del navegador bloqueo navegar a
  `localhost`; el servidor Vite respondio HTTP 200 por una comprobacion local.
  El evento correspondiente esta en `ejecuciones/validacion-visor-20261107.jsonl`.

Los eventos de cada ejecucion automatizada se almacenan como JSONL y no incluyen
credenciales ni URLs firmadas.
