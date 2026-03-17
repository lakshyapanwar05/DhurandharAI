-- Add real attack tracking columns to incidents table
-- Run this in your Supabase SQL Editor

-- Add real attack tracking columns to incidents table
ALTER TABLE public.incidents 
ADD COLUMN IF NOT EXISTS is_real_attack BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS source_ip VARCHAR(45) DEFAULT '',
ADD COLUMN IF NOT EXISTS target_ip VARCHAR(45) DEFAULT '',
ADD COLUMN IF NOT EXISTS attack_payload JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS attack_type VARCHAR(50) DEFAULT '';

-- Add indexes for the new columns
CREATE INDEX IF NOT EXISTS idx_incidents_is_real_attack ON public.incidents(is_real_attack);
CREATE INDEX IF NOT EXISTS idx_incidents_source_ip ON public.incidents(source_ip);
CREATE INDEX IF NOT EXISTS idx_incidents_attack_type ON public.incidents(attack_type);

-- Add comments for documentation
COMMENT ON COLUMN public.incidents.is_real_attack IS 'TRUE if this incident was triggered by a real external attack';
COMMENT ON COLUMN public.incidents.source_ip IS 'Source IP of the attacker (for real attacks)';
COMMENT ON COLUMN public.incidents.target_ip IS 'Target IP that was attacked (for real attacks)';
COMMENT ON COLUMN public.incidents.attack_payload IS 'Original attack payload data (for real attacks)';
COMMENT ON COLUMN public.incidents.attack_type IS 'Attack type: ddos, bruteforce, cryptominer, insider (for real attacks)';
