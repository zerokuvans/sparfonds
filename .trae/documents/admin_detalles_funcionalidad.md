# Funcionalidad de Detalles para Administradores

## 1. Resumen de la Funcionalidad

Implementar vista de detalles interactivos para administradores que permita:
- Ver detalles completos de ahorros al hacer clic
- Visualizar modal con pronóstico de pagos para préstamos
- Mostrar tabla de amortización mensual con desglose de pagos

## 2. Componentes a Implementar

### 2.1 Vista de Detalles de Ahorros
**Ubicación:** `templates/admin_ahorros_detalle.html`

**Elementos a mostrar:**
- ID del ahorro
- Usuario propietario
- Monto del ahorro
- Fecha de registro
- Estado de validación
- Historial de modificaciones

### 2.2 Modal de Pronóstico de Préstamos
**Ubicación:** `templates/admin_prestamos_modal.html`

**Tabla de amortización mensual:**
| Columna | Descripción |
|---------|-------------|
| Mes | Número de mes del préstamo |
| Fecha | Fecha de pago correspondiente |
| Abono Capital | Monto que se paga al capital |
| Interés | Monto de interés del mes |
| Cuota Total | Suma de abono capital + interés |
| Saldo Restante | Capital pendiente después del pago |

### 2.3 Endpoints API Nuevos

**Detalles de Ahorro:**
```
GET /api/admin/ahorros/<int:ahorro_id>
Response: {
    "id": int,
    "usuario_nombre": string,
    "usuario_apellido": string,
    "monto": decimal,
    "fecha": datetime,
    "validado": boolean,
    "usuario_email": string
}
```

**Pronóstico de Préstamo:**
```
GET /api/admin/prestamos/<int:prestamo_id>/pronostico
Response: {
    "prestamo_id": int,
    "monto_total": decimal,
    "tasa_interes": decimal,
    "plazo_meses": int,
    "cuota_mensual": decimal,
    "total_intereses": decimal,
    "tabla_amortizacion": [
        {
            "mes": int,
            "fecha": string,
            "abono_capital": decimal,
            "interes": decimal,
            "cuota_total": decimal,
            "saldo_restante": decimal
        }
    ]
}
```

## 3. Modificaciones en Templates Existentes

### 3.1 admin_ahorros.html
- Agregar atributo `data-id` a cada fila de ahorro
- Agregar clase `clickable-row` para manejo de clicks
- Incluir modal container para detalles

### 3.2 admin_pagos_prestamos.html
- Agregar botón "Ver Pronóstico" en cada préstamo
- Incluir modal para tabla de amortización
- Agregar atributos de data para préstamo ID

## 4. JavaScript para Funcionalidad Interactiva

### 4.1 Manejo de Clicks en Ahorros
```javascript
$('.clickable-row').click(function() {
    const ahorroId = $(this).data('id');
    cargarDetallesAhorro(ahorroId);
});

function cargarDetallesAhorro(ahorroId) {
    $.get(`/api/admin/ahorros/${ahorroId}`, function(data) {
        $('#modalDetalleAhorro .modal-body').html(generarHtmlDetalleAhorro(data));
        $('#modalDetalleAhorro').modal('show');
    });
}
```

### 4.2 Modal de Prónstico de Préstamos
```javascript
function cargarPronosticoPrestamo(prestamoId) {
    $.get(`/api/admin/prestamos/${prestamoId}/pronostico`, function(data) {
        $('#modalPronostico .modal-title').text(`Pronóstico de Pagos - Préstamo #${prestamoId}`);
        $('#tablaAmortizacion').html(generarTablaAmortizacion(data.tabla_amortizacion));
        $('#resumenPrestamo').html(generarResumenPrestamo(data));
        $('#modalPronostico').modal('show');
    });
}
```

## 5. Funciones Backend Necesarias

### 5.1 app.py - Nuevas Rutas
```python
@app.route('/api/admin/ahorros/<int:ahorro_id>')
@admin_required
def api_admin_ahorro_detalle(ahorro_id):
    # Obtener detalles del ahorro con información del usuario
    pass

@app.route('/api/admin/prestamos/<int:prestamo_id>/pronostico')
@admin_required
def api_admin_prestamo_pronostico(prestamo_id):
    # Calcular tabla de amortización
    pass
```

### 5.2 Función de Cálculo de Amortización
```python
def calcular_tabla_amortizacion(monto, tasa_interes, plazo_meses):
    """
    Calcula la tabla de amortización mensual
    """
    tasa_mensual = tasa_interes / 100 / 12
    cuota_fija = monto * (tasa_mensual * (1 + tasa_mensual)**plazo_meses) / ((1 + tasa_mensual)**plazo_meses - 1)
    
    tabla = []
    saldo = monto
    
    for mes in range(1, plazo_meses + 1):
        interes = saldo * tasa_mensual
        abono_capital = cuota_fija - interes
        saldo -= abono_capital
        
        tabla.append({
            'mes': mes,
            'fecha': datetime.now().replace(day=1) + timedelta(days=30*mes),
            'abono_capital': round(abono_capital, 2),
            'interes': round(interes, 2),
            'cuota_total': round(cuota_fija, 2),
            'saldo_restante': round(saldo, 2)
        })
    
    return tabla
```

## 6. Diseño de Modales

### 6.1 Modal Detalle Ahorro
- Header con ID del ahorro
- Body con información en formato de lista
- Footer con botón de cierre

### 6.2 Modal Pronóstico Préstamo
- Header con ID del préstamo y resumen
- Body con:
  - Resumen del préstamo (monto, tasa, plazo)
  - Tabla scrollable con la amortización mensual
  - Totales al final
- Footer con opciones de exportación (opcional)

## 7. Mejoras de UX

- Loading spinner mientras se cargan datos
- Mensajes de error si falla la carga
- Responsive design para modales
- Animaciones suaves al abrir/cerrar modales
- Resaltado de fila seleccionada

## 8. Seguridad

- Verificar que el usuario sea administrador
- Validar IDs numéricos
- Manejar errores de base de datos
- No exponer información sensible de usuarios

## 9. Testing

- Verificar carga de detalles de ahorros
- Validar cálculo de tabla de amortización
- Probar modales en diferentes resoluciones
- Verificar permisos de administrador