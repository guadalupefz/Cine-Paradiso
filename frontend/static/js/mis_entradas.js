document.addEventListener("DOMContentLoaded", () => {
    const tabs = document.querySelectorAll(".tab[data-tab]");
    const secciones = document.querySelectorAll(".contenido-tab");

    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            tabs.forEach(item => item.classList.remove("active"));
            secciones.forEach(item => item.classList.remove("active"));
            tab.classList.add("active");
            document.getElementById(tab.dataset.tab)?.classList.add("active");
        });
    });

    const modal = document.getElementById("modalCancelacion");
    const formulario = document.getElementById("formCancelarCompra");
    const cerrar = document.getElementById("cerrarModal");
    const conservar = document.getElementById("conservarEntradas");

    function cerrarModal() {
        modal?.classList.remove("visible");
        modal?.setAttribute("aria-hidden", "true");
    }

    document.querySelectorAll(".boton-cancelar-compra").forEach(boton => {
        boton.addEventListener("click", () => {
            const id = boton.dataset.idCompra;
            formulario.action = `/mis-compras/${id}/cancelar`;
            document.getElementById("textoCompraModal").textContent = `Compra #${id}. Revisá los datos antes de confirmar.`;
            document.getElementById("modalPelicula").textContent = boton.dataset.pelicula || "Compra de entradas";
            document.getElementById("modalPeliculaPoster").textContent = boton.dataset.pelicula || "CINE PARADISO";
            document.getElementById("modalFecha").textContent = boton.dataset.fecha || "Fecha no disponible";
            document.getElementById("modalHoraSala").textContent = [boton.dataset.hora, boton.dataset.sala].filter(Boolean).join(" · ");
            document.getElementById("modalButacas").textContent = boton.dataset.butacas ? `Butacas: ${boton.dataset.butacas}` : "";
            document.getElementById("modalTotal").textContent = `ARS ${boton.dataset.total || "0"}`;
            modal.classList.add("visible");
            modal.setAttribute("aria-hidden", "false");
        });
    });

    cerrar?.addEventListener("click", cerrarModal);
    conservar?.addEventListener("click", cerrarModal);
    modal?.addEventListener("click", event => {
        if (event.target === modal) cerrarModal();
    });
    formulario?.addEventListener("submit", event => {
        if (!window.confirm("¿Confirmás la cancelación de toda esta compra?")) {
            event.preventDefault();
        }
    });

});
