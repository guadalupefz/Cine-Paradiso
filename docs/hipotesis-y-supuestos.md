# Sistema de venta de entradas de cine — Cine Paradiso

## 1. Hipótesis

Se plantea que el desarrollo de una aplicación web permitirá a Cine Paradiso centralizar, en un único sistema, la gestión de sus tres locales, incluidas las películas, las salas, las funciones, las ventas y los servicios adicionales. Esta mejora se considerará verificable si los administradores pueden consultar y modificar dicha información desde la aplicación, sin recurrir a registros independientes para cada local.

Se considera que una plataforma en línea que permita a los usuarios consultar la cartelera, seleccionar una función, elegir sus butacas y realizar compras contribuirá a reducir el tiempo necesario para completar una transacción y a disminuir los errores en la asignación de butacas. Esta hipótesis se validará mediante pruebas de uso que midan el tiempo requerido para efectuar una compra y la cantidad de conflictos de reserva registrados.

Asimismo, se espera que el sistema facilite las tareas administrativas mediante herramientas destinadas a gestionar salas, programar funciones, administrar servicios adicionales y consultar estadísticas de ventas y ocupación. Esta hipótesis se considerará cumplida si un administrador puede ejecutar dichas operaciones desde el sistema y obtener informes filtrados por local, sala y período.

## 2. Supuestos

Para el desarrollo del sistema se establecen los siguientes supuestos iniciales:

1. **Locales y salas:** Cine Paradiso cuenta con exactamente tres locales. Cada local dispone de una o más salas, y cada sala tiene una capacidad definida mediante un número entero positivo de butacas.

2. **Películas y funciones:** una película puede proyectarse en distintas funciones. Cada función corresponde a una única película, una única sala y una fecha y hora de inicio previamente establecidas. No podrán existir dos funciones superpuestas en una misma sala.

3. **Butacas:** cada sala cuenta con butacas identificadas individualmente mediante un código único dentro de la sala. Una butaca no podrá venderse ni reservarse para más de una compra confirmada en una misma función.

4. **Usuarios y roles:** el sistema contempla dos roles principales: cliente y administrador. El cliente puede consultar funciones, seleccionar butacas y comprar entradas; el administrador puede gestionar la información operativa y consultar estadísticas. Cada usuario tendrá un único rol activo.

5. **Compras:** los clientes podrán adquirir entradas únicamente para funciones con estado disponible y contratar los servicios adicionales habilitados para dicha función o compra. Cada compra deberá registrar, como mínimo, el cliente, la función, las butacas, el importe total, la fecha y el estado de la operación.

6. **Confirmación de compra:** una vez aprobada una compra, el sistema deberá generar un código QR por entrada asociado de forma única a ella y enviar un correo electrónico de confirmación a la dirección registrada del cliente. Si el envío falla, la compra deberá conservar su estado y quedar registrada para su reintento o consulta administrativa.

7. **Cancelaciones:** las entradas podrán cancelarse únicamente hasta el plazo establecido antes del inicio de la función. El sistema deberá rechazar automáticamente las solicitudes recibidas después de dicho límite y registrar la fecha, el usuario y el resultado de cada solicitud.

8. **Administración:** los administradores podrán crear, consultar, modificar y desactivar películas, salas, funciones y servicios, siempre que dichos cambios no contradigan compras confirmadas. También podrán consultar estadísticas de ventas y ocupación filtradas, como mínimo, por local y período.

9. **Catálogo de películas:** el sistema consumirá una API externa gratuita para obtener información sobre las películas. Deberá almacenar la identificación externa, el título, la sinopsis, la duración, la clasificación y la fecha de consulta. Si la API no estuviera disponible, el sistema deberá conservar la última información válida o permitir su carga manual por parte de un administrador.

10. **Acceso al sistema:** las funcionalidades estarán disponibles según el rol del usuario. El servidor deberá verificar el acceso a cada funcionalidad protegida. Si un usuario no está autenticado, el sistema responderá con el código HTTP **401 (Unauthorized)**. Si se solicita un recurso que no existe, responderá con el código HTTP **404 (Not Found)**.

11. **Acceso desde dispositivos móviles:** la aplicación web deberá adaptarse a pantallas con un ancho mínimo de 320 píxeles y funcionar en las versiones vigentes de los navegadores Chrome, Firefox, Safari y Edge en celulares, tabletas y computadoras. Las funciones principales de consulta y compra no deberán requerir desplazamiento horizontal.

Los aspectos que aún no estén definidos deberán acordarse durante la planificación del proyecto y registrarse antes de iniciar la implementación de las funcionalidades afectadas. Como mínimo, deberán establecerse el plazo exacto de cancelación, los medios de pago aceptados, los servicios adicionales disponibles, la API externa seleccionada, las políticas de reembolso, el tiempo de retención de las reservas no pagadas y los criterios de disponibilidad de las funciones.
