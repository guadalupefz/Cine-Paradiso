from datetime import datetime

def validar_crear_funcion(data):
    
    error = None

    if not data:
        error = "No se proporcionaron datos en formato JSON."
    elif not data.get('id_pelicula'):
        error = 'El campo id_pelicula es obligatorio.'
    elif not isinstance(data.get('id_pelicula'), int):
        error = 'El id_pelicula debe ser un número entero.'
    elif not data.get('id_sala'):
        error = 'El campo id_sala es obligatorio.'
    elif not isinstance(data.get('id_sala'), int):
        error = 'El id_sala debe ser un número entero.'
    elif not data.get('fecha_hora_inicio'):
        error = 'El campo fecha_hora_inicio es obligatorio.'
    else:
    
        try:
            datetime.fromisoformat(data.get('fecha_hora_inicio'))
        except ValueError:
            error = 'Formato de fecha_hora_inicio inválido. Utilice formato ISO (YYYY-MM-DDTHH:MM:SS).'

        if error is None:
            precio = data.get('precio_base')
            if precio is None:
                error = 'El campo precio_base es obligatorio.'
            else:
                try:
                    if float(precio) < 0:
                        error = 'El precio_base no puede ser negativo.'
                except (ValueError, TypeError):
                    error = 'El precio_base debe ser un valor numérico.'

    return error