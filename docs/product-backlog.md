# Proyecto Cine Paraíso: Product Backlog

## Requerimientos Prioridad Alta

### Tareas Técnicas:
- **[TEC-01]** Configuración del Repositorio y Entorno Inicial  
  Creación del repositorio en GitHub, invitación de los integrantes, configuración de la estructura inicial de directorios del proyecto y creación del archivo `init.sh` para la gestión de dependencias.
- **[TEC-02]** Definición Conceptual de la Base de Datos  
  Modelado conceptual de las entidades principales del sistema (usuarios, películas, salas, funciones, butacas y entradas) y sus relaciones lógicas generales para el desarrollo posterior.
- **[TEC-03]** Configuración de Conexión SQL y API Backend  
  Implementación del conector MySQL nativo en Flask para la ejecución de sentencias SQL explícitas y estructuración base de respuestas en formato JSON.

### Módulo de Autenticación y Seguridad:
- **[US-01]** Autenticación de Usuarios y Control de Roles  
  Como cliente/administrador, quiero iniciar sesión con credenciales seguras para acceder a las pantallas y recursos correspondientes a mi rol.
- **[US-02]** Registro de Nuevos Clientes  
  Como cliente, quiero registrarme en la plataforma mediante un formulario para poder realizar compras y guardar mi historial de actividad.

### Módulo de Cartelera y Catálogo:
- **[US-03]** Visualización de Cartelera  
  Como cliente, quiero visualizar el listado de películas en cartel, incluyendo sinopsis, póster, duración, clasificación y funciones disponibles, para elegir qué ver.
- **[TEC-04]** Integración con API Externa de Películas  
  Implementación de una API externa en el backend para automatizar la importación y sincronización de datos, agilizando la carga del catálogo para el administrador.
- **[US-05]** Gestión y Configuración de Funciones (Backoffice)  
  Como administrador, quiero asociar una película a un local, sala, fecha y horario específicos para dar de alta una nueva función disponible.


## Requerimientos Prioridad Media

### Módulo de Venta de Entradas y Validación:
- **[US-06]** Selección Interactiva de Butacas  
  Como cliente, quiero visualizar el estado de las butacas de una sala (libres y ocupadas) para seleccionar mis asientos de forma precisa.
- **[US-07]** Checkout y Confirmación por Correo Electrónico  
  Como cliente, quiero confirmar mi compra de entradas y recibir un correo electrónico automático con el comprobante, resumen y código QR de acceso.
- **[US-08]** Adición de Servicios Extra  
  Como cliente, quiero incorporar opcionalmente servicios adicionales (comida, bebidas, estacionamiento) durante el proceso de compra.
- **[US-09]** Validación de Ingreso por Código QR  
  Como personal del cine o administrador, quiero escanear el código QR del cliente en la sala para verificar su validez, comprobar la función y marcarlo como utilizado.
- **[US-10]** Cancelación de Compras  
  Como cliente, quiero poder cancelar una compra efectuada dentro del margen de tiempo límite permitido antes del inicio de la función.

### Módulo de Backoffice y Estadísticas:
- **[US-11]** Administración de Servicios Extra (Backoffice)  
  Como administrador, quiero realizar operaciones de alta, baja y modificación de los servicios adicionales ofrecidos por el cine.
- **[US-12]** Dashboard Informativo de Métricas y Ventas  
  Como administrador, quiero acceder a un panel de control con métricas de ocupación por función/película, recaudación por género, franjas horarias de mayor demanda y registro de cancelaciones.


## Requerimientos Prioridad Baja/Deseables

- **[US-13]** Historial y Perfil de Cliente  
  Como cliente, quiero consultar en mi perfil el historial de consumos y las películas que vi anteriormente.
- **[US-14]** Reseñas y Puntuación de Películas (Deseable)  
  Como cliente con asistencia validada por QR a una función, quiero puntuar y dejar una reseña sobre la película vista.
- **[TEC-05]** Generación de Reportes en PDF (Deseable)  
  Implementar la exportación de reportes en formato PDF con las estadísticas de ventas y rendimiento de películas.
- **[TEC-06]** Contenerización y Despliegue (Deseable)  
  Configurar `Dockerfile` y `docker-compose.yml` para empaquetar la aplicación y desplegar el sistema en un entorno en la nube gratuito.
