document.addEventListener("DOMContentLoaded", () => {
    const envolturaServicios = document.querySelector(".envoltura-servicios");
    const inputServiciosOcultos = document.getElementById("input-servicios-ocultos");
    const textoServiciosAgregados = document.getElementById("texto-servicios-agregados");
    const montoTotalVisita = document.getElementById("monto-total-visita");

    const cantidadButacas = parseInt(envolturaServicios.dataset.cantidadButacas) || 0;
    const precioBaseEntrada = parseFloat(envolturaServicios.dataset.precioEntrada) || 8500;
    let subtotalEntradas = cantidadButacas * precioBaseEntrada;

    let carritoServicios = {};

    function actualizarVista() {
        let totalItems = 0;
        let totalServicios = 0;
        let arrayParaBackend = [];

        for (const [idServicio, cantidad] of Object.entries(carritoServicios)) {
            if (cantidad > 0) {
                totalItems += cantidad;
                const tarjeta = document.querySelector(`.tarjeta-servicio[data-id="${idServicio}"]`);

                const precio = parseFloat(tarjeta.querySelector(".precio-servicio").getAttribute("data-precio")) || 0;
                totalServicios += precio * cantidad;

                for (let i = 0; i < cantidad; i++) {
                    arrayParaBackend.push(idServicio);
                }
            }
        }

        if (textoServiciosAgregados) {
            textoServiciosAgregados.querySelector("span").textContent = `Servicios agregados: ${totalItems}`;
            textoServiciosAgregados.querySelector("strong").textContent = `ARS ${totalServicios.toLocaleString()}`;
        }

        let totalGeneral = subtotalEntradas + totalServicios;
        if (montoTotalVisita) {
            montoTotalVisita.textContent = `ARS ${totalGeneral.toLocaleString()}`;
        }

        if (inputServiciosOcultos) {
            inputServiciosOcultos.value = arrayParaBackend.join(",");
        }
    }

    document.querySelectorAll(".tarjeta-servicio").forEach(tarjeta => {
        const idServicio = tarjeta.getAttribute("data-id");
        const btnSumar = tarjeta.querySelector(".btn-sumar");
        const btnRestar = tarjeta.querySelector(".btn-restar");
        const spanContador = document.getElementById(`cant-${idServicio}`);

        carritoServicios[idServicio] = 0;

        if (btnSumar && btnRestar && spanContador) {
            btnSumar.addEventListener("click", () => {
                carritoServicios[idServicio]++;
                spanContador.textContent = carritoServicios[idServicio];
                btnRestar.disabled = false;
                actualizarVista();
            });

            btnRestar.addEventListener("click", () => {
                if (carritoServicios[idServicio] > 0) {
                    carritoServicios[idServicio]--;
                    spanContador.textContent = carritoServicios[idServicio];
                    if (carritoServicios[idServicio] === 0) {
                        btnRestar.disabled = true;
                    }
                    actualizarVista();
                }
            });
        }
    });

    actualizarVista();
});