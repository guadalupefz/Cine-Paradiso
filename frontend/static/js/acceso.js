document.querySelectorAll("[data-mostrar-password]").forEach((boton) => {
    const campo = document.getElementById(boton.dataset.mostrarPassword);
    if (!campo) return;
    boton.addEventListener("click", () => {
        const mostrar = campo.type === "password";
        campo.type = mostrar ? "text" : "password";
        boton.textContent = mostrar ? "Ocultar" : "Mostrar";
        boton.setAttribute("aria-pressed", String(mostrar));
    });
});
