import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import './style.css';

const base = import.meta.env.BASE_URL;
const ruta = (valor) => new URL(valor, window.location.origin + base).href;
const contenedor = document.getElementById('visor');
const estado = document.getElementById('estado');
const escena = new THREE.Scene();
escena.background = new THREE.Color(0x10243a);
const camara = new THREE.PerspectiveCamera(45, innerWidth / innerHeight, 0.01, 2000);
const renderizador = new THREE.WebGLRenderer({ antialias: true });
renderizador.setSize(innerWidth, innerHeight);
renderizador.setPixelRatio(Math.min(devicePixelRatio, 2));
renderizador.outputColorSpace = THREE.SRGBColorSpace;
contenedor.appendChild(renderizador.domElement);
const controles = new OrbitControls(camara, renderizador.domElement);
controles.enableDamping = true;
controles.dampingFactor = 0.06;
controles.screenSpacePanning = true;
camara.up.set(0, 1, 0);
escena.add(new THREE.HemisphereLight(0xddeeff, 0x26351f, 2));
const sol = new THREE.DirectionalLight(0xffffff, 2.5);
sol.position.set(40, 80, 50);
escena.add(sol);
let vistaInicial;
let terreno;
let texturaSatelital;
let vistaActual = 'relieve';
const gruposCapas = [];

function colorAltura(altura, minimo, maximo) {
  const t = THREE.MathUtils.clamp(
    (altura - minimo) / Math.max(1, maximo - minimo),
    0,
    1
  );

  // Paleta natural del relieve: sin azul.
  const escala = [
    [0.00, 0x087E38],  // Verde oscuro
    [0.18, 0x21B52B],  // Verde intenso
    [0.36, 0x83C52A],  // Verde amarillento
    [0.54, 0xD4C735],  // Amarillo ocre
    [0.70, 0xCB8D28],  // Naranja terroso
    [0.86, 0xA74A1B],  // Marron rojizo
    [0.96, 0x6D351F],  // Marron oscuro
    [1.00, 0xF5F4EF]   // Blanco en las mayores elevaciones
  ];

  const indice = escala.findIndex(([umbral]) => t <= umbral);
  const superior = escala[Math.max(1, indice)];
  const inferior = escala[Math.max(0, indice - 1)];

  const proporcion = (t - inferior[0]) /
    Math.max(0.001, superior[0] - inferior[0]);

  return new THREE.Color(inferior[1]).lerp(
    new THREE.Color(superior[1]),
    proporcion
  );
}

function aplicarHipsometria(objeto, config) {
  const minimo = config.elevacion_base_m ?? 0;
  const maximo = config.elevacion_max_m ?? minimo + 1000;
  objeto.traverse((malla) => {
    if (!malla.isMesh) return;
    const posiciones = malla.geometry.attributes.position;
    const colores = new Float32Array(posiciones.count * 3);
    const color = new THREE.Color();
    for (let i = 0; i < posiciones.count; i += 1) {
      color.copy(colorAltura(minimo + posiciones.getY(i) * 1000, minimo, maximo));
      colores.set([color.r, color.g, color.b], i * 3);
    }
    malla.geometry.setAttribute('color', new THREE.BufferAttribute(colores, 3));
    malla.userData.materialRelieve = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.86, side: THREE.DoubleSide });
    malla.material = malla.userData.materialRelieve;
  });
  document.getElementById('leyenda').innerHTML = `<strong>Elevacion (m)</strong><div class="gradiente"></div><span>${Math.round(minimo)}</span><span>${Math.round(maximo)}</span>`;
}

function prepararUVSatelital(objeto) {
  // Extension exacta del DEM EPSG:9377.
  // Centro del modelo: [4864806.879551535, 2031437.5551363965].
  // Una unidad del modelo representa 1000 metros.
  const anchoDEM = 51.72;
  const altoDEM = 122.22;

  objeto.traverse((malla) => {
    if (!malla.isMesh) return;

    const posiciones = malla.geometry.attributes.position;
    const uv = new Float32Array(posiciones.count * 2);

    for (let i = 0; i < posiciones.count; i += 1) {
      const x = posiciones.getX(i);
      const z = posiciones.getZ(i);

      // Coordenadas normalizadas respecto a toda la extension del DEM.
      uv[i * 2] = (x + anchoDEM / 2) / anchoDEM;

      // Z negativa corresponde al norte del terreno.
      // Con flipY=false, V=0 corresponde a la parte superior de la imagen.
      uv[i * 2 + 1] = (z + altoDEM / 2) / altoDEM;
    }

    malla.geometry.setAttribute(
      'uv',
      new THREE.BufferAttribute(uv, 2)
    );
  });
}

