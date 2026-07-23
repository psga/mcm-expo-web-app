-- Esquema del prototipo de base de datos para MCM Expo.
-- PostgreSQL. Incluye ya incorporadas: las columnas de coordenadas de
-- grilla y color/precio por categoría para el diseñador de stands
-- (admin.html) y el selector de cliente (index.html), las dimensiones de
-- grid embebidas en `plano`, la dotación base en
-- `reserva_servicio_adicional`, y `empresa_marca.password_hash` para el
-- login de marcas expositoras (ver streamlit_app/db/auth.py).

-- 1. TABLA: EDICION EXPO
CREATE TABLE edicion_expo (
    id_edicion SERIAL PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE NOT NULL, -- UNIQUE para que db/seed.py sea idempotente (ON CONFLICT DO NOTHING)
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    ubicacion VARCHAR(150) DEFAULT 'Plaza Mayor, Medellín',
    estado VARCHAR(20) NOT NULL CHECK (estado IN ('Planificacion', 'Publicada', 'En_Curso', 'Finalizada'))
);

-- 2. TABLA: CATEGORIA STAND / PRIORIDAD
CREATE TABLE categoria_stand (
    id_categoria SERIAL PRIMARY KEY,
    nombre_categoria VARCHAR(50) NOT NULL UNIQUE, -- Patrocinador, Apoyo, General
    prioridad_seleccion INT NOT NULL UNIQUE CHECK (prioridad_seleccion > 0),
    descripcion TEXT,
    color VARCHAR(7) DEFAULT '#e05b26', -- color de la zona en el plano (admin.html)
    precio_m2 NUMERIC(12,2) -- precio por m2 de la zona; alimenta stand.precio_base
);

