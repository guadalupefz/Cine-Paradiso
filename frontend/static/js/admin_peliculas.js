document.querySelectorAll("img[data-poster-fallback]").forEach((imagen) => {
    const mostrarImagenPredeterminada = () => {
        const respaldo = imagen.dataset.posterFallback;
        if (imagen.getAttribute("src") !== respaldo) {
            imagen.src = respaldo;
        }
    };
    imagen.addEventListener("error", mostrarImagenPredeterminada);
    if (imagen.complete && imagen.naturalWidth === 0) {
        mostrarImagenPredeterminada();
    }
});
