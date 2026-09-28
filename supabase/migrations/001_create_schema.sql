-- Supabase Migration: YouTube Uploader Pro Schema
-- Project: https://aisbzppswxqknjvntaaa.supabase.co
-- Generated: 2026-09-27

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================
-- TABLE: accounts (YouTube account management)
-- ============================================
CREATE TABLE IF NOT EXISTS public.accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    account_type TEXT DEFAULT 'personal' CHECK (account_type IN ('personal', 'brand', 'business')),
    google_access_token TEXT,
    google_refresh_token TEXT,
    google_token_expires_at TIMESTAMPTZ,
    google_profile_image TEXT,
    is_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- TABLE: channels (YouTube channel management)
-- ============================================
CREATE TABLE IF NOT EXISTS public.channels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID REFERENCES public.accounts(id) ON DELETE CASCADE,
    channel_id TEXT UNIQUE,
    name TEXT NOT NULL,
    handle TEXT,
    description TEXT,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    subscriber_count INTEGER DEFAULT 0,
    video_count INTEGER DEFAULT 0,
    view_count BIGINT DEFAULT 0,
    custom_url TEXT,
    default_language TEXT DEFAULT 'en',
    country TEXT DEFAULT 'US',
    branding_settings JSONB DEFAULT '{}',
    is_managed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- TABLE: upload_jobs (Upload queue and tracking)
-- ============================================
CREATE TABLE IF NOT EXISTS public.upload_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    channel_id UUID REFERENCES public.channels(id),
    account_id UUID REFERENCES public.accounts(id),
    video_path TEXT NOT NULL,
    video_file_url TEXT,
    metadata_path TEXT,
    thumbnail_path TEXT,
    thumbnail_url TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'cancelled', 'scheduled')),
    priority TEXT DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high')),
    progress FLOAT DEFAULT 0.0,
    video_id TEXT,
    video_title TEXT,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    schedule_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- TABLE: metadata_templates (Per-channel templates)
