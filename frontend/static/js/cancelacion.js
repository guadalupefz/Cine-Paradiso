document.addEventListener("DOMContentLoaded", () => {
    cargarMisEntradas();
});

async function cargarMisEntradas() {
    const contenedorEntradas = document.getElementById("contenedor-entradas"); // Asegúrate que este sea el ID en tu HTML
    
    // Recuperar el token JWT guardado al iniciar sesión
    const token = localStorage.getItem("access_token"); 

    if (!token) {
        window.location.href = "/login"; // Redirigir si no está autenticado
        return;
    }

    try {
        const response = await fetch("/api/mis-entradas", {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            }
        });

        const data = await response.json();

        if (response.ok && data.success) {
            renderizarEntradas(data.entradas);
        } else {
            console.error("Error al obtener entradas:", data.message);
            contenedorEntradas.innerHTML = `<p class="text-danger">No se pudieron cargar tus entradas.</p>`;
        }
    } catch (error) {
        console.error("Error de conexión:", error);
    }
}

function renderizarEntradas(entradas) {
    const contenedor = document.getElementById("contenedor-entradas");
    contenedor.innerHTML = "";

    if (entradas.length === 0) {
        contenedor.innerHTML = `<p>No tenés entradas compradas actualmente.</p>`;
        return;
    }

    entradas.forEach(entrada => {
        const tarjeta = document.createElement("div");
        tarjeta.className = "entrada-card";
        tarjeta.innerHTML = `
            <h3>${entrada.pelicula_titulo}</h3>
            <p><strong>Función:</strong> ${entrada.fecha_funcion} - ${entrada.hora_funcion}</p>
            <p><strong>Sala:</strong> ${entrada.sala_nombre}</p>
            <p><strong>Butacas:</strong> ${entrada.butacas.join(", ")}</p>
            <p><strong>Código QR:</strong> <img src="${entrada.qr_url}" alt="QR Entradas" width="100"></p>
        `;
        contenedor.appendChild(tarjeta);
    });
}
