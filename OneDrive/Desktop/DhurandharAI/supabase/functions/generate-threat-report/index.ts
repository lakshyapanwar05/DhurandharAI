import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const supabase = createClient(
  Deno.env.get('SUPABASE_URL')!,
  Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
)

Deno.serve(async () => {
  const { data: incidents } = await supabase
    .from('incidents')
    .select('*')
    .order('timestamp', { ascending: false })
    .limit(50)

  const stats = {
    total: incidents?.length || 0,
    critical: incidents?.filter(i => i.severity === 'CRITICAL').length || 0,
    high: incidents?.filter(i => i.severity === 'HIGH').length || 0,
    resolved: incidents?.filter(i => i.status === 'RESOLVED').length || 0
  }

  const geminiKey = Deno.env.get('GEMINI_API_KEY')
  const prompt = `
You are DhurandarAI. Generate a professional threat intelligence report.

Incidents: ${JSON.stringify(incidents?.slice(0, 20), null, 2)}
Stats: ${JSON.stringify(stats)}

Format in markdown:
# DhurandarAI Threat Intelligence Report
## Executive Summary
## Attack Timeline
## Critical Incidents
## Affected Domains Analysis
## Recommended Security Improvements
## Conclusion
`

  const geminiRes = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${geminiKey}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ parts: [{ text: prompt }] }]
      })
    }
  )

  const geminiData = await geminiRes.json()
  const report = geminiData.candidates?.[0]?.content?.parts?.[0]?.text || 
    '# Report generation failed'

  return new Response(JSON.stringify({ 
    report,
    stats,
    generated_at: new Date().toISOString()
  }), {
    headers: { 'Content-Type': 'application/json' }
  })
})