-- ============================================
CREATE TABLE IF NOT EXISTS public.metadata_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    channel_id UUID REFERENCES public.channels(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    title_template TEXT DEFAULT '{video_title}',
    description_template TEXT DEFAULT '{video_description}',
    tags TEXT[],
    category TEXT DEFAULT '22',
    language TEXT DEFAULT 'en',
    privacy_status TEXT DEFAULT 'private' CHECK (privacy_status IN ('public', 'private', 'unlisted')),
    made_for_kids BOOLEAN DEFAULT FALSE,
    upload_schedule TEXT,
    branding_settings JSONB DEFAULT '{}',
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- TABLE: bulk_batches (Batch uploads)
-- ============================================
CREATE TABLE IF NOT EXISTS public.bulk_batches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    channel_id UUID REFERENCES public.channels(id),
    account_id UUID REFERENCES public.accounts(id),
    name TEXT NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
    video_count INTEGER DEFAULT 0,
    uploaded_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    template_id UUID REFERENCES public.metadata_templates(id),
    priority TEXT DEFAULT 'normal',
    batch_data JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

-- ============================================
-- TABLE: upload_history (Complete history)
-- ============================================
CREATE TABLE IF NOT EXISTS public.upload_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES public.upload_jobs(id),
    channel_id UUID REFERENCES public.channels(id),
    video_id TEXT,
    video_title TEXT,
    video_url TEXT,
    status TEXT,
    progress FLOAT,
    duration_seconds INTEGER,
    file_size BIGINT,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- TABLE: notifications (User notifications)
-- ============================================
CREATE TABLE IF NOT EXISTS public.notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.accounts(id),
    type TEXT CHECK (type IN ('upload_complete', 'upload_failed', 'upload_scheduled', 'batch_complete', 'system')),
    message TEXT,
    data JSONB,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- TABLE: settings (User preferences)
-- ============================================
CREATE TABLE IF NOT EXISTS public.settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.accounts(id) UNIQUE,
    theme TEXT DEFAULT 'dark' CHECK (theme IN ('dark', 'light')),
    max_retries INTEGER DEFAULT 3,
    retry_delay INTEGER DEFAULT 10,
    auto_login BOOLEAN DEFAULT FALSE,
    notifications_enabled BOOLEAN DEFAULT TRUE,
    default_channel UUID REFERENCES public.channels(id),
    default_priority TEXT DEFAULT 'normal',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================
CREATE INDEX IF NOT EXISTS idx_upload_jobs_channel ON public.upload_jobs(channel_id);
CREATE INDEX IF NOT EXISTS idx_upload_jobs_account ON public.upload_jobs(account_id);
CREATE INDEX IF NOT EXISTS idx_upload_jobs_status ON public.upload_jobs(status);
CREATE INDEX IF NOT EXISTS idx_upload_jobs_schedule ON public.upload_jobs(schedule_at) WHERE schedule_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_channels_account ON public.channels(account_id);
CREATE INDEX IF NOT EXISTS idx_channels_name ON public.channels(name);
CREATE INDEX IF NOT EXISTS idx_templates_channel ON public.metadata_templates(channel_id);
CREATE INDEX IF NOT EXISTS idx_batches_channel ON public.bulk_batches(channel_id);
CREATE INDEX IF NOT EXISTS idx_batches_status ON public.bulk_batches(status);
CREATE INDEX IF NOT EXISTS idx_history_job ON public.upload_history(job_id);
CREATE INDEX IF NOT EXISTS idx_history_channel ON public.upload_history(channel_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON public.notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_settings_user ON public.settings(user_id);

-- ============================================
-- REAL-TIME SUBSCRIPTION SETUP
-- ============================================
ALTER PUBLICATION supabase_realtime ADD TABLE public.upload_jobs;
ALTER PUBLICATION supabase_realtime ADD TABLE public.channels;
ALTER PUBLICATION supabase_realtime ADD TABLE public.bulk_batches;
ALTER PUBLICATION supabase_realtime ADD TABLE public.notifications;

-- ============================================
-- FUNCTIONS
-- ============================================
CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- TRIGGERS
-- ============================================
CREATE TRIGGER trigger_accounts_updated BEFORE UPDATE ON public.accounts
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();
CREATE TRIGGER trigger_channels_updated BEFORE UPDATE ON public.channels
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();
CREATE TRIGGER trigger_upload_jobs_updated BEFORE UPDATE ON public.upload_jobs
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();
CREATE TRIGGER trigger_bulk_batches_updated BEFORE UPDATE ON public.bulk_batches
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();
CREATE TRIGGER trigger_settings_updated BEFORE UPDATE ON public.settings
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

-- ============================================
-- VIEWS FOR DASHBOARD
-- ============================================
CREATE OR REPLACE VIEW public.dashboard_stats AS
SELECT
    COUNT(DISTINCT a.id) as total_accounts,
    COUNT(DISTINCT c.id) as total_channels,
    COUNT(DISTINCT t.id) as total_templates,
    COUNT(DISTINCT b.id) as total_batches,
    COUNT(DISTINCT j.id) as total_uploads,
    COUNT(DISTINCT CASE WHEN j.status = 'completed' THEN j.id END) as completed_uploads,
    COUNT(DISTINCT CASE WHEN j.status = 'failed' THEN j.id END) as failed_uploads,
    COUNT(DISTINCT CASE WHEN c.status = 'active' THEN c.id END) as active_channels,
    COALESCE(SUM(j.progress), 0) / NULLIF(COUNT(DISTINCT j.id), 0) as avg_progress
FROM public.accounts a
LEFT JOIN public.channels c ON c.account_id = a.id
LEFT JOIN public.metadata_templates t ON t.channel_id = c.id
LEFT JOIN public.bulk_batches b ON b.channel_id = c.id
LEFT JOIN public.upload_jobs j ON j.channel_id = c.id OR j.account_id = a.id;

-- ============================================
-- RLS POLICIES
-- ============================================
ALTER TABLE public.accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.channels ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.upload_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.metadata_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bulk_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.upload_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.settings ENABLE ROW LEVEL SECURITY;

-- Accounts policies
CREATE POLICY "Users can view own accounts" ON public.accounts
    FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can insert own accounts" ON public.accounts
    FOR INSERT WITH CHECK (auth.uid() = id);
CREATE POLICY "Users can update own accounts" ON public.accounts
    FOR UPDATE USING (auth.uid() = id);

-- Channels policies
CREATE POLICY "Users can view own channels" ON public.channels
    FOR SELECT USING (auth.uid() IN (SELECT id FROM public.accounts));
CREATE POLICY "Users can insert own channels" ON public.channels
    FOR INSERT WITH CHECK (auth.uid() IN (SELECT id FROM public.accounts));
CREATE POLICY "Users can update own channels" ON public.channels
    FOR UPDATE USING (auth.uid() IN (SELECT id FROM public.accounts));

-- Upload jobs policies
CREATE POLICY "Users can view own upload jobs" ON public.upload_jobs
    FOR SELECT USING (auth.uid() IN (SELECT id FROM public.accounts));
CREATE POLICY "Users can insert own upload jobs" ON public.upload_jobs
    FOR INSERT WITH CHECK (auth.uid() IN (SELECT id FROM public.accounts));
CREATE POLICY "Users can update own upload jobs" ON public.upload_jobs
    FOR UPDATE USING (auth.uid() IN (SELECT id FROM public.accounts));

-- Metadata templates policies
CREATE POLICY "Users can view own templates" ON public.metadata_templates
    FOR SELECT USING (auth.uid() IN (SELECT id FROM public.accounts));
CREATE POLICY "Users can insert own templates" ON public.metadata_templates
    FOR INSERT WITH CHECK (auth.uid() IN (SELECT id FROM public.accounts));
CREATE POLICY "Users can update own templates" ON public.metadata_templates
    FOR UPDATE USING (auth.uid() IN (SELECT id FROM public.accounts));

-- Bulk batches policies
CREATE POLICY "Users can view own batches" ON public.bulk_batches
    FOR SELECT USING (auth.uid() IN (SELECT id FROM public.accounts));
CREATE POLICY "Users can insert own batches" ON public.bulk_batches
    FOR INSERT WITH CHECK (auth.uid() IN (SELECT id FROM public.accounts));
CREATE POLICY "Users can update own batches" ON public.bulk_batches
    FOR UPDATE USING (auth.uid() IN (SELECT id FROM public.accounts));

-- Upload history policies
CREATE POLICY "Users can view own history" ON public.upload_history
    FOR SELECT USING (auth.uid() IN (SELECT id FROM public.accounts));
CREATE POLICY "Users can insert own history" ON public.upload_history
    FOR INSERT WITH CHECK (auth.uid() IN (SELECT id FROM public.accounts));

-- Notifications policies
CREATE POLICY "Users can view own notifications" ON public.notifications
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own notifications" ON public.notifications
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own notifications" ON public.notifications
    FOR UPDATE USING (auth.uid() = user_id);

-- Settings policies
CREATE POLICY "Users can view own settings" ON public.settings
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can upsert own settings" ON public.settings
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own settings" ON public.settings
    FOR UPDATE USING (auth.uid() = user_id);