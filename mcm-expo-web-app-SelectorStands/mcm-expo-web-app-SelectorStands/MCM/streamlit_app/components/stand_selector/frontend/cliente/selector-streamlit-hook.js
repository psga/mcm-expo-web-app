// Hook de integración con Streamlit para index.html (vista de marca/cliente).
// No modifica la lógica de renderizado de selector.js: solo escucha
// streamlit:render y llama a la función que selector.js ya expone en window
// (cargarDisenoDesdeJSON).
//
// El envío de la reserva confirmada YA NO se hace desde aquí: el payload que
// necesita Streamlit (personalización con dotación base, costoExtra, tomas)
// solo existe dentro del closure de abrirModalReserva() en selector.js, así
// que ese código llama a Streamlit.setComponentValue() directamente en el
// punto donde antes descargaba el JSON (ver enviarConfirmacionAStreamlit).
(() => {
	function onRender(event) {
		const { standsData, imagenUrl, idMarca } = event.detail.args || {};

		if (typeof idMarca !== 'undefined') {
			window.idMarcaActual = idMarca;
		}

		if (standsData && Array.isArray(standsData.stands) && typeof window.cargarDisenoDesdeJSON === 'function') {
			// standsData ya trae imagenPlano; imagenUrl (si viene) la sobreescribe.
			const fuente = imagenUrl ? { ...standsData, imagenPlano: imagenUrl } : standsData;
			window.cargarDisenoDesdeJSON(standsData.stands, fuente);
		}

		Streamlit.setFrameHeight();
	}

	window.addEventListener('load', () => Streamlit.setFrameHeight());
	window.addEventListener('resize', () => Streamlit.setFrameHeight());

	Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender);
	Streamlit.setComponentReady();
})();
