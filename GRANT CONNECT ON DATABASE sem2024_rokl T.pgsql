


GRANT CONNECT ON DATABASE sem2024_rokl TO javnost;

-- Uporaba sheme
GRANT USAGE ON SCHEMA public TO javnost;

-- Tabele (beri, vstavi, spremeni, briši)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO javnost;

-- Sekvence (za SERIAL id-je)
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO javnost;

-- Funkcije (če uporabljaš custom SQL funkcije)
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO javnost;

-- Tipi (če uporabljaš ENUM ali custom TYPE)
--GRANT USAGE ON ALL TYPES IN SCHEMA public TO javnost;

-- Da boš imel pravice tudi na prihodnjih objektih
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL PRIVILEGES ON TABLES TO javnost;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT USAGE, SELECT ON SEQUENCES TO javnost;


