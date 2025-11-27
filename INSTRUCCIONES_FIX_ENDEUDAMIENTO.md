# CORRECCIÓN URGENTE: Tarjeta de Endeudamiento

## Problema:
La tarjeta de "Endeudamiento" NO tiene el mismo formato visual que la tarjeta de "Rentabilidad". La barra de progreso está FUERA del contenedor de la tarjeta.

## Ubicación del Problema:
Archivo: `app/templates/dashboard_cliente.htmlbr/>
Líneas: 1019-1029

## Código ACTUAL (INCORRECTO):
```html
        <div class="highlight-card">
            <span style="color: var(--text-secondary);">Endeudamiento:</span>
            <strong style="color: var(--text-primary);">{{ "{:.1f}%".format(kpis.razon_endeudamiento)
                }}</strong>
        </div>
        <div class="progress-bar">
            <div class="progress-fill"
                style="width: {{ kpis.razon_endeudamiento }}%; background: {% if kpis.razon_endeudamiento < 50 %}var(--success){% elif kpis.razon_endeudamiento < 70 %}var(--warning){% else %}var(--error){% endif %};">
            </div>
        </div>
    </div>
```

## Código CORRECTO (NUEVO):
```html
        <div class="highlight-card">
            <h3><i class="fa-solid fa-chart-pie"></i> Endeudamiento</h3>
            <div style="margin-top: 15px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                    <span style="color: var(--text-secondary);">Nivel de Endeudamiento:</span>
                    <strong style="color: var(--text-primary);">{{ "{:.1f}%".format(kpis.razon_endeudamiento) }}</strong>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill"
                        style="width: {{ kpis.razon_endeudamiento }}%; background: {% if kpis.razon_endeudamiento < 50 %}var(--success){% elif kpis.razon_endeudamiento < 70 %}var(--warning){% else %}var(--error){% endif %};">
                    </div>
                </div>
            </div>
        </div>
    </div>
```

## Cambios clave:
1. **Añadido título con icono**: `<h3><i class="fa-solid fa-chart-pie"></i> Endeudamiento</h3>`
2. **Contenedor interno**: Ahora todo está dentro de un `<div style="margin-top: 15px;">`
3. **Etiqueta mejorada**: Cambio de "Endeudamiento:" a "Nivel de Endeudamiento:"
4. **Layout consistente**: Usa `display: flex; justify-content: space-between` igual que Rentabilidad
5. **Barra de progreso DENTRO**: Ahora la barra de progreso está contenida dentro de la tarjeta

## INSTRUCCIONES PARA APLICAR:

### Opción 1: Edición Manual en VS Code
1. Abre `dashboard_cliente.html`
2. Ve a la línea 1019
3. Selecciona desde la línea 1019 hasta la línea 1029
4. Reemplaza todo ese bloque con el "Código CORRECTO" de arriba

### Opción 2: Buscar y Reemplazar
1. Abre `dashboard_cliente.html`  
2. Presiona Ctrl+H (Buscar y Reemplazar)
3. En "Buscar": Pega el bloc "Código ACTUAL"
4. En "Reemplazar con": Pega el bloque "Código CORRECTO"
5. Haz clic en "Reemplazar"

## Resultado Esperado:
Después de aplicar el cambio, la tarjeta de "Endeudamiento" se verá exactamente igual que la tarjeta de "Renta bilidad":
- ✅ Título con icono en la parte superior
- ✅ Etiqueta y valor en una línea con flex
- ✅ Barra de progreso visual abajo
- ✅ Todo contenido dentro del borde de la tarjeta

## Verificación:
1. Guarda el archivo
2. Recarga la página en el navegador (Ctrl+F5)
3. Verifica que ambas tarjetas se vean iguales en estilo
