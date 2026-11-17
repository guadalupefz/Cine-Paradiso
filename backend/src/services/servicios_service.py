from backend.src.repositories import servicios_repository as repo


def listar_servicios(cursor):
    return repo.obtener_servicios(cursor)


def obtener_servicio(cursor, id_servicio):
    return repo.obtener_servicio(cursor, id_servicio)


def crear_servicio(cursor, nombre, descripcion, precio, imagen):
    return repo.crear_servicio(
        cursor, nombre, descripcion, precio, imagen
    )


def modificar_servicio(cursor, id_servicio, nombre, descripcion, precio, imagen):
    return repo.modificar_servicio(
        cursor, id_servicio, nombre, descripcion, precio, imagen
    )


def eliminar_servicio(cursor, id_servicio):
    return repo.eliminar_servicio(cursor, id_servicio)
