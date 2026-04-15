(function setupRuntimeApiBase() {
	const isLocal =
		location.protocol === "file:" ||
		location.hostname === "localhost" ||
		location.hostname === "127.0.0.1";

	window.__GIFT_API_BASE__ = isLocal
		? "http://127.0.0.1:8000/api"
		: "https://shouge66.pythonanywhere.com/api";
})();
