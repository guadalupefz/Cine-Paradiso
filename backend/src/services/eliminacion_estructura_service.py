from backend.src.repositories import locales_repository as locales
from backend.src.repositories import salas_repository as salas


def eliminar_estructura(cursor, tipo, identificador):
    """Coordina la eliminación de salas o locales sin actividad."""

    if tipo not in ("local", "sala"):
        raise ValueError("Tipo de estructura inválido")

    if tipo == "local":
        elemento = locales.bloquear_local(cursor, identificador)

        if elemento is not None:
            locales.bloquear_salas_del_local(cursor, identificador)
            en_uso = locales.local_en_uso(cursor, identificador)

    else:
        elemento = salas.bloquear_sala(cursor, identificador)

        if elemento is not None:
            en_uso = salas.sala_en_uso(cursor, identificador)

    if elemento is None:
        return "no_existe"

    if en_uso:
        return "en_uso"

    if tipo == "local":
        eliminados = locales.eliminar_local_salas_y_butacas(
            cursor, identificador
        )
    else:
        eliminados = salas.eliminar_sala_y_butacas(
            cursor, identificador
        )

    if eliminados != 1:
        return "no_eliminado"

    return "eliminado"