async function cargarTexturaSatelital(config) {
  if (!config.imagen_satelital) return;
  texturaSatelital = await new THREE.TextureLoader().loadAsync(ruta(config.imagen_satelital));
  texturaSatelital.colorSpace = THREE.SRGBColorSpace;
  // El PNG esta orientado norte-arriba y las UV ya incluyen esa orientacion.
  texturaSatelital.flipY = false;
  texturaSatelital.needsUpdate = true;
  texturaSatelital.anisotropy = Math.min(8, renderizador.capabilities.getMaxAnisotropy());
  prepararUVSatelital(terreno);
  terreno.traverse((malla) => {
    if (!malla.isMesh) return;
    malla.userData.materialSatelite = new THREE.MeshBasicMaterial({ map: texturaSatelital, transparent: true, alphaTest: 0.01, side: THREE.DoubleSide });
  });
}

function actualizarVisibilidadCapas() {
  for (const grupo of gruposCapas) {
    grupo.visible = vistaActual !== 'satelite' && grupo.userData.check.checked;
  }
}

function cambiarVista(vista) {
  if ((vista === 'satelite' || vista === 'hibrido') && !texturaSatelital) {
    estado.textContent = 'Imagen satelital no disponible para este municipio';
    return;
  }
  vistaActual = vista;
  terreno?.traverse((malla) => {
    if (malla.isMesh) malla.material = vista === 'relieve' ? malla.userData.materialRelieve : malla.userData.materialSatelite;
  });
  document.getElementById('leyenda').hidden = vista !== 'relieve';
  document.querySelectorAll('#vistas button').forEach((boton) => boton.classList.toggle('activa', boton.dataset.vista === vista));
  actualizarVisibilidadCapas();
}

function ajustarEtiquetasVias() {
  for (const grupo of gruposCapas) {
    grupo.traverse((objeto) => {
      const esVia = objeto.userData.esEtiquetaVia;
      const esLugar = objeto.userData.esEtiquetaLugar;

      if (!esVia && !esLugar) return;

      const distancia = camara.position.distanceTo(objeto.position);

      const factor = THREE.MathUtils.clamp(
        distancia / 35,
        0.35,
        1.2
      );

      if (esVia) {
        objeto.scale.set(factor, factor * 0.125, 1);
      } else {
        objeto.scale.set(
          factor * 0.55,
          factor * 0.103,
          1
        );
      }

      objeto.visible = distancia < 100;
    });
  }
}
function ajustarCamara(objeto) {
  const caja = new THREE.Box3().setFromObject(objeto);
  const centro = caja.getCenter(new THREE.Vector3());
  const dimension = Math.max(...caja.getSize(new THREE.Vector3()).toArray());
  controles.target.copy(centro);
  camara.position.set(centro.x + dimension * 0.72, centro.y + dimension * 0.8, centro.z + dimension * 0.9);
  camara.near = Math.max(0.001, dimension / 10000);
  camara.far = dimension * 30;
  camara.updateProjectionMatrix();
  controles.update();
  vistaInicial = { posicion: camara.position.clone(), objetivo: controles.target.clone() };
}

