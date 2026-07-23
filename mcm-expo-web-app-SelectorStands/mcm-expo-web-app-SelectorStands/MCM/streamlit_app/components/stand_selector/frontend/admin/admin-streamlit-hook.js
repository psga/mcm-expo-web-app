// Hook de integración con Streamlit para admin.html.
// No modifica la lógica de admin.js: solo escucha eventos y lee/llama las
// funciones que admin.js ya expone en window (obtenerDisenoAdmin, cargarDisenoImportado).
(() => {
	function onRender(event) {
		const { standsData } = event.detail.args || {};
		const tieneDiseno = standsData && Array.isArray(standsData.stands) && standsData.stands.length > 0;

		if (tieneDiseno && typeof window.cargarDisenoImportado === 'function') {
			window.cargarDisenoImportado(standsData);
		}

		Streamlit.setFrameHeight();
	}

	document.addEventListener('click', (evento) => {
		if (!evento.target.closest('#guardar-diseno')) {
			return;
		}

		if (typeof window.obtenerDisenoAdmin === 'function') {
			Streamlit.setComponentValue({
				accion: 'guardar_diseno',
				diseno: window.obtenerDisenoAdmin(),
			});
		}
	});

	window.addEventListener('load', () => Streamlit.setFrameHeight());
	window.addEventListener('resize', () => Streamlit.setFrameHeight());

	Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender);
	Streamlit.setComponentReady();
})();
