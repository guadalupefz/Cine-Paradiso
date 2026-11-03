const formulario = document.querySelector(".formulario-funcion");

if (formulario) {
    const local = document.querySelector("#local");
    const sala = document.querySelector("#sala");
    const pelicula = document.querySelector("#pelicula");
    const fecha = document.querySelector("#fecha_hora");
    const opcionesSalas = Array.from(sala.options).map((opcion) => opcion.cloneNode(true));
    const salaInicial = sala.value;
    local.value = sala.selectedOptions[0]?.dataset.local || "";
    document.querySelector(".selector-local").hidden = false;
    document.querySelector(".selector-sala").classList.remove("ancho-completo");

    function actualizarInformacion() {
        const seleccionSala = sala.selectedOptions[0];
        const capacidad = seleccionSala?.dataset.capacidad;
        const duracion = Number(pelicula.selectedOptions[0]?.dataset.duracion?.trim().split(/\s+/)[0]);
        document.querySelector("#capacidad-elegida").textContent = capacidad ? `${capacidad} butacas` : "—";
        document.querySelector("#duracion-elegida").textContent = Number.isFinite(duracion) && duracion > 0 ? `${duracion} min` : "—";
        document.querySelector("#detalle-sala").textContent = sala.value && seleccionSala?.dataset.local ? `${local.selectedOptions[0].textContent} · ${seleccionSala.textContent}` : "Elegí una sala para consultar su programación.";

        const estadoAgenda = document.querySelector("#estado-agenda");
        if (!estadoAgenda) return;
        const dia = fecha.value.slice(0, 10);
        let cantidad = 0;
        document.querySelectorAll(".agenda-lista li").forEach((funcion) => {
            const coincide = sala.value && funcion.dataset.sala === sala.value && (!dia || funcion.dataset.dia === dia);
            funcion.hidden = !coincide;
            if (coincide) cantidad++;
        });
        if (!sala.value) {
            estadoAgenda.textContent = "Seleccioná una sala y una fecha para consultar los horarios.";
        } else if (cantidad === 0) {
            estadoAgenda.textContent = dia ? "No hay otras funciones registradas para esta sala en la fecha elegida." : "No hay otras funciones registradas para esta sala.";
        } else {
            estadoAgenda.textContent = `${cantidad} ${cantidad === 1 ? "función registrada" : "funciones registradas"}${dia ? " en la fecha elegida" : " en esta sala"}.`;
        }
    }

    function filtrarSalas(idActual = "") {
        sala.replaceChildren(new Option(local.value ? "Seleccioná una sala" : "Primero seleccioná un local", ""));
        opcionesSalas.forEach((opcion) => {
            if (opcion.value && (opcion.dataset.local === local.value || (opcion.value === idActual && !opcion.dataset.local))) {
                const copia = opcion.cloneNode(true);
                copia.textContent = opcion.dataset.nombre || opcion.textContent;
                copia.selected = opcion.value === idActual;
                sala.append(copia);
            }
        });
        sala.value = idActual;
        if (sala.selectedIndex < 0) sala.selectedIndex = 0;
        sala.disabled = !local.value;
        actualizarInformacion();
    }

    local.addEventListener("change", () => filtrarSalas());
    sala.addEventListener("change", actualizarInformacion);
    pelicula.addEventListener("change", actualizarInformacion);
    fecha.addEventListener("input", actualizarInformacion);
    filtrarSalas(salaInicial);
}
