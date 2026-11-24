from io import BytesIO
from datetime import datetime
from email.utils import parsedate_to_datetime
from xml.sax.saxutils import escape
import requests

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image

from frontend.utils.api_client import BACKEND_URL


def _tabla_informe_pdf(titulo, encabezados, filas, anchos, estilos):
    """Construye una sección con título y tabla formateada para el informe en PDF."""
    contenido = [
        [
            Paragraph(escape(str(valor if valor is not None else "")), estilos["BodyText"])
            for valor in encabezados
        ]
    ]
    for fila in filas:
        contenido.append([
            Paragraph(
                escape(str(valor if valor is not None else "")),
                estilos["BodyText"],
            )
            for valor in fila
        ])
    if not filas:
        contenido.append([
            Paragraph("Sin datos para mostrar.", estilos["BodyText"]),
            *[Paragraph("", estilos["BodyText"]) for _ in encabezados[1:]],
        ])

    tabla = Table(contenido, colWidths=anchos, repeatRows=1, hAlign="LEFT")
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#922632")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#dfd1b8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
            colors.white,
            colors.HexColor("#fff8e9"),
        ]),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return [Paragraph(escape(titulo), estilos["Heading2"]), Spacer(1, 5), tabla, Spacer(1, 12)]


def crear_informe_estadisticas_pdf(ventas, ocupacion):
    """Genera un archivo PDF con el informe completo de ventas y ocupación para el admin."""
    buffer = BytesIO()
    documento = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="Informe de ventas y rendimiento",
        author="Cine Paradiso",
    )
    estilos = getSampleStyleSheet()
    historia = [
        Paragraph("Informe de ventas y rendimiento", estilos["Title"]),
        Paragraph(
            f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}. "
            "Incluye los datos históricos disponibles.",
            estilos["BodyText"],
        ),
        Spacer(1, 14),
    ]

    historia.extend(_tabla_informe_pdf(
        "Ventas por género",
        ["Género", "Entradas vendidas", "Recaudación estimada"],
        [
            [
                fila.get("genero") or "Sin género",
                fila.get("entradas_vendidas", 0),
                f"${fila.get('importe_estimado_entradas', 0)}",
            ]
            for fila in ventas.get("ventas_por_genero", [])
        ],
        [52 * mm, 48 * mm, 70 * mm],
        estilos,
    ))

    historia.extend(_tabla_informe_pdf(
        "Ventas por franja horaria",
        ["Franja", "Entradas vendidas", "Recaudación estimada"],
        [
            [
                fila.get("franja_horaria", ""),
                fila.get("entradas_vendidas", 0),
                f"${fila.get('importe_estimado_entradas', 0)}",
            ]
            for fila in ventas.get("ventas_por_franja_horaria", [])
        ],
        [52 * mm, 48 * mm, 70 * mm],
        estilos,
    ))

    historia.extend([
        Paragraph("Cancelaciones", estilos["Heading2"]),
        Paragraph(
            f"Compras canceladas: {ventas.get('cantidad_cancelaciones', 0)}",
            estilos["BodyText"],
        ),
        Spacer(1, 12),
    ])

    historia.extend(_tabla_informe_pdf(
        "Ocupación por función",
        ["Película", "Inicio", "Sala", "Butacas", "Capacidad", "Ocupación"],
        [
            [
                fila.get("pelicula", ""),
                fila.get("fecha_hora_inicio", ""),
                fila.get("sala", ""),
                fila.get("butacas_ocupadas", 0),
                fila.get("capacidad", 0),
                f"{fila.get('porcentaje_ocupacion', 0)}%",
            ]
            for fila in ocupacion.get("ocupacion_por_funcion", [])
        ],
        [40 * mm, 36 * mm, 24 * mm, 22 * mm, 24 * mm, 24 * mm],
        estilos,
    ))

    historia.extend(_tabla_informe_pdf(
        "Ocupación por película",
        ["Película", "Ocupación promedio", "Aforo total vendido"],
        [
            [
                fila.get("pelicula", ""),
                f"{fila.get('porcentaje_ocupacion', 0)}%",
                f"{fila.get('butacas_ocupadas', 0)} / {fila.get('capacidad_total', 0)}",
            ]
            for fila in ocupacion.get("ocupacion_por_pelicula", [])
        ],
        [70 * mm, 50 * mm, 50 * mm],
        estilos,
    ))

    documento.build(historia)
    buffer.seek(0)
    return buffer


def formatear_fecha(fecha):
    """Formatea cadenas de fecha u objetos datetime a formato legible DD/MM/YYYY - HH:MM."""
    if not fecha:
        return "No disponible"

    try:
        fecha_obj = parsedate_to_datetime(str(fecha))
        return fecha_obj.strftime("%d/%m/%Y - %H:%M")
    except (TypeError, ValueError):
        return str(fecha)


