import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { readFileSync } from 'node:fs';

const loader = new GLTFLoader();
const ruta = process.argv[2] || './public/models/bogota-dc/terreno.glb';
const archivo = readFileSync(ruta);

const datos = archivo.buffer.slice(
  archivo.byteOffset,
  archivo.byteOffset + archivo.byteLength
);

const gltf = await loader.parseAsync(datos, '');

gltf.scene.updateMatrixWorld(true);

gltf.scene.traverse((objeto) => {
  if (!objeto.isMesh) return;

  const cajaLocal = new THREE.Box3()
    .setFromBufferAttribute(objeto.geometry.attributes.position);

  const cajaMundo = new THREE.Box3().setFromObject(objeto);

  console.log('=== GEOMETRIA DEL TERRENO ===');
  console.log('Objeto:', objeto.name);
  console.log('Minimo local:', cajaLocal.min.toArray());
  console.log('Maximo local:', cajaLocal.max.toArray());
  console.log('Minimo mundial:', cajaMundo.min.toArray());
  console.log('Maximo mundial:', cajaMundo.max.toArray());
  console.log('Vertices:', objeto.geometry.attributes.position.count);
  const tamano = cajaMundo.getSize(new THREE.Vector3());
  if (tamano.y >= Math.min(tamano.x, tamano.z)) {
    throw new Error('El GLB no presenta Y como la dimension vertical del terreno.');
  }
  console.log('Eje vertical verificado: Y');
});

