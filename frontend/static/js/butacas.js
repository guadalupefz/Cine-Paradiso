document.addEventListener("DOMContentLoaded", function () {

    // Elementos del DOM
    const contenedor = document.querySelector(".contenido-seleccion-butacas");

    if (!contenedor) {
        return;
    }

    const butacas = document.querySelectorAll(".butaca.disponible");
    const contador = document.getElementById("cantidad-seleccionadas");
    const continuar = document.getElementById("continuar-compra");
    const mensaje = document.getElementById("mensaje-seleccion");
    const detalle = document.getElementById("detalle-butacas");
    const total = document.getElementById("total-butacas");

    // Datos de la función
    const precioUnitario = Number(contenedor.dataset.precio);
    const idFuncion = contenedor.dataset.idFuncion;

    // Obtener las butacas seleccionadas
    function obtenerSeleccionadas() {
        return Array.from(
            document.querySelectorAll(".butaca.seleccionada")
        );
    }

    // Actualizar el resumen de compra
    function actualizarResumen() {

        const seleccionadas = obtenerSeleccionadas();
        const cantidad = seleccionadas.length;
        const importe = cantidad * precioUnitario;

        contador.textContent = cantidad;
        continuar.disabled = cantidad === 0;

        detalle.innerHTML = "";

        seleccionadas.forEach(function (butaca) {

            const elemento = document.createElement("li");
            elemento.classList.add("item-butaca-resumen");

            const etiqueta = butaca.dataset.etiqueta;

            const nombre = document.createElement("span");
            nombre.textContent =
                "FILA " + etiqueta.charAt(0) +
                " - Asiento " + etiqueta.slice(1);

            const precio = document.createElement("strong");
            precio.textContent =
                "ARS " + precioUnitario.toLocaleString("es-AR");

            elemento.appendChild(nombre);
            elemento.appendChild(precio);

            detalle.appendChild(elemento);
        });

        mensaje.textContent = cantidad > 0
            ? "Seleccionaste " + cantidad + " butaca(s)."
            : "";

        total.textContent = "$" + importe.toFixed(2);
    }

    // Seleccionar o deseleccionar butacas
    function configurarSeleccion() {

        butacas.forEach(function (butaca) {

            butaca.addEventListener("click", function () {

                const seleccionada =
                    butaca.classList.toggle("seleccionada");

                butaca.setAttribute("aria-pressed", seleccionada);

                actualizarResumen();
            });
        });
    }

    // Continuar al siguiente paso
    function continuarCompra() {

        continuar.addEventListener("click", function () {

            const seleccionadas = obtenerSeleccionadas();

            if (seleccionadas.length === 0) {
                return;
            }

            const idsSeleccionados = seleccionadas.map(function (butaca) {
                return Number(butaca.dataset.idButaca);
            });

            const params = new URLSearchParams({
                id_funcion: idFuncion,
                butacas: idsSeleccionados.join(",")
            });

            window.location.href = "/servicios?" + params.toString();
        });
    }

    // Inicialización
    configurarSeleccion();
    continuarCompra();
    actualizarResumen();

});