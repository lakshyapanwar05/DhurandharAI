import { useEffect, useRef, useState, Component } from 'react'
import { ComposableMap, Geographies, Geography, Marker, Line } from 'react-simple-maps'
import anime from 'animejs'

// Error boundary for map component
class MapErrorBoundary extends Component<{children: React.ReactNode, fallback: React.ReactNode}, {hasError: boolean}> {
  constructor(props: any) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback
    }
    return this.props.children
  }
}

interface AttackOrigin {
  id: string
  coordinates: [number, number]
  city: string
  country: string
  attackType: string
  timestamp: string
  ip?: string
}

const geoUrl = 'https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json'

// Attack origin coordinates per scenario
const ATTACK_ORIGINS: Record<string, AttackOrigin[]> = {
  ddos: [
    { id: 'moscow', coordinates: [37.6, 55.7], city: 'Moscow', country: 'Russia', attackType: 'DDoS', timestamp: new Date().toISOString() },
    { id: 'beijing', coordinates: [116.4, 39.9], city: 'Beijing', country: 'China', attackType: 'DDoS', timestamp: new Date().toISOString() }
  ],
  bruteforce: [
    { id: 'bucharest', coordinates: [26.1, 44.4], city: 'Bucharest', country: 'Romania', attackType: 'Brute Force', timestamp: new Date().toISOString() },
    { id: 'saopaulo', coordinates: [-46.6, -23.5], city: 'São Paulo', country: 'Brazil', attackType: 'Brute Force', timestamp: new Date().toISOString() }
  ],
  insider: [
    { id: 'india', coordinates: [80.0, 20.0], city: 'Mumbai', country: 'India', attackType: 'Insider Threat', timestamp: new Date().toISOString() }
  ],
  cryptominer: [
    { id: 'kiev', coordinates: [30.5, 50.4], city: 'Kiev', country: 'Ukraine', attackType: 'Cryptominer', timestamp: new Date().toISOString() },
    { id: 'jakarta', coordinates: [106.8, -6.2], city: 'Jakarta', country: 'Indonesia', attackType: 'Cryptominer', timestamp: new Date().toISOString() }
  ]
}

// Target coordinates (India)
const TARGET_COORDINATES: [number, number] = [80.0, 20.0]

interface GeoAttackMapProps {
  activeScenario: string | null
  onReset?: () => void
}

