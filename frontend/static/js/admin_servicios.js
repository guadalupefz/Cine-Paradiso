document.querySelectorAll("[data-confirmar-eliminacion]").forEach((formulario) => {
    formulario.addEventListener("submit", (evento) => {
        if (!window.confirm("¿Eliminar este servicio? Solo se eliminará si no está asociado a una compra.")) {
            evento.preventDefault();
        }
    });
});
