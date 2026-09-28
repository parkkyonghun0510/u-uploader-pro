// Supabase Edge Function: Upload Handler
// Handles video upload processing, YouTube API interaction, and status updates

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const { channelId, videoPath, accountId, metadata, priority } = await req.json();

    const supabaseUrl = Deno.env.get('SUPABASE_URL') || 'https://aisbzppswxqknjvntaaa.supabase.co';
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
    const supabase = createClient(supabaseUrl, supabaseKey);

    // Create upload job
    const { data: job, error: jobError } = await supabase
      .from('upload_jobs')
      .insert({
        channel_id: channelId,
        account_id: accountId,
        video_path: videoPath,
        status: 'pending',
        priority: priority || 'normal',
        metadata: metadata || {},
      })
      .select()
      .single();

    if (jobError) throw jobError;

    // Return job ID to client
    return new Response(
      JSON.stringify({ success: true, jobId: job.id, status: 'pending' }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  } catch (error) {
    return new Response(
      JSON.stringify({ success: false, error: error.message }),
      { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});
