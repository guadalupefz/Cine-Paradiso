document.addEventListener("DOMContentLoaded", () => {
    const boton = document.getElementById("btn-escanear");
    const campoToken = document.getElementById("qr_token");

    let scanner = null;

    boton.addEventListener("click", () => {
        if (!scanner) {
            scanner = new Html5Qrcode("reader");
        }

        scanner.start(
            { facingMode: "environment" },
            {
                fps: 10,
                qrbox: 250
            },
            (decodedText) => {
                campoToken.value = decodedText;

                scanner.stop().catch(console.error);

                alert("QR leído correctamente");
            }
        ).catch((error) => {
            console.error(error);
            alert("No se pudo abrir la cámara");
        });
    });
});