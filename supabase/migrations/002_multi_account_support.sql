-- Supabase Migration: Multi-Account Support
-- Project: https://aisbzppswxqknjvntaaa.supabase.co
-- Generated: 2026-09-27

-- ============================================
-- TABLE: profiles (user profiles linked to auth.users)
-- ============================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    auth_user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
    email TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    avatar_url TEXT,
    role TEXT DEFAULT 'user' CHECK (role IN ('user', 'admin', 'owner')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- ALTER TABLE: accounts (add profile_id)
-- ============================================
ALTER TABLE public.accounts ADD COLUMN IF NOT EXISTS profile_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE;
ALTER TABLE public.accounts DROP CONSTRAINT IF EXISTS accounts_email_key;
ALTER TABLE public.accounts DROP CONSTRAINT IF EXISTS accounts_email_unique;
CREATE INDEX IF NOT EXISTS idx_accounts_profile ON public.accounts(profile_id);
CREATE INDEX IF NOT EXISTS idx_accounts_email ON public.accounts(email);

-- ============================================
-- TABLE: profile_connections (track connected accounts)
-- ============================================
CREATE TABLE IF NOT EXISTS public.profile_connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    account_id UUID REFERENCES public.accounts(id) ON DELETE CASCADE,
    connection_type TEXT DEFAULT 'google' CHECK (connection_type IN ('google', 'youtube', 'manual')),
    is_primary BOOLEAN DEFAULT FALSE,
    connected_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(profile_id, account_id)
);

-- ============================================
-- ENABLE RLS
-- ============================================
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profile_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.channels ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.upload_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.metadata_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bulk_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.upload_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.settings ENABLE ROW LEVEL SECURITY;

-- ============================================
-- UPDATE RLS POLICIES
-- ============================================

-- Profiles policies
DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
CREATE POLICY "Users can view own profile" ON public.profiles
    FOR SELECT USING (auth.uid() = auth_user_id);

DROP POLICY IF EXISTS "Users can insert own profile" ON public.profiles;
CREATE POLICY "Users can insert own profile" ON public.profiles
    FOR INSERT WITH CHECK (auth.uid() = auth_user_id);

DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
CREATE POLICY "Users can update own profile" ON public.profiles
    FOR UPDATE USING (auth.uid() = auth_user_id);

-- Profile connections policies
DROP POLICY IF EXISTS "Users can view own connections" ON public.profile_connections;
CREATE POLICY "Users can view own connections" ON public.profile_connections
    FOR SELECT USING (profile_id IN (SELECT id FROM public.profiles));

DROP POLICY IF EXISTS "Users can insert own connections" ON public.profile_connections;
CREATE POLICY "Users can insert own connections" ON public.profile_connections
    FOR INSERT WITH CHECK (profile_id IN (SELECT id FROM public.profiles));

DROP POLICY IF EXISTS "Users can delete own connections" ON public.profile_connections;
CREATE POLICY "Users can delete own connections" ON public.profile_connections
    FOR DELETE USING (profile_id IN (SELECT id FROM public.profiles));

-- Accounts policies (based on profile_id instead of id)
DROP POLICY IF EXISTS "Users can view own accounts" ON public.accounts;
CREATE POLICY "Users can view own accounts" ON public.accounts
    FOR SELECT USING (profile_id IN (SELECT id FROM public.profiles));

DROP POLICY IF EXISTS "Users can insert own accounts" ON public.accounts;
CREATE POLICY "Users can insert own accounts" ON public.accounts
    FOR INSERT WITH CHECK (profile_id IN (SELECT id FROM public.profiles));

DROP POLICY IF EXISTS "Users can update own accounts" ON public.accounts;
CREATE POLICY "Users can update own accounts" ON public.accounts
    FOR UPDATE USING (profile_id IN (SELECT id FROM public.profiles));

DROP POLICY IF EXISTS "Users can delete own accounts" ON public.accounts;
CREATE POLICY "Users can delete own accounts" ON public.accounts
    FOR DELETE USING (profile_id IN (SELECT id FROM public.profiles));

-- Channels policies (updated to use profile_id)
DROP POLICY IF EXISTS "Users can view own channels" ON public.channels;
CREATE POLICY "Users can view own channels" ON public.channels
    FOR SELECT USING (account_id IN (SELECT a.id FROM public.accounts a JOIN public.profiles p ON a.profile_id = p.id));

DROP POLICY IF EXISTS "Users can insert own channels" ON public.channels;
CREATE POLICY "Users can insert own channels" ON public.channels
    FOR INSERT WITH CHECK (account_id IN (SELECT a.id FROM public.accounts a JOIN public.profiles p ON a.profile_id = p.id));

DROP POLICY IF EXISTS "Users can update own channels" ON public.channels;
CREATE POLICY "Users can update own channels" ON public.channels
    FOR UPDATE USING (account_id IN (SELECT a.id FROM public.accounts a JOIN public.profiles p ON a.profile_id = p.id));

