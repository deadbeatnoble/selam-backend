-- Run this in pgAdmin Query Tool (connected to PostgreSQL server)
-- Right-click Databases → Create → Database, OR run:

CREATE DATABASE selammind
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    CONNECTION LIMIT = -1;

-- Tables are created automatically when you start the backend (FastAPI lifespan).

-- Optional: remove phone column from users if upgrading an older database
-- ALTER TABLE users DROP COLUMN IF EXISTS phone;

-- Optional: add email to professionals if upgrading an older database
-- ALTER TABLE professionals ADD COLUMN IF NOT EXISTS email VARCHAR(100);
-- UPDATE professionals SET email = 'doctor@selammind.et' WHERE email IS NULL;
