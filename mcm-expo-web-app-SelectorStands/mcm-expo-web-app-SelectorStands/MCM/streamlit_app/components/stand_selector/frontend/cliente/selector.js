(() => {
	const utils = window.selectorStandsUtils;
	const elementos = {
		contenedorPlano: document.getElementById('contenedor-plano'),
		gridCeldas: document.getElementById('grid-celdas'),
		estadoVacio: document.getElementById('estado-vacio'),
		contenedorConfirmar: document.getElementById('contenedor-confirmar'),
		btnConfirmar: document.getElementById('btn-confirmar'),
		botonCargarDiseno: document.getElementById('cargar-diseno'),
		archivoDiseno: document.getElementById('archivo-diseno'),
		resumenArea: document.getElementById('resumen-area'),
		resumenPrecio: document.getElementById('resumen-precio'),
		resumenCoordenadas: document.getElementById('resumen-coordenadas'),
		resumenMensaje: document.getElementById('resumen-mensaje'),
	};

	const estadosValidos = new Set(['disponible', 'ocupado', 'reservado', 'patrocinador']);
	const COSTOS_EXTRA = {
		sillas: 25000,
		mesas: 45000,
		paneles: 60000,
	};
	let planoData = null;
	let mapaCeldas = new Map();
	let mapaStands = new Map();
	let tieneStands = false;
	let controladorPan = null;

	const estado = {
		seleccionConfirmada: null,
		previsualizacion: null,
		interaccion: null,
		resumenMensaje: 'No hay diseño de feria cargado todavía',
	};

	const elementosExtra = {
		imagenReferencia: document.getElementById('imagen-referencia'),
		colReferencia: document.getElementById('col-referencia'),
		modalImagen: document.getElementById('modal-imagen'),
		modalImagenSrc: document.getElementById('modal-imagen-src'),
		modalReserva: document.getElementById('modal-reserva'),
		modalReservaContenido: document.querySelector('#modal-reserva .modal-reserva-contenido'),
	};

	window.planoData = planoData;
	window.calcularRectangulo = utils.calcularRectangulo;
	window.validarSeleccion = validarSeleccion;
	window.obtenerSeleccionActual = obtenerSeleccionActual;
	window.cargarDisenoDesdeJSON = cargarDisenoDesdeJSON;

	inicializar();

	function inicializar() {
		configurarEscena();
		renderizarGrid();
		registrarEventos();
		renderizarEstado();
		cargarDisenoInicial();
	}

	async function cargarDisenoInicial() {
		if (Array.isArray(window.planoData?.stands) && window.planoData.stands.length > 0) {
			cargarDisenoDesdeJSON(window.planoData.stands, window.planoData);
			return;
		}

		if (enComponenteStreamlit()) {
			// Embebido en Streamlit: los datos reales llegan async por
			// selector-streamlit-hook.js (evento streamlit:render). Traer acá
			// el JSON de demo es una condición de carrera — a veces ese fetch
			// termina después y pisa los datos reales de la DB con los del
			// archivo estático (ver enComponenteStreamlit más abajo).
			return;
		}

		await cargarDisenoDesdeEndpoint('./data/stands.json');
	}

	async function cargarDisenoDesdeEndpoint(ruta) {
		mostrarEstadoVacio();

		try {
			const respuesta = await fetch(ruta, { cache: 'no-store' });
			if (!respuesta.ok) {
				throw new Error(`HTTP ${respuesta.status}`);
			}

			const datos = await respuesta.json();
			const stands = Array.isArray(datos) ? datos : datos?.stands;
			if (!Array.isArray(stands)) {
				throw new Error('El archivo no contiene un array de stands');
			}

			cargarDisenoDesdeJSON(stands, datos);
		} catch (error) {
			console.error(`No se pudo cargar el diseño desde ${ruta}`, error);
			establecerPlanoVacio('No hay diseño de feria cargado todavía');
		}
	}

	function cargarDisenoDesdeArchivo(archivo) {
		if (!archivo) {
			return;
		}

		mostrarEstadoVacio(`Leyendo ${archivo.name}...`);
		archivo
			.text()
			.then((contenido) => {
				const datos = JSON.parse(contenido);
				const stands = Array.isArray(datos) ? datos : datos?.stands;
				if (!Array.isArray(stands)) {
					throw new Error('El archivo no contiene un array de stands');
				}

				cargarDisenoDesdeJSON(stands, datos);
			})
			.catch((error) => {
				console.error(`No se pudo leer ${archivo.name}`, error);
				establecerPlanoVacio('No hay diseño de feria cargado todavía');
			});
	}

	function cargarDisenoDesdeJSON(jsonStands, planoFuente = {}) {
		planoFuente.zonas = Array.isArray(planoFuente.zonas) ? planoFuente.zonas : [];
		const standsOriginales = Array.isArray(jsonStands) ? jsonStands : [];
		const standsValidos = [];

		for (const stand of standsOriginales) {
			const estadoStand = typeof stand?.estado === 'string'
				? stand.estado
				: stand?.tipo === 'patrocinador'
					? 'patrocinador'
					: 'disponible';
			if (!estadosValidos.has(estadoStand)) {
				console.error(`Stand inválido omitido por estado no reconocido: ${stand?.id ?? 'sin-id'}`, stand);
				continue;
			}

			const zona = Array.isArray(planoFuente.zonas)
				? planoFuente.zonas.find((item) => item.id === stand?.zonaId)
				: null;
			const color = typeof stand?.color === 'string' && stand.color ? stand.color : zona?.color || '#3b82f6';
			const tipo = estadoStand === 'patrocinador'
				? 'patrocinador'
				: typeof stand?.tipo === 'string' && stand.tipo
					? stand.tipo
					: zona?.tipo || 'venta';

			standsValidos.push({
				...stand,
				color,
				tipo,
				estado: estadoStand,
			});
		}

		const planoBase = {
			imagen: typeof planoFuente.imagenPlano === 'string' ? planoFuente.imagenPlano : '',
			filas: Number(planoFuente.filas ?? 0),
			columnas: Number(planoFuente.columnas ?? 0),
			tamanoCeldaPx: Number(planoFuente.tamanoCeldaPx ?? 34),
		};

		const planoArmado = utils.cargarStandsParaCliente(standsValidos, planoBase);
		const celdasPlano = utils.expandirStandsACeldas(standsValidos);

		planoData = {
			...planoArmado,
			zonas: Array.isArray(planoFuente.zonas) ? planoFuente.zonas.map((zona) => ({ ...zona })) : [],
			celdas: celdasPlano,
			mapaCeldas: utils.crearMapaCeldasDesdeCeldas(celdasPlano),
		};
		mapaCeldas = planoData.mapaCeldas;
		mapaStands = planoData.mapaStands ?? new Map();
		tieneStands = standsValidos.length > 0;
		window.planoData = planoData;

		estado.seleccionConfirmada = null;
		estado.previsualizacion = null;
		estado.interaccion = null;
		estado.resumenMensaje = tieneStands ? 'Diseño cargado' : 'El archivo no contiene stands válidos';

		configurarEscena();
		renderizarGrid();
		asegurarControladorPan(true);
		renderizarEstado();

		// Imagen de referencia en columna derecha
		if (elementosExtra?.imagenReferencia) {
			const imagenPlano = planoFuente.imagenPlano;
			if (imagenPlano) {
				elementosExtra.imagenReferencia.src = imagenPlano;
				elementosExtra.colReferencia?.removeAttribute('aria-hidden');
				elementosExtra.colReferencia.style.display = 'flex';
				elementosExtra.imagenReferencia.style.display = 'block';
				elementosExtra.imagenReferencia.onclick = () => openModalImagen(imagenPlano);
				elementosExtra.imagenReferencia.onerror = () => {
					elementosExtra.imagenReferencia.style.display = 'none';
					elementosExtra.colReferencia?.setAttribute('aria-hidden', 'true');
					elementosExtra.colReferencia.style.display = 'none';
				};
			} else {
				elementosExtra.imagenReferencia.style.display = 'none';
				elementosExtra.colReferencia?.setAttribute('aria-hidden', 'true');
				elementosExtra.colReferencia.style.display = 'none';
			}
		}
	}

	function openModalImagen(url) {
		const modal = document.getElementById('modal-imagen');
		const img = document.getElementById('modal-imagen-src');
		const btnCerrar = document.getElementById('btn-cerrar-modal-imagen');
		const indicador = document.getElementById('indicador-zoom');
		if (!modal || !img) return;
		img.src = url;
		modal.hidden = false;
		document.body.style.overflow = 'hidden';

		let escala = 1;
		let panX = 0;
		let panY = 0;
		let arrastrando = false;
		let inicioX = 0;
		let inicioY = 0;
		let panInicioX = 0;
		let panInicioY = 0;

		const MIN_SCALE = 1;
		const MAX_SCALE = 6;
		const DOBLE_SCALES = [1, 2, 4];

		function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }

		function limitarPan() {
			const cont = modal.querySelector('.modal-contenido');
			if (!cont) return;
			const contW = cont.clientWidth;
			const contH = cont.clientHeight;
			const imgW = img.naturalWidth || img.clientWidth;
			const imgH = img.naturalHeight || img.clientHeight;
			const minPanX = Math.min(0, contW - imgW * escala);
			const minPanY = Math.min(0, contH - imgH * escala);
			panX = clamp(panX, minPanX, 0);
			panY = clamp(panY, minPanY, 0);
		}

		function aplicarTransform() {
			img.style.transform = `translate(${panX}px, ${panY}px) scale(${escala})`;
			if (indicador) indicador.textContent = `${Number(Math.round(escala * 100) / 100)}×`;
			img.classList.toggle('arrastrando', arrastrando === true);
			img.style.cursor = escala > 1 ? (arrastrando ? 'grabbing' : 'grab') : 'zoom-in';
		}

		function centrarImagen() {
			panX = 0;
			panY = 0;
			aplicarTransform();
		}

		function onDblClick() {
			const idx = DOBLE_SCALES.findIndex((v) => Math.abs(v - escala) < 0.001);
			const next = DOBLE_SCALES[(idx + 1) % DOBLE_SCALES.length];
			escala = clamp(next, MIN_SCALE, MAX_SCALE);
			centrarImagen();
		}

		function onWheel(e) {
			e.preventDefault();
			const delta = -e.deltaY;
			const factor = delta > 0 ? 1.08 : 0.92;
			escala = clamp(escala * factor, MIN_SCALE, MAX_SCALE);
			centrarImagen();
		}

		function onMouseDown(e) {
			if (e.button !== 0) return;
			if (escala <= 1) return;
			arrastrando = true;
			inicioX = e.clientX;
			inicioY = e.clientY;
			panInicioX = panX;
			panInicioY = panY;
			aplicarTransform();
			window.addEventListener('mousemove', onMouseMove);
			window.addEventListener('mouseup', onMouseUp);
		}

		function onMouseMove(e) {
			if (!arrastrando) return;
			const dx = e.clientX - inicioX;
			const dy = e.clientY - inicioY;
			panX = panInicioX + dx;
			panY = panInicioY + dy;
			limitarPan();
			aplicarTransform();
		}

		function onMouseUp() {
			if (!arrastrando) return;
			arrastrando = false;
			aplicarTransform();
			window.removeEventListener('mousemove', onMouseMove);
			window.removeEventListener('mouseup', onMouseUp);
		}

		function onCerrarClick() {
			closeModalImagen();
		}

		// attach handlers
		img.addEventListener('dblclick', onDblClick);
		modal.addEventListener('wheel', onWheel, { passive: false });
		img.addEventListener('mousedown', onMouseDown);
		if (btnCerrar) btnCerrar.addEventListener('click', onCerrarClick);

		modal._zoomHandlers = { onDblClick, onWheel, onMouseDown, onMouseMove, onMouseUp, onCerrarClick };

		if (img.complete && img.naturalWidth > 0) {
			requestAnimationFrame(centrarImagen);
		} else {
			img.onload = () => requestAnimationFrame(centrarImagen);
		}
	}

	function closeModalImagen() {
		const modal = document.getElementById('modal-imagen');
		const imgSrc = document.getElementById('modal-imagen-src');
		if (!modal || !imgSrc) return;
		// cleanup handlers
		const h = modal._zoomHandlers || {};
		try {
			if (h.onDblClick) imgSrc.removeEventListener('dblclick', h.onDblClick);
			if (h.onWheel) modal.removeEventListener('wheel', h.onWheel, { passive: false });
			if (h.onMouseDown) imgSrc.removeEventListener('mousedown', h.onMouseDown);
			if (h.onMouseMove) window.removeEventListener('mousemove', h.onMouseMove);
			if (h.onMouseUp) window.removeEventListener('mouseup', h.onMouseUp);
			if (h.onCerrarClick) {
				const btnCerrar = document.getElementById('btn-cerrar-modal-imagen');
				if (btnCerrar) btnCerrar.removeEventListener('click', h.onCerrarClick);
			}
		} catch (err) {
			// ignore
		}

		modal._zoomHandlers = null;
		modal.hidden = true;
		imgSrc.style.transform = '';
		// No limpiamos imgSrc.src para evitar disparar onerror en otros elementos
		document.body.style.overflow = '';
	}

	function abrirModalReserva() {
		const seleccion = estado.seleccionConfirmada;
		const modalReserva = document.getElementById('modal-reserva');
		const modalReservaContenido = document.querySelector('#modal-reserva .modal-reserva-contenido');
		if (!seleccion || !modalReserva || !modalReservaContenido) return;

		const stand = obtenerStandPorId(seleccion.standId);
		if (!stand) return;

		const dotacionBase = calcularDotacionBase(seleccion.areaM2);
		let personalizacion = {
			sillas: dotacionBase.sillas,
			mesas: dotacionBase.mesas,
			paneles: dotacionBase.paneles,
		};

		const pintarModal = () => {
			const costoExtraTotal = calcularCostoExtraTotal(personalizacion, dotacionBase);
			modalReservaContenido.innerHTML = construirContenidoModal(stand, seleccion, personalizacion, dotacionBase, costoExtraTotal);

			const botonCancelar = modalReservaContenido.querySelector('[data-accion="cancelar"]');
			const botonConfirmar = modalReservaContenido.querySelector('[data-accion="confirmar"]');
			const filas = modalReservaContenido.querySelectorAll('[data-rol="fila-personalizacion"]');

			if (botonCancelar) {
				botonCancelar.addEventListener('click', cerrarModalReserva);
			}

			if (botonConfirmar) {
				botonConfirmar.addEventListener('click', async () => {
					if (enComponenteStreamlit()) {
						enviarConfirmacionAStreamlit(stand, seleccion, personalizacion, dotacionBase, costoExtraTotal);
						estado.seleccionConfirmada = null;
						estado.resumenMensaje = 'Reserva enviada';
						renderizarGrid();
						renderizarEstado();
						cerrarModalReserva();
						return;
					}

					const jsonActualizado = await construirJsonReserva(stand, seleccion, personalizacion, dotacionBase, costoExtraTotal);
					await guardarReserva(jsonActualizado);
					aplicarReservaEnMemoria(stand.id, jsonActualizado);
					estado.seleccionConfirmada = null;
					estado.resumenMensaje = 'Reserva confirmada';
					renderizarGrid();
					renderizarEstado();
					cerrarModalReserva();
				});
			}

			for (const fila of filas) {
				const tipo = fila.dataset.tipo;
				const base = dotacionBase[tipo];
				const costoUnitario = COSTOS_EXTRA[tipo];
				const cantidadElemento = fila.querySelector('[data-campo="cantidad"]');
				const costoElemento = fila.querySelector('[data-campo="costo"]');
				const botonMenos = fila.querySelector('[data-accion="menos"]');
				const botonMas = fila.querySelector('[data-accion="mas"]');

				if (cantidadElemento) {
					cantidadElemento.textContent = String(personalizacion[tipo]);
				}

				if (costoElemento) {
					costoElemento.textContent = formatearMoneda((personalizacion[tipo] - base) * costoUnitario);
				}

				if (botonMenos) {
					botonMenos.disabled = personalizacion[tipo] <= base;
					botonMenos.addEventListener('click', () => {
						if (personalizacion[tipo] <= base) return;
						personalizacion = { ...personalizacion, [tipo]: personalizacion[tipo] - 1 };
						pintarModal();
					});
				}

				if (botonMas) {
					botonMas.addEventListener('click', () => {
						personalizacion = { ...personalizacion, [tipo]: personalizacion[tipo] + 1 };
						pintarModal();
					});
				}
			}

			const totalElemento = modalReservaContenido.querySelector('[data-campo="total"]');
			if (totalElemento) {
				const precioBase = Number(stand.precioM2 || 0) * Number(seleccion.areaM2 || 0);
				totalElemento.textContent = formatearMoneda(precioBase + costoExtraTotal);
			}
		};

		pintarModal();
		modalReserva.hidden = false;
	}

	function enComponenteStreamlit() {
		return typeof window.Streamlit !== 'undefined' && window.parent !== window;
	}

	function enviarConfirmacionAStreamlit(stand, seleccion, personalizacion, dotacionBase, costoExtraTotal) {
		const precioBase = Number(stand.precioM2 || 0) * Number(seleccion.areaM2 || 0);

		window.Streamlit.setComponentValue({
			accion: 'confirmar_reserva',
			standId: seleccion.standId,
			areaM2: seleccion.areaM2,
			precioBase,
			personalizacion: {
				sillas: personalizacion.sillas,
				sillaBase: dotacionBase.sillas,
				mesas: personalizacion.mesas,
				mesaBase: dotacionBase.mesas,
				paneles: personalizacion.paneles,
				panelBase: dotacionBase.paneles,
			},
			costoExtra: costoExtraTotal,
			precioTotal: precioBase + costoExtraTotal,
			tomas: calcularTomas(seleccion.areaM2),
		});
	}

	function cerrarModalReserva() {
		const modalReserva = document.getElementById('modal-reserva');
		const modalReservaContenido = document.querySelector('#modal-reserva .modal-reserva-contenido');
		if (!modalReserva || !modalReservaContenido) return;
		modalReserva.hidden = true;
		modalReservaContenido.innerHTML = '';
	}

	function construirContenidoModal(stand, seleccion, personalizacion, dotacionBase, costoExtraTotal) {
		const precioBase = Number(stand.precioM2 || 0) * Number(seleccion.areaM2 || 0);

		return `
			<header class="modal-reserva-cabecera">
				<div>
					<p class="modal-reserva-etiqueta">Confirmación de reserva</p>
					<h2>${formatearEtiquetaStand(stand.id)}</h2>
				</div>
				<button class="boton modal-reserva-cerrar" type="button" data-accion="cancelar">Cancelar</button>
			</header>
			<section class="modal-reserva-resumen">
				<article><span>Número de stand</span><strong>${formatearEtiquetaStand(stand.id)}</strong></article>
				<article><span>Metros cuadrados</span><strong>${seleccion.areaM2} m²</strong></article>
				<article><span>Precio base</span><strong>${formatearMoneda(precioBase)}</strong></article>
				<article><span>Tomas de corriente</span><strong>${calcularTomas(seleccion.areaM2)}</strong></article>
			</section>
			<section class="modal-reserva-lista">
				${construirFilaPersonalizacion('sillas', 'Sillas', '🪑', personalizacion.sillas, dotacionBase.sillas)}
				${construirFilaPersonalizacion('mesas', 'Mesas', '🧰', personalizacion.mesas, dotacionBase.mesas)}
				${construirFilaPersonalizacion('paneles', 'Panelería', '🧱', personalizacion.paneles, dotacionBase.paneles)}
			</section>
			<footer class="modal-reserva-total">
				<div>
					<span>Precio total</span>
					<strong data-campo="total">${formatearMoneda(precioBase + costoExtraTotal)}</strong>
				</div>
				<button class="boton boton--primario" type="button" data-accion="confirmar">Confirmar reserva</button>
			</footer>
		`;
	}

	function construirFilaPersonalizacion(tipo, nombre, icono, cantidad, base) {
		const costoUnitario = COSTOS_EXTRA[tipo];
		return `
			<div class="modal-reserva-fila" data-rol="fila-personalizacion" data-tipo="${tipo}">
				<div class="modal-reserva-fila-etiqueta">
					<span class="modal-reserva-icono">${icono}</span>
					<div>
						<strong>${nombre}</strong>
						<small>${formatearMoneda(costoUnitario)} por unidad adicional</small>
					</div>
				</div>
				<div class="modal-reserva-controles">
					<button class="boton" type="button" data-accion="menos" ${cantidad <= base ? 'disabled' : ''}>−</button>
					<strong data-campo="cantidad">${cantidad}</strong>
					<button class="boton" type="button" data-accion="mas">+</button>
				</div>
				<div class="modal-reserva-costo" data-campo="costo">${formatearMoneda((cantidad - base) * costoUnitario)}</div>
			</div>
		`;
	}

	function calcularTomas(areaM2) {
		if (areaM2 <= 17) return 1;
		if (areaM2 <= 26) return 2;
		return Math.floor(areaM2 / 9);
	}

	function calcularDotacionBase(areaM2) {
		const sillas = areaM2 <= 12 ? 2 : areaM2 <= 18 ? 4 : Math.floor(areaM2 / 4);
		const mesas = areaM2 <= 12 ? 1 : areaM2 <= 18 ? 2 : Math.floor(areaM2 / 9);
		const paneles = areaM2 <= 12 ? 3 : areaM2 <= 18 ? 4 : Math.floor(areaM2 / 5);
		return { sillas, mesas, paneles };
	}

	function formatearMoneda(valor) {
		return new Intl.NumberFormat('es-CO', {
			style: 'currency',
			currency: 'COP',
			maximumFractionDigits: 0,
		}).format(valor);
	}

	function calcularCostoExtraTotal(personalizacion, dotacionBase) {
		return (
			(personalizacion.sillas - dotacionBase.sillas) * COSTOS_EXTRA.sillas +
			(personalizacion.mesas - dotacionBase.mesas) * COSTOS_EXTRA.mesas +
			(personalizacion.paneles - dotacionBase.paneles) * COSTOS_EXTRA.paneles
		);
	}

	async function construirJsonReserva(stand, seleccion, personalizacion, dotacionBase, costoExtraTotal) {
		let jsonActual = null;

		try {
			const respuesta = await fetch('./data/stands.json', { cache: 'no-store' });
			if (respuesta.ok) {
				jsonActual = await respuesta.json();
			}
		} catch (error) {
			console.warn('No se pudo leer ./data/stands.json, usando el estado en memoria', error);
		}

		if (!jsonActual || typeof jsonActual !== 'object' || Array.isArray(jsonActual)) {
			jsonActual = {
				version: '1.0',
				imagenPlano: planoData?.imagen ?? '',
				filas: planoData?.filas ?? 0,
				columnas: planoData?.columnas ?? 0,
				tamanoCeldaPx: planoData?.tamanoCeldaPx ?? 34,
				zonas: Array.isArray(planoData?.zonas) ? planoData.zonas.map((item) => ({ ...item })) : [],
				stands: Array.isArray(planoData?.stands) ? planoData.stands.map((item) => ({ ...item })) : [],
			};
		}

		if (!Array.isArray(jsonActual.zonas)) {
			jsonActual.zonas = Array.isArray(planoData?.zonas) ? planoData.zonas.map((item) => ({ ...item })) : [];
		}

		const stands = Array.isArray(jsonActual.stands) ? jsonActual.stands : [];
		let standActualizado = stands.find((item) => item.id === stand.id);
		if (!standActualizado) {
			standActualizado = { ...stand };
			stands.push(standActualizado);
		}

		const precioBase = Number(stand.precioM2 || 0) * Number(seleccion.areaM2 || 0);
		standActualizado.estado = 'reservado';
		standActualizado.reserva = {
			fechaReserva: new Date().toISOString(),
			areaM2: seleccion.areaM2,
			precioBase,
			personalizacion: {
				sillas: personalizacion.sillas,
				sillaExtra: personalizacion.sillas - dotacionBase.sillas,
				mesas: personalizacion.mesas,
				mesasExtra: personalizacion.mesas - dotacionBase.mesas,
				paneles: personalizacion.paneles,
				panelesExtra: personalizacion.paneles - dotacionBase.paneles,
			},
			costoExtra: costoExtraTotal,
			precioTotal: precioBase + costoExtraTotal,
			tomas: calcularTomas(seleccion.areaM2),
		};

		jsonActual.stands = stands;
		return jsonActual;
	}

	async function guardarReserva(jsonActualizado) {
		// En un backend real, aquí iría un PUT:
		// await fetch('/api/stands', { method: 'PUT', body: JSON.stringify(jsonActualizado) });

		const contenido = JSON.stringify(jsonActualizado, null, 2);
		const blob = new Blob([contenido], { type: 'application/json;charset=utf-8' });
		const url = URL.createObjectURL(blob);
		const enlace = document.createElement('a');
		enlace.href = url;
		enlace.download = 'stands.json';
		enlace.style.display = 'none';
		document.body.appendChild(enlace);
		enlace.click();
		enlace.remove();
		URL.revokeObjectURL(url);
		estado.resumenMensaje = 'Descarga el archivo y reemplaza data/stands.json para que los cambios sean visibles.';
		renderizarEstado();
	}

	function aplicarReservaEnMemoria(standId, jsonActualizado) {
		if (!planoData) {
			return;
		}

		const standsActualizados = Array.isArray(jsonActualizado?.stands) ? jsonActualizado.stands : [];
		const standActualizado = standsActualizados.find((item) => item.id === standId);
		if (!standActualizado) {
			return;
		}

		planoData.stands = standsActualizados.map((item) => ({ ...item }));
		planoData.celdas = utils.expandirStandsACeldas(planoData.stands);
		planoData.mapaCeldas = utils.crearMapaCeldasDesdeCeldas(planoData.celdas);
		planoData.mapaStands = new Map(planoData.stands.map((item) => [item.id, item]));
		mapaCeldas = planoData.mapaCeldas;
		mapaStands = planoData.mapaStands;
		window.planoData = planoData;
	}

	function obtenerStandPorId(standId) {
		return planoData?.stands?.find((s) => s.id === standId) ?? null;
	}

	function establecerPlanoVacio(mensaje) {
		planoData = null;
		mapaCeldas = new Map();
		mapaStands = new Map();
		tieneStands = false;
		window.planoData = null;

		estado.seleccionConfirmada = null;
		estado.previsualizacion = null;
		estado.interaccion = null;
		estado.resumenMensaje = mensaje;

		configurarEscena();
		renderizarGrid();
		renderizarEstado();
	}

	function mostrarEstadoVacio(mensaje) {
		if (!elementos.estadoVacio) {
			return;
		}

		elementos.estadoVacio.hidden = false;
		elementos.estadoVacio.textContent = mensaje;
		elementos.gridCeldas.style.pointerEvents = 'none';
	}

	function ocultarEstadoVacio() {
		if (!elementos.estadoVacio) {
			return;
		}

		elementos.estadoVacio.hidden = true;
		elementos.gridCeldas.style.pointerEvents = 'auto';
	}

	function configurarEscena() {
		if (!planoData || !tieneStands) {
			elementos.gridCeldas.style.width = '100%';
			elementos.gridCeldas.style.height = '100%';
			elementos.gridCeldas.style.position = 'absolute';
			elementos.gridCeldas.style.top = '0';
			elementos.gridCeldas.style.left = '0';
			elementos.gridCeldas.style.gridTemplateColumns = '1fr';
			elementos.gridCeldas.style.gridTemplateRows = '1fr';
			elementos.contenedorPlano.style.backgroundImage = 'linear-gradient(rgba(7, 12, 18, 0.28), rgba(7, 12, 18, 0.28)), linear-gradient(135deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.01))';
			return;
		}

		const ancho = planoData.columnas * planoData.tamanoCeldaPx;
		const alto = planoData.filas * planoData.tamanoCeldaPx;

		elementos.gridCeldas.style.width = `${ancho}px`;
		elementos.gridCeldas.style.height = `${alto}px`;
		elementos.gridCeldas.style.position = 'absolute';
		elementos.gridCeldas.style.top = '0';
		elementos.gridCeldas.style.left = '0';
		elementos.gridCeldas.style.gridTemplateColumns = `repeat(${planoData.columnas}, ${planoData.tamanoCeldaPx}px)`;
		elementos.gridCeldas.style.gridTemplateRows = `repeat(${planoData.filas}, ${planoData.tamanoCeldaPx}px)`;
		elementos.contenedorPlano.style.backgroundImage = 'linear-gradient(rgba(7, 12, 18, 0.28), rgba(7, 12, 18, 0.28)), linear-gradient(135deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.01))';

	}

	function registrarEventos() {
		elementos.gridCeldas.addEventListener('click', manejarClickStand);

		if (elementos.btnConfirmar) {
			elementos.btnConfirmar.addEventListener('click', abrirModalReserva);
		}

		if (elementosExtra.modalReserva) {
			elementosExtra.modalReserva.addEventListener('click', (evento) => {
				if (evento.target === elementosExtra.modalReserva) {
					cerrarModalReserva();
				}
			});
		}

		const modalImagen = document.getElementById('modal-imagen');
		if (modalImagen) {
			modalImagen.addEventListener('click', closeModalImagen);
		}
		document.addEventListener('keydown', (evt) => {
			if (evt.key === 'Escape') {
				cerrarModalReserva();
				closeModalImagen();
			}
		});
	}

	function renderizarGrid() {
		elementos.gridCeldas.innerHTML = '';

		if (!tieneStands) {
			mostrarEstadoVacio(estado.resumenMensaje || 'No hay diseño de feria cargado todavía');
			actualizarVista();
			asegurarControladorPan(false);
			return;
		}

		ocultarEstadoVacio();
		renderizarStandsCliente();
		actualizarVista();
		asegurarControladorPan(false);
	}

	function asegurarControladorPan(centrar = false) {
		if (!controladorPan) {
			controladorPan = utils.iniciarPan(elementos.contenedorPlano, elementos.gridCeldas);
		}

		if (centrar) {
			controladorPan.centrar();
		}
	}

	function renderizarStandsCliente() {
		for (const stand of planoData.stands) {
			const wrapper = document.createElement('div');
			wrapper.className = 'stand-visual stand-cliente';
			wrapper.dataset.standId = stand.id;
			wrapper.dataset.zonaId = stand.zonaId || '';
			wrapper.style.position = 'absolute';
			wrapper.style.left = `${stand.columnaInicio * planoData.tamanoCeldaPx}px`;
			wrapper.style.top = `${stand.filaInicio * planoData.tamanoCeldaPx}px`;
			wrapper.style.width = `${(stand.columnaFin - stand.columnaInicio + 1) * planoData.tamanoCeldaPx}px`;
			wrapper.style.height = `${(stand.filaFin - stand.filaInicio + 1) * planoData.tamanoCeldaPx}px`;
			wrapper.style.zIndex = '1';
			wrapper.dataset.estado = stand.estado;

			const miniGrid = document.createElement('div');
			miniGrid.className = 'mini-grid-stand';
			miniGrid.style.gridTemplateColumns = `repeat(${stand.columnaFin - stand.columnaInicio + 1}, 1fr)`;
			miniGrid.style.gridTemplateRows = `repeat(${stand.filaFin - stand.filaInicio + 1}, 1fr)`;

			for (let fila = stand.filaInicio; fila <= stand.filaFin; fila += 1) {
				for (let columna = stand.columnaInicio; columna <= stand.columnaFin; columna += 1) {
					const celda = obtenerCeldaReal(fila, columna);
					const elementoCelda = document.createElement('div');
					elementoCelda.className = `celda celda--${celda.estado}`;
					elementoCelda.dataset.fila = String(fila);
					elementoCelda.dataset.columna = String(columna);
					elementoCelda.dataset.standId = stand.id;
					elementoCelda.title = `Fila ${fila}, columna ${columna} · ${celda.estado} · $${celda.precio}`;
					miniGrid.appendChild(elementoCelda);
				}
			}

			const etiqueta = document.createElement('div');
			etiqueta.className = 'etiqueta-stand etiqueta-stand--principal';
			etiqueta.textContent = formatearEtiquetaStand(stand.id);

			if (stand.tipo === 'patrocinador') {
				const etiquetaPatrocinador = document.createElement('span');
				etiquetaPatrocinador.className = 'etiqueta-stand etiqueta-stand--patrocinador';
				etiquetaPatrocinador.textContent = '⭐ Patrocinador';
				etiquetaPatrocinador.style.zIndex = '3';
				wrapper.appendChild(etiquetaPatrocinador);
			}

			wrapper.appendChild(miniGrid);
			wrapper.appendChild(etiqueta);
			elementos.gridCeldas.appendChild(wrapper);
		}
	}

	function renderizarCeldasLegado() {
		for (let fila = 0; fila < planoData.filas; fila += 1) {
			for (let columna = 0; columna < planoData.columnas; columna += 1) {
				const celda = obtenerCeldaReal(fila, columna);
				const elementoCelda = document.createElement('div');
				elementoCelda.className = `celda celda--${celda.estado}`;
				elementoCelda.dataset.fila = String(fila);
				elementoCelda.dataset.columna = String(columna);
				elementoCelda.title = `Fila ${fila}, columna ${columna} · ${celda.estado} · $${celda.precio}`;
				elementos.gridCeldas.appendChild(elementoCelda);
			}
		}
	}

	function manejarClickStand(evento) {
		if (!tieneStands) return;

		const wrapper = evento.target?.closest('.stand-cliente');
		if (!wrapper || !elementos.gridCeldas.contains(wrapper)) return;

		const standId = wrapper.dataset.standId;
		if (!standId) return;

		const stand = mapaStands.get(standId);
		if (!stand || stand.estado !== 'disponible') return;

		if (estado.seleccionConfirmada?.standId === stand.id) {
			estado.seleccionConfirmada = null;
			estado.resumenMensaje = 'Selección cancelada';
		} else {
			const celdas = utils.expandirStandsACeldas([stand]).map((c) => ({ fila: c.fila, columna: c.columna }));
			estado.seleccionConfirmada = {
				standId: stand.id,
				celdas,
				areaM2: celdas.length,
				precioTotal: stand.precioM2 * celdas.length,
				limites: {
					filaInicio: stand.filaInicio,
					filaFin: stand.filaFin,
					columnaInicio: stand.columnaInicio,
					columnaFin: stand.columnaFin,
				},
			};
			estado.resumenMensaje = 'Stand seleccionado';
		}

		actualizarVista();
		renderizarEstado();
	}

	function seleccionarStandPorDefecto(stand, celdaReferencia) {
		const rectangulo = construirRectanguloDefecto(stand, celdaReferencia) ?? buscarRectanguloMinimoDisponible(stand);
		if (!rectangulo) {
			estado.resumenMensaje = 'Stand sin bloque disponible de 3 x 3';
			renderizarGrid();
			renderizarEstado();
			return false;
		}

		estado.seleccionConfirmada = construirSeleccion(rectangulo, stand.id);
		estado.resumenMensaje = 'Selección base 3 x 3 aplicada';
		renderizarGrid();
		renderizarEstado();
		return true;
	}

	function construirRectanguloDefecto(stand, celdaReferencia) {
		const limiteFilaInicio = stand.filaInicio;
		const limiteFilaFin = stand.filaFin;
		const limiteColumnaInicio = stand.columnaInicio;
		const limiteColumnaFin = stand.columnaFin;

		const filaInicio = utils.limitar(celdaReferencia.fila - 1, limiteFilaInicio, limiteFilaFin - 2);
		const columnaInicio = utils.limitar(celdaReferencia.columna - 1, limiteColumnaInicio, limiteColumnaFin - 2);

		const rectangulo = utils.calcularRectangulo(
			{ fila: filaInicio, columna: columnaInicio },
			{ fila: filaInicio + 2, columna: columnaInicio + 2 },
			{
				limitesMaximos: {
					filaInicio: stand.filaInicio,
					filaFin: stand.filaFin,
					columnaInicio: stand.columnaInicio,
					columnaFin: stand.columnaFin,
				},
			},
		);

		if (!utils.validarTamanoMinimo(rectangulo, 3, 3)) {
			return null;
		}

		if (!validarSeleccion(rectangulo, stand.id)) {
			return null;
		}

		return rectangulo;
	}

	function buscarRectanguloMinimoDisponible(stand) {
		for (let fila = stand.filaInicio; fila <= stand.filaFin - 2; fila += 1) {
			for (let columna = stand.columnaInicio; columna <= stand.columnaFin - 2; columna += 1) {
				const rectangulo = utils.calcularRectangulo(
					{ fila, columna },
					{ fila: fila + 2, columna: columna + 2 },
					{
						limitesMaximos: {
							filaInicio: stand.filaInicio,
							filaFin: stand.filaFin,
							columnaInicio: stand.columnaInicio,
							columnaFin: stand.columnaFin,
						},
					},
				);

				if (utils.validarTamanoMinimo(rectangulo, 3, 3) && validarSeleccion(rectangulo, stand.id)) {
					return rectangulo;
				}
			}
		}

		return null;
	}

	function manejarMouseMove(evento) {
		if (!estado.interaccion) {
			return;
		}

		actualizarPrevisualizacion(obtenerCeldaDesdeEvento(evento));
	}

	function manejarMouseUp() {
		if (!estado.interaccion) {
			return;
		}

		confirmarOCancelarSeleccion();
	}

	function manejarMouseLeave(evento) {
		if (!estado.interaccion) {
			return;
		}

		if (evento.relatedTarget && elementos.contenedorPlano.contains(evento.relatedTarget)) {
			return;
		}

		confirmarOCancelarSeleccion();
	}

	function iniciarNuevaSeleccion(standId, puntoFijo) {
		estado.interaccion = {
			tipo: 'nueva',
			standId,
			puntoFijo,
			limitesMaximos: obtenerLimitesSeleccion(standId),
		};
	}

	function iniciarRedimension(standId, tipoRedimension) {
		const seleccionActual = estado.seleccionConfirmada;
		const limitesMaximos = obtenerLimitesSeleccion(standId ?? seleccionActual?.standId);
		const limitesSeleccion = seleccionActual ? calcularLimites(seleccionActual.celdas) : null;
		const puntoFijo = obtenerPuntoFijoParaRedimension(tipoRedimension, limitesSeleccion);

		estado.interaccion = {
			tipo: 'redimensionar',
			standId: standId ?? seleccionActual?.standId ?? null,
			tipoRedimension,
			puntoFijo,
			limitesMaximos,
		};
	}

	function obtenerPuntoFijoParaRedimension(tipoRedimension, limites) {
		if (!limites) {
			return null;
		}

		switch (tipoRedimension) {
			case 'superior-izquierda':
				return { fila: limites.filaFin, columna: limites.columnaFin };
			case 'superior-derecha':
				return { fila: limites.filaFin, columna: limites.columnaInicio };
			case 'inferior-izquierda':
				return { fila: limites.filaInicio, columna: limites.columnaFin };
			case 'inferior-derecha':
				return { fila: limites.filaInicio, columna: limites.columnaInicio };
			case 'superior':
				return { fila: limites.filaFin, columna: limites.columnaInicio };
			case 'inferior':
				return { fila: limites.filaInicio, columna: limites.columnaInicio };
			case 'izquierdo':
				return { fila: limites.filaInicio, columna: limites.columnaFin };
			case 'derecho':
				return { fila: limites.filaInicio, columna: limites.columnaInicio };
			default:
				return { fila: limites.filaInicio, columna: limites.columnaInicio };
		}
	}

	function obtenerLimitesSeleccion(standId) {
		if (!tieneStands || !standId) {
			return null;
		}

		const stand = mapaStands.get(standId);
		if (!stand) {
			return null;
		}

		return {
			filaInicio: stand.filaInicio,
			filaFin: stand.filaFin,
			columnaInicio: stand.columnaInicio,
			columnaFin: stand.columnaFin,
		};
	}

	function actualizarPrevisualizacion(celdaActual) {
		if (!estado.interaccion || !celdaActual) {
			return;
		}

		const limitesMaximos = estado.interaccion.limitesMaximos ?? null;
		const rectangulo = utils.calcularRectangulo(estado.interaccion.puntoFijo, celdaActual, { limitesMaximos });
		const minValido = utils.validarTamanoMinimo(rectangulo, 3, 3);
		const disponible = validarSeleccion(rectangulo, estado.interaccion.standId);
		const valida = minValido && disponible;
		const motivo = !minValido ? 'Mínimo 3 x 3' : disponible ? '' : 'No disponible';

		estado.previsualizacion = {
			rectangulo,
			valida,
			motivo,
		};

		renderizarGrid();
		renderizarEstado();
	}

	function confirmarOCancelarSeleccion() {
		const previsualizacion = estado.previsualizacion;

		if (!previsualizacion) {
			estado.interaccion = null;
			renderizarEstado();
			return;
		}

		if (previsualizacion.valida) {
			estado.seleccionConfirmada = construirSeleccion(previsualizacion.rectangulo, estado.interaccion.standId);
			estado.resumenMensaje = 'Selección confirmada';
		} else {
			estado.resumenMensaje = previsualizacion.motivo || 'Selección cancelada';
		}

		estado.interaccion = null;
		estado.previsualizacion = null;
		renderizarGrid();
		renderizarEstado();
	}

	function construirSeleccion(rectangulo, standId) {
		const seleccionCeldas = rectangulo.celdas.map((celda) => ({ fila: celda.fila, columna: celda.columna }));
		const precioTotal = calcularPrecioSeleccion(standId, seleccionCeldas.length);

		return {
			standId,
			celdas: seleccionCeldas,
			areaM2: seleccionCeldas.length,
			precioTotal,
			limites: {
				filaInicio: rectangulo.filaInicio,
				filaFin: rectangulo.filaFin,
				columnaInicio: rectangulo.columnaInicio,
				columnaFin: rectangulo.columnaFin,
			},
		};
	}

	function calcularLimites(celdas) {
		const filas = celdas.map((celda) => celda.fila);
		const columnas = celdas.map((celda) => celda.columna);

		return {
			filaInicio: Math.min(...filas),
			filaFin: Math.max(...filas),
			columnaInicio: Math.min(...columnas),
			columnaFin: Math.max(...columnas),
		};
	}

	function detectarRedimension(seleccionActual, celda) {
		if (!seleccionActual) {
			return null;
		}

		const limites = seleccionActual.limites;
		if (!limites) {
			return null;
		}

		const dentro =
			celda.fila >= limites.filaInicio &&
			celda.fila <= limites.filaFin &&
			celda.columna >= limites.columnaInicio &&
			celda.columna <= limites.columnaFin;

		if (!dentro) {
			return null;
		}

		const esSuperior = celda.fila === limites.filaInicio;
		const esInferior = celda.fila === limites.filaFin;
		const esIzquierdo = celda.columna === limites.columnaInicio;
		const esDerecho = celda.columna === limites.columnaFin;

		if (esSuperior && esIzquierdo) return 'superior-izquierda';
		if (esSuperior && esDerecho) return 'superior-derecha';
		if (esInferior && esIzquierdo) return 'inferior-izquierda';
		if (esInferior && esDerecho) return 'inferior-derecha';
		if (esSuperior) return 'superior';
		if (esInferior) return 'inferior';
		if (esIzquierdo) return 'izquierdo';
		if (esDerecho) return 'derecho';

		return null;
	}

	function obtenerCeldaDesdeEvento(evento) {
		if (!planoData || !tieneStands) {
			return null;
		}

		const rectangulo = elementos.contenedorPlano.getBoundingClientRect();
		if (!rectangulo.width || !rectangulo.height) {
			return null;
		}

		const x = utils.limitar(evento.clientX - rectangulo.left, 0, rectangulo.width - 0.001);
		const y = utils.limitar(evento.clientY - rectangulo.top, 0, rectangulo.height - 0.001);

		return {
			fila: utils.limitar(Math.floor(y / planoData.tamanoCeldaPx), 0, planoData.filas - 1),
			columna: utils.limitar(Math.floor(x / planoData.tamanoCeldaPx), 0, planoData.columnas - 1),
		};
	}

	function obtenerStandPorCelda(fila, columna) {
		if (!tieneStands) {
			return null;
		}

		return planoData.stands.find((stand) => (
			fila >= stand.filaInicio &&
			fila <= stand.filaFin &&
			columna >= stand.columnaInicio &&
			columna <= stand.columnaFin
		));
	}

	function obtenerCeldaReal(fila, columna) {
		if (!tieneStands) {
			return {
				fila,
				columna,
				estado: 'disponible',
				precio: 0,
				standId: null,
			};
		}

		return mapaCeldas.get(utils.claveCelda(fila, columna)) ?? {
			fila,
			columna,
			estado: 'disponible',
			precio: 0,
			standId: null,
		};
	}

	function validarSeleccion(rectangulo, standId = null) {
		return rectangulo.celdas.every((celda) => {
			const real = obtenerCeldaReal(celda.fila, celda.columna);
			if (!real || real.estado !== 'disponible') {
				return false;
			}

			if (standId && real.standId !== standId) {
				return false;
			}

			return true;
		});
	}

	function actualizarVista() {
		if (!tieneStands) {
			return;
		}

		const seleccion = estado.previsualizacion ?? estado.seleccionConfirmada;
		const celdasSeleccionadas = new Set((estado.seleccionConfirmada?.celdas ?? []).map((celda) => utils.claveCelda(celda.fila, celda.columna)));
		const celdasPrevisualizadas = new Set((estado.previsualizacion?.rectangulo?.celdas ?? []).map((celda) => utils.claveCelda(celda.fila, celda.columna)));

		for (const stand of planoData.stands) {
			const wrapper = elementos.gridCeldas.querySelector(`[data-stand-id="${stand.id}"]`);
			if (!wrapper) {
				continue;
			}

			const rectSeleccion = estado.seleccionConfirmada?.standId === stand.id ? estado.seleccionConfirmada.limites : null;
			const rectPrevisualizacion = estado.previsualizacion && estado.interaccion?.standId === stand.id ? estado.previsualizacion.rectangulo : null;
			const esSeleccionado = estado.seleccionConfirmada?.standId === stand.id;

			wrapper.className = `stand-visual stand-cliente stand-visual--${stand.estado}`;
			wrapper.dataset.standId = stand.id;
			wrapper.dataset.estado = stand.estado;
			wrapper.style.position = 'absolute';
			wrapper.style.left = `${stand.columnaInicio * planoData.tamanoCeldaPx}px`;
			wrapper.style.top = `${stand.filaInicio * planoData.tamanoCeldaPx}px`;
			wrapper.style.width = `${(stand.columnaFin - stand.columnaInicio + 1) * planoData.tamanoCeldaPx}px`;
			wrapper.style.height = `${(stand.filaFin - stand.filaInicio + 1) * planoData.tamanoCeldaPx}px`;
			wrapper.style.zIndex = esSeleccionado ? '2' : '1';
			wrapper.style.pointerEvents = stand.estado === 'disponible' ? 'auto' : 'none';
			wrapper.style.borderColor = '';
			wrapper.style.backgroundColor = '';

			if (esSeleccionado) {
				wrapper.classList.add('stand-visual--seleccionado');
			} else if (stand.estado === 'patrocinador' || stand.tipo === 'patrocinador') {
				wrapper.classList.add('stand-visual--patrocinador');
			} else if (stand.estado === 'ocupado') {
				wrapper.classList.add('stand-visual--ocupado');
			} else if (stand.estado === 'reservado') {
				wrapper.classList.add('stand-visual--reservado');
			} else if (stand.estado === 'disponible' && stand.color) {
				wrapper.style.borderColor = stand.color;
				wrapper.style.backgroundColor = utils.hexARgba(stand.color, 0.18);
			}

			const celdas = wrapper.querySelectorAll('.celda');
			for (const celdaElemento of celdas) {
				const fila = Number(celdaElemento.dataset.fila);
				const columna = Number(celdaElemento.dataset.columna);
				const clave = utils.claveCelda(fila, columna);
				const celda = obtenerCeldaReal(fila, columna);

				celdaElemento.className = `celda celda--${celda.estado}`;
				celdaElemento.title = `Fila ${fila}, columna ${columna} · ${celda.estado} · $${celda.precio}`;

				if (celdasPrevisualizadas.has(clave)) {
					celdaElemento.classList.add(estado.previsualizacion?.valida ? 'celda--previsualizada' : 'celda--previsualizada-invalida');
				} else if (celdasSeleccionadas.has(clave)) {
					celdaElemento.classList.add('celda--seleccionado');
				}
			}

			const etiqueta = wrapper.querySelector('.etiqueta-stand--principal');
			if (etiqueta && rectSeleccion) {
				etiqueta.textContent = `Stand ${stand.id.split('-')[1] ?? stand.id}`;
			}

			if (stand.tipo === 'patrocinador' && !wrapper.querySelector('.etiqueta-stand--patrocinador')) {
				const etiquetaPatrocinador = document.createElement('span');
				etiquetaPatrocinador.className = 'etiqueta-stand etiqueta-stand--patrocinador';
				etiquetaPatrocinador.textContent = '⭐ Patrocinador';
				etiquetaPatrocinador.style.zIndex = '3';
				wrapper.appendChild(etiquetaPatrocinador);
			}

			if (rectPrevisualizacion) {
				wrapper.classList.add(estado.previsualizacion.valida ? 'stand-visual--previsualizacion-valida' : 'stand-visual--previsualizacion-invalida');
			} else if (esSeleccionado) {
				wrapper.classList.add('stand-visual--seleccionado');
			}
		}
	}

	function renderizarEstado() {
		const seleccion = estado.previsualizacion
			? {
				celdas: estado.previsualizacion.rectangulo.celdas,
				areaM2: estado.previsualizacion.rectangulo.celdas.length,
				precioTotal: calcularPrecioSeleccion(estado.interaccion?.standId, estado.previsualizacion.rectangulo.celdas.length),
				limites: estado.previsualizacion.rectangulo,
			}
			: estado.seleccionConfirmada;

		if (elementos.contenedorConfirmar) {
			elementos.contenedorConfirmar.style.display = estado.seleccionConfirmada ? 'block' : 'none';
		}

		if (!seleccion) {
			elementos.resumenArea.textContent = '0';
			elementos.resumenPrecio.textContent = '$0';
			elementos.resumenCoordenadas.textContent = 'Sin selección';
			elementos.resumenMensaje.textContent = estado.resumenMensaje;
			return;
		}

		const limites = seleccion.limites;
		elementos.resumenArea.textContent = String(seleccion.areaM2);
		elementos.resumenPrecio.textContent = `$${formatearNumero(seleccion.precioTotal)}`;
		elementos.resumenCoordenadas.textContent = `(${limites.filaInicio}, ${limites.columnaInicio}) → (${limites.filaFin}, ${limites.columnaFin})`;
		elementos.resumenMensaje.textContent = estado.previsualizacion
			? estado.previsualizacion.valida
				? 'Previsualización válida'
				: estado.previsualizacion.motivo
			: estado.resumenMensaje;
	}

	function obtenerSeleccionActual() {
		if (!estado.seleccionConfirmada) {
			return { celdas: [], areaM2: 0, precioTotal: 0, standId: null };
		}

		return {
			celdas: estado.seleccionConfirmada.celdas.map((celda) => ({ ...celda })),
			areaM2: estado.seleccionConfirmada.areaM2,
			precioTotal: estado.seleccionConfirmada.precioTotal,
			standId: estado.seleccionConfirmada.standId,
		};
	}

	function calcularPrecioSeleccion(standId, cantidadCeldas) {
		const stand = mapaStands.get(standId);
		const precioM2 = Number(stand?.precioM2 ?? 0);
		return cantidadCeldas * precioM2;
	}

	function formatearNumero(valor) {
		return new Intl.NumberFormat('es-ES').format(valor);
	}

	function formatearEtiquetaStand(id) {
		const sufijo = id.split('-')[1] ?? id;
		return `Stand ${sufijo}`;
	}
})();