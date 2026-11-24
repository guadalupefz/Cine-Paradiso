document.addEventListener("DOMContentLoaded", () => {
    configurarTabs();
    configurarModalCancelacion();
});

function configurarTabs() {
    const tabs = document.querySelectorAll(".tab");
    const contenidos = document.querySelectorAll(".contenido-tab");

    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            const targetId = tab.getAttribute("data-tab");

            tabs.forEach(t => t.classList.remove("active"));
            contenidos.forEach(c => c.classList.remove("active"));

            tab.classList.add("active");
            const seccionActiva = document.getElementById(targetId);
            if (seccionActiva) {
                seccionActiva.classList.add("active");
            }
        });
    });
}

function configurarModalCancelacion() {
    const modal = document.getElementById("modal-cancelacion");
    const formulario = document.getElementById("form-cancelacion");
    const cerrarModal = document.getElementById("cerrar-modal-cancelacion");
    const botonesAbrir = document.querySelectorAll(".boton-cancelar-compra");

    botonesAbrir.forEach(btn => {
        btn.addEventListener("click", (e) => {
            e.preventDefault();
            const idCompra = btn.getAttribute("data-id-compra");

            if (formulario && idCompra) {
                formulario.action = `/mis-compras/${idCompra}/cancelar`;
            }

            if (modal && typeof modal.showModal === "function") {
                modal.showModal();
            }
        });
    });

    if (cerrarModal && modal) {
        cerrarModal.addEventListener("click", () => {
            modal.close();
        });
    }
}
