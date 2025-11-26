CREATE DATABASE FinanzaDB
GO
USE FinanzaDB
GO

-- Tabla 0: Roles
-- Define los roles de usuario (Administrador, Cliente, etc.)
CREATE TABLE Roles (
    Id_Rol INT PRIMARY KEY IDENTITY(1,1),
    Nombre NVARCHAR(50) NOT NULL UNIQUE,
    Estado INT NOT NULL DEFAULT 1 -- 1: Activo, 0: Inactivo
);
GO

-- Insertar Roles por defecto
INSERT INTO Roles (Nombre, Estado) VALUES ('Administrador', 1);
INSERT INTO Roles (Nombre, Estado) VALUES ('Cliente', 1);
GO

-- Tabla 0.5: Usuarios
-- Almacena los usuarios del sistema
CREATE TABLE Usuarios (
    Id_Usuario INT PRIMARY KEY IDENTITY(1,1),
    Nombre NVARCHAR(100) NOT NULL,
    Correo NVARCHAR(100) NOT NULL UNIQUE,
    Contrasena VARBINARY(MAX) NOT NULL, -- Almacena el hash de bcrypt
    Id_Rol INT NOT NULL,
    Estado INT NOT NULL DEFAULT 1, -- 1: Activo, 0: Inactivo
    
    CONSTRAINT FK_Usuario_Rol FOREIGN KEY (Id_Rol)
        REFERENCES Roles(Id_Rol)
);
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
