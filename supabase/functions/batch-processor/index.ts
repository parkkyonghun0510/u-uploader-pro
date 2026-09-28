// Supabase Edge Function: Batch Upload Processor
// Processes batch uploads using Supabase Queue

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
    const { batchId, action } = await req.json();

    const supabaseUrl = Deno.env.get('SUPABASE_URL') || 'https://aisbzppswxqknjvntaaa.supabase.co';
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
    const supabase = createClient(supabaseUrl, supabaseKey);

    if (action === 'start') {
      const { data: batch, error } = await supabase
        .from('bulk_batches')
        .update({ status: 'in_progress', started_at: new Date().toISOString() })
        .eq('id', batchId)
        .select()
        .single();

      if (error) throw error;

      // Get all videos from batch_data
      const videos = batch.batch_data || [];
      const videosProcessed = [];

      for (const video of videos) {
        const { data: job } = await supabase
          .from('upload_jobs')
          .insert({
            channel_id: batch.channel_id,
            account_id: batch.account_id,
            video_path: video.path,
            status: 'pending',
            metadata: video.metadata || {},
            priority: batch.priority || 'normal',
          })
          .select()
          .single();

        if (job) {
          videosProcessed.push(job);
        }
      }

      return new Response(
        JSON.stringify({ success: true, jobs: videosProcessed, count: videosProcessed.length }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    } else if (action === 'status') {
      const { data: batch } = await supabase
        .from('bulk_batches')
        .select('*')
        .eq('id', batchId)
        .single();

      return new Response(
        JSON.stringify({ success: true, batch }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      );
    }

    return new Response(
      JSON.stringify({ success: false, error: 'Invalid action' }),
      { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  } catch (error) {
    return new Response(
      JSON.stringify({ success: false, error: error.message }),
      { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }
});
