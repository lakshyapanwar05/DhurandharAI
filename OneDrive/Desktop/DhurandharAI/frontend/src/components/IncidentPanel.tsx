import { useEffect, useState } from 'react'
import anime from 'animejs'
import { useIncidents } from '../hooks/useIncidents'

export default function IncidentPanel() {
  const { incidents, stats, resolveIncident, resolveAllIncidents, clearIncidentsView } = useIncidents()
  const [fallbackIncidents, setFallbackIncidents] = useState<any[]>([])

  // Fallback direct fetch from backend
  useEffect(() => {
    const fetchIncidents = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/incidents')
        const data = await response.json()
        const incidents = Array.isArray(data) ? data : 
                         Array.isArray(data?.incidents) ? data.incidents : []
        setFallbackIncidents(incidents)
        console.log("📊 Fallback incidents fetched:", incidents.length)
      } catch (error) {
        console.error("❌ Failed to fetch fallback incidents:", error)
        setFallbackIncidents([])
      }
    }

    // Initial fetch
    fetchIncidents()
    
    // Poll every 5 seconds
    const interval = setInterval(fetchIncidents, 5000)
    
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    // Animate new rows
    anime({
      targets: '.incident-row-new',
      backgroundColor: [
        { value: '#ff3131', duration: 500 },
        { value: 'transparent', duration: 500 }
      ],
      duration: 1000,
      easing: 'easeInOutQuad'
    })
  }, [incidents])

  const handleResolve = async (incidentId: number) => {
    const success = await resolveIncident(incidentId)
    if (success) {
      // Animate resolution
      anime({
        targets: `.incident-row-${incidentId}`,
        opacity: [1, 0.5],
        translateX: [0, 20],
        duration: 500,
        easing: 'easeInQuad'
      })
    }
  }

  const handleResolveAll = async () => {
    const success = await resolveAllIncidents()
    if (success) {
      // Animate all rows resolution
      anime({
        targets: '.incident-row-new',
        opacity: [1, 0.3],
        translateX: [0, 20],
        duration: 500,
        easing: 'easeInQuad'
      })
    }
  }

  const handleClearView = () => {
    clearIncidentsView()
    // Animate clearing
    anime({
      targets: '.incident-row-new',
      opacity: [1, 0],
      translateY: [0, -10],
      duration: 300,
      easing: 'easeInQuad'
    })
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-400 bg-red-400/10 border-red-400/30'
      case 'high': return 'text-orange-400 bg-orange-400/10 border-orange-400/30'
      case 'medium': return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/30'
      case 'low': return 'text-green-400 bg-green-400/10 border-green-400/30'
      default: return 'text-gray-400 bg-gray-400/10 border-gray-400/30'
    }
  }

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="bg-[#0d1117]/60 border-t border-white/10">
      {/* Stats Bar */}
      <div className="grid grid-cols-8 gap-4 p-4 border-b border-white/10">
        <div className="text-center">
          <div className="text-2xl font-bold text-white">{stats?.total ?? 0}</div>
          <div className="text-xs text-white/60">Total</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-red-400">{stats?.critical ?? 0}</div>
          <div className="text-xs text-white/60">Critical</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-orange-400">{stats?.high ?? 0}</div>
          <div className="text-xs text-white/60">High</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-yellow-400">{stats?.medium ?? 0}</div>
          <div className="text-xs text-white/60">Medium</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-green-400">{stats?.resolved ?? 0}</div>
          <div className="text-xs text-white/60">Resolved</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-blue-400">{stats?.active ?? 0}</div>
          <div className="text-xs text-white/60">Active</div>
        </div>
        <div className="text-center">
          <button
            onClick={handleClearView}
            className="px-3 py-1 bg-blue-500 hover:bg-blue-600 text-white text-xs rounded transition-colors"
          >
            Clear View
          </button>
          <div className="text-xs text-white/60 mt-1">Reset View</div>
        </div>
        <div className="text-center">
          <button
            onClick={handleResolveAll}
            className="px-3 py-1 bg-red-500 hover:bg-red-600 text-white text-xs rounded transition-colors"
          >
            Clear All
          </button>
          <div className="text-xs text-white/60 mt-1">Resolve All</div>
        </div>
      </div>

      {/* Incidents Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-[#0a0f0a] border-b border-white/10">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-white/60 uppercase tracking-wider">Time</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-white/60 uppercase tracking-wider">Severity</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-white/60 uppercase tracking-wider">Rule</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-white/60 uppercase tracking-wider">Domains</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-white/60 uppercase tracking-wider">Confidence</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-white/60 uppercase tracking-wider">Status</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-white/60 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {(incidents?.length > 0 ? incidents : fallbackIncidents ?? []).map((incident, index) => (
              <tr 
                key={incident.id}
                className={`incident-row-${incident.id} ${index === 0 ? 'incident-row-new' : ''} hover:bg-white/5 transition-colors`}
              >
                <td className="px-4 py-3 font-mono text-white/60">
                  {formatTime(incident.timestamp)}
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 text-xs font-semibold rounded border ${getSeverityColor(incident.severity)}`}>
                    {incident.severity.toUpperCase()}
                  </span>
                </td>
                <td className="px-4 py-3 text-white/80 max-w-xs truncate">
                  {incident.rule_name}
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {(incident.affected_domains ?? []).map((domain, i) => (
                      <span key={i} className="px-1.5 py-0.5 bg-white/10 text-white/60 rounded text-xs">
                        {domain}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="px-4 py-3 font-mono text-white/80">
                  {(incident.confidence_score * 100).toFixed(1)}%
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 text-xs font-semibold rounded ${
                    incident.status === 'active' 
                      ? 'bg-red-400/20 text-red-400' 
                      : 'bg-green-400/20 text-green-400'
                  }`}>
                    {incident.status.toUpperCase()}
                  </span>
                </td>
                <td className="px-4 py-3">
                  {incident.status === 'active' && (
                    <button
                      onClick={() => handleResolve(incident.id)}
                      className="px-3 py-1 bg-blue-500 hover:bg-blue-600 text-white text-xs rounded transition-colors"
                    >
                      Resolve
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {incidents.length === 0 && (
          <div className="text-center py-8 text-white/40">
            No incidents recorded. System operating normally.
          </div>
        )}
      </div>
    </div>
  )
}