export default function GeoAttackMap({ activeScenario, onReset }: GeoAttackMapProps) {
  const [attacks, setAttacks] = useState<AttackOrigin[]>([])
  const [hoveredAttack, setHoveredAttack] = useState<AttackOrigin | null>(null)
  const [mapLoaded, setMapLoaded] = useState(false)
  const [mapError, setMapError] = useState(false)
  const mapRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    if (activeScenario && ATTACK_ORIGINS[activeScenario]) {
      const newAttacks = ATTACK_ORIGINS[activeScenario].map(attack => ({
        ...attack,
        timestamp: new Date().toISOString(),
        ip: generateMockIP()
      }))
      
      setAttacks(newAttacks)
      animateAttackDots()
    } else if (activeScenario === null) {
      // Clear attacks when reset
      setAttacks([])
    }
  }, [activeScenario])

  const generateMockIP = () => {
    return `${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`
  }

  const animateAttackDots = () => {
    // Animate attack dots pulsing
    anime({
      targets: '.attack-dot',
      scale: [1, 1.5, 1],
      opacity: [1, 0.7, 1],
      duration: 2000,
      easing: 'easeInOutSine',
      loop: true
    })

    // Animate arc lines
    anime({
      targets: '.attack-line',
      strokeDashoffset: [1000, 0],
      duration: 1500,
      easing: 'easeOutQuad',
      delay: anime.stagger(200)
    })
  }

  const getAttackColor = (attackType: string) => {
    switch (attackType) {
      case 'DDoS': return '#ff3131'
      case 'Brute Force': return '#ff9500'
      case 'Insider Threat': return '#ff9500'
      case 'Cryptominer': return '#ff3131'
      default: return '#00ff41'
    }
  }

  if (!activeScenario) return null

  // Fallback component when map fails to load
  const FallbackMap = () => (
    <div className="relative w-full h-96 bg-[#0a0f0a] rounded-lg border border-white/10 overflow-hidden">
      <div className="absolute top-4 left-4 z-10 bg-[#0d1117]/90 px-3 py-2 rounded border border-white/20">
        <h3 className="text-sm font-semibold text-white/80">ATTACK ORIGINS</h3>
      </div>
      
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="text-red-400 mb-4">🌍 Map unavailable</div>
          <div className="text-white/60 text-sm mb-4">Attack coordinates:</div>
          <div className="space-y-2">
            {attacks.map((attack) => (
              <div key={attack.id} className="text-white/80 text-xs bg-white/5 px-3 py-2 rounded">
                <span className="text-red-400">{attack.attackType}:</span> {attack.city}, {attack.country} 
                <span className="text-white/60"> ({attack.coordinates[0]}, {attack.coordinates[1]})</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )

  return (
    <div className="relative w-full h-96 bg-[#0a0f0a] rounded-lg border border-white/10 overflow-hidden" style={{ height: '400px' }}>
      {/* Header */}
      <div className="absolute top-4 left-4 z-10 bg-[#0d1117]/90 px-3 py-2 rounded border border-white/20">
        <h3 className="text-sm font-semibold text-white/80">ATTACK ORIGINS</h3>
      </div>

      {/* Reset button */}
      {onReset && (
        <button
          onClick={onReset}
          className="absolute top-4 right-4 z-10 px-3 py-1 bg-red-500/20 border border-red-500/50 text-red-400 text-sm rounded hover:bg-red-500/30 transition-colors"
        >
          Clear Map
        </button>
      )}

      {/* Loading state */}
      {!mapLoaded && !mapError && (
        <div className="flex items-center justify-center h-full">
          <div className="text-white/60">Loading attack map...</div>
        </div>
      )}

      {/* Map with error boundary */}
      <MapErrorBoundary fallback={<FallbackMap />}>
        <div ref={mapRef as any} className="w-full h-full">
          <ComposableMap
            projection="geoNaturalEarth1"
            projectionConfig={{
              scale: 100,
              center: [0, 0]
            }}
            onLoad={() => setMapLoaded(true)}
            onError={() => setMapError(true)}
          >
            <Geographies geography={geoUrl}>
              {({ geographies }: any) =>
                geographies.map((geo: any) => (
                  <Geography
                    key={geo.rsmKey}
                    geography={geo}
                    fill="#1a2332"
                    stroke="#00ff41"
                    strokeWidth={0.5}
                    style={{
                      default: { outline: 'none' },
                      hover: { fill: '#2a3342', outline: 'none' },
                      pressed: { outline: 'none' }
                    }}
                  />
                ))
              }
            </Geographies>

            {/* Attack markers */}
            {attacks.map((attack) => (
              <g key={attack.id}>
                {/* Arc line from origin to target */}
                <Line
                  from={attack.coordinates}
                  to={TARGET_COORDINATES}
                  stroke={getAttackColor(attack.attackType)}
                  strokeWidth={2}
                  strokeOpacity={0.6}
                  className="attack-line"
                  strokeDasharray="5,5"
                />
                
                {/* Attack origin dot */}
                <Marker coordinates={attack.coordinates}>
                  <circle
                    r="6"
                    fill={getAttackColor(attack.attackType)}
                    className="attack-dot"
                    onMouseEnter={() => setHoveredAttack(attack)}
                    onMouseLeave={() => setHoveredAttack(null)}
                    style={{ cursor: 'pointer' }}
                  />
                </Marker>
              </g>
            ))}

            {/* Target marker (India) */}
            <Marker coordinates={TARGET_COORDINATES}>
              <circle r="8" fill="#00ff41" opacity={0.8} />
              <text
                textAnchor="middle"
                y="-12"
                fill="#00ff41"
                fontSize="12"
                fontWeight="bold"
              >
                TARGET
              </text>
            </Marker>
          </ComposableMap>
        </div>
      </MapErrorBoundary>

      {/* Tooltip */}
      {hoveredAttack && (
        <div className="absolute bottom-4 left-4 bg-[#0d1117]/95 border border-white/20 rounded p-3 text-xs">
          <div className="text-red-400 font-semibold mb-1">{hoveredAttack.attackType}</div>
          <div className="text-white/80">{hoveredAttack.city}, {hoveredAttack.country}</div>
          <div className="text-white/60">IP: {hoveredAttack.ip}</div>
          <div className="text-white/60">Time: {new Date(hoveredAttack.timestamp).toLocaleTimeString()}</div>
        </div>
      )}
    </div>
  )
}
