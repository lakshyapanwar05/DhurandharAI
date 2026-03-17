import { useEffect, useRef, useState } from 'react'
import anime from 'animejs'
import type { NetworkEvent } from '../types'

interface TimelineEvent {
  id: string
  timestamp: string
  domain: string
  description: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  color: string
}

interface AttackTimelineProps {
  networkData: NetworkEvent | null
  isActive: boolean
}

const DOMAIN_COLORS = {
  network: '#3b82f6',      // blue
  hardware: '#f97316',     // orange  
  user: '#a855f7',         // purple
  security: '#ef4444'      // red
}

export default function AttackTimeline({ networkData, isActive }: AttackTimelineProps) {
  const [events, setEvents] = useState<TimelineEvent[]>([])
  const timelineRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (networkData && isActive) {
      const newEvents = extractEventsFromNetworkData(networkData)
      setEvents(prev => [...prev, ...newEvents].slice(-20)) // Keep last 20 events
    } else if (!isActive) {
      // Clear timeline when not active
      setEvents([])
    }
  }, [networkData, isActive])

  useEffect(() => {
    // Animate new events entering from right
    anime({
      targets: '.timeline-event',
      translateX: [100, 0],
      opacity: [0, 1],
      duration: 500,
      easing: 'easeOutQuad',
      delay: anime.stagger(100)
    })
  }, [events])

  const extractEventsFromNetworkData = (data: NetworkEvent): TimelineEvent[] => {
    const newEvents: TimelineEvent[] = []
    const timestamp = new Date().toISOString()

    // Check each domain for anomalies
    Object.entries(data.domains).forEach(([domain, metrics]) => {
      if (metrics.anomaly) {
        newEvents.push({
          id: `${domain}-${Date.now()}`,
          timestamp,
          domain,
          description: getAnomalyDescription(domain, metrics),
          severity: getSeverityFromMetrics(metrics),
          color: DOMAIN_COLORS[domain as keyof typeof DOMAIN_COLORS]
        })
      }
    })

    return newEvents
  }

  const getAnomalyDescription = (domain: string, metrics: any): string => {
    switch (domain) {
      case 'network':
        if (metrics.ddos_score > 0.7) return 'High DDoS attack probability detected'
        if (metrics.packets_per_sec > 10000) return 'Unusual packet surge detected'
        return 'Network traffic anomaly detected'
      case 'hardware':
        if (metrics.cpu_percent > 90) return 'Critical CPU utilization spike'
        if (metrics.memory_percent > 85) return 'Memory usage threshold exceeded'
        return 'Hardware performance anomaly detected'
      case 'user':
        if (metrics.failed_logins > 5) return 'Multiple failed login attempts'
        if (metrics.suspicious_activity) return 'Suspicious user activity pattern'
        return 'User behavior anomaly detected'
      case 'security':
        if (metrics.firewall_hits > 1000) return 'Firewall hit threshold exceeded'
        if (metrics.ids_alerts?.length > 0) return 'IDS alerts triggered'
        return 'Security event anomaly detected'
      default:
        return 'Anomaly detected'
    }
  }

  const getSeverityFromMetrics = (metrics: any): 'low' | 'medium' | 'high' | 'critical' => {
    // Simple severity calculation based on metrics
    if (metrics.ddos_score > 0.8 || metrics.cpu_percent > 95) return 'critical'
    if (metrics.ddos_score > 0.6 || metrics.cpu_percent > 85) return 'high'
    if (metrics.anomaly) return 'medium'
    return 'low'
  }

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  if (!isActive || events.length === 0) return null

  return (
    <div className="w-full bg-[#0d1117]/60 border-t border-white/10 py-4">
      <div className="px-6">
        <h3 className="text-sm font-semibold text-white/60 uppercase tracking-wider mb-3">
          Attack Timeline
        </h3>
        
        <div ref={timelineRef} className="flex gap-4 overflow-x-auto pb-2 scrollbar-thin">
          {events.map((event, index) => (
            <div
              key={event.id}
              className="timeline-event flex-shrink-0 flex items-center gap-3 bg-[#0a0f0a] border border-white/10 rounded-lg px-4 py-2"
              style={{ borderLeftColor: event.color, borderLeftWidth: '3px' }}
            >
              {/* Time */}
              <span className="text-xs font-mono text-white/60">
                {formatTime(event.timestamp)}
              </span>
              
              {/* Event */}
              <div className="flex flex-col">
                <span 
                  className="text-xs font-semibold"
                  style={{ color: event.color }}
                >
                  {event.domain.toUpperCase()}
                </span>
                <span className="text-xs text-white/80 max-w-xs">
                  {event.description}
                </span>
              </div>
              
              {/* Severity indicator */}
              <div className={`w-2 h-2 rounded-full ${
                event.severity === 'critical' ? 'bg-red-400' :
                event.severity === 'high' ? 'bg-orange-400' :
                event.severity === 'medium' ? 'bg-yellow-400' :
                'bg-green-400'
              }`} />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
