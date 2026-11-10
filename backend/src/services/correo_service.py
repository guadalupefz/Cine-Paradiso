from io import BytesIO
from flask_mail import Mail, Message
from urllib.parse import quote_plus
from flask import current_app

from backend.src.services.qr_service import generar_qr
from backend.src.constants import ESTADO_COMPRA_CONFIRMADA

mail = Mail()


def enviar_mail_compra(comprobante, entradas_qr):
    compra = comprobante["compra"]
    entradas = comprobante["entradas"]

    if compra["estado"] != ESTADO_COMPRA_CONFIRMADA:
        raise ValueError("La compra no está confirmada")

    mensaje = Message(
        subject=f"Cine Paradiso - Compra {compra['id_compra']}",
        recipients=[compra["email"]]
    )

    detalle_entradas = ""

    for entrada in entradas:
        direccion = entrada.get("direccion") or ""

        enlace_mapa = ""
        if direccion:
            enlace_mapa = (
                "https://www.google.com/maps/search/?api=1&query="
                + quote_plus(direccion)
            )

        detalle_entradas += (
            f"\nPelícula: {entrada['pelicula']}"
            f"\nFunción: {entrada['fecha_hora_inicio']}"
            f"\nCine: {entrada['local']}"
            f"\nDirección: {direccion or 'No disponible'}"
            f"\nUbicación: {enlace_mapa or 'No disponible'}"
            f"\nSala: {entrada['sala']}"
            f"\nButaca: {entrada['fila']}{entrada['numero']}\n"
        )

    detalle_servicios = ""

    for servicio in comprobante.get("servicios", []):
        detalle_servicios += (
            f"\n- {servicio['nombre']} x{servicio['cantidad']}: "
            f"${servicio['subtotal']}"
        )

    if not detalle_servicios:
        detalle_servicios = "\nSin servicios adicionales"

    frontend_url = current_app.config["FRONTEND_URL"]
    enlace_compras = f"{frontend_url}/mis-compras"

    mensaje.body = (
        f"hola {compra['nombre']}!\n\n"
        f"tu compra {compra['id_compra']} fue confirmada\n"
        f"Total: ${compra['total']}\n"
        f"\nServicios adicionales:{detalle_servicios}\n\n"
        f"\ntus entradas:\n{detalle_entradas}\n"
        "Estos son los codigos qr de tus entradas\n\n"
        "Consultá tus entradas y gestioná tus compras:\n"
        f"\n{enlace_compras}\n"
    )

    for entrada in entradas_qr:
        imagen = generar_qr(entrada["qr_token"])

        archivo = BytesIO()
        imagen.save(archivo, format="PNG")

        mensaje.attach(
            filename=f"entrada_{entrada['id_entrada']}.png",
            content_type="image/png",
            data=archivo.getvalue()
        )

    mail.send(mensaje)