-- Upload jobs policies (updated to use profile_id)
DROP POLICY IF EXISTS "Users can view own upload jobs" ON public.upload_jobs;
CREATE POLICY "Users can view own upload jobs" ON public.upload_jobs
    FOR SELECT USING (account_id IN (SELECT a.id FROM public.accounts a JOIN public.profiles p ON a.profile_id = p.id));

DROP POLICY IF EXISTS "Users can insert own upload jobs" ON public.upload_jobs;
CREATE POLICY "Users can insert own upload jobs" ON public.upload_jobs
    FOR INSERT WITH CHECK (account_id IN (SELECT a.id FROM public.accounts a JOIN public.profiles p ON a.profile_id = p.id));

DROP POLICY IF EXISTS "Users can update own upload jobs" ON public.upload_jobs;
CREATE POLICY "Users can update own upload jobs" ON public.upload_jobs
    FOR UPDATE USING (account_id IN (SELECT a.id FROM public.accounts a JOIN public.profiles p ON a.profile_id = p.id));

-- Metadata templates policies (updated to use profile_id)
DROP POLICY IF EXISTS "Users can view own templates" ON public.metadata_templates;
CREATE POLICY "Users can view own templates" ON public.metadata_templates
    FOR SELECT USING (channel_id IN (SELECT c.id FROM public.channels c JOIN public.accounts a ON c.account_id = a.id));

DROP POLICY IF EXISTS "Users can insert own templates" ON public.metadata_templates;
CREATE POLICY "Users can insert own templates" ON public.metadata_templates
    FOR INSERT WITH CHECK (channel_id IN (SELECT c.id FROM public.channels c JOIN public.accounts a ON c.account_id = a.id));

DROP POLICY IF EXISTS "Users can update own templates" ON public.metadata_templates;
CREATE POLICY "Users can update own templates" ON public.metadata_templates
    FOR UPDATE USING (channel_id IN (SELECT c.id FROM public.channels c JOIN public.accounts a ON c.account_id = a.id));

-- Bulk batches policies (updated to use profile_id)
DROP POLICY IF EXISTS "Users can view own batches" ON public.bulk_batches;
CREATE POLICY "Users can view own batches" ON public.bulk_batches
    FOR SELECT USING (account_id IN (SELECT a.id FROM public.accounts a JOIN public.profiles p ON a.profile_id = p.id));

DROP POLICY IF EXISTS "Users can insert own batches" ON public.bulk_batches;
CREATE POLICY "Users can insert own batches" ON public.bulk_batches
    FOR INSERT WITH CHECK (account_id IN (SELECT a.id FROM public.accounts a JOIN public.profiles p ON a.profile_id = p.id));

DROP POLICY IF EXISTS "Users can update own batches" ON public.bulk_batches;
CREATE POLICY "Users can update own batches" ON public.bulk_batches
    FOR UPDATE USING (account_id IN (SELECT a.id FROM public.accounts a JOIN public.profiles p ON a.profile_id = p.id));

-- Upload history policies (updated to use profile_id)
DROP POLICY IF EXISTS "Users can view own history" ON public.upload_history;
CREATE POLICY "Users can view own history" ON public.upload_history
    FOR SELECT USING (channel_id IN (SELECT c.id FROM public.channels c JOIN public.accounts a ON c.account_id = a.id));

DROP POLICY IF EXISTS "Users can insert own history" ON public.upload_history;
CREATE POLICY "Users can insert own history" ON public.upload_history
    FOR INSERT WITH CHECK (channel_id IN (SELECT c.id FROM public.channels c JOIN public.accounts a ON c.account_id = a.id));

DROP POLICY IF EXISTS "Users can update own history" ON public.upload_history;
CREATE POLICY "Users can update own history" ON public.upload_history
    FOR UPDATE USING (channel_id IN (SELECT c.id FROM public.channels c JOIN public.accounts a ON c.account_id = a.id));

-- Notifications policies (updated to use profile_id via accounts)
DROP POLICY IF EXISTS "Users can view own notifications" ON public.notifications;
CREATE POLICY "Users can view own notifications" ON public.notifications
    FOR SELECT USING (user_id IN (SELECT a.id FROM public.accounts a JOIN public.profiles p ON a.profile_id = p.id));

DROP POLICY IF EXISTS "Users can insert own notifications" ON public.notifications;
CREATE POLICY "Users can insert own notifications" ON public.notifications
    FOR INSERT WITH CHECK (user_id IN (SELECT a.id FROM public.accounts a JOIN public.profiles p ON a.profile_id = p.id));

DROP POLICY IF EXISTS "Users can update own notifications" ON public.notifications;
CREATE POLICY "Users can update own notifications" ON public.notifications
    FOR UPDATE USING (user_id IN (SELECT a.id FROM public.accounts a JOIN public.profiles p ON a.profile_id = p.id));

-- Settings policies (updated to use profile_id)
DROP POLICY IF EXISTS "Users can view own settings" ON public.settings;
CREATE POLICY "Users can view own settings" ON public.settings
    FOR SELECT USING (user_id IN (SELECT a.id FROM public.accounts a JOIN public.profiles p ON a.profile_id = p.id));

