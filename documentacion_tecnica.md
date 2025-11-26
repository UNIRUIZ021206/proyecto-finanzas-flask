# Informe Técnico: Sistema de Análisis Financiero

**Fecha:** 25 de Noviembre de 2025
**Asunto:** Documentación de Lógica de Programación, Metodología Financiera y Arquitectura de Datos

---

## 1. Introducción

El presente informe tiene como objetivo describir la arquitectura técnica y la lógica de negocio implementada en el Sistema de Análisis Financiero. Este sistema ha sido desarrollado para facilitar la interpretación de estados financieros mediante el cálculo automático de indicadores clave y el uso de inteligencia artificial para el análisis de datos.

## 2. Lógica de Programación y Arquitectura del Sistema

El sistema está construido sobre una arquitectura web moderna, priorizando la modularidad, la escalabilidad y la seguridad.

### 2.1. Tecnologías Base
*   **Lenguaje:** Python 3.x
*   **Framework Web:** Flask
*   **Motor de Plantillas:** Jinja2 (para la generación dinámica de HTML)
*   **Inteligencia Artificial:** Google Gemini API

### 2.2. Estructura Modular (Patrón MVC)
La aplicación sigue el patrón de diseño Modelo-Vista-Controlador (MVC) adaptado, organizando el código en módulos funcionales denominados "Blueprints":

1.  **Controladores (Rutas):**
    *   Ubicación: `app/main/routes.py`
    *   Función: Gestionan las solicitudes HTTP del usuario. Por ejemplo, la ruta `/dashboard-cliente` orquesta la obtención de datos financieros y su presentación.
    *   Seguridad: Se implementan decoradores como `@login_required` para restringir el acceso a usuarios autenticados.

2.  **Lógica de Negocio (Servicios):**
    *   Ubicación: `app/utils.py`
    *   Función: Contiene las funciones puras que realizan los cálculos complejos. Destaca la función `get_financial_reports` para la extracción de datos y `calcular_ratios_financieros` para el procesamiento analítico.

3.  **Vistas (Interfaz de Usuario):**
    *   Ubicación: `app/templates/`
    *   Función: Presentan la información procesada al usuario final de manera interactiva y visualmente atractiva.

### 2.3. Integración de Inteligencia Artificial
El sistema incorpora un módulo de IA (`/chatbot`) que actúa como un analista financiero virtual.
*   **Proceso:** Recibe consultas en lenguaje natural, inyecta contexto financiero específico del sistema y utiliza el modelo **Gemini** para generar explicaciones detalladas y contextualizadas sobre los resultados financieros.

---

## 3. Metodología de Análisis Financiero

El núcleo analítico del sistema reside en la automatización de cálculos de razones financieras, implementados rigurosamente según estándares contables.

### 3.1. Análisis Vertical (Estructura Porcentual)
Este análisis determina la participación de cada cuenta dentro de los totales principales, permitiendo evaluar la estructura de activos y resultados.

*   **Implementación:** El cálculo se realiza dinámicamente en la capa de presentación (`analisis_vertical.html`) para garantizar que siempre refleje los datos más actuales.
*   **Bases de Cálculo:**
    *   **Balance General:** Se toma como base (100%) el **Total de Activos**.
        *   $\text{Porcentaje} = \frac{\text{Saldo Cuenta}}{\text{Total Activos}} \times 100$
    *   **Estado de Resultados:** Se toma como base (100%) el **Total de Ingresos**.
        *   $\text{Porcentaje} = \frac{\text{Saldo Cuenta}}{\text{Total Ingresos}} \times 100$

### 3.2. Estado de Flujo de Efectivo (Método Indirecto)
El sistema genera automáticamente el Estado de Flujo de Efectivo utilizando el **Método Indirecto**, partiendo de la Utilidad Neta y ajustándola por partidas que no afectan el efectivo.

*   **Actividades de Operación:**
    *   Inicio: **Utilidad Neta**.
    *   (+) Depreciaciones y Amortizaciones (Gastos no monetarios).
    *   (+/-) Cambios en Capital de Trabajo Operativo:
        *   Disminución de Activos Corrientes (CxC, Inventarios) $\rightarrow$ Fuente (+).
        *   Aumento de Activos Corrientes $\rightarrow$ Uso (-).
        *   Aumento de Pasivos Corrientes (CxP) $\rightarrow$ Fuente (+).
        *   Disminución de Pasivos Corrientes $\rightarrow$ Uso (-).
*   **Actividades de Inversión:**
    *   Compra/Venta de Activos No Corrientes (Propiedad, Planta y Equipo).
    *   Movimientos en Inversiones Temporales.
*   **Actividades de Financiamiento:**
    *   Obtención/Pago de Préstamos (Pasivos No Corrientes y Deuda Corto Plazo).
    *   Aportes de Capital o Pago de Dividendos (Movimientos en Patrimonio).

### 3.3. Ratios de Liquidez
Evalúan la solvencia a corto plazo de la entidad.

| Indicador | Fórmula Técnica | Interpretación del Sistema |
| :--- | :--- | :--- |
| **Razón Circulante** | $\frac{\text{Activo Corriente}}{\text{Pasivo Corriente}}$ | Mide la capacidad de cubrir obligaciones inmediatas. |
| **Prueba Ácida** | $\frac{\text{Activo Corriente} - \text{Inventarios}}{\text{Pasivo Corriente}}$ | Evalúa la liquidez inmediata sin depender de la venta de existencias. |
| **Capital de Trabajo** | $\text{Activo Corriente} - \text{Pasivo Corriente}$ | Recursos disponibles para operar tras liquidar deudas a corto plazo. |

