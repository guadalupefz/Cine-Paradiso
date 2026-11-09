document.addEventListener("DOMContentLoaded", () => {
    // 1. Activar la interactividad de las pestañas (Tabs)
    configurarTabs();

    // 2. Activar la lógica del modal de cancelación
    configurarModalCancelacion();
});

// --- LÓGICA DE LAS PESTAÑAS ---
function configurarTabs() {
    const tabs = document.querySelectorAll(".tab");
    const contenidos = document.querySelectorAll(".contenido-tab");

    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            const targetId = tab.getAttribute("data-tab");

            // Remover la clase active de todas las pestañas y contenidos
            tabs.forEach(t => t.classList.remove("active"));
            contenidos.forEach(c => c.classList.remove("active"));

            // Activar la pestaña clickeada y su sección correspondiente
            tab.classList.add("active");
            const seccionActiva = document.getElementById(targetId);
            if (seccionActiva) {
                seccionActiva.classList.add("active");
            }
        });
    });
}

// --- LÓGICA DEL MODAL Y CANCELACIÓN DE COMPRAS ---
function configurarModalCancelacion() {
    const modal = document.getElementById("modalCancelacion");
    const botonesAbrir = document.querySelectorAll(".btn-cancelar"); // Los botones en cada tarjeta
    const cerrarModal = document.getElementById("cerrarModal");
    const conservarEntradas = document.getElementById("conservarEntradas");
    const aceptarCheckbox = document.getElementById("aceptarCancelacion");
    const confirmarBtn = document.getElementById("confirmarCancelacion");

    let compraIdSeleccionada = null;

    // Abrir modal al hacer clic en "Cancelar compra"
    botonesAbrir.forEach(btn => {
        btn.addEventListener("click", (e) => {
            // Si el botón está dentro de un form, evitamos que recargue la página por defecto
            e.preventDefault();
            
            // Obtenemos el id_compra del atributo data (o podemos extraerlo del HTML)
            compraIdSeleccionada = btn.getAttribute("data-id-compra");
            
            if (modal) {
                modal.style.display = "flex";
            }
        });
    });

    // Cerrar modal
    const cerrarAccion = () => {
        if (modal) modal.style.display = "none";
        if (aceptarCheckbox) aceptarCheckbox.checked = false;
        if (confirmarBtn) confirmarBtn.disabled = true;
    };

    if (cerrarModal) cerrarModal.addEventListener("click", cerrarAccion);
    if (conservarEntradas) conservarEntradas.addEventListener("click", cerrarAccion);

    // Habilitar botón de confirmación solo si tilda el checkbox
    if (aceptarCheckbox && confirmarBtn) {
        aceptarCheckbox.addEventListener("change", (e) => {
            confirmarBtn.disabled = !e.target.checked;
        });

        // Manejar la petición POST al backend cuando confirma
        confirmarBtn.addEventListener("click", async () => {
            if (!compraIdSeleccionada) return;

            const token = localStorage.getItem("access_token");
            if (!token) {
                window.location.href = "/login";
                return;
            }

            try {
                const response = await fetch(`/compras/${compraIdSeleccionada}/cancelar`, {
                    method: "POST",
                    headers: {
                        "Authorization": `Bearer ${token}`,
                        "Content-Type": "application/json"
                    }
                });

                const data = await response.json();

                if (response.ok) {
                    // Ocultar modal de cancelación y mostrar el de éxito (o recargar)
                    modal.style.display = "none";
                    const modalExito = document.getElementById("modalExito");
                    if (modalExito) {
                        modalExito.style.display = "flex";
                        document.getElementById("finalizar").onclick = () => location.reload();
                    } else {
                        alert(data.mensaje || "Compra cancelada correctamente.");
                        location.reload();
                    }
                } else {
                    alert(data.error || "No se pudo cancelar la compra.");
                }
            } catch (error) {
                console.error("Error de red:", error);
                alert("Ocurrió un error al procesar la cancelación.");
            }
        });
    }
}
