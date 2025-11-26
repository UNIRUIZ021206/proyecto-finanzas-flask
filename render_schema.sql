-- Script compatible con PostgreSQL para Render

-- Tabla Roles
CREATE TABLE Roles (
    Id_Rol SERIAL PRIMARY KEY,
    Nombre VARCHAR(50) NOT NULL UNIQUE,
    Estado INT NOT NULL DEFAULT 1
);

INSERT INTO Roles (Nombre, Estado) VALUES ('Administrador', 1);
INSERT INTO Roles (Nombre, Estado) VALUES ('Cliente', 1);

-- Tabla Usuarios
CREATE TABLE Usuarios (
    Id_Usuario SERIAL PRIMARY KEY,
    Nombre VARCHAR(100) NOT NULL,
    Correo VARCHAR(100) NOT NULL UNIQUE,
    Contrasena BYTEA NOT NULL, -- Postgres usa BYTEA para binarios
    Id_Rol INT NOT NULL,
    Estado INT NOT NULL DEFAULT 1,
    CONSTRAINT FK_Usuario_Rol FOREIGN KEY (Id_Rol) REFERENCES Roles(Id_Rol)
);

-- Tabla Periodo
CREATE TABLE Periodo (
    PeriodoID SERIAL PRIMARY KEY,
    Anio INT NOT NULL UNIQUE,
    FechaCierre DATE NOT NULL
);

-- Tabla CatalogoCuentas
CREATE TABLE CatalogoCuentas (
    CuentaID VARCHAR(20) PRIMARY KEY,
    NombreCuenta VARCHAR(100) NOT NULL,
    TipoCuenta VARCHAR(50) NOT NULL 
        CHECK (TipoCuenta IN ('Activo', 'Pasivo', 'Patrimonio', 'Ingreso', 'Costo', 'Gasto')),
    SubTipoCuenta VARCHAR(50) NOT NULL 
        CHECK (SubTipoCuenta IN (
            'Activo Corriente', 'Activo No Corriente',
            'Pasivo Corriente', 'Pasivo No Corriente',
            'Capital', 'Resultados',
            'Ingresos Operativos', 'Otros Ingresos',
            'Costo de Ventas',
            'Gasto Operativo', 'Gasto No Operativo'
        ))
);

-- Tabla SaldoCuenta
CREATE TABLE SaldoCuenta (
    SaldoID SERIAL PRIMARY KEY,
    PeriodoID INT NOT NULL,
    CuentaID VARCHAR(20) NOT NULL,
    Monto NUMERIC(18, 2) NOT NULL, -- NUMERIC es mejor que DECIMAL en Postgres
    CONSTRAINT FK_Saldo_Periodo FOREIGN KEY (PeriodoID) REFERENCES Periodo(PeriodoID),
    CONSTRAINT FK_Saldo_Cuenta FOREIGN KEY (CuentaID) REFERENCES CatalogoCuentas(CuentaID),
    CONSTRAINT UQ_Cuenta_Periodo UNIQUE (PeriodoID, CuentaID)
);