-- 3. TABLA: EMPRESA MARCA
CREATE TABLE empresa_marca (
    id_marca SERIAL PRIMARY KEY,
    nit VARCHAR(20) UNIQUE NOT NULL,
    razon_social VARCHAR(150) NOT NULL,
    nombre_comercial VARCHAR(150) NOT NULL,
    sector_economico VARCHAR(100),
    correo_corporativo VARCHAR(100) UNIQUE NOT NULL, -- username de login de la marca
    password_hash VARCHAR(255) NOT NULL, -- hash bcrypt, ver db/auth.py
    telefono VARCHAR(20) NOT NULL,
    -- Datos de redes sociales del perfil (HU9 — Gestión de Activos de Marca)
    instagram VARCHAR(150),
    facebook VARCHAR(150),
    sitio_web VARCHAR(255),
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. TABLA: EXPOSITOR CONTACTO (Personas a cargo de la marca)
CREATE TABLE expositor_contacto (
    id_contacto SERIAL PRIMARY KEY,
    id_marca INT NOT NULL REFERENCES empresa_marca(id_marca) ON DELETE CASCADE,
    nombre_completo VARCHAR(120) NOT NULL,
    cargo VARCHAR(80),
    correo VARCHAR(100) NOT NULL,
    telefono VARCHAR(20) NOT NULL,
    es_principal BOOLEAN DEFAULT FALSE
);

-- 5. TABLA: PLANO MAESTRO
CREATE TABLE plano (
    id_plano SERIAL PRIMARY KEY,
    id_edicion INT NOT NULL REFERENCES edicion_expo(id_edicion),
    version_plano VARCHAR(20) NOT NULL,
    estado_validacion VARCHAR(20) NOT NULL CHECK (estado_validacion IN ('Borrador', 'En_Revision', 'Aprobado', 'Rechazado')),
    url_archivo_diseno VARCHAR(255),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Dimensiones del contenedor del selector (admin.html/index.html) y la
    -- imagen del plano embebida en base64; sin esto no se puede reconstruir
    -- el grid desde la DB.
    filas INT NOT NULL DEFAULT 20,
    columnas INT NOT NULL DEFAULT 30,
    tamano_celda_px INT NOT NULL DEFAULT 34,
    imagen_plano TEXT,
    CONSTRAINT uq_edicion_version UNIQUE(id_edicion, version_plano)
);

-- 6. TABLA: STAND
CREATE TABLE stand (
    id_stand SERIAL PRIMARY KEY,
    id_plano INT NOT NULL REFERENCES plano(id_plano),
    id_categoria INT NOT NULL REFERENCES categoria_stand(id_categoria),
    codigo_stand VARCHAR(20) NOT NULL, -- Ej: A-101, stand-003 (coincide con stand.id del JSON del editor)
    dimensiones VARCHAR(30) DEFAULT '3x3 metros',
    area_m2 NUMERIC(6,2) NOT NULL DEFAULT 9.00,
    precio_base NUMERIC(12,2) NOT NULL CHECK (precio_base >= 0),
    estado_stand VARCHAR(20) NOT NULL DEFAULT 'Disponible'
        CHECK (estado_stand IN ('Disponible', 'Pre_Reservado', 'Bloqueado', 'Mantenimiento')),
    -- Coordenadas de grilla y color: alimentan directamente el rectángulo que
    -- dibuja admin.html/index.html (filaInicio, columnaInicio, filaFin, columnaFin, color).
    fila_inicio INT,
    columna_inicio INT,
    fila_fin INT,
    columna_fin INT,
    color VARCHAR(7) DEFAULT '#e05b26', -- hex de la zona; si es NULL se usa categoria_stand.color
    zona_nombre VARCHAR(80), -- nombre de la zona tal como se definió en admin.html
    tipo_stand VARCHAR(20) NOT NULL DEFAULT 'venta'
        CHECK (tipo_stand IN ('venta', 'patrocinador')),
    CONSTRAINT uq_plano_codigo UNIQUE(id_plano, codigo_stand)
);

-- 7. TABLA: RESERVA
CREATE TABLE reserva (
    id_reserva SERIAL PRIMARY KEY,
    id_stand INT NOT NULL UNIQUE REFERENCES stand(id_stand), -- Un stand solo tiene una reserva activa
    id_marca INT NOT NULL REFERENCES empresa_marca(id_marca),
    fecha_reserva TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado_reserva VARCHAR(20) NOT NULL DEFAULT 'Pendiente'
        CHECK (estado_reserva IN ('Pendiente', 'Formalizada', 'Cancelada', 'Penalizada')),
    observaciones TEXT
);

-- 8. TABLA: CONTRATO
CREATE TABLE contrato (
    id_contrato SERIAL PRIMARY KEY,
    id_reserva INT NOT NULL UNIQUE REFERENCES reserva(id_reserva),
    fecha_generacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    firmado_marca BOOLEAN DEFAULT FALSE,
    firmado_mcm BOOLEAN DEFAULT FALSE,
    url_documento_pdf VARCHAR(255),
    estado_contrato VARCHAR(20) NOT NULL DEFAULT 'Borrador'
        CHECK (estado_contrato IN ('Borrador', 'Enviado', 'Firmado', 'Anulado'))
);

-- 9. TABLA: FACTURA (DIAN)
CREATE TABLE factura (
    id_factura SERIAL PRIMARY KEY,
    id_contrato INT NOT NULL UNIQUE REFERENCES contrato(id_contrato),
    numero_factura_dian VARCHAR(50) UNIQUE,
    fecha_emision TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    monto_subtotal NUMERIC(12,2) NOT NULL CHECK (monto_subtotal >= 0),
    monto_iva NUMERIC(12,2) NOT NULL CHECK (monto_iva >= 0),
    monto_total NUMERIC(12,2) NOT NULL CHECK (monto_total >= 0),
    estado_factura VARCHAR(20) NOT NULL DEFAULT 'Emitida'
        CHECK (estado_factura IN ('Emitida', 'Pagada_Parcial', 'Pagada_Total', 'Anulada'))
);

-- 10. TABLA: PAGO (Soporta múltiples abonos)
CREATE TABLE pago (
    id_pago SERIAL PRIMARY KEY,
    id_factura INT NOT NULL REFERENCES factura(id_factura),
    fecha_pago TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    monto_pagado NUMERIC(12,2) NOT NULL CHECK (monto_pagado > 0),
    metodo_pago VARCHAR(30) NOT NULL CHECK (metodo_pago IN ('Transferencia', 'Pasarela_PSE', 'Tarjeta_Credito')),
    numero_referencia VARCHAR(100) NOT NULL,
    url_comprobante VARCHAR(255),
    estado_pago VARCHAR(20) NOT NULL DEFAULT 'En_Verificacion'
        CHECK (estado_pago IN ('En_Verificacion', 'Verificado', 'Rechazado'))
);

-- 11. TABLA: SERVICIOS Y MOBILIARIO ADICIONAL
CREATE TABLE servicio_adicional (
    id_servicio SERIAL PRIMARY KEY,
    -- UNIQUE porque streamlit_app/db/reserva_queries.py busca el id_servicio
    -- por este nombre exacto, y para que db/seed.py sea idempotente.
    nombre_servicio VARCHAR(100) UNIQUE NOT NULL,
    precio_unitario NUMERIC(10,2) NOT NULL CHECK (precio_unitario >= 0)
);

CREATE TABLE reserva_servicio_adicional (
    id_reserva INT NOT NULL REFERENCES reserva(id_reserva),
    id_servicio INT NOT NULL REFERENCES servicio_adicional(id_servicio),
    cantidad INT NOT NULL CHECK (cantidad > 0),
    cantidad_base INT NOT NULL DEFAULT 0, -- dotación incluida sin costo extra (ver calcularDotacionBase en selector.js)
    PRIMARY KEY (id_reserva, id_servicio)
);

-- 12. TABLA: ACTIVOS PUBLICITARIOS (Pauta / Soporte de Marca)
CREATE TABLE activo_publicitario (
    id_activo SERIAL PRIMARY KEY,
    id_marca INT NOT NULL REFERENCES empresa_marca(id_marca),
    tipo_activo VARCHAR(50) NOT NULL, -- Logo_Vectorial, Manual_Marca, Banner_Web
    url_archivo VARCHAR(255) NOT NULL,
    estado_validacion VARCHAR(20) DEFAULT 'Pendiente' CHECK (estado_validacion IN ('Pendiente', 'Aprobado', 'Rechazado')),
    fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
