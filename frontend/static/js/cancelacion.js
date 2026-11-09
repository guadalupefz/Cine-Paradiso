
const aceptar = document.getElementById("aceptar");
const confirmar = document.querySelector(".btn-confirmar");
const comentario = document.getElementById("comentario");
const contador = document.querySelector(".contador");

aceptar.addEventListener("change", () => {
    confirmar.disabled = !aceptar.checked;
});

comentario.addEventListener("input", () => {
    contador.textContent =
        `${comentario.value.length} / 300 caracteres`;
});
