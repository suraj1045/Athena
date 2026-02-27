import React, { useEffect, useRef, useState, useCallback } from 'react'
import ReactDOM from 'react-dom/client'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// ── Types ──────────────────────────────────────────────────────────────────────
interface Incident {
  id: string
  incident_type?: string
  type?: string
  latitude: number
  longitude: number
  camera_id: string
  confidence: number
  status: string
  detected_at: string
  cleared_at?: string
}

interface CriticalAlert {
  vehicle_id: string
  license_plate: string
  make: string
  model: string
  case_type: string
  case_number: string
  priority: string
  location: { latitude: number; longitude: number }
  camera_id: string
  timestamp: string
}

interface InterceptAlert {
  alert_id: string
  vehicle_plate: string
  vehicle_make: string
  vehicle_model: string
  violation_type: string
  location: { latitude: number; longitude: number }
  distance_m: number
  direction: string
  estimated_intercept_s: number
  generated_at?: string
}

// ── Constants ──────────────────────────────────────────────────────────────────
const API = 'http://localhost:8000'
const WS_URL = `ws://localhost:8000/ws/control/control-${Math.random().toString(36).slice(2)}`

const INCIDENT_COLORS: Record<string, string> = {
  STALLED_VEHICLE: '#F0883E',
  BREAKDOWN: '#E3B341',
  ACCIDENT: '#F85149',
  PEDESTRIAN_VIOLATION: '#BC8CFF',
}

const CASE_COLORS: Record<string, string> = {
  KIDNAPPING: '#F85149',
  HIT_AND_RUN: '#FF7B72',
  STOLEN: '#E3B341',
}

