from backend.src.repositories import salas_repository as repo


def obtener_salas_por_local(cursor, id_local):
    if not repo.existe_local(cursor, id_local):
        return None

    return repo.obtener_salas_por_local(cursor, id_local)


def crear_sala(cursor, id_local, nombre, capacidad):
    if not repo.existe_local(cursor, id_local):
        return None

    return repo.crear_sala(cursor, id_local, nombre, capacidad)
