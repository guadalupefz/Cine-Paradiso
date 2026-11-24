document.querySelectorAll(".sitio-publico img[data-poster-fallback]").forEach((imagen) => {
    function mostrarRespaldo() {
        if (imagen.getAttribute("src") !== imagen.dataset.posterFallback) {
            imagen.src = imagen.dataset.posterFallback;
        }
    }
    imagen.addEventListener("error", mostrarRespaldo);
    if (imagen.complete && imagen.naturalWidth === 0) mostrarRespaldo();
});
