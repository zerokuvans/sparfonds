# Solución a Problemas en SparFonds

Este documento explica cómo resolver cinco problemas específicos en la aplicación SparFonds:

1. Error de base de datos con el campo `tasa_interes`
2. Regeneración de certificados SSL
3. Modificación del proceso de solicitud de préstamos
4. Filtrado del historial de movimientos por usuario
5. Implementación de historial de pagos de préstamos con saldo restante

## 1. Solución al Error de Base de Datos

El error `DatabaseError: 1364 (HY000): Field 'tasa_interes' doesn't have a default value` ocurre porque la tabla `prestamos` tiene un campo `tasa_interes` que no permite valores NULL y no tiene un valor predeterminado.

### Pasos para solucionar:

1. Ejecute el script de corrección:

```
python corregir_tasa_interes.py
```

Este script realizará las siguientes acciones:

- Modificará la columna `tasa_interes` para permitir valores NULL
- Actualizará los préstamos pendientes existentes para tener `tasa_interes = NULL`

Después de ejecutar este script, podrá insertar nuevos préstamos sin especificar un valor para `tasa_interes`. La tasa de interés se establecerá cuando el administrador apruebe el préstamo.

## 2. Regeneración de Certificados SSL

El script `generar_certificados.py` ha sido actualizado para permitir la regeneración de certificados SSL existentes.

### Pasos para regenerar certificados:

1. Para generar certificados nuevos (si no existen):

```
python generar_certificados.py
```

2. Para forzar la regeneración (eliminar y crear nuevos):

```
python generar_certificados.py --forzar
```

Esta opción eliminará los certificados existentes y generará nuevos certificados autofirmados para el entorno de desarrollo.

## 3. Cambios en el Registro de Ahorros

Se ha modificado la aplicación para que solo los administradores puedan registrar ahorros para los ahorradores:

- Se eliminó la opción de registro de ahorros en la interfaz de usuario para ahorradores
- Se creó un nuevo módulo en el panel de administración para registrar ahorros
- Los administradores ahora pueden seleccionar un ahorrador, especificar el monto y la fecha del ahorro

### Acceso al Nuevo Módulo

1. Inicie sesión como administrador
2. Vaya al Panel de Administración
3. Haga clic en el botón "Registrar Ahorros para Ahorradores"

## 3. Modificación del Proceso de Solicitud de Préstamos

Se ha modificado la aplicación para que el plazo del préstamo sea determinado por el administrador en lugar del ahorrador:

- Se eliminó el campo de plazo del formulario de solicitud de préstamos para ahorradores
- Se agregó un campo de selección de plazo en el panel de administración cuando se aprueba un préstamo
- Se modificó la estructura de la tabla `prestamos` para permitir valores NULL en el campo `plazo_meses`

### Pasos para solucionar:

1. Ejecute el script de corrección:

```
python corregir_plazo_meses.py
```

Este script realizará las siguientes acciones:

- Modificará la columna `plazo_meses` para permitir valores NULL
- Actualizará los préstamos pendientes existentes para tener `plazo_meses = NULL`

Después de ejecutar este script, los ahorradores podrán solicitar préstamos sin especificar un plazo. El plazo será establecido cuando el administrador apruebe el préstamo.

## 4. Filtrado del Historial de Movimientos por Usuario

Se ha modificado la aplicación para que el historial de movimientos muestre solo los datos del ahorrador que inició sesión, mientras que los administradores pueden ver el historial completo de cada ahorrador.

### Cambios implementados:

1. **Filtrado de historial para ahorradores:**
   - La ruta `/historial` ahora muestra solo las transacciones del usuario que ha iniciado sesión
   - Se mantiene la misma interfaz de usuario para los ahorradores

2. **Nuevo módulo para administradores:**
   - Se ha creado una nueva ruta `/admin/historial` exclusiva para administradores
   - Los administradores pueden seleccionar cualquier ahorrador y ver su historial completo
   - Se pueden filtrar las transacciones por tipo (ahorros, préstamos, pagos)

3. **Acceso al nuevo módulo:**
   - Inicie sesión como administrador
   - Vaya al Panel de Administración
   - Haga clic en el botón "Ver Historial de Ahorradores"
   - Seleccione un ahorrador de la lista desplegable para ver su historial

## 5. Implementación de Historial de Pagos de Préstamos

Se ha implementado un sistema para registrar y mostrar el historial de pagos de préstamos, así como el saldo pendiente para cada préstamo.

### Cambios implementados:

1. **Nueva tabla en la base de datos:**
   - Se ha creado una tabla `pagos_prestamos` para registrar cada pago realizado a un préstamo
   - La tabla almacena el ID del préstamo, el monto pagado y la fecha del pago

2. **Interfaz para administradores:**
   - Se ha creado un nuevo módulo en el panel de administración para registrar pagos de préstamos
   - Los administradores pueden seleccionar un ahorrador, un préstamo específico y registrar el monto del pago
   - El sistema verifica que el pago no exceda el saldo pendiente
   - Si el pago completa el préstamo, se actualiza automáticamente su estado a 'pagado'

3. **Visualización para ahorradores:**
   - En la página de préstamos, los ahorradores pueden ver el saldo pendiente de cada préstamo
   - Se ha añadido un botón para ver el historial detallado de pagos de cada préstamo
   - El historial muestra cada pago realizado con su fecha y monto

### Pasos para implementar:

1. Ejecute el script de actualización de la base de datos:

```
python actualizar_pagos_prestamos.py
```

Este script realizará las siguientes acciones:
   - Creará la tabla `pagos_prestamos` si no existe
   - Añadirá un índice para mejorar el rendimiento de las consultas

2. **Acceso al nuevo módulo para administradores:**
   - Inicie sesión como administrador
   - Vaya al Panel de Administración
   - Haga clic en el botón "Registrar Pagos de Préstamos"
   - Seleccione un ahorrador y luego un préstamo para registrar el pago

## Notas Adicionales

- Después de aplicar estas soluciones, reinicie la aplicación con `python app.py`
- Los certificados SSL son solo para entorno de desarrollo. En producción, debe usar certificados emitidos por una autoridad certificadora confiable.
- La modificación de la estructura de la tabla `prestamos` no afecta a los datos existentes, solo permite que los nuevos préstamos se creen sin tasa de interés inicial y sin plazo inicial.
- El filtrado del historial de movimientos mejora la privacidad de los datos de los ahorradores mientras proporciona a los administradores una visión completa de todas las transacciones.
- El sistema de pagos de préstamos calcula automáticamente el saldo pendiente y actualiza el estado del préstamo cuando se completa el pago total.