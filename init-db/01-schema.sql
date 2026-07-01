-- ============================================
-- СХЕМА БАЗЫ ДАННЫХ (3NF + SCD Type 2)
-- ============================================

-- 1. Таблица версий (историчность)
CREATE TABLE IF NOT EXISTS spp_versions (
    id SERIAL PRIMARY KEY,
    version_date DATE NOT NULL,
    valid_from TIMESTAMP NOT NULL DEFAULT NOW(),
    valid_to TIMESTAMP,
    is_current BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 2. Иерархический справочник элементов
CREATE TABLE IF NOT EXISTS spp_elements (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    parent_id INTEGER REFERENCES spp_elements(id),
    version_id INTEGER REFERENCES spp_versions(id),
    status VARCHAR(20) CHECK (status IN ('Действующий', 'Недействующий')),
    level INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 3. Справочник отделов
CREATE TABLE IF NOT EXISTS departments (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 4. Связи элементов с отделами
CREATE TABLE IF NOT EXISTS element_departments (
    element_id INTEGER REFERENCES spp_elements(id) ON DELETE CASCADE,
    department_id INTEGER REFERENCES departments(id) ON DELETE CASCADE,
    PRIMARY KEY (element_id, department_id)
);

-- 5. Таблица сохраненных расчетов
CREATE TABLE IF NOT EXISTS saved_calculations (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    version_id INTEGER REFERENCES spp_versions(id),
    calculation_date TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'active',
    result_data JSONB NOT NULL,
    total_amount DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 6. Индексы для производительности
CREATE INDEX IF NOT EXISTS idx_elements_parent ON spp_elements(parent_id);
CREATE INDEX IF NOT EXISTS idx_elements_version ON spp_elements(version_id);
CREATE INDEX IF NOT EXISTS idx_calc_session ON saved_calculations(session_id);
