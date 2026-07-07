(() => {
	function clonarPunto(punto) {
		return {
			fila: Number(punto.fila),
			columna: Number(punto.columna),
		};
	}

	function limitar(valor, minimo, maximo) {
		return Math.min(Math.max(valor, minimo), maximo);
	}

	function claveCelda(fila, columna) {
		return `${fila}-${columna}`;
	}

	function normalizarRectangulo(puntoA, puntoB) {
		const filaInicio = Math.min(puntoA.fila, puntoB.fila);
		const filaFin = Math.max(puntoA.fila, puntoB.fila);
		const columnaInicio = Math.min(puntoA.columna, puntoB.columna);
		const columnaFin = Math.max(puntoA.columna, puntoB.columna);

		return {
			filaInicio,
			filaFin,
			columnaInicio,
			columnaFin,
			ancho: columnaFin - columnaInicio + 1,
			alto: filaFin - filaInicio + 1,
		};
	}

	function rectanguloACeldas(rectangulo) {
		const celdas = [];

		for (let fila = rectangulo.filaInicio; fila <= rectangulo.filaFin; fila += 1) {
			for (let columna = rectangulo.columnaInicio; columna <= rectangulo.columnaFin; columna += 1) {
				celdas.push({ fila, columna });
			}
		}

		return celdas;
	}

	function calcularRectangulo(puntoA, puntoB, opciones = {}) {
		const limites = opciones.limitesMaximos;
		const puntoInicial = clonarPunto(puntoA);
		const puntoFinal = clonarPunto(puntoB);

		if (limites) {
			puntoInicial.fila = limitar(puntoInicial.fila, limites.filaInicio, limites.filaFin);
			puntoInicial.columna = limitar(puntoInicial.columna, limites.columnaInicio, limites.columnaFin);
			puntoFinal.fila = limitar(puntoFinal.fila, limites.filaInicio, limites.filaFin);
			puntoFinal.columna = limitar(puntoFinal.columna, limites.columnaInicio, limites.columnaFin);
		}

		const rectangulo = normalizarRectangulo(puntoInicial, puntoFinal);

		return {
			...rectangulo,
			celdas: rectanguloACeldas(rectangulo),
		};
	}

	function validarTamanoMinimo(rectangulo, minFilas = 3, minColumnas = 3) {
		const filas = rectangulo.filaFin - rectangulo.filaInicio + 1;
		const columnas = rectangulo.columnaFin - rectangulo.columnaInicio + 1;

		return filas >= minFilas && columnas >= minColumnas;
	}

	function validarSolapamiento(nuevoRect, standsExistentes) {
		return standsExistentes.some((stand) => {
			const filasSeCruzan = !(
				nuevoRect.filaFin < stand.filaInicio ||
				nuevoRect.filaInicio > stand.filaFin
			);
			const columnasSeCruzan = !(
				nuevoRect.columnaFin < stand.columnaInicio ||
				nuevoRect.columnaInicio > stand.columnaFin
			);

			return filasSeCruzan && columnasSeCruzan;
		});
	}

	function expandirStandsACeldas(stands) {
		const celdas = [];

		for (const stand of stands) {
			for (let fila = stand.filaInicio; fila <= stand.filaFin; fila += 1) {
				for (let columna = stand.columnaInicio; columna <= stand.columnaFin; columna += 1) {
					celdas.push({
						fila,
						columna,
						standId: stand.id,
						estado: stand.estado ?? 'disponible',
						precio: Number(stand.precioM2 ?? 0),
					});
				}
			}
		}

		return celdas;
	}

	function crearMapaCeldasDesdeCeldas(celdas) {
		const mapa = new Map();

		for (const celda of celdas) {
			mapa.set(claveCelda(celda.fila, celda.columna), {
				fila: Number(celda.fila),
				columna: Number(celda.columna),
				estado: celda.estado,
				precio: Number(celda.precio ?? 0),
				standId: celda.standId ?? null,
			});
		}

		return mapa;
	}

	function obtenerLimitesStand(stand) {
		return {
			filaInicio: Number(stand.filaInicio),
			filaFin: Number(stand.filaFin),
			columnaInicio: Number(stand.columnaInicio),
			columnaFin: Number(stand.columnaFin),
		};
	}

	function cargarStandsParaCliente(stands, planoBase = {}) {
		const standsNormalizados = stands.map((stand) => ({
			...stand,
			...obtenerLimitesStand(stand),
			precioM2: Number(stand.precioM2 ?? 0),
			estado: stand.estado ?? 'disponible',
		}));
		const celdas = expandirStandsACeldas(standsNormalizados);
		const filas = planoBase.filas ?? Math.max(0, ...standsNormalizados.map((stand) => stand.filaFin + 1));
		const columnas = planoBase.columnas ?? Math.max(0, ...standsNormalizados.map((stand) => stand.columnaFin + 1));
		const tamanoCeldaPx = Number(planoBase.tamanoCeldaPx ?? 34);
		const imagen = typeof planoBase.imagen === 'string' ? planoBase.imagen : '';

		return {
			imagen,
			filas,
			columnas,
			tamanoCeldaPx,
			stands: standsNormalizados,
			celdas,
			mapaCeldas: crearMapaCeldasDesdeCeldas(celdas),
			mapaStands: new Map(standsNormalizados.map((stand) => [stand.id, stand])),
		};
	}

	function hexARgba(hex, alpha) {
		const h = hex.replace('#', '');
		const r = parseInt(h.slice(0, 2), 16);
		const g = parseInt(h.slice(2, 4), 16);
		const b = parseInt(h.slice(4, 6), 16);
		return `rgba(${r}, ${g}, ${b}, ${alpha})`;
	}

	function iniciarPan(contenedor, gridElement) {
		const pan = { activo: false, espacioPresionado: false, offsetX: 0, offsetY: 0, inicioX: 0, inicioY: 0 };

		function aplicarTransform() {
			const rectC = contenedor.getBoundingClientRect();
			const maxX = 80;
			const maxY = 80;
			const minX = Math.min(0, rectC.width - gridElement.offsetWidth + 80);
			const minY = Math.min(0, rectC.height - gridElement.offsetHeight + 80);
			pan.offsetX = Math.max(minX, Math.min(maxX, pan.offsetX));
			pan.offsetY = Math.max(minY, Math.min(maxY, pan.offsetY));
			gridElement.style.transform = `translate(${pan.offsetX}px, ${pan.offsetY}px)`;
		}

		function onKeyDown(e) {
			if (e.code === 'Space' && !e.repeat && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'SELECT') {
				e.preventDefault();
				pan.espacioPresionado = true;
				contenedor.style.cursor = 'grab';
			}
		}

		function onKeyUp(e) {
			if (e.code === 'Space') {
				pan.espacioPresionado = false;
				pan.activo = false;
				contenedor.style.cursor = '';
			}
		}

		function onMouseDown(e) {
			const esPan = (pan.espacioPresionado && e.button === 0) || e.button === 1;
			if (!esPan) return;
			e.preventDefault();
			e.stopPropagation();
			pan.activo = true;
			pan.inicioX = e.clientX - pan.offsetX;
			pan.inicioY = e.clientY - pan.offsetY;
			contenedor.style.cursor = 'grabbing';
		}

		function onMouseMove(e) {
			if (!pan.activo) return;
			pan.offsetX = e.clientX - pan.inicioX;
			pan.offsetY = e.clientY - pan.inicioY;
			aplicarTransform();
		}

		function onMouseUp(e) {
			if (!pan.activo) return;
			if (e.button === 0 || e.button === 1) {
				pan.activo = false;
				contenedor.style.cursor = pan.espacioPresionado ? 'grab' : '';
			}
		}

		function onAuxClick(e) { if (e.button === 1) e.preventDefault(); }

		document.addEventListener('keydown', onKeyDown);
		document.addEventListener('keyup', onKeyUp);
		contenedor.addEventListener('mousedown', onMouseDown);
		document.addEventListener('mousemove', onMouseMove);
		document.addEventListener('mouseup', onMouseUp);
		contenedor.addEventListener('auxclick', onAuxClick);

		return {
			resetear() { pan.offsetX = 0; pan.offsetY = 0; aplicarTransform(); },
			centrar() {
				const rectC = contenedor.getBoundingClientRect();
				pan.offsetX = Math.max(0, (rectC.width - gridElement.offsetWidth) / 2);
				pan.offsetY = Math.max(0, (rectC.height - gridElement.offsetHeight) / 2);
				aplicarTransform();
			},
			getOffset() { return { x: pan.offsetX, y: pan.offsetY }; },
		};
	}

	window.selectorStandsUtils = {
		calcularRectangulo,
		validarTamanoMinimo,
		validarSolapamiento,
		expandirStandsACeldas,
		cargarStandsParaCliente,
		crearMapaCeldasDesdeCeldas,
		obtenerLimitesStand,
		normalizarRectangulo,
		rectanguloACeldas,
		claveCelda,
		limitar,
		iniciarPan,
		hexARgba,
	};
})();