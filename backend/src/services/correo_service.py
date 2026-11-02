from io import BytesIO
from flask_mail import Mail, Message

from backend.src.services.qr_service import generar_qr

mail = Mail()


def enviar_mail_compra(comprobante, entradas_qr):
    compra = comprobante["compra"]
    entradas = comprobante["entradas"]

    if compra["estado"] not in ("aprobada", "confirmada"):
        raise ValueError("La compra no está confirmada")

    mensaje = Message(
        subject=f"Cine Paradiso - Compra {compra['id_compra']}",
        recipients=[compra["email"]]
    )

    detalle_entradas = ""

    for entrada in entradas:
        detalle_entradas += (
            f"\nPelícula: {entrada['pelicula']}"
            f"\nFunción: {entrada['fecha_hora_inicio']}"
            f"\nCine: {entrada['local']}"
            f"\nSala: {entrada['sala']}"
            f"\nButaca: {entrada['fila']}{entrada['numero']}\n"
        )

    mensaje.body = (
        f"hola {compra['nombre']}!\n\n"
        f"tu compra {compra['id_compra']} fue confirmada\n"
        f"Total: ${compra['total']}\n"
        f"\ntus entradas:\n{detalle_entradas}\n"
        "Estos son los codigos qr de tus entradas\n\n"
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