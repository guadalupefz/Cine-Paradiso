document.addEventListener("DOMContentLoaded", function () {
    const modal = document.getElementById("modal-cancelacion");
    const formulario = document.getElementById("form-cancelacion");
    const cerrar = document.getElementById("cerrar-modal-cancelacion");

    if (!modal || !formulario || !cerrar) return;

    document.querySelectorAll(".boton-cancelar-compra").forEach(function (boton) {
        boton.addEventListener("click", function () {
            const idCompra = boton.dataset.idCompra;

            formulario.action = `/mis-compras/${idCompra}/cancelar`;
            modal.showModal();
        });
    });

    cerrar.addEventListener("click", function () {
        modal.close();
    });

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