function agregarEtiquetaVia(grupo, feature, linea) {
  const nombre = feature.properties?.nombre?.trim();
  const clase = feature.properties?.clase;

  const principales = new Set([
    'motorway', 'trunk', 'primary', 'secondary'
  ]);

  if (!nombre || !principales.has(clase) || linea.length < 2) return;

  // Evitar etiquetas repetidas dentro de cada grupo.
  if (!grupo.userData.nombresVias) {
    grupo.userData.nombresVias = new Set();
  }

  const clave = nombre.toLowerCase();
  if (grupo.userData.nombresVias.has(clave)) return;
  grupo.userData.nombresVias.add(clave);

  const medio = Math.floor(linea.length / 2);
  const punto = linea[medio];
  if (!punto || punto.length < 3) return;

  const lienzo = document.createElement('canvas');
  lienzo.width = 1024;
  lienzo.height = 128;

  const ctx = lienzo.getContext('2d');
  ctx.font = 'bold 52px Arial';
  ctx.textAlign = 'center';
  ctx.strokeStyle = '#10243a';
  ctx.lineWidth = 8;
  ctx.fillStyle = '#ffffff';

  const texto = nombre.length > 38
    ? nombre.slice(0, 35) + '...'
    : nombre;

  ctx.strokeText(texto, 512, 82);
  ctx.fillText(texto, 512, 82);

  const textura = new THREE.CanvasTexture(lienzo);
  const material = new THREE.SpriteMaterial({
    map: textura,
    transparent: true,
    depthTest: false
  });

  const etiqueta = new THREE.Sprite(material);
  etiqueta.position.set(punto[0], punto[1] + 0.12, punto[2]);
  etiqueta.scale.set(1, 0.125, 1);
  etiqueta.userData.escalaBase = 1;
  etiqueta.userData.esEtiquetaVia = true;

  grupo.add(etiqueta);
}
function grupoGeoJSON(geojson, capa) {
  const grupo = new THREE.Group();
  for (const feature of geojson.features ?? []) {
    const geometria = feature.geometry;
    if (!geometria) continue;
    const lineas = geometria.type === 'LineString' ? [geometria.coordinates]
      : geometria.type === 'Polygon' ? geometria.coordinates
      : geometria.type === 'MultiPolygon' ? geometria.coordinates.flat() : [];
    for (const linea of lineas) {
      const puntos = linea.map(([x, y, z]) => new THREE.Vector3(x, y, z));
      if (puntos.length > 1) {
        const tipoVia = feature.properties?.tipo
          ?? feature.properties?.highway
          ?? feature.properties?.clase
          ?? '';

        const viaPrincipal = [
          'motorway', 'trunk', 'primary', 'secondary'
        ].includes(tipoVia);

        const linea3D = new THREE.Line(
          new THREE.BufferGeometry().setFromPoints(puntos),
          new THREE.LineBasicMaterial({
            color: capa.color,
            transparent: true,
            opacity: capa.id === 'vias' ? 0.65 : 1,
            depthTest: true,
            depthWrite: false
          })
        );

        if (capa.id === 'vias') {
          linea3D.userData.esVia = true;
          linea3D.userData.viaPrincipal = viaPrincipal;
          linea3D.visible = viaPrincipal;
        }

        grupo.add(linea3D);
        if (capa.id === 'vias') {
          agregarEtiquetaVia(grupo, feature, linea);
        }
      }
    }
    if (geometria.type === 'Point') {
      const [x, y, z] = geometria.coordinates;
      const marcador = new THREE.Mesh(new THREE.SphereGeometry(0.012, 10, 8), new THREE.MeshBasicMaterial({ color: 0xFF00CC }));
      marcador.position.set(x, y, z);
      marcador.userData.esMarcadorLugar = true;
      marcador.userData.propiedadesLugar = feature.properties ?? {};
      grupo.add(marcador);
      if (feature.properties?.nombre) {
        const lienzo = document.createElement('canvas');
        lienzo.width = 512; lienzo.height = 96;
        const contexto = lienzo.getContext('2d');
        contexto.font = 'bold 42px Arial';
        contexto.fillStyle = '#ffffff';
        contexto.strokeStyle = '#182536';
        contexto.lineWidth = 7;
        contexto.strokeText(feature.properties.nombre, 10, 60);
        contexto.fillText(feature.properties.nombre, 10, 60);
        const etiqueta = new THREE.Sprite(new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(lienzo), depthTest: false }));
        etiqueta.position.set(x, y + 0.08, z);
        etiqueta.scale.set(0.55, 0.103, 1);
        etiqueta.userData.esEtiquetaLugar = true;
        grupo.add(etiqueta);
      }
    }
  }
  return grupo;
}

async function cargarCapas(config) {
  const panel = document.getElementById('capas');
  for (const capa of config.capas ?? []) {
    try {
      const respuesta = await fetch(ruta(capa.url));
      if (!respuesta.ok) throw new Error(`HTTP ${respuesta.status}`);
      const grupo = grupoGeoJSON(await respuesta.json(), capa);
      grupo.visible = capa.visible !== false;
      gruposCapas.push(grupo);
      escena.add(grupo);
      const etiqueta = document.createElement('label');
      const check = document.createElement('input');
      check.type = 'checkbox'; check.checked = grupo.visible;
      grupo.userData.check = check;
      check.addEventListener('change', actualizarVisibilidadCapas);
      etiqueta.append(check, document.createTextNode(` ${capa.nombre}`));
      panel.append(etiqueta);
    } catch (error) {
      console.warn(`No se pudo cargar la capa ${capa.id}:`, error);
      estado.textContent = `Terreno cargado; capa ${capa.nombre} no disponible`;
    }
  }
}

