document.addEventListener("DOMContentLoaded", function () {

    const opciones = document.querySelectorAll(
        'input[name="funcion_seleccionada"]'
    );

    const resumen = document.getElementById("detalle-funcion");
    const precio = document.getElementById("precio-funcion");
    const datos = document.getElementById("datos-funcion-seleccionada");
    const boton = document.getElementById("btn-elegir-butacas");
    const poster = document.querySelector(".u8-poster img");

    // Actualizar el resumen de la función seleccionada.
    function actualizarResumen(opcion) {

        if (!opcion || !resumen || !precio || !datos || !boton) {
            return;
        }

        opciones.forEach(function (otra) {

            otra.closest(".u8-opcion").classList.toggle(
                "seleccionada",
                otra === opcion
            );

        });

        const valor = Number(opcion.dataset.precio || 0);

        precio.textContent =
            "ARS " + valor.toLocaleString("es-AR") + " por entrada";

        datos.textContent =
            opcion.dataset.fechaCompleta + " · " +
            opcion.dataset.horario + " · " +
            opcion.dataset.local + " · " +
            opcion.dataset.sala;

        resumen.hidden = false;

        boton.dataset.url = opcion.dataset.url;
    }

    // Detectar la selección de una función.
    opciones.forEach(function (opcion) {

        opcion.addEventListener("change", function () {
            actualizarResumen(opcion);
        });

    });

    // Continuar hacia la selección de butacas.
    if (boton) {

        boton.addEventListener("click", function () {

            if (boton.dataset.url) {
                window.location.href = boton.dataset.url;
            }

        });

    }
    if (poster && poster.dataset.fallback) {
        const mostrarFallback = () => {
            if (poster.getAttribute("src") !== poster.dataset.fallback) {
                poster.src = poster.dataset.fallback;
            }
        };

        poster.addEventListener("error", mostrarFallback, {
            once: true
        });

        if (poster.complete && poster.naturalWidth === 0) {
            mostrarFallback();
        }
    }   

});