-- Ejecutar sobre la base seleccionada antes de iniciar la aplicación actualizada.
ALTER TABLE pelicula MODIFY COLUMN poster VARCHAR(2048) NOT NULL;
