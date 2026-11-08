-- Update the check constraint to include 'code', 'embedding', 'watermark' media types
ALTER TABLE detection_history
DROP CONSTRAINT IF EXISTS detection_history_media_type_check;

ALTER TABLE detection_history
ADD CONSTRAINT detection_history_media_type_check
CHECK (media_type IN ('image', 'video', 'audio', 'text', 'code', 'embedding', 'watermark'));

-- Add optional breakdown metadata column if not exists
ALTER TABLE detection_history
ADD COLUMN IF NOT EXISTS metadata JSONB;