DROP POLICY IF EXISTS "Users can upsert own settings" ON public.settings;
CREATE POLICY "Users can upsert own settings" ON public.settings
    FOR INSERT WITH CHECK (user_id IN (SELECT a.id FROM public.accounts a JOIN public.profiles p ON a.profile_id = p.id));

DROP POLICY IF EXISTS "Users can update own settings" ON public.settings;
CREATE POLICY "Users can update own settings" ON public.settings
    FOR UPDATE USING (user_id IN (SELECT a.id FROM public.accounts a JOIN public.profiles p ON a.profile_id = p.id));

-- Settings policies (updated to use profile_id)
DROP POLICY IF EXISTS "Users can view own settings" ON public.settings;
CREATE POLICY "Users can view own settings" ON public.settings
    FOR SELECT USING (user_id IN (SELECT a.id FROM public.accounts a JOIN public.profiles p ON a.profile_id = p.id WHERE p.auth_user_id = auth.uid()));

DROP POLICY IF EXISTS "Users can upsert own settings" ON public.settings;
CREATE POLICY "Users can upsert own settings" ON public.settings
    FOR INSERT WITH CHECK (user_id IN (SELECT a.id FROM public.accounts a JOIN public.profiles p ON a.profile_id = p.id WHERE p.auth_user_id = auth.uid()));

DROP POLICY IF EXISTS "Users can update own settings" ON public.settings;
CREATE POLICY "Users can update own settings" ON public.settings
    FOR UPDATE USING (user_id IN (SELECT a.id FROM public.accounts a JOIN public.profiles p ON a.profile_id = p.id WHERE p.auth_user_id = auth.uid()));

-- ============================================
-- UPDATE VIEWS
-- ============================================
CREATE OR REPLACE VIEW public.dashboard_stats AS
SELECT
    COUNT(DISTINCT p.id) as total_accounts,
    COUNT(DISTINCT c.id) as total_channels,
    COUNT(DISTINCT t.id) as total_templates,
    COUNT(DISTINCT b.id) as total_batches,
    COUNT(DISTINCT j.id) as total_uploads,
    COUNT(DISTINCT CASE WHEN j.status = 'completed' THEN j.id END) as completed_uploads,
    COUNT(DISTINCT CASE WHEN j.status = 'failed' THEN j.id END) as failed_uploads,
    COUNT(DISTINCT CASE WHEN c.status = 'active' THEN c.id END) as active_channels,
    COALESCE(SUM(j.progress), 0) / NULLIF(COUNT(DISTINCT j.id), 0) as avg_progress
FROM public.profiles p
LEFT JOIN public.accounts a ON a.profile_id = p.id
LEFT JOIN public.channels c ON c.account_id = a.id
LEFT JOIN public.metadata_templates t ON t.channel_id = c.id
LEFT JOIN public.bulk_batches b ON b.account_id = a.id
LEFT JOIN public.upload_jobs j ON j.channel_id = c.id OR j.account_id = a.id;

CREATE OR REPLACE FUNCTION public.get_dashboard_stats()
RETURNS SETOF public.dashboard_stats AS $$
BEGIN
    RETURN QUERY SELECT * FROM public.dashboard_stats;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- FUNCTIONS
-- ============================================
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, auth_user_id, email, display_name)
    VALUES (
        gen_random_uuid(),
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'display_name', split_part(NEW.email, '@', 1))
    )
    ON CONFLICT (auth_user_id) DO UPDATE SET
        email = EXCLUDED.email,
        display_name = COALESCE(EXCLUDED.display_name, public.profiles.display_name),
        updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to auto-create profile on new auth user
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for profile
DROP TRIGGER IF EXISTS trigger_profiles_updated ON public.profiles;
CREATE TRIGGER trigger_profiles_updated BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

DROP TRIGGER IF EXISTS trigger_accounts_updated ON public.accounts;
CREATE TRIGGER trigger_accounts_updated BEFORE UPDATE ON public.accounts
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

DROP TRIGGER IF EXISTS trigger_channels_updated ON public.channels;
CREATE TRIGGER trigger_channels_updated BEFORE UPDATE ON public.channels
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

DROP TRIGGER IF EXISTS trigger_upload_jobs_updated ON public.upload_jobs;
CREATE TRIGGER trigger_upload_jobs_updated BEFORE UPDATE ON public.upload_jobs
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

DROP TRIGGER IF EXISTS trigger_bulk_batches_updated ON public.bulk_batches;
CREATE TRIGGER trigger_bulk_batches_updated BEFORE UPDATE ON public.bulk_batches
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

DROP TRIGGER IF EXISTS trigger_settings_updated ON public.settings;
CREATE TRIGGER trigger_settings_updated BEFORE UPDATE ON public.settings
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

-- ============================================
-- REAL-TIME SUBSCRIPTIONS
-- ============================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_publication_tables 
        WHERE pubname = 'supabase_realtime' AND tablename = 'profiles'
    ) THEN
        ALTER PUBLICATION supabase_realtime ADD TABLE public.profiles;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_publication_tables 
        WHERE pubname = 'supabase_realtime' AND tablename = 'profile_connections'
    ) THEN
        ALTER PUBLICATION supabase_realtime ADD TABLE public.profile_connections;
    END IF;
END $$;
