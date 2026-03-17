import { useState, useEffect } from 'react'
// import { supabase } from '../lib/supabase'
// import type { RealtimeChannel } from '@supabase/supabase-js'
import { handleProactiveAlert } from '../components/ChatAssistant'

interface Incident {
  id: number
  timestamp: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  rule_name: string
  affected_domains: string[]
  confidence_score: number
  root_cause: string
  recommended_actions: string[]
  matched_indicators: string[]
  status: 'active' | 'resolved'
  resolved_at?: string
}

interface IncidentStats {
  total: number
  active: number
  resolved: number
  critical: number
  high: number
  medium: number
  low: number
}

export function useIncidents() {
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [stats, setStats] = useState<IncidentStats>({
    total: 0,
    active: 0,
    resolved: 0,
    critical: 0,
    high: 0,
    medium: 0,
    low: 0
  })

  useEffect(() => {
    // Fetch initial data
    fetchIncidents()
    fetchStats()

    // Poll both incidents and stats every 3 seconds as fallback
    const interval = setInterval(() => {
      fetchIncidents()
      fetchStats()
    }, 3000)

    return () => clearInterval(interval)
  }, [])

  const fetchIncidents = async (timeFilterMinutes = 10) => {
    try {
      const response = await fetch('http://localhost:8000/api/incidents')
      const data = await response.json()
      
      // Filter to show only recent incidents and limit to 20
      const now = new Date()
      const timeAgo = new Date(now.getTime() - timeFilterMinutes * 60 * 1000)
      
      const recentIncidents = (data.incidents || [])
        .filter(incident => new Date(incident.timestamp) > timeAgo)
        .slice(0, 20)
      
      setIncidents(recentIncidents)
    } catch (error) {
      console.error('Error fetching incidents:', error)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/incidents/stats')
      const data = await response.json()
      setStats(data)
    } catch (error) {
      console.error('Error fetching stats:', error)
    }
  }

  const resolveIncident = async (incidentId: number) => {
    try {
      const response = await fetch(`http://localhost:8000/api/incidents/${incidentId}/resolve`, {
        method: 'PATCH'
      })
      const result = await response.json()
      
      // Refresh data after resolving
      if (result.success) {
        await fetchIncidents()
        await fetchStats()
      }
      
      return result.success
    } catch (error) {
      console.error('Error resolving incident:', error)
      return false
    }
  }

  const resolveAllIncidents = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/incidents/resolve-all', {
        method: 'PATCH'
      })
      const result = await response.json()
      
      // Refresh data after resolving
      if (result.success) {
        await fetchIncidents()
        await fetchStats()
      }
      
      return result.success
    } catch (error) {
      console.error('Error resolving all incidents:', error)
      return false
    }
  }

  const clearIncidentsView = () => {
    // Clear the incidents array immediately
    setIncidents([])
    // Refresh data
    fetchIncidents()
    fetchStats()
  }

  const triggerThreatAnimation = (incident: Incident) => {
    // This will be called from ThreatPopup component
    console.log('Triggering threat animation for:', incident)
    
    // Dispatch custom event for ThreatPopup to listen to
    window.dispatchEvent(new CustomEvent('criticalThreat', { 
      detail: incident 
    }))
  }

  return {
    incidents,
    stats,
    resolveIncident,
    resolveAllIncidents,
    clearIncidentsView,
    fetchIncidents,
    fetchStats
  }
}
