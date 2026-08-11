ALTER TABLE destination_images
    ADD COLUMN source_url TEXT,
    ADD COLUMN source_name TEXT,
    ADD COLUMN attribution TEXT;