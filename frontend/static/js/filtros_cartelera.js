document.addEventListener("DOMContentLoaded", () => {
    const botones = document.querySelectorAll(".filtro-genero");
    const peliculas = document.querySelectorAll(".pelicula");

    if (!botones.length || !peliculas.length) {
        return;
    }

    botones.forEach((boton) => {
        boton.addEventListener("click", () => {
            const filtro = boton.dataset.genero;

            botones.forEach((otroBoton) => {
                otroBoton.classList.toggle("activo", otroBoton === boton);
            });

            peliculas.forEach((pelicula) => {
                const genero = pelicula.dataset.genero || "";
                const coincide =
                    filtro === "todos" ||
                    (filtro === "otros"
                        ? genero !== "drama" && genero !== "comedia"
                        : genero.includes(filtro));

                pelicula.hidden = !coincide;
            });
        });
    });
});
