import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const supabase = createClient(
  Deno.env.get('SUPABASE_URL')!,
  Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
)

const ESCALATION_MAP: Record<string, string> = {
  'LOW': 'MEDIUM',
  'MEDIUM': 'HIGH',
  'HIGH': 'CRITICAL'
}

Deno.serve(async () => {
  const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000).toISOString()
  
  const { data: incidents } = await supabase
    .from('incidents')
    .select('*')
    .eq('status', 'ACTIVE')
    .neq('severity', 'CRITICAL')
    .lt('timestamp', fiveMinutesAgo)

  if (!incidents || incidents.length === 0) {
    return new Response(JSON.stringify({ escalated: 0 }), {
      headers: { 'Content-Type': 'application/json' }
    })
  }

  const escalated = []
  for (const incident of incidents) {
    const newSeverity = ESCALATION_MAP[incident.severity]
    if (newSeverity) {
      await supabase
        .from('incidents')
        .update({ severity: newSeverity })
        .eq('id', incident.id)
      escalated.push({ id: incident.id, from: incident.severity, to: newSeverity })
    }
  }

  return new Response(JSON.stringify({ escalated: escalated.length, details: escalated }), {
    headers: { 'Content-Type': 'application/json' }
  })
})
