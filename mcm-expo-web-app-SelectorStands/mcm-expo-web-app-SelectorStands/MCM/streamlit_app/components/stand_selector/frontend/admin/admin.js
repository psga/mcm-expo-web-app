(() => {
	const utils = window.selectorStandsUtils;
	const elementos = {
		contenedorPlano: document.getElementById('contenedor-plano'),
		gridCeldas: document.getElementById('grid-celdas'),
		zonaNombre: document.getElementById('zona-nombre'),
		zonaColor: document.getElementById('zona-color'),
		zonaPrecio: document.getElementById('zona-precio'),
		zonaTipo: document.getElementById('zona-tipo'),
		btnCrearZona: document.getElementById('btn-crear-zona'),
		zonaError: document.getElementById('zona-error'),
		listaZonas: document.getElementById('lista-zonas'),
		zonaActiva: document.getElementById('zona-activa'),
		avisoZonaActiva: document.getElementById('aviso-zona-activa'),
		archivoPlano: document.getElementById('archivo-plano'),
		importarDiseno: document.getElementById('importar-diseno'),
		archivoDiseno: document.getElementById('archivo-diseno'),
		filasGrid: document.getElementById('filas-grid'),
		columnasGrid: document.getElementById('columnas-grid'),
		aplicarDimensiones: document.getElementById('aplicar-dimensiones'),
		standSeleccionado: document.getElementById('stand-seleccionado'),
		aplicarPrecio: document.getElementById('aplicar-precio'),
		eliminarStand: document.getElementById('eliminar-stand'),
		guardarDiseno: document.getElementById('guardar-diseno'),
		indicadorCambios: document.getElementById('indicador-cambios'),
		resumenZona: document.getElementById('resumen-zona-admin'),
		resumenStand: document.getElementById('resumen-stand-admin'),
		resumenEstado: document.getElementById('resumen-estado-admin'),
	};

	const TAMANO_CELDA_PX = 34;
	let controladorPan = null;
	let zonas = [];
	let zonaActivaId = null;
	let imagenBase64 = null;
	let lecturaImagenPendiente = false;

	const planoBase = {
		imagenPlano: '', // filename only
		filas: Number(elementos.filasGrid.value || 20),
		columnas: Number(elementos.columnasGrid.value || 30),
		tamanoCeldaPx: TAMANO_CELDA_PX,
	};

	const estado = {
		stands: [],
		precioActual: 0,
		interaccion: null,
		previsualizacion: null,
		standSeleccionadoId: null,
		siguienteIndice: 1,
		disenoModificado: false,
	};

	window.obtenerDisenoAdmin = obtenerDisenoAdmin;
	window.cargarDisenoImportado = cargarDisenoImportado;

	inicializar();

	function inicializar() {
		configurarEscena();
		renderizarListaZonas();
		actualizarDropdownZonas();
		renderizarGrid();
		asegurarControladorPan(true);
		registrarEventos();
		marcarDisenoSinCambios();
		actualizarResumen();
	}

	function configurarEscena() {
		const ancho = planoBase.columnas * planoBase.tamanoCeldaPx;
		const alto = planoBase.filas * planoBase.tamanoCeldaPx;

		elementos.gridCeldas.style.width = `${ancho}px`;
		elementos.gridCeldas.style.height = `${alto}px`;
		elementos.gridCeldas.style.position = 'absolute';
		elementos.gridCeldas.style.top = '0';
		elementos.gridCeldas.style.left = '0';
		elementos.gridCeldas.style.gridTemplateColumns = `repeat(${planoBase.columnas}, ${planoBase.tamanoCeldaPx}px)`;
		elementos.gridCeldas.style.gridTemplateRows = `repeat(${planoBase.filas}, ${planoBase.tamanoCeldaPx}px)`;
		elementos.contenedorPlano.style.backgroundImage = 'linear-gradient(rgba(7, 12, 18, 0.28), rgba(7, 12, 18, 0.28)), linear-gradient(135deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.01))';
		// Background image for admin is set when an image file is selected (object URL)
	}

	function registrarEventos() {
		elementos.gridCeldas.addEventListener('mousedown', manejarMouseDown);
		document.addEventListener('mousemove', manejarMouseMove);
		document.addEventListener('mouseup', manejarMouseUp);
		elementos.aplicarPrecio.addEventListener('click', aplicarPrecioAlStandSeleccionado);
		elementos.eliminarStand.addEventListener('click', eliminarStandSeleccionado);
		elementos.guardarDiseno.addEventListener('click', guardarDiseno);
		if (elementos.btnCrearZona) {
			elementos.btnCrearZona.addEventListener('click', crearZona);
		}
		if (elementos.zonaActiva) {
			elementos.zonaActiva.addEventListener('change', manejarCambioZonaActiva);
		}
		for (const campo of [elementos.zonaNombre, elementos.zonaColor, elementos.zonaPrecio, elementos.zonaTipo]) {
			campo?.addEventListener('input', limpiarErrorZona);
			campo?.addEventListener('change', limpiarErrorZona);
		}
		if (elementos.importarDiseno) {
			elementos.importarDiseno.addEventListener('click', abrirSelectorImportacion);
		}
		if (elementos.archivoDiseno) {
			elementos.archivoDiseno.addEventListener('change', manejarImportacionDiseno);
		}
		if (elementos.archivoPlano) {
			elementos.archivoPlano.addEventListener('change', manejarArchivoPlano);
		}

		if (elementos.aplicarDimensiones) {
			elementos.aplicarDimensiones.addEventListener('click', aplicarDimensiones);
		}
	}

	function manejarArchivoPlano(evento) {
		const archivo = evento.target.files?.[0] ?? null;
		if (!archivo) return;

		lecturaImagenPendiente = true;
		elementos.guardarDiseno.disabled = true;
		imagenBase64 = null;
		aplicarImagenFondoPlano(URL.createObjectURL(archivo));
		elementos.resumenEstado.textContent = `Plano cargado: ${archivo.name}`;

		const lector = new FileReader();
		lector.onload = (ev) => {
			imagenBase64 = ev.target?.result ?? null;
			lecturaImagenPendiente = false;
			elementos.guardarDiseno.disabled = false;
		};
		lector.onerror = () => {
			imagenBase64 = null;
			lecturaImagenPendiente = false;
			elementos.guardarDiseno.disabled = false;
			elementos.resumenEstado.textContent = 'No se pudo leer la imagen del plano';
		};
		lector.readAsDataURL(archivo);
	}

	function abrirSelectorImportacion() {
		if (elementos.archivoDiseno) {
			elementos.archivoDiseno.value = '';
			elementos.archivoDiseno.click();
		}
	}

	function manejarImportacionDiseno(evento) {
		const archivo = evento.target.files?.[0] ?? null;
		if (!archivo) {
			return;
		}

		const lector = new FileReader();
		lector.onload = () => {
			try {
				const datos = JSON.parse(String(lector.result || '{}'));
				const errores = validarDisenoImportado(datos);
				if (errores.length > 0) {
					alert(`No se pudo importar el diseño:\n- ${errores.join('\n- ')}`);
					return;
				}

				if (estado.stands.length > 0) {
					const reemplazar = window.confirm('Ya hay stands en el editor. ¿Desea reemplazar el diseño actual?');
					if (!reemplazar) {
						return;
					}
				}

				cargarDisenoImportado(datos);
			} catch (error) {
				console.error('No se pudo importar el diseño', error);
				alert('No se pudo importar el diseño: el archivo no contiene JSON válido.');
			}
		};
		lector.onerror = () => {
			alert('No se pudo leer el archivo seleccionado.');
		};
		lector.readAsText(archivo);
	}

	function validarDisenoImportado(datos) {
		const errores = [];
		if (!datos || typeof datos !== 'object' || Array.isArray(datos)) {
			errores.push('El archivo debe contener un objeto JSON.');
			return errores;
		}

		if (!Array.isArray(datos.stands)) {
			errores.push('Debe tener "stands" como array.');
		}

		if (typeof datos.filas !== 'number' || Number.isNaN(datos.filas)) {
			errores.push('Debe tener "filas" como número.');
		}

		if (typeof datos.columnas !== 'number' || Number.isNaN(datos.columnas)) {
			errores.push('Debe tener "columnas" como número.');
		}

		return errores;
	}

	function cargarDisenoImportado(datos) {
		zonas = normalizarZonasImportadas(Array.isArray(datos.zonas) ? datos.zonas : []);
		const zonaPorId = new Map(zonas.map((zona) => [zona.id, zona]));
		const standsImportados = datos.stands.map((stand) => {
			const zona = zonaPorId.get(stand.zonaId);
			const tipo = stand.estado === 'patrocinador'
				? 'patrocinador'
				: normalizarTipoZona(stand.tipo ?? zona?.tipo);
			const color = typeof stand.color === 'string' && stand.color ? stand.color : zona?.color || '#3b82f6';
			const precioM2 = Number(stand.precioM2 ?? zona?.precioM2 ?? estado.precioActual);
			const estadoStand = typeof stand.estado === 'string'
				? stand.estado
				: tipo === 'patrocinador'
					? 'patrocinador'
					: 'disponible';

			return {
				id: stand.id,
				zonaId: stand.zonaId ?? zona?.id ?? null,
				filaInicio: Number(stand.filaInicio),
				columnaInicio: Number(stand.columnaInicio),
				filaFin: Number(stand.filaFin),
				columnaFin: Number(stand.columnaFin),
				precioM2,
				color,
				tipo,
				estado: estadoStand,
			};
		});

		planoBase.filas = Number(datos.filas);
		planoBase.columnas = Number(datos.columnas);
		imagenBase64 = typeof datos.imagenPlano === 'string' && datos.imagenPlano ? datos.imagenPlano : null;
		estado.stands = standsImportados;
		estado.standSeleccionadoId = null;
		zonaActivaId = zonas[0]?.id ?? null;
		estado.precioActual = Number(obtenerZonaActiva()?.precioM2 ?? 0);
		estado.siguienteIndice = obtenerSiguienteIndice(standsImportados);
		elementos.standSeleccionado.value = 'Ninguno';
		elementos.eliminarStand.disabled = true;
		aplicarImagenFondoPlano(imagenBase64);
		configurarEscena();
		renderizarListaZonas();
		actualizarDropdownZonas();
		renderizarGrid();
		asegurarControladorPan(true);
		estado.resumenMensaje = 'Diseño importado';
		marcarDisenoSinCambios();
		actualizarResumen();
		elementos.resumenEstado.textContent = 'Diseño importado';
	}

	function normalizarZonasImportadas(zonasImportadas) {
		if (!Array.isArray(zonasImportadas)) {
			return [];
		}

		return zonasImportadas.map((zona, indice) => ({
			id: typeof zona?.id === 'string' && zona.id ? zona.id : `zona-${String(indice + 1).padStart(3, '0')}`,
			nombre: typeof zona?.nombre === 'string' && zona.nombre.trim() ? zona.nombre.trim() : `Zona ${indice + 1}`,
			color: typeof zona?.color === 'string' && zona.color ? zona.color : '#3b82f6',
			precioM2: Number(zona?.precioM2 ?? 0),
			tipo: normalizarTipoZona(zona?.tipo),
		}));
	}

	function normalizarTipoZona(tipo) {
		return tipo === 'patrocinador' ? 'patrocinador' : 'venta';
	}

	function obtenerSiguienteIndiceZona() {
		let maximo = 0;
		for (const zona of zonas) {
			const numero = Number(String(zona.id || '').split('-')[1] || 0);
			if (numero > maximo) {
				maximo = numero;
			}
		}

		return maximo + 1;
	}

	function obtenerZonaActiva() {
		return zonas.find((zona) => zona.id === zonaActivaId) ?? null;
	}

	function formatearPrecioZona(valor) {
		return `$${Number(valor || 0).toLocaleString('es-CO')}`;
	}

	function limpiarErrorZona() {
		if (elementos.zonaError) {
			elementos.zonaError.textContent = '';
			elementos.zonaError.hidden = true;
		}
	}

	function mostrarErrorZona(mensaje) {
		if (!elementos.zonaError) {
			return;
		}

		elementos.zonaError.textContent = mensaje;
		elementos.zonaError.hidden = !mensaje;
	}

	function crearZona() {
		const nombre = String(elementos.zonaNombre?.value || '').trim();
		const color = String(elementos.zonaColor?.value || '#3b82f6');
		const precioM2 = Number(elementos.zonaPrecio?.value || 0);
		const tipo = normalizarTipoZona(elementos.zonaTipo?.value);

		if (!nombre) {
			mostrarErrorZona('El nombre de la zona es obligatorio.');
			return;
		}

		if (precioM2 <= 0) {
			mostrarErrorZona('El precio por m² debe ser mayor a 0.');
			return;
		}

		const nombreNormalizado = nombre.toLocaleLowerCase('es-ES');
		const existeZona = zonas.some((zona) => String(zona.nombre || '').trim().toLocaleLowerCase('es-ES') === nombreNormalizado);
		if (existeZona) {
			mostrarErrorZona('Ya existe una zona con ese nombre.');
			return;
		}

		const nuevaZona = {
			id: `zona-${String(obtenerSiguienteIndiceZona()).padStart(3, '0')}`,
			nombre,
			color,
			precioM2,
			tipo,
		};

		zonas.push(nuevaZona);
		zonaActivaId = nuevaZona.id;
		estado.precioActual = nuevaZona.precioM2;
		mostrarErrorZona('');
		renderizarListaZonas();
		actualizarDropdownZonas();
		marcarDisenoModificado();
		actualizarResumen();
	}

	function renderizarListaZonas() {
		if (!elementos.listaZonas) {
			return;
		}

		elementos.listaZonas.innerHTML = '';

		if (zonas.length === 0) {
			const vacio = document.createElement('p');
			vacio.className = 'zona-vacia';
			vacio.textContent = 'No hay zonas creadas todavía.';
			elementos.listaZonas.appendChild(vacio);
			return;
		}

		for (const zona of zonas) {
			const usaZona = estado.stands.some((stand) => stand.zonaId === zona.id);
			const fila = document.createElement('div');
			fila.className = 'zona-fila';
			fila.dataset.zonaId = zona.id;

			const muestra = document.createElement('span');
			muestra.className = 'zona-color-muestra';
			muestra.style.background = zona.color;

			const nombre = document.createElement('strong');
			nombre.textContent = zona.nombre;

			const precio = document.createElement('span');
			precio.textContent = `${formatearPrecioZona(zona.precioM2)}/m²`;

			const badge = document.createElement('span');
			badge.className = `badge ${zona.tipo === 'patrocinador' ? 'badge--patrocinador' : 'badge--venta'}`;
			badge.textContent = zona.tipo === 'patrocinador' ? 'Patrocinador' : 'Venta';

			const botonAplicar = document.createElement('button');
			botonAplicar.type = 'button';
			botonAplicar.className = 'boton';
			botonAplicar.textContent = 'Aplicar precio a stands existentes';
			botonAplicar.addEventListener('click', () => aplicarPrecioAZona(zona.id));

			const botonEliminar = document.createElement('button');
			botonEliminar.type = 'button';
			botonEliminar.className = 'boton boton--peligro';
			botonEliminar.textContent = 'Eliminar';
			botonEliminar.disabled = usaZona;
			botonEliminar.title = usaZona ? 'Hay stands asignados a esta zona' : 'Eliminar esta zona';
			if (!usaZona) {
				botonEliminar.addEventListener('click', () => eliminarZona(zona.id));
			}

			fila.append(muestra, nombre, precio, badge, botonAplicar, botonEliminar);
			elementos.listaZonas.appendChild(fila);
		}
	}

	function actualizarDropdownZonas() {
		if (!elementos.zonaActiva) {
			return;
		}

		const zonaValidaActual = zonas.some((zona) => zona.id === zonaActivaId);
		if (!zonaValidaActual) {
			zonaActivaId = zonas[0]?.id ?? null;
		}

		elementos.zonaActiva.innerHTML = '';

		const placeholder = document.createElement('option');
		placeholder.value = '';
		placeholder.textContent = '— Selecciona una zona —';
		elementos.zonaActiva.appendChild(placeholder);

		for (const zona of zonas) {
			const opcion = document.createElement('option');
			opcion.value = zona.id;
			opcion.textContent = `● ${zona.nombre} — ${formatearPrecioZona(zona.precioM2)}/m²`;
			opcion.style.color = zona.color;
			elementos.zonaActiva.appendChild(opcion);
		}

		elementos.zonaActiva.value = zonaActivaId ?? '';
		actualizarAvisoZonaActiva();
	}

	function actualizarAvisoZonaActiva() {
		if (!elementos.avisoZonaActiva) {
			return;
		}

		elementos.avisoZonaActiva.hidden = Boolean(zonaActivaId);
	}

	function manejarCambioZonaActiva() {
		zonaActivaId = elementos.zonaActiva?.value || null;
		const zona = obtenerZonaActiva();
		estado.precioActual = Number(zona?.precioM2 ?? 0);
		actualizarAvisoZonaActiva();
		actualizarResumen();
	}

	function aplicarPrecioAZona(zonaId) {
		const zona = zonas.find((item) => item.id === zonaId);
		if (!zona) {
			return;
		}

		const confirmar = window.confirm(`¿Aplicar ${formatearPrecioZona(zona.precioM2)}/m² a todos los stands de ${zona.nombre}?`);
		if (!confirmar) {
			return;
		}

		for (const stand of estado.stands) {
			if (stand.zonaId === zona.id) {
				stand.precioM2 = zona.precioM2;
			}
		}

		estado.precioActual = Number(obtenerZonaActiva()?.precioM2 ?? estado.precioActual);
		estado.resumenMensaje = 'Precio aplicado a stands de la zona';
		marcarDisenoModificado();
		renderizarGrid();
		renderizarListaZonas();
		actualizarResumen();
	}

	function eliminarZona(zonaId) {
		zonas = zonas.filter((zona) => zona.id !== zonaId);
		if (zonaActivaId === zonaId) {
			zonaActivaId = zonas[0]?.id ?? null;
		}

		const zonaActiva = obtenerZonaActiva();
		estado.precioActual = Number(zonaActiva?.precioM2 ?? 0);
		estado.resumenMensaje = 'Zona eliminada';
		marcarDisenoModificado();
		renderizarListaZonas();
		actualizarDropdownZonas();
		renderizarGrid();
		actualizarResumen();
	}

	function aplicarImagenFondoPlano(imagen) {
		// Eliminar imagen anterior si existe
		const imgAnterior = elementos.gridCeldas.querySelector('.img-fondo-plano');
		if (imgAnterior) imgAnterior.remove();

		// Limpiar background del contenedor
		elementos.contenedorPlano.style.backgroundImage = 'linear-gradient(rgba(7, 12, 18, 0.28), rgba(7, 12, 18, 0.28)), linear-gradient(135deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.01))';
		elementos.contenedorPlano.style.backgroundSize = '';
		elementos.contenedorPlano.style.backgroundPosition = '';

		if (!imagen) return;

		// Poner la imagen dentro del gridCeldas para que se mueva con el pan
		const img = document.createElement('img');
		img.className = 'img-fondo-plano';
		img.src = imagen;
		img.style.cssText = `
			position: absolute;
			top: 0; left: 0;
			width: 100%; height: 100%;
			object-fit: cover;
			opacity: 0.35;
			pointer-events: none;
			z-index: 0;
			border-radius: 0;
		`;
		elementos.gridCeldas.insertBefore(img, elementos.gridCeldas.firstChild);
	}

	function marcarDisenoModificado() {
		estado.disenoModificado = true;
		actualizarIndicadorCambios();
	}

	function marcarDisenoSinCambios() {
		estado.disenoModificado = false;
		actualizarIndicadorCambios();
	}

	function actualizarIndicadorCambios() {
		if (!elementos.indicadorCambios) {
			return;
		}

		if (estado.disenoModificado) {
			elementos.indicadorCambios.textContent = '⚠ Cambios sin guardar';
			elementos.indicadorCambios.classList.add('indicador-cambios--modificado');
		} else {
			elementos.indicadorCambios.textContent = 'Sin cambios sin guardar';
			elementos.indicadorCambios.classList.remove('indicador-cambios--modificado');
		}
	}

	function obtenerSiguienteIndice(stands) {
		let maximo = 0;
		for (const stand of stands) {
			const numero = Number(String(stand.id || '').split('-')[1] || 0);
			if (numero > maximo) {
				maximo = numero;
			}
		}

		return maximo + 1;
	}

	function aplicarDimensiones() {
		const filas = Number(elementos.filasGrid.value || 0);
		const columnas = Number(elementos.columnasGrid.value || 0);
		if (filas <= 0 || columnas <= 0) {
			elementos.resumenEstado.textContent = 'Dimensiones inválidas';
			return;
		}

		if (estado.stands.length > 0) {
			const ok = window.confirm('Cambiar las dimensiones borrará todos los stands actuales. ¿Desea continuar?');
			if (!ok) return;
			estado.stands = [];
			estado.standSeleccionadoId = null;
			marcarDisenoModificado();
		}

		planoBase.filas = filas;
		planoBase.columnas = columnas;
		elementos.resumenEstado.textContent = 'Dimensiones aplicadas';
		configurarEscena();
		renderizarGrid();
		asegurarControladorPan(true);
		marcarDisenoModificado();
		actualizarResumen();
	}

	function renderizarGrid() {
		elementos.gridCeldas.innerHTML = '';

		for (let fila = 0; fila < planoBase.filas; fila += 1) {
			for (let columna = 0; columna < planoBase.columnas; columna += 1) {
				const elementoCelda = document.createElement('div');
				elementoCelda.className = 'celda celda--admin-vacia';
				elementoCelda.dataset.fila = String(fila);
				elementoCelda.dataset.columna = String(columna);
				elementos.gridCeldas.appendChild(elementoCelda);
			}
		}

		for (const stand of estado.stands) {
			renderizarStand(stand);
		}

		renderizarPrevisualizacion();
		reordenarCapas();
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

	function renderizarStand(stand) {
		const contenedorStand = document.createElement('div');
		contenedorStand.className = 'stand-visual';
		if (stand.id === estado.standSeleccionadoId) {
			contenedorStand.classList.add('stand-visual--seleccionado');
		}
		contenedorStand.dataset.standId = stand.id;
		contenedorStand.dataset.zonaId = stand.zonaId || '';
		contenedorStand.dataset.estado = stand.estado || 'disponible';
		contenedorStand.style.left = `${stand.columnaInicio * planoBase.tamanoCeldaPx}px`;
		contenedorStand.style.top = `${stand.filaInicio * planoBase.tamanoCeldaPx}px`;
		contenedorStand.style.width = `${(stand.columnaFin - stand.columnaInicio + 1) * planoBase.tamanoCeldaPx}px`;
		contenedorStand.style.height = `${(stand.filaFin - stand.filaInicio + 1) * planoBase.tamanoCeldaPx}px`;
		if (stand.id !== estado.standSeleccionadoId) {
			const color = stand.color || '#3b82f6';
			contenedorStand.style.borderColor = color;
			contenedorStand.style.backgroundColor = utils.hexARgba(color, 0.2);
		}

		const miniGrid = document.createElement('div');
		miniGrid.className = 'mini-grid-stand';
		miniGrid.style.gridTemplateColumns = `repeat(${stand.columnaFin - stand.columnaInicio + 1}, 1fr)`;
		miniGrid.style.gridTemplateRows = `repeat(${stand.filaFin - stand.filaInicio + 1}, 1fr)`;

		for (let fila = stand.filaInicio; fila <= stand.filaFin; fila += 1) {
			for (let columna = stand.columnaInicio; columna <= stand.columnaFin; columna += 1) {
				const celda = document.createElement('div');
				celda.className = 'celda celda--seleccionado';
				celda.dataset.fila = String(fila);
				celda.dataset.columna = String(columna);
				celda.dataset.standId = stand.id;
				miniGrid.appendChild(celda);
			}
		}

		const etiqueta = document.createElement('div');
		etiqueta.className = 'etiqueta-stand';
		etiqueta.textContent = formatearIdStand(stand.id);

		contenedorStand.appendChild(miniGrid);
		contenedorStand.appendChild(etiqueta);
		elementos.gridCeldas.appendChild(contenedorStand);
	}

	function renderizarPrevisualizacion() {
		const existente = elementos.gridCeldas.querySelector('.stand-visual--previsualizacion-valida, .stand-visual--previsualizacion-invalida');
		if (existente) {
			existente.remove();
		}

		if (!estado.previsualizacion) {
			return;
		}

		const rectangulo = estado.previsualizacion.rectangulo;
		const previsualizacion = document.createElement('div');
		previsualizacion.className = 'stand-visual';
		previsualizacion.classList.add(estado.previsualizacion.valida ? 'stand-visual--previsualizacion-valida' : 'stand-visual--previsualizacion-invalida');
		previsualizacion.style.left = `${rectangulo.columnaInicio * planoBase.tamanoCeldaPx}px`;
		previsualizacion.style.top = `${rectangulo.filaInicio * planoBase.tamanoCeldaPx}px`;
		previsualizacion.style.width = `${rectangulo.ancho * planoBase.tamanoCeldaPx}px`;
		previsualizacion.style.height = `${rectangulo.alto * planoBase.tamanoCeldaPx}px`;
		previsualizacion.style.pointerEvents = 'none';

		const etiqueta = document.createElement('div');
		etiqueta.className = 'etiqueta-stand';
		etiqueta.textContent = estado.previsualizacion.valida
			? `${rectangulo.ancho} x ${rectangulo.alto}`
			: estado.previsualizacion.motivo;

		previsualizacion.appendChild(etiqueta);
		elementos.gridCeldas.appendChild(previsualizacion);
		reordenarCapas();
	}

	function reordenarCapas() {
		const nodos = Array.from(elementos.gridCeldas.children);
		for (const nodo of nodos) {
			nodo.style.zIndex = nodo.classList.contains('stand-visual--previsualizacion-valida') || nodo.classList.contains('stand-visual--previsualizacion-invalida') ? '3' : '2';
		}
	}

	function manejarMouseDown(evento) {
		if (evento.button !== 0) {
			return;
		}

		const celda = obtenerCeldaDesdeEvento(evento);
		if (!celda) {
			return;
		}

		const stand = obtenerStandPorCelda(celda.fila, celda.columna);
		if (stand) {
			seleccionarStand(stand.id);
			return;
		}

		if (!zonaActivaId) {
			estado.resumenMensaje = 'Selecciona o crea una zona antes de dibujar stands.';
			actualizarResumen();
			return;
		}

		evento.preventDefault();
		estado.interaccion = {
			tipo: 'nuevo',
			puntoFijo: celda,
		};
		actualizarPrevisualizacion(celda);
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

		confirmarOCancelarStand();
	}

	function actualizarPrevisualizacion(celdaActual) {
		if (!estado.interaccion || !celdaActual) {
			return;
		}

		const rectangulo = utils.calcularRectangulo(estado.interaccion.puntoFijo, celdaActual);
		const validoTamano = utils.validarTamanoMinimo(rectangulo, 3, 3);
		const solapado = utils.validarSolapamiento(rectangulo, estado.stands);
		const motivo = !validoTamano
			? 'Mínimo 3 x 3'
			: solapado
				? 'Se solapa'
				: '';
		estado.resumenMensaje = motivo || 'Rectángulo válido';

		estado.previsualizacion = {
			rectangulo,
			valida: validoTamano && !solapado,
			motivo,
		};

		renderizarGrid();
		actualizarResumen();
	}

	function confirmarOCancelarStand() {
		const previsualizacion = estado.previsualizacion;
		if (!previsualizacion) {
			estado.interaccion = null;
			return;
		}

		if (previsualizacion.valida) {
			const nuevoStand = crearStandDesdeRectangulo(previsualizacion.rectangulo);
			if (!nuevoStand) {
				estado.interaccion = null;
				estado.previsualizacion = null;
				renderizarGrid();
				actualizarResumen();
				return;
			}
			estado.stands.push(nuevoStand);
			estado.siguienteIndice += 1;
			estado.standSeleccionadoId = nuevoStand.id;
			estado.resumenMensaje = 'Stand creado';
			marcarDisenoModificado();
		} else {
			estado.resumenMensaje = previsualizacion.motivo || 'Rectángulo inválido';
		}

		estado.interaccion = null;
		estado.previsualizacion = null;
		renderizarGrid();
		actualizarResumen();
	}

	function crearStandDesdeRectangulo(rectangulo) {
		const zona = obtenerZonaActiva();
		if (!zona) {
			estado.resumenMensaje = 'Selecciona o crea una zona antes de dibujar stands.';
			return null;
		}

		return {
			id: generarIdStand(),
			zonaId: zona.id,
			filaInicio: rectangulo.filaInicio,
			columnaInicio: rectangulo.columnaInicio,
			filaFin: rectangulo.filaFin,
			columnaFin: rectangulo.columnaFin,
			precioM2: Number(zona.precioM2 || 0),
			color: zona.color,
			tipo: zona.tipo,
			estado: zona.tipo === 'patrocinador' ? 'patrocinador' : 'disponible',
		};
	}

	function seleccionarStand(standId) {
		estado.standSeleccionadoId = standId;
		const stand = estado.stands.find((item) => item.id === standId);
		if (stand) {
			estado.resumenMensaje = 'Stand seleccionado';
		}

		renderizarGrid();
		actualizarResumen();
	}

	function obtenerStandPorCelda(fila, columna) {
		return estado.stands.find((stand) => (
			fila >= stand.filaInicio &&
			fila <= stand.filaFin &&
			columna >= stand.columnaInicio &&
			columna <= stand.columnaFin
		));
	}

	function obtenerCeldaDesdeEvento(evento) {
		const rectangulo = elementos.contenedorPlano.getBoundingClientRect();
		const offset = controladorPan ? controladorPan.getOffset() : { x: 0, y: 0 };
		const x = evento.clientX - rectangulo.left - offset.x;
		const y = evento.clientY - rectangulo.top - offset.y;

		return {
			fila: utils.limitar(Math.floor(y / planoBase.tamanoCeldaPx), 0, planoBase.filas - 1),
			columna: utils.limitar(Math.floor(x / planoBase.tamanoCeldaPx), 0, planoBase.columnas - 1),
		};
	}

	function aplicarPrecioAlStandSeleccionado() {
		const stand = estado.stands.find((item) => item.id === estado.standSeleccionadoId);
		if (!stand) {
			estado.resumenMensaje = 'No hay stand seleccionado';
			actualizarResumen();
			return;
		}

		const zona = obtenerZonaActiva();
		if (!zona) {
			estado.resumenMensaje = 'Selecciona una zona activa antes de aplicar precio';
			actualizarResumen();
			return;
		}

		stand.precioM2 = Number(zona.precioM2 || 0);
		estado.precioActual = stand.precioM2;
		estado.resumenMensaje = 'Precio aplicado';
		marcarDisenoModificado();
		renderizarGrid();
		actualizarResumen();
	}

	function eliminarStandSeleccionado() {
		if (!estado.standSeleccionadoId) {
			return;
		}

		estado.stands = estado.stands.filter((stand) => stand.id !== estado.standSeleccionadoId);
		estado.standSeleccionadoId = null;
		estado.resumenMensaje = 'Stand eliminado';
		marcarDisenoModificado();
		elementos.standSeleccionado.value = 'Ninguno';
		elementos.eliminarStand.disabled = true;
		renderizarGrid();
		actualizarResumen();
	}

	function guardarDiseno() {
		if (lecturaImagenPendiente) {
			elementos.resumenEstado.textContent = 'Esperando a que termine de cargarse la imagen del plano';
			return;
		}

		const contenido = JSON.stringify(obtenerDisenoAdmin(), null, 2);
		const blob = new Blob([contenido], { type: 'application/json;charset=utf-8' });
		const url = URL.createObjectURL(blob);
		const enlace = document.createElement('a');
		enlace.href = url;
		enlace.download = 'stands-diseno.json';
		enlace.style.display = 'none';
		document.body.appendChild(enlace);
		enlace.click();
		enlace.remove();
		URL.revokeObjectURL(url);
		estado.resumenMensaje = 'Diseño descargado';
		marcarDisenoSinCambios();
		actualizarResumen();
	}

	function obtenerDisenoAdmin() {
		const stands = estado.stands.map((stand) => ({
			id: stand.id,
			zonaId: stand.zonaId ?? null,
			filaInicio: Number(stand.filaInicio),
			columnaInicio: Number(stand.columnaInicio),
			filaFin: Number(stand.filaFin),
			columnaFin: Number(stand.columnaFin),
			precioM2: Number(stand.precioM2),
			color: stand.color || '#3b82f6',
			tipo: stand.tipo || 'venta',
			estado: stand.estado ?? 'disponible',
		}));

		return {
			version: '1.0',
			imagenPlano: imagenBase64,
			filas: Number(planoBase.filas || 0),
			columnas: Number(planoBase.columnas || 0),
			tamanoCeldaPx: Number(planoBase.tamanoCeldaPx || TAMANO_CELDA_PX),
			zonas: zonas.map((zona) => ({
				id: zona.id,
				nombre: zona.nombre,
				color: zona.color,
				precioM2: Number(zona.precioM2),
				tipo: zona.tipo,
			})),
			stands,
		};
	}

	function generarIdStand() {
		const numero = String(estado.siguienteIndice).padStart(3, '0');
		return `stand-${numero}`;
	}

	function formatearIdStand(id) {
		const numero = id.split('-')[1] || id;
		return `Stand ${numero}`;
	}

	function actualizarResumen() {
		const zonaActiva = obtenerZonaActiva();
		elementos.resumenZona.textContent = zonaActiva ? `${zonaActiva.nombre} · ${formatearPrecioZona(zonaActiva.precioM2)}/m²` : 'Sin zona';
		elementos.resumenStand.textContent = estado.standSeleccionadoId ? formatearIdStand(estado.standSeleccionadoId) : 'Ninguno';
		elementos.resumenEstado.textContent = estado.resumenMensaje || 'Listo para dibujar';
		elementos.standSeleccionado.value = estado.standSeleccionadoId ? formatearIdStand(estado.standSeleccionadoId) : 'Ninguno';
		elementos.eliminarStand.disabled = !estado.standSeleccionadoId;
		elementos.aplicarPrecio.disabled = !estado.standSeleccionadoId || !zonaActivaId;
		actualizarAvisoZonaActiva();
		actualizarIndicadorCambios();
	}
})();