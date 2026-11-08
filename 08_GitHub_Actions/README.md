# GitHub Actions y Pages

El workflow real esta en `.github/workflows/deploy-pages.yml`. Compila unicamente
`07_Visor_Web`; no intenta ejecutar Earth Engine, QGIS ni Blender en GitHub.

El despliegue se activa despues de crear un repositorio remoto, subir una rama
`main` y autorizar GitHub Pages. Antes de publicar, confirme el propietario y el
nombre del repositorio para validar la ruta base y la URL resultante.