// ── Leaflet icon fix ──────────────────────────────────────────────────────────
function makeIcon(color: string, size = 14) {
  return L.divIcon({
    className: '',
    html: `<div style="width:${size}px;height:${size}px;background:${color};border:2px solid #fff;border-radius:50%;box-shadow:0 0 8px ${color}80"></div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  })
}

// ── Map auto-fit ──────────────────────────────────────────────────────────────
function FitBounds({ incidents }: { incidents: Incident[] }) {
  const map = useMap()
  useEffect(() => {
    if (incidents.length === 0) return
    const bounds = L.latLngBounds(incidents.map(i => [i.latitude, i.longitude]))
    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 15 })
  }, [incidents.length])
  return null
}

// ── Helpers ───────────────────────────────────────────────────────────────────
const fmtTime = (iso: string) =>
  new Date(iso).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })

const incidentLabel = (inc: Incident) =>
  (inc.incident_type || inc.type || 'UNKNOWN').replace(/_/g, ' ')

// ── Main App ──────────────────────────────────────────────────────────────────
const App: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [criticalAlerts, setCriticalAlerts] = useState<CriticalAlert[]>([])
  const [interceptAlerts, setInterceptAlerts] = useState<InterceptAlert[]>([])
  const [wsStatus, setWsStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting')
  const [activeTab, setActiveTab] = useState<'incidents' | 'critical' | 'intercept'>('incidents')
  const wsRef = useRef<WebSocket | null>(null)

  // ── Fetch initial data ──────────────────────────────────────────────────────
  useEffect(() => {
    fetch(`${API}/api/v1/incidents?limit=50`)
      .then(r => r.json())
      .then((data: Incident[]) => setIncidents(data))
      .catch(() => { })
  }, [])

  // ── WebSocket ───────────────────────────────────────────────────────────────
  const connectWs = useCallback(() => {
    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen = () => setWsStatus('connected')

    ws.onmessage = (e) => {
      const data = JSON.parse(e.data)
      if (data.type === 'INCIDENT_DETECTED') {
        setIncidents(prev => [data as Incident, ...prev].slice(0, 100))
      } else if (data.type === 'INCIDENT_CLEARED') {
        setIncidents(prev =>
          prev.map(i => i.id === data.incident_id ? { ...i, status: 'CLEARED' } : i)
        )
      } else if (data.type === 'CRITICAL_VEHICLE_DETECTED') {
        setCriticalAlerts(prev => [data as CriticalAlert, ...prev].slice(0, 30))
      } else if (data.type === 'INTERCEPT_ALERT') {
        setInterceptAlerts(prev => [data as InterceptAlert, ...prev].slice(0, 30))
      }
    }

    ws.onclose = () => {
      setWsStatus('disconnected')
      setTimeout(connectWs, 3000) // auto-reconnect
    }
  }, [])

  useEffect(() => { connectWs(); return () => wsRef.current?.close() }, [])

  // ── Clear incident ──────────────────────────────────────────────────────────
  const clearIncident = async (id: string) => {
    await fetch(`${API}/api/v1/incidents/${id}/clear`, { method: 'POST' })
    setIncidents(prev => prev.map(i => i.id === id ? { ...i, status: 'CLEARED' } : i))
  }

  const activeIncidents = incidents.filter(i => i.status === 'ACTIVE')

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: '#0D1117', color: '#C9D1D9', fontFamily: "'Inter', sans-serif" }}>

      {/* ── Header ── */}
      <header style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 20px', background: '#161B22', borderBottom: '1px solid #21262D', flexShrink: 0 }}>
        <span style={{ fontSize: 22 }}>🏛️</span>
        <div>
          <span style={{ fontSize: 18, fontWeight: 700, color: '#58A6FF', letterSpacing: 2 }}>ATHENA</span>
          <span style={{ fontSize: 12, color: '#8B949E', marginLeft: 10 }}>Urban Intelligence — Command Center</span>
        </div>
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 16 }}>
          <Stat label="Active Incidents" value={activeIncidents.length} color="#F85149" />
          <Stat label="Critical Vehicles" value={criticalAlerts.length} color="#FF7B72" />
          <Stat label="Intercept Alerts" value={interceptAlerts.length} color="#58A6FF" />
          <WsBadge status={wsStatus} />
        </div>
      </header>

      {/* ── Body ── */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>

        {/* ── Map ── */}
        <div style={{ flex: 1, position: 'relative' }}>
          <MapContainer
            center={[20.5937, 78.9629]}
            zoom={5}
            style={{ width: '100%', height: '100%' }}
            zoomControl={false}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            />
            {incidents.map(inc => (
              <Marker
                key={inc.id}
                position={[inc.latitude, inc.longitude]}
                icon={makeIcon(
                  inc.status === 'CLEARED' ? '#3D444D' : (INCIDENT_COLORS[inc.incident_type || inc.type || ''] || '#58A6FF'),
                  inc.status === 'ACTIVE' ? 16 : 10
                )}
              >
                <Popup>
                  <div style={{ background: '#161B22', color: '#C9D1D9', padding: 8, borderRadius: 6, minWidth: 180 }}>
                    <b style={{ color: INCIDENT_COLORS[inc.incident_type || inc.type || ''] || '#58A6FF' }}>
                      {incidentLabel(inc)}
                    </b>
                    <div style={{ fontSize: 11, marginTop: 4, color: '#8B949E' }}>Camera: {inc.camera_id}</div>
                    <div style={{ fontSize: 11, color: '#8B949E' }}>Conf: {(inc.confidence * 100).toFixed(0)}%</div>
                    <div style={{ fontSize: 11, color: '#8B949E' }}>{inc.detected_at ? fmtTime(inc.detected_at) : ''}</div>
                    {inc.status === 'ACTIVE' && (
                      <button onClick={() => clearIncident(inc.id)}
                        style={{ marginTop: 6, padding: '3px 8px', background: '#238636', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer', fontSize: 11 }}>
                        Clear Incident
                      </button>
                    )}
                  </div>
                </Popup>
              </Marker>
            ))}
            {criticalAlerts.map((a, i) => (
              <Marker
                key={`c-${i}`}
                position={[a.location.latitude, a.location.longitude]}
                icon={makeIcon(CASE_COLORS[a.case_type] || '#F85149', 18)}
              >
                <Popup>
                  <div style={{ background: '#161B22', color: '#C9D1D9', padding: 8, borderRadius: 6 }}>
                    <b style={{ color: '#F85149' }}>🚨 {a.case_type}</b>
                    <div style={{ fontSize: 12 }}>{a.license_plate} — {a.make} {a.model}</div>
                    <div style={{ fontSize: 11, color: '#8B949E' }}>Case: {a.case_number}</div>
                  </div>
                </Popup>
              </Marker>
            ))}
            {activeIncidents.length > 0 && <FitBounds incidents={activeIncidents} />}
          </MapContainer>

          {/* Map legend */}
          <div style={{ position: 'absolute', bottom: 12, left: 12, background: '#161B22CC', border: '1px solid #21262D', borderRadius: 8, padding: '8px 12px', zIndex: 1000, fontSize: 11 }}>
            {Object.entries(INCIDENT_COLORS).map(([k, v]) => (
              <div key={k} style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
                <div style={{ width: 10, height: 10, borderRadius: '50%', background: v }} />
                <span style={{ color: '#8B949E' }}>{k.replace(/_/g, ' ')}</span>
              </div>
            ))}
          </div>
        </div>

        {/* ── Right panel ── */}
        <div style={{ width: 380, display: 'flex', flexDirection: 'column', background: '#161B22', borderLeft: '1px solid #21262D', overflow: 'hidden' }}>

          {/* Tabs */}
          <div style={{ display: 'flex', borderBottom: '1px solid #21262D', flexShrink: 0 }}>
            {([['incidents', '🚦 Incidents'], ['critical', '🚨 Critical'], ['intercept', '⚡ Intercept']] as const).map(([tab, label]) => (
              <button key={tab} onClick={() => setActiveTab(tab)}
                style={{ flex: 1, padding: '10px 4px', background: activeTab === tab ? '#0D1117' : 'transparent', border: 'none', borderBottom: activeTab === tab ? '2px solid #58A6FF' : '2px solid transparent', color: activeTab === tab ? '#E6EDF3' : '#8B949E', cursor: 'pointer', fontSize: 12, fontFamily: 'inherit', fontWeight: activeTab === tab ? 600 : 400 }}>
                {label}
                <span style={{ marginLeft: 4, fontSize: 10, background: '#21262D', borderRadius: 10, padding: '1px 5px' }}>
                  {tab === 'incidents' ? incidents.filter(i => i.status === 'ACTIVE').length : tab === 'critical' ? criticalAlerts.length : interceptAlerts.length}
                </span>
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div style={{ flex: 1, overflowY: 'auto', padding: 8 }}>
            {activeTab === 'incidents' && incidents.map(inc => (
              <IncidentCard key={inc.id} inc={inc} onClear={clearIncident} />
            ))}
            {activeTab === 'critical' && criticalAlerts.length === 0 && <EmptyState label="No critical vehicle alerts" />}
            {activeTab === 'critical' && criticalAlerts.map((a, i) => (
              <CriticalCard key={i} alert={a} />
            ))}
            {activeTab === 'intercept' && interceptAlerts.length === 0 && <EmptyState label="No intercept alerts" />}
            {activeTab === 'intercept' && interceptAlerts.map((a, i) => (
              <InterceptCard key={i} alert={a} />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Sub-components ─────────────────────────────────────────────────────────────

const Stat: React.FC<{ label: string; value: number; color: string }> = ({ label, value, color }) => (
  <div style={{ textAlign: 'center' }}>
    <div style={{ fontSize: 20, fontWeight: 700, color }}>{value}</div>
    <div style={{ fontSize: 10, color: '#8B949E' }}>{label}</div>
  </div>
)

const WsBadge: React.FC<{ status: string }> = ({ status }) => {
  const colors = { connected: '#3FB950', connecting: '#E3B341', disconnected: '#F85149' }
  const c = colors[status as keyof typeof colors]
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, color: c, background: `${c}22`, border: `1px solid ${c}44`, borderRadius: 12, padding: '3px 10px' }}>
      <div style={{ width: 7, height: 7, borderRadius: '50%', background: c, animation: status === 'connected' ? 'pulse 2s infinite' : 'none' }} />
      {status.toUpperCase()}
    </div>
  )
}

const IncidentCard: React.FC<{ inc: Incident; onClear: (id: string) => void }> = ({ inc, onClear }) => {
  const label = incidentLabel(inc)
  const color = INCIDENT_COLORS[inc.incident_type || inc.type || ''] || '#58A6FF'
  const isActive = inc.status === 'ACTIVE'
  return (
    <div style={{ background: '#0D1117', border: `1px solid ${isActive ? color + '44' : '#21262D'}`, borderRadius: 8, padding: '10px 12px', marginBottom: 6 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <span style={{ fontSize: 11, fontWeight: 600, color, background: color + '22', padding: '2px 7px', borderRadius: 10 }}>{label}</span>
          <div style={{ fontSize: 11, color: '#8B949E', marginTop: 4 }}>📍 {inc.latitude.toFixed(4)}, {inc.longitude.toFixed(4)}</div>
          <div style={{ fontSize: 11, color: '#8B949E' }}>📷 {inc.camera_id} · {(inc.confidence * 100).toFixed(0)}% conf</div>
          {inc.detected_at && <div style={{ fontSize: 10, color: '#484F58', marginTop: 2 }}>{fmtTime(inc.detected_at)}</div>}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4, alignItems: 'flex-end' }}>
          <span style={{ fontSize: 10, color: isActive ? '#3FB950' : '#8B949E', background: isActive ? '#23863622' : '#21262D', padding: '2px 6px', borderRadius: 8 }}>{inc.status}</span>
          {isActive && (
            <button onClick={() => onClear(inc.id)}
              style={{ fontSize: 10, padding: '2px 6px', background: '#1F2937', border: '1px solid #30363D', borderRadius: 4, color: '#8B949E', cursor: 'pointer' }}>
              Clear
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

const CriticalCard: React.FC<{ alert: CriticalAlert }> = ({ alert }) => {
  const color = CASE_COLORS[alert.case_type] || '#F85149'
  return (
    <div style={{ background: '#0D1117', border: `1px solid ${color}44`, borderRadius: 8, padding: '10px 12px', marginBottom: 6 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <div>
          <span style={{ fontSize: 11, fontWeight: 700, color }}>🚨 {alert.case_type.replace(/_/g, ' ')}</span>
          <div style={{ fontSize: 13, fontWeight: 600, color: '#E6EDF3', marginTop: 3 }}>{alert.license_plate}</div>
          <div style={{ fontSize: 11, color: '#8B949E' }}>{alert.make} {alert.model}</div>
          <div style={{ fontSize: 11, color: '#8B949E' }}>Case: {alert.case_number}</div>
        </div>
        <span style={{ fontSize: 10, padding: '2px 7px', background: color + '22', color, borderRadius: 10, height: 'fit-content' }}>{alert.priority}</span>
      </div>
      {alert.timestamp && <div style={{ fontSize: 10, color: '#484F58', marginTop: 4 }}>{fmtTime(alert.timestamp)}</div>}
    </div>
  )
}

const InterceptCard: React.FC<{ alert: InterceptAlert }> = ({ alert }) => (
  <div style={{ background: '#0D1117', border: '1px solid #58A6FF44', borderRadius: 8, padding: '10px 12px', marginBottom: 6 }}>
    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
      <div>
        <span style={{ fontSize: 11, fontWeight: 700, color: '#58A6FF' }}>⚡ INTERCEPT</span>
        <div style={{ fontSize: 13, fontWeight: 600, color: '#E6EDF3', marginTop: 3 }}>{alert.vehicle_plate}</div>
        <div style={{ fontSize: 11, color: '#8B949E' }}>{alert.vehicle_make} {alert.vehicle_model}</div>
        <div style={{ fontSize: 11, color: '#E3B341' }}>{alert.violation_type.replace(/_/g, ' ')}</div>
      </div>
      <div style={{ textAlign: 'right' }}>
        <div style={{ fontSize: 16, fontWeight: 700, color: '#58A6FF' }}>{Math.round(alert.distance_m)}m</div>
        <div style={{ fontSize: 12, color: '#8B949E' }}>{alert.direction}</div>
        <div style={{ fontSize: 10, color: '#484F58' }}>{Math.round(alert.estimated_intercept_s)}s away</div>
      </div>
    </div>
  </div>
)

const EmptyState: React.FC<{ label: string }> = ({ label }) => (
  <div style={{ textAlign: 'center', padding: '40px 20px', color: '#484F58' }}>
    <div style={{ fontSize: 32, marginBottom: 8 }}>✓</div>
    <div style={{ fontSize: 13 }}>{label}</div>
  </div>
)

// ── Mount ─────────────────────────────────────────────────────────────────────
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode><App /></React.StrictMode>
)

export default App
