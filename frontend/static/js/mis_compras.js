document.addEventListener("DOMContentLoaded", function () {
    const modal = document.getElementById("modal-cancelacion");
    const formulario = document.getElementById("form-cancelacion");
    const cerrar = document.getElementById("cerrar-modal-cancelacion");

    if (!modal || !formulario || !cerrar) return;

    // Abrir el modal y configurar la ruta de cancelación.
    document.querySelectorAll(".boton-cancelar-compra").forEach(function (boton) {
        boton.addEventListener("click", function () {
            const idCompra = boton.dataset.idCompra;

            formulario.action = `/mis-compras/${idCompra}/cancelar`;
            modal.showModal();
        });
    });

    // Confirmar antes de enviar el formulario.
    formulario.addEventListener("submit", function (event) {
        const confirmar = window.confirm("¿Querés cancelar esta compra?");

        if (!confirmar) {
            event.preventDefault();
        }
    });

    // Cerrar el modal sin cancelar la compra.
    cerrar.addEventListener("click", function () {
        modal.close();
    });

    // Recuperar la apertura del modal si hay una compra pendiente de cancelar.
    const idCompraCancelar = modal.dataset.idCompraCancelar;

    if (idCompraCancelar) {
        const boton = document.querySelector(
            `.boton-cancelar-compra[data-id-compra="${idCompraCancelar}"]`
        );

        if (boton) {
            boton.click();
        }
    }
});