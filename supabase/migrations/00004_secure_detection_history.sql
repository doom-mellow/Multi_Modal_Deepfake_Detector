-- Associate detection records with authenticated users.
ALTER TABLE public.detection_history
ADD COLUMN IF NOT EXISTS user_id UUID
REFERENCES auth.users(id) ON DELETE CASCADE;

-- Automatically assign the currently authenticated user.
ALTER TABLE public.detection_history
ALTER COLUMN user_id SET DEFAULT auth.uid();

-- Enable Row Level Security.
ALTER TABLE public.detection_history
ENABLE ROW LEVEL SECURITY;

-- Users can only view their own records.
CREATE POLICY "Users can view their own detection history"
ON public.detection_history
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

-- Users can only insert records belonging to themselves.
CREATE POLICY "Users can insert their own detection history"
ON public.detection_history
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

-- Users can only delete their own records.
CREATE POLICY "Users can delete their own detection history"
ON public.detection_history
FOR DELETE
TO authenticated
USING (auth.uid() = user_id);

-- Index user-specific history queries.
CREATE INDEX IF NOT EXISTS idx_detection_history_user_created
ON public.detection_history(user_id, created_at DESC);