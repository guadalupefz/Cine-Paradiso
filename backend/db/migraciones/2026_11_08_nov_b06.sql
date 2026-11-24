-- NOV-B06: identifica películas importadas desde OMDb por su IMDb ID.
ALTER TABLE pelicula
    ADD COLUMN id_externo_api VARCHAR(20) NULL AFTER id_pelicula,
    ADD UNIQUE KEY uq_pelicula_id_externo_api (id_externo_api);