function activarSeleccionLugares() {
  const raycasterLugares = new THREE.Raycaster();
  const punteroLugares = new THREE.Vector2();
  const canvas = renderizador.domElement;

  const ficha = document.createElement('div');
  ficha.id = 'ficha-lugar';
  Object.assign(ficha.style, {
    position: 'fixed',
    right: '18px',
    bottom: '65px',
    width: 'min(320px, calc(100vw - 36px))',
    maxHeight: '45vh',
    overflowY: 'auto',
    padding: '16px',
    borderRadius: '12px',
    background: 'rgba(10, 29, 43, 0.96)',
    color: '#ffffff',
    fontFamily: 'Arial, sans-serif',
    fontSize: '14px',
    boxShadow: '0 8px 24px rgba(0,0,0,0.35)',
    zIndex: '1000',
    display: 'none'
  });

  document.body.appendChild(ficha);

  let inicioPuntero = null;

  canvas.addEventListener('pointerdown', (evento) => {
    if (evento.button !== 0) return;
    inicioPuntero = { x: evento.clientX, y: evento.clientY };
  });

  canvas.addEventListener('pointerup', (evento) => {
    if (evento.button !== 0 || !inicioPuntero) return;

    const distancia = Math.hypot(
      evento.clientX - inicioPuntero.x,
      evento.clientY - inicioPuntero.y
    );
    inicioPuntero = null;

    // No seleccionar lugares cuando se esta rotando el modelo.
    if (distancia > 5) return;

    const rect = canvas.getBoundingClientRect();

    punteroLugares.set(
      ((evento.clientX - rect.left) / rect.width) * 2 - 1,
      -((evento.clientY - rect.top) / rect.height) * 2 + 1
    );

    raycasterLugares.setFromCamera(punteroLugares, camara);

    const marcadores = [];

    for (const grupo of gruposCapas) {
      if (!grupo.visible) continue;

      grupo.traverse((objeto) => {
        if (objeto.userData.esMarcadorLugar && objeto.visible) {
          marcadores.push(objeto);
        }
      });
    }

    const impacto = raycasterLugares.intersectObjects(marcadores, false)[0];

    if (!impacto) {
      ficha.style.display = 'none';
      return;
    }

    const propiedades = impacto.object.userData.propiedadesLugar;
    ficha.replaceChildren();

    const encabezado = document.createElement('div');
    encabezado.style.display = 'flex';
    encabezado.style.justifyContent = 'space-between';
    encabezado.style.alignItems = 'center';

    const titulo = document.createElement('strong');
    titulo.textContent = String(propiedades.nombre || 'Lugar sin nombre');
    titulo.style.fontSize = '18px';

    const cerrar = document.createElement('button');
    cerrar.textContent = 'Ã—';
    cerrar.setAttribute('aria-label', 'Cerrar ficha');
    cerrar.style.cssText = 'background:none;border:0;color:white;font-size:24px;cursor:pointer';
    cerrar.addEventListener('click', () => {
      ficha.style.display = 'none';
    });

    encabezado.append(titulo, cerrar);
    ficha.appendChild(encabezado);

    for (const [clave, valor] of Object.entries(propiedades)) {
      if (valor === null || valor === undefined || valor === '') continue;
      if (typeof valor === 'object') continue;

      const fila = document.createElement('p');
      fila.style.margin = '9px 0';
      fila.textContent = `${clave}: ${valor}`;
      ficha.appendChild(fila);
    }

    const fuente = document.createElement('small');
    fuente.textContent = 'Fuente: OpenStreetMap';
    fuente.style.opacity = '0.7';
    ficha.appendChild(fuente);

    ficha.style.display = 'block';
  });
}
function activarConsulta(config) {
  const raycaster = new THREE.Raycaster();
  const puntero = new THREE.Vector2();
  renderizador.domElement.addEventListener('pointermove', (evento) => {
    if (!terreno) return;
    const rect = renderizador.domElement.getBoundingClientRect();
    puntero.set(((evento.clientX - rect.left) / rect.width) * 2 - 1, -((evento.clientY - rect.top) / rect.height) * 2 + 1);
    raycaster.setFromCamera(puntero, camara);
    const impacto = raycaster.intersectObject(terreno, true)[0];
    if (impacto) document.getElementById('consulta').textContent = `Elevacion: ${Math.round((config.elevacion_base_m ?? 0) + impacto.point.y * 1000)} m`;
  });
}

