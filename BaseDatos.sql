CREATE DATABASE FinanzaDB
GO
USE FinanzaDB
GO


-- Tabla 1: Periodos Contables
-- Almacena los años o períodos que quieres analizar.
CREATE TABLE Periodo (
    PeriodoID INT PRIMARY KEY IDENTITY(1,1),
    Anio INT NOT NULL UNIQUE,
    FechaCierre DATE NOT NULL
);
GO

-- Tabla 2: Catálogo de Cuentas
-- El corazón del sistema. Define cada cuenta contable.
CREATE TABLE CatalogoCuentas (
    CuentaID NVARCHAR(20) PRIMARY KEY,     -- Ej: '1101', '4101', '5101'
    NombreCuenta NVARCHAR(100) NOT NULL,
    
    -- Clasificación Principal (para el Estado de Resultados o Balance)
    TipoCuenta NVARCHAR(50) NOT NULL 
        CHECK (TipoCuenta IN ('Activo', 'Pasivo', 'Patrimonio', 'Ingreso', 'Costo', 'Gasto')),
    
    -- Sub-clasificación (para análisis más finos)
    SubTipoCuenta NVARCHAR(50) NOT NULL 
        CHECK (SubTipoCuenta IN (
            'Activo Corriente', 'Activo No Corriente',
            'Pasivo Corriente', 'Pasivo No Corriente',
            'Capital', 'Resultados', -- Patrimonio
            'Ingresos Operativos', 'Otros Ingresos', -- Ingreso
            'Costo de Ventas', -- Costo
            'Gasto Operativo', 'Gasto No Operativo' -- Gasto
        ))
);
GO

-- Tabla 3: Saldos de Cuentas
-- Aquí se almacenan los saldos finales de cada cuenta para cada período.
CREATE TABLE SaldoCuenta (
    SaldoID INT PRIMARY KEY IDENTITY(1,1),
    PeriodoID INT NOT NULL,
    CuentaID NVARCHAR(20) NOT NULL,
    Monto DECIMAL(18, 2) NOT NULL,

    -- Creamos las llaves foráneas para mantener la integridad de los datos
    CONSTRAINT FK_Saldo_Periodo FOREIGN KEY (PeriodoID)
        REFERENCES Periodo(PeriodoID),
    
    CONSTRAINT FK_Saldo_Cuenta FOREIGN KEY (CuentaID)
        REFERENCES CatalogoCuentas(CuentaID),

    -- Creamos un índice único para asegurar que no puedas ingresar
    -- dos saldos para la misma cuenta en el mismo período.
    CONSTRAINT UQ_Cuenta_Periodo UNIQUE (PeriodoID, CuentaID)
);
GO