import { useEffect, useState } from 'react'
import anime from 'animejs'

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
}

interface ThreatPopupProps {
  incident: Incident | null
  onClose: () => void
  onAskAI: () => void
}

export default function ThreatPopup({ incident, onClose, onAskAI }: ThreatPopupProps) {
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    if (incident) {
      setIsVisible(true)
      playAlertSound()
      animateEntrance()
      
      // Auto-dismiss after 30 seconds
      const timer = setTimeout(() => {
        handleClose()
      }, 30000)

      return () => clearTimeout(timer)
    }
  }, [incident])

  const playAlertSound = () => {
    try {
      const ctx = new AudioContext()
      const osc = ctx.createOscillator()
      const gainNode = ctx.createGain()
      
      osc.connect(gainNode)
      gainNode.connect(ctx.destination)
      
      osc.frequency.value = 880
      gainNode.gain.setValueAtTime(0.3, ctx.currentTime)
      gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.5)
      
      osc.start()
      osc.stop(ctx.currentTime + 0.5)
    } catch (error) {
      console.error('Error playing alert sound:', error)
    }
  }

  const animateEntrance = () => {
    anime({
      targets: '.threat-popup',
      scale: [0, 1],
      opacity: [0, 1],
      duration: 500,
      easing: 'easeOutElastic(1, .5)'
    })

    anime({
      targets: '.threat-border',
      borderColor: ['#ff3131', '#ff6b6b', '#ff3131'],
      duration: 2000,
      easing: 'linear',
      loop: true
    })

    anime({
      targets: '.threat-title',
      opacity: [1, 0.3, 1],
      duration: 1000,
      easing: 'linear',
      loop: true
    })
  }

  const handleClose = () => {
    anime({
      targets: '.threat-popup',
      scale: [1, 0],
      opacity: [1, 0],
      duration: 300,
      easing: 'easeInBack',
      complete: () => {
        setIsVisible(false)
        onClose()
      }
    })
  }

  const handleAcknowledge = () => {
    handleClose()
  }

  if (!isVisible || !incident) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Dark overlay */}
      <div className="absolute inset-0 bg-black/80 backdrop-blur-sm" />
      
      {/* Popup */}
      <div className="threat-popup relative w-full max-w-2xl mx-4 bg-[#0d1117] border-4 border-red-500 rounded-lg shadow-2xl">
        {/* Animated border glow */}
        <div className="threat-border absolute inset-0 rounded-lg border-4 border-red-500 shadow-[0_0_50px_rgba(255,49,49,0.5)]" />
        
        <div className="relative p-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="threat-title flex items-center gap-3">
              <span className="text-4xl">⚠</span>
              <h1 className="text-3xl font-bold text-red-400 uppercase tracking-wider">
                CRITICAL THREAT DETECTED
              </h1>
            </div>
            <button
              onClick={handleClose}
              className="text-white/60 hover:text-white transition-colors text-2xl"
            >
              ×
            </button>
          </div>

          {/* Incident details */}
          <div className="space-y-4 mb-8">
            <div className="bg-red-500/10 border border-red-500/30 rounded p-4">
              <h2 className="text-xl font-semibold text-red-400 mb-2">
                {incident.rule_name}
              </h2>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-white/60">Affected Domains:</span>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {incident.affected_domains.map((domain, i) => (
                      <span key={i} className="px-2 py-1 bg-red-500/20 text-red-300 rounded text-xs">
                        {domain}
                      </span>
                    ))}
                  </div>
                </div>
                <div>
                  <span className="text-white/60">Confidence Score:</span>
                  <div className="text-red-400 font-mono">
                    {(incident.confidence_score * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            </div>

            {/* Recommended actions */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-3">Recommended Actions:</h3>
              <ol className="space-y-2">
                {incident.recommended_actions.map((action, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <span className="text-red-400 font-mono">{i + 1}.</span>
                    <span className="text-white/80">{action}</span>
                  </li>
                ))}
              </ol>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex gap-4">
            <button
              onClick={handleAcknowledge}
              className="flex-1 px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white font-semibold rounded transition-colors"
            >
              ACKNOWLEDGE
            </button>
            <button
              onClick={onAskAI}
              className="flex-1 px-6 py-3 bg-red-500 hover:bg-red-600 text-white font-semibold rounded transition-colors flex items-center justify-center gap-2"
            >
              🤖 ASK AI
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