### 3.2. Ratios de Actividad (Eficiencia Operativa)
Miden la eficiencia en la gestión de los recursos.

| Indicador | Fórmula Técnica | Interpretación del Sistema |
| :--- | :--- | :--- |
| **Rotación de Inventarios** | $\frac{\text{Costo de Ventas}}{\text{Inventario Promedio}}$ | Velocidad de renovación del stock. |
| **Rotación de Cuentas por Cobrar** | $\frac{\text{Ventas a Crédito}}{\text{Cuentas por Cobrar}}$ | Eficacia en la gestión de cobros. |
| **Rotación de Activos Totales** | $\frac{\text{Ventas Totales}}{\text{Total Activos}}$ | Capacidad de los activos para generar ingresos. |

### 3.3. Ratios de Endeudamiento (Solvencia a Largo Plazo)
Analizan la estructura financiera y el riesgo.

| Indicador | Fórmula Técnica | Interpretación del Sistema |
| :--- | :--- | :--- |
| **Nivel de Endeudamiento** | $\frac{\text{Total Pasivo}}{\text{Total Activo}}$ | Proporción de activos financiados por terceros. |
| **Relación Pasivo/Patrimonio** | $\frac{\text{Total Pasivo}}{\text{Patrimonio Neto}}$ | Grado de apalancamiento financiero frente a los accionistas. |

### 3.4. Ratios de Rentabilidad
Miden el retorno generado sobre las inversiones y ventas.

| Indicador | Fórmula Técnica | Interpretación del Sistema |
| :--- | :--- | :--- |
| **Margen Bruto** | $\frac{\text{Utilidad Bruta}}{\text{Ventas}} \times 100$ | Beneficio directo tras costos de producción. |
| **Margen Operativo** | $\frac{\text{Utilidad Operativa}}{\text{Ventas}} \times 100$ | Eficiencia operativa antes de intereses e impuestos. |
| **Margen Neto** | $\frac{\text{Utilidad Neta}}{\text{Ventas}} \times 100$ | Beneficio final por cada unidad monetaria vendida. |
| **ROA (Retorno sobre Activos)** | $\frac{\text{Utilidad Neta}}{\text{Total Activos}} \times 100$ | Rentabilidad económica de los activos. |
| **ROE (Retorno sobre Patrimonio)** | $\frac{\text{Utilidad Neta}}{\text{Patrimonio}} \times 100$ | Rentabilidad financiera para los accionistas. |

---

## 4. Módulo de Seguridad y Autenticación

El sistema implementa un esquema de seguridad robusto para proteger la información financiera sensible.

### 4.1. Mecanismo de Autenticación
*   **Librerías:** `Flask-Login` para gestión de sesiones y `bcrypt` para criptografía.
*   **Proceso de Login:**
    1.  El usuario ingresa credenciales en `/login`.
    2.  El sistema consulta la tabla `Usuarios` buscando el correo activo.
    3.  Se verifica la contraseña utilizando `bcrypt.checkpw` contra el hash almacenado.
    4.  Si es exitoso, se crea la sesión de usuario.
*   **Control de Acceso (Roles):**
    *   El sistema redirige automáticamente según el rol del usuario:
        *   **Cliente:** Redirigido a `/dashboard-cliente`.
        *   **Administrador/Otros:** Redirigido a la página principal (`/`).
    *   Protección de rutas mediante el decorador `@login_required`.

---

## 5. Arquitectura de Datos y Conectividad

El sistema garantiza la integridad y disponibilidad de los datos mediante una conexión robusta a una base de datos relacional.

### 4.1. Especificaciones de Conexión
A diferencia de sistemas Java que utilizan JDBC, esta aplicación utiliza el estándar **ODBC (Open Database Connectivity)**, optimizado para entornos Python/Windows.

*   **Motor de Base de Datos:** Microsoft SQL Server.
*   **Librería de Conexión:** `SQLAlchemy` (Core & ORM).
*   **Driver:** `ODBC Driver 17 for SQL Server`.
*   **Protocolo:** TCP/IP sobre `(localdb)\Universidad`.

### 4.2. Estrategia de Acceso a Datos
La capa de persistencia se maneja en el archivo `app/extensions.py`.
*   **Gestión de Conexiones:** Se utiliza un `Engine` de SQLAlchemy que administra un pool de conexiones para optimizar el rendimiento bajo carga.
*   **Consultas:** Para los reportes financieros complejos, el sistema utiliza **SQL Nativo (Raw SQL)**. Esto permite ejecutar consultas altamente optimizadas con múltiples `JOINs` y agregaciones que serían ineficientes a través de un ORM tradicional, garantizando tiempos de respuesta rápidos incluso con grandes volúmenes de datos transaccionales.

---

## 6. Conclusión

La arquitectura del sistema combina la flexibilidad de Python/Flask con la robustez de SQL Server, proporcionando una plataforma sólida para el análisis financiero. La implementación rigurosa de las fórmulas financieras, sumada a la capacidad explicativa de la Inteligencia Artificial, convierte a esta herramienta en un activo valioso para la toma de decisiones estratégicas.
