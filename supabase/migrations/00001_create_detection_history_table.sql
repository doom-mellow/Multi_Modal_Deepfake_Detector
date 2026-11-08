-- Create detection_history table for storing analysis records
CREATE TABLE IF NOT EXISTS detection_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  media_type TEXT NOT NULL CHECK (media_type IN ('video', 'audio', 'text')),
  result TEXT NOT NULL CHECK (result IN ('real', 'ai-generated')),
  confidence INTEGER NOT NULL CHECK (confidence >= 0 AND confidence <= 100),
  content_preview TEXT,
  file_name TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_detection_history_created_at ON detection_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_detection_history_media_type ON detection_history(media_type);