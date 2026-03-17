import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const supabase = createClient(
  Deno.env.get('SUPABASE_URL')!,
  Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
)

Deno.serve(async () => {
  const oneMinuteAgo = new Date(Date.now() - 60 * 1000).toISOString()
  
  const { data: recentIncidents, count } = await supabase
    .from('incidents')
    .select('*', { count: 'exact' })
    .gte('timestamp', oneMinuteAgo)

  if (!count || count < 3) {
    return new Response(JSON.stringify({ campaign_detected: false, count }), {
      headers: { 'Content-Type': 'application/json' }
    })
  }

  const severityCounts = recentIncidents!.reduce((acc: any, inc) => {
    acc[inc.severity] = (acc[inc.severity] || 0) + 1
    return acc
  }, {})

  const allDomains = [...new Set(
    recentIncidents!.flatMap(inc => inc.affected_domains || [])
  )]

  await supabase.from('incidents').insert({
    severity: 'CRITICAL',
    rule_name: 'Attack Campaign',
    affected_domains: allDomains,
    root_cause: `Coordinated attack: ${count} incidents in 60 seconds`,
    recommended_actions: [
      'Initiate incident response protocol',
      'Isolate affected network segments',
      'Alert security team immediately'
    ],
    confidence_score: 0.99,
    scenario_name: 'campaign'
  })

  return new Response(JSON.stringify({ 
    campaign_detected: true,
    incident_count: count,
    severity_breakdown: severityCounts,
    affected_domains: allDomains
  }), {
    headers: { 'Content-Type': 'application/json' }
  })
})