async function iniciar() {
  activarSeleccionLugares();
  const datos = await (await fetch(ruta('config/municipios.json'))).json();
  const id = new URLSearchParams(location.search).get('municipio') || 'bogota';
  const config = datos.municipios[id];
  if (!config) throw new Error(`Municipio no configurado: ${id}`);
  if (config.metadata) Object.assign(config, await (await fetch(ruta(config.metadata))).json());
  document.title = `MAPA 3D | ${config.nombre}`;
  document.getElementById('titulo').textContent = config.nombre.toUpperCase();
  document.getElementById('subtitulo').textContent = config.subtitulo;
  document.getElementById('fuentes').textContent = config.atribuciones.join(' | ');
  estado.textContent = `Cargando terreno de ${config.nombre}...`;
  new GLTFLoader().load(ruta(config.modelo), (gltf) => {
    terreno = gltf.scene;
    aplicarHipsometria(terreno, config);
    escena.add(terreno); ajustarCamara(terreno); activarConsulta(config);
    estado.textContent = 'Terreno cargado correctamente';
    cargarCapas(config);
    cargarTexturaSatelital(config).then(() => cambiarVista('relieve')).catch((error) => console.warn('Textura satelital no disponible:', error));
  }, (evento) => {
    if (evento.total) estado.textContent = `Cargando modelo: ${Math.round(evento.loaded / evento.total * 100)}%`;
  }, (error) => { console.error(error); estado.textContent = 'Error al cargar el terreno'; });
}

const recorrido3D = {
  activo: false,
  progreso: 0,
  duracion: 110000,
  ultimoTiempo: 0
};

const botonReproducir = document.getElementById('recorrido-reproducir');
const botonPausar = document.getElementById('recorrido-pausar');
const botonReiniciarRecorrido = document.getElementById('recorrido-reiniciar');

function actualizarBotonesRecorrido() {
  botonReproducir.textContent = recorrido3D.progreso > 0 && !recorrido3D.activo
    ? 'Reanudar recorrido'
    : 'Reproducir recorrido';

  botonPausar.disabled = !recorrido3D.activo;
}

const puntosVuelo = [
  // Circuito por los lugares de Sumapaz
  new THREE.Vector3(-10.687, 2.3482, 28.082),
  new THREE.Vector3(-11.422, 2.3482, 39.477),
  new THREE.Vector3(-3.251, 2.3482, 28.099),
  new THREE.Vector3(-10.687, 2.3482, 28.082)
];

// Vuelo panoramico hacia el norte por la zona central del DEM.
const puntosCentrales = [
  new THREE.Vector3(-10.687, 2.3482, 28.082),
  new THREE.Vector3(4.630, 2.3482, 20.468),
  new THREE.Vector3(4.238, 2.3482, 15.168),
  new THREE.Vector3(7.794, 2.3482, 12.234),
  new THREE.Vector3(8.038, 2.3482, 7.228),
  new THREE.Vector3(7.218, 2.3482, 3.000),
  new THREE.Vector3(8.938, 2.3482, -13.922),
  new THREE.Vector3(6.989, 2.3482, -17.790),
  new THREE.Vector3(10.385, 2.3482, -20.700),
  new THREE.Vector3(6.365099, 2.3482, -31.184556),
  new THREE.Vector3(10.208317, 2.3482, -30.841563),
  new THREE.Vector3(13.756547, 2.3482, -31.271300),
  new THREE.Vector3(20.815, 2.3482, -45.219)
];

const puntosFinales = [
  new THREE.Vector3(20.815, 2.3482, -45.219),
  new THREE.Vector3(8.610, 2.3482, -45.928),
  new THREE.Vector3(18.163, 2.3482, -35.521)
];

const curvaSumapaz = new THREE.CatmullRomCurve3(
  puntosVuelo, false, 'centripetal'
);

const curvaCentral = new THREE.CatmullRomCurve3(
  puntosCentrales, false, 'centripetal'
);

const curvaFinal = new THREE.CatmullRomCurve3(
  puntosFinales, false, 'centripetal'
);

