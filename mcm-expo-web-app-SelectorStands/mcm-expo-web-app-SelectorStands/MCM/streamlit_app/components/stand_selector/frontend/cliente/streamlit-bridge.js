// Puente mínimo con Streamlit para componentes HTML estáticos (sin build de Node/React).
// Implementa el mismo contrato que streamlit-component-lib: Streamlit.setComponentReady(),
// Streamlit.setComponentValue(value), Streamlit.setFrameHeight(height) y el evento
// Streamlit.RENDER_EVENT ("streamlit:render") con los argumentos en event.detail.args.
(() => {
	function enviarMensajeAStreamlit(type, data = {}) {
		const mensaje = Object.assign({ isStreamlitMessage: true, type }, data);
		window.parent.postMessage(mensaje, '*');
	}

	const Streamlit = {
		setComponentReady: function () {
			enviarMensajeAStreamlit('streamlit:componentReady', { apiVersion: 1 });
		},
		setFrameHeight: function (height) {
			enviarMensajeAStreamlit('streamlit:setFrameHeight', {
				height: height ?? document.documentElement.scrollHeight,
			});
		},
		setComponentValue: function (value) {
			enviarMensajeAStreamlit('streamlit:setComponentValue', { value });
		},
		RENDER_EVENT: 'streamlit:render',
		events: {
			addEventListener: function (type, callback) {
				window.addEventListener('message', (event) => {
					if (event.data?.type === type) {
						event.detail = event.data;
						callback(event);
					}
				});
			},
		},
	};

	window.Streamlit = Streamlit;
})();