def crear_tabla(datos, anchos, encabezado=False):
    """Crea una tabla estilizada de ReportLab."""
    tabla = Table(datos, colWidths=anchos)
    estilos_tabla = [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE")
    ]
    if encabezado:
        estilos_tabla.append(
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eee4d5"))
        )
    tabla.setStyle(TableStyle(estilos_tabla))
    return tabla


def agregar_entrada(elementos, entrada, estilos, estilo_codigo, token_session=None):
    """Agrega la sección y tabla de una entrada con su correspondiente imagen de código QR."""
    elementos.append(Paragraph(
        f"&lt;b&gt;{escape(str(entrada.get('pelicula', '')))}&lt;/b&gt;",
        estilos["Heading3"]
    ))

    datos = [
        ["Función", escape(formatear_fecha(entrada.get("fecha_hora_inicio", "")))],
        ["Cine", escape(str(entrada.get("local", "")))],
        ["Dirección", escape(str(entrada.get("direccion", "No disponible")))],
        ["Sala", escape(str(entrada.get("sala", "")))],
        ["Butaca", f"{escape(str(entrada.get('fila', '')))}{escape(str(entrada.get('numero', '')))}"]
    ]

    elementos.append(crear_tabla(datos, [35 * mm, 120 * mm]))
    elementos.append(Spacer(1, 8))

    headers = {}
    if token_session:
        headers["Authorization"] = "Bearer " + token_session

    try:
        respuesta_qr = requests.get(
            f"{BACKEND_URL}/qr/{entrada['id_entrada']}",
            headers=headers,
            timeout=15
        )
        if respuesta_qr.status_code == 200:
            imagen_qr = Image(
                BytesIO(respuesta_qr.content),
                width=35 * mm,
                height=35 * mm
            )
            elementos.append(imagen_qr)
            elementos.append(Spacer(1, 5))
    except requests.exceptions.RequestException:
        pass

    codigo_manual = entrada.get("qr_token", "No disponible")
    texto_codigo = Paragraph(
        f"Token QR: &lt;b&gt;{escape(str(codigo_manual))}&lt;/b&gt;",
        estilo_codigo
    )
    elementos.append(texto_codigo)
    elementos.append(Spacer(1, 15))


def agregar_servicios(elementos, servicios, estilos):
    """Agrega la sección y tabla de servicios adicionales comprados."""
    elementos.append(Paragraph(
        "SERVICIOS ADICIONALES",
        estilos["Heading2"]
    ))

    if servicios:
        datos = [["Servicio", "Cantidad", "Subtotal"]]
        for servicio in servicios:
            datos.append([
                escape(str(servicio.get("nombre", ""))),
                str(servicio.get("cantidad", 0)),
                f"$ {servicio.get('subtotal', 0)}"
            ])
        elementos.append(
            crear_tabla(datos, [80 * mm, 30 * mm, 45 * mm], encabezado=True)
        )
    else:
        elementos.append(Paragraph(
            "No se compraron servicios adicionales.",
            estilos["Normal"]
        ))

    elementos.append(Spacer(1, 15))


def crear_comprobante_pdf(compra, entradas, servicios, token_session=None):
    """Genera el comprobante de compra en PDF con código QR e información completa."""
    buffer = BytesIO()
    documento = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm
    )

    estilos = getSampleStyleSheet()
    elementos = []

    titulo = ParagraphStyle(
        "TituloCine",
        parent=estilos["Title"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#702f24"),
        fontSize=20,
        spaceAfter=15
    )

    estilo_codigo = ParagraphStyle(
        "CodigoValidacion",
        parent=estilos["Normal"],
        alignment=TA_CENTER,
        fontSize=9,
        textColor=colors.HexColor("#444444")
    )

    elementos.append(Paragraph("CINE PARADISO", titulo))
    elementos.append(Paragraph(
        f"Comprobante de compra N° {compra.get('id_compra', '')}",
        estilos["Heading2"]
    ))
    elementos.append(Spacer(1, 10))

    datos_compra = [
        ["Cliente", f"{escape(str(compra.get('nombre', '')))} {escape(str(compra.get('apellido', '')))}"],
        ["Email", escape(str(compra.get("email", "")))],
        ["Fecha", escape(formatear_fecha(compra.get("fecha_hora", "")))],
        ["Estado", escape(str(compra.get("estado", "")))],
        ["Total", f"$ {compra.get('total', 0)}"]
    ]

    elementos.append(crear_tabla(
        datos_compra,
        [35 * mm, 120 * mm]
    ))

    elementos.append(Spacer(1, 18))
    elementos.append(Paragraph("ENTRADAS", estilos["Heading2"]))

    for entrada in entradas:
        agregar_entrada(elementos, entrada, estilos, estilo_codigo, token_session)

    agregar_servicios(elementos, servicios, estilos)

    documento.build(elementos)
    buffer.seek(0)
    return buffer