function posicionRecorrido(t) {
  const segundos = t * 110;

  if (segundos <= 20) {
    return curvaSumapaz.getPoint(
      THREE.MathUtils.clamp(segundos / 20, 0, 1)
    );
  }

  if (segundos <= 85) {
    return curvaCentral.getPointAt(
      THREE.MathUtils.clamp((segundos - 20) / 65, 0, 1)
    );
  }

  return curvaFinal.getPoint(
    THREE.MathUtils.clamp((segundos - 85) / 25, 0, 1)
  );
}

const destinoMonserrate = new THREE.Vector3(
  18.1629, 0.8606, -35.5212
);

const tiemposRecorrido = [
  0,
  7 / 110,
  14 / 110,
  20 / 110,
  40 / 110,
  60 / 110,
  70 / 110,
  90 / 110,
  1
];

function interpolarTramo(t) {
  for (let i = 0; i < tiemposRecorrido.length - 1; i++) {
    const inicio = tiemposRecorrido[i];
    const fin = tiemposRecorrido[i + 1];

    if (t <= fin) {
      const local = THREE.MathUtils.clamp(
        (t - inicio) / (fin - inicio),
        0,
        1
      );

      const suave = local * local * (3 - 2 * local);

      return (i + suave) / (tiemposRecorrido.length - 1);
    }
  }

  return 1;
}

function actualizarRecorrido(tiempo) {
  if (!recorrido3D.activo || !terreno || !vistaInicial) return;

  if (!recorrido3D.ultimoTiempo) {
    recorrido3D.ultimoTiempo = tiempo;
  }

  const delta = Math.min(
    Math.max(tiempo - recorrido3D.ultimoTiempo, 0),
    100
  );

  recorrido3D.ultimoTiempo = tiempo;

  recorrido3D.progreso = Math.min(
    1,
    recorrido3D.progreso + delta / recorrido3D.duracion
  );

  const t = recorrido3D.progreso;
  const posicion = posicionRecorrido(t);
  camara.position.copy(posicion);

  const siguiente = posicionRecorrido(
    Math.min(1, t + 0.005)
  );

  const objetivo = siguiente.clone();

  if (t > 0.78) {
    const mezcla = THREE.MathUtils.smoothstep(t, 0.78, 0.98);
    objetivo.lerp(destinoMonserrate, mezcla);
  }

  controles.target.copy(objetivo);
  camara.lookAt(objetivo);

  if (recorrido3D.progreso >= 1) {
    recorrido3D.activo = false;
    actualizarBotonesRecorrido();
  }
}
botonReproducir.addEventListener('click', () => {
  if (!terreno || !vistaInicial) return;

  if (recorrido3D.progreso >= 1) recorrido3D.progreso = 0;

  recorrido3D.activo = true;
  recorrido3D.ultimoTiempo = 0;
  actualizarBotonesRecorrido();
});

botonPausar.addEventListener('click', () => {
  recorrido3D.activo = false;
  recorrido3D.ultimoTiempo = 0;
  actualizarBotonesRecorrido();
});

botonReiniciarRecorrido.addEventListener('click', () => {
  recorrido3D.activo = false;
  recorrido3D.progreso = 0;
  recorrido3D.ultimoTiempo = 0;

  if (vistaInicial) {
    camara.position.copy(vistaInicial.posicion);
    controles.target.copy(vistaInicial.objetivo);
    controles.update();
  }

  actualizarBotonesRecorrido();
});

controles.addEventListener('start', () => {
  if (recorrido3D.activo) {
    recorrido3D.activo = false;
    recorrido3D.ultimoTiempo = 0;
    actualizarBotonesRecorrido();
  }
});

actualizarBotonesRecorrido();
document.getElementById('reiniciar').addEventListener('click', () => {
  if (vistaInicial) { camara.position.copy(vistaInicial.posicion); controles.target.copy(vistaInicial.objetivo); controles.update(); }
});
document.querySelectorAll('#vistas button').forEach((boton) => boton.addEventListener('click', () => cambiarVista(boton.dataset.vista)));
addEventListener('resize', () => { camara.aspect = innerWidth / innerHeight; camara.updateProjectionMatrix(); renderizador.setSize(innerWidth, innerHeight); });
iniciar().catch((error) => { console.error(error); estado.textContent = `Error de configuracion: ${error.message}`; });
(function animar() {
  requestAnimationFrame(animar);
  controles.update();
  actualizarRecorrido(performance.now());
  ajustarEtiquetasVias();
  renderizador.render(escena, camara);
}());






