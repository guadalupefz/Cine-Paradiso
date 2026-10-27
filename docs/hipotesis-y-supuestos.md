# Sistema de venta de entradas de cine — Cine Paradiso — Hipótesis y supuestos

## 1. Hipótesis

**1.1. Centralización de la información**

Se plantea que centralizar la información de las tres sucursales permitirá administrar las películas, funciones, salas y compras desde un único sistema, facilitando la organización y el acceso a la información.

**1.2. Simplificación de la compra de entradas**

Se plantea que permitir la compra de entradas por internet facilitará el proceso para los clientes y reducirá los errores relacionados con la disponibilidad de butacas.

**1.3. Simplificación de la administración**

Se plantea que contar con un panel de administración permitirá gestionar la información del cine y consultar estadísticas de manera más sencilla.

## 2. Supuestos y decisiones de funcionamiento

### 2.1. Cancelación de compras

Se propone permitir la cancelación de una compra hasta dos horas antes del comienzo de la función. Una vez superado ese límite, el sistema no permitirá cancelarla.

### 2.2. Reserva temporal de butacas

Cuando un cliente seleccione una butaca, esta quedará reservada temporalmente durante diez minutos para que pueda completar la compra. Si el tiempo se cumple sin confirmar la operación, la butaca volverá a estar disponible.

Antes de confirmar la compra, el sistema deberá verificar nuevamente que las butacas seleccionadas continúen disponibles.

### 2.3. Registro e inicio de sesión

Los clientes podrán consultar la cartelera sin iniciar sesión. Para realizar una compra, deberán registrarse o iniciar sesión con una cuenta existente.

El sistema permitirá consultar el perfil y las compras realizadas por cada cliente.

### 2.4. Confirmación de compras y pagos

El sistema contará con una pantalla de pago simulado, sin procesar dinero real ni integrar una plataforma de pagos externa.

Una compra se considerará confirmada únicamente cuando el sistema registre que el pago fue aprobado. Si el pago es rechazado, la compra no se confirmará y las butacas reservadas volverán a estar disponibles.

Mientras el pago no tenga un resultado definitivo, la compra permanecerá pendiente y no se emitirán entradas confirmadas.

### 2.5. Servicios adicionales

Los clientes podrán agregar servicios adicionales disponibles a su compra, según lo que ofrezca el cine.

Si una compra que incluye servicios adicionales se cancela dentro del plazo permitido, los servicios asociados también quedarán cancelados. No se permitirá cancelar los servicios por separado desde el sistema una vez superado el plazo de cancelación de la compra.

### 2.6. Obtención y actualización de información de películas

Se utilizará una API externa gratuita para obtener información de las películas.

Se propone importar los datos al momento de incorporar una película al sistema y permitir que un administrador los actualice manualmente cuando sea necesario.

Si la API no estuviera disponible, el sistema conservará la información ya almacenada. Además, el administrador podrá completar o corregir manualmente los datos necesarios.

### 2.7. Envío de confirmaciones por correo electrónico

Una vez confirmada la compra, el sistema intentará enviar un correo electrónico con los datos de la operación y las entradas correspondientes.

Si el envío falla, la compra seguirá confirmada. El sistema deberá permitir consultar las entradas desde el perfil del cliente y contemplar la posibilidad de volver a intentar el envío del correo.

### 2.8. Modificación o cancelación de funciones con entradas vendidas

No se permitirá eliminar directamente una función que tenga entradas vendidas sin resolver previamente qué ocurrirá con esas compras.

Si una función debe modificarse o cancelarse, se deberá contemplar un procedimiento para gestionar las compras afectadas y notificar a los clientes correspondientes.

### 2.9. Validación de entradas mediante código QR

Cada entrada tendrá un código QR único asociado a su compra y función.

El código será válido únicamente si la compra está confirmada, no fue cancelada y la entrada todavía no fue utilizada. Una vez validada, la entrada quedará marcada como utilizada y no podrá validarse nuevamente.

### 2.10. Permisos y seguridad

Los clientes solo podrán consultar sus propios datos, compras y entradas.

Los administradores podrán realizar las operaciones de gestión que correspondan a su rol. Los endpoints deberán verificar que el usuario tenga autorización para ejecutar cada operación y rechazar las solicitudes de usuarios que no tengan los permisos necesarios.

### 2.11. Cuentas de usuario

El registro solicitará los datos necesarios para identificar al cliente y gestionar sus compras.

Las contraseñas se almacenarán mediante un mecanismo seguro de hash, nunca como texto plano. La creación de cuentas de administrador estará restringida y no podrá realizarse mediante el registro público de clientes.

### 2.12. Disponibilidad y precios de los servicios adicionales

Solo se ofrecerán durante la compra los servicios que estén disponibles.

El precio de cada servicio se registrará en la compra al momento de confirmarla, de modo que los cambios posteriores en los precios no modifiquen las compras anteriores.

## 3. Consideración final

Estas hipótesis y supuestos constituyen una propuesta inicial para definir el funcionamiento de Cine Paradiso y orientar el diseño de la base de datos, los endpoints y las interfaces.

Las decisiones deberán revisarse con el grupo antes de implementarlas. Si alguna contradice un requisito explícito de la consigna, deberá prevalecer lo establecido en el proyecto.
