CREATE TABLE IF NOT EXISTS weather_readings (
    id SERIAL PRIMARY KEY,
    city TEXT NOT NULL,
    month TEXT NOT NULL,      -- e.g. 'September'
    avg_temp_celsius NUMERIC NOT NULL
);

-- seed a few rows so there's something to query
INSERT INTO weather_readings (city, month, avg_temp_celsius) VALUES
    ('Ahmedabad', 'September', 32.5),
    ('Mumbai', 'September', 29.0),
    ('Delhi', 'September', 33.0);
