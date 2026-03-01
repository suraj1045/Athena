import React, { useEffect, useRef, useState, useCallback } from 'react'
import ReactDOM from 'react-dom/client'
import { MapContainer, TileLayer, Marker, Popup, useMap, Polyline } from 'react-leaflet'
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

interface Officer {
  officer_id: string
  latitude: number
  longitude: number
  heading: number
  speed_mps: number
  on_duty: boolean
  last_updated: string
}

// ── Constants ──────────────────────────────────────────────────────────────────
const API = 'http://localhost:8000'
const WS_URL = `ws://localhost:8000/ws/control/control-${Math.random().toString(36).slice(2)}`

// Bengaluru city center + bounds
const BENGALURU_CENTER: [number, number] = [12.9716, 77.5946]
const BENGALURU_BOUNDS = L.latLngBounds(
  L.latLng(12.7342, 77.3791), // SW corner
  L.latLng(13.1726, 77.8415)  // NE corner
)
const BENGALURU_ZOOM = 13

// Demo seed data — shown when backend has no data (purely for visual verification)
const DEMO_OFFICERS: Officer[] = [
  { officer_id: 'KA-BLR-001', latitude: 12.9719, longitude: 77.5937, heading: 45, speed_mps: 0, on_duty: true, last_updated: new Date().toISOString() },
  { officer_id: 'KA-BLR-002', latitude: 12.9352, longitude: 77.6245, heading: 135, speed_mps: 4.2, on_duty: true, last_updated: new Date().toISOString() },
  { officer_id: 'KA-BLR-003', latitude: 13.0079, longitude: 77.5643, heading: 270, speed_mps: 8.3, on_duty: true, last_updated: new Date().toISOString() },
  { officer_id: 'KA-BLR-004', latitude: 12.9592, longitude: 77.6416, heading: 0, speed_mps: 0, on_duty: true, last_updated: new Date().toISOString() },
  { officer_id: 'KA-BLR-005', latitude: 12.9698, longitude: 77.7500, heading: 90, speed_mps: 5.6, on_duty: false, last_updated: new Date().toISOString() },
  { officer_id: 'KA-BLR-006', latitude: 12.9279, longitude: 77.5003, heading: 200, speed_mps: 2.1, on_duty: true, last_updated: new Date().toISOString() },
]

const DEMO_TRACKED_VEHICLES = [
  { id: 'tv-1', plate: 'KA 05 MN 1234', make: 'Toyota', model: 'Innova', caseType: 'STOLEN', latitude: 12.9658, longitude: 77.6197, color: '#E3B341' },
  { id: 'tv-2', plate: 'KA 01 AB 9876', make: 'Honda', model: 'City', caseType: 'HIT_AND_RUN', latitude: 12.9890, longitude: 77.5720, color: '#FF7B72' },
  { id: 'tv-3', plate: 'KA 19 CD 5555', make: 'Maruti', model: 'Swift', caseType: 'KIDNAPPING', latitude: 12.9445, longitude: 77.6890, color: '#F85149' },
  { id: 'tv-4', plate: 'KA 03 EF 7777', make: 'Hyundai', model: 'Creta', caseType: 'STOLEN', latitude: 13.0200, longitude: 77.6100, color: '#E3B341' },
]

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

// ── Icons ──────────────────────────────────────────────────────────────────────
function makeIcon(color: string, size = 14) {
  return L.divIcon({
    className: '',
    html: `<div style="width:${size}px;height:${size}px;background:${color};border:2px solid #fff;border-radius:50%;box-shadow:0 0 8px ${color}80"></div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  })
}

function makeOfficerIcon(onDuty: boolean, heading: number) {
  const color = onDuty ? '#58A6FF' : '#8B949E'
  const arrowRotate = heading
  return L.divIcon({
    className: '',
    html: `
      <div style="position:relative;width:32px;height:32px;">
        <div style="
          position:absolute;inset:0;
          background:${color};
          border:2px solid #fff;
          border-radius:50%;
          box-shadow:0 0 12px ${color}99;
          display:flex;align-items:center;justify-content:center;
          font-size:14px;line-height:1;
        ">🚔</div>
        <div style="
          position:absolute;top:-6px;left:50%;transform:translateX(-50%) rotate(${arrowRotate}deg);
          width:0;height:0;
          border-left:5px solid transparent;
          border-right:5px solid transparent;
          border-bottom:8px solid ${color};
          transform-origin:50% 100%;
        "></div>
      </div>`,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
  })
}

function makeVehicleIcon(color: string) {
  return L.divIcon({
    className: '',
    html: `
      <div style="position:relative;width:36px;height:36px;">
        <div style="
          position:absolute;inset:4px;
          background:#0D1117;
          border:2px solid ${color};
          border-radius:6px;
          display:flex;align-items:center;justify-content:center;
          font-size:15px;
          box-shadow:0 0 14px ${color}99;
        ">🚗</div>
        <div style="
          position:absolute;inset:-2px;
          border:2px solid ${color};
          border-radius:10px;
          animation:vehiclePulse 1.5s ease-in-out infinite;
          opacity:0.5;
        "></div>
      </div>`,
    iconSize: [36, 36],
    iconAnchor: [18, 18],
  })
}

// ── Map helpers ────────────────────────────────────────────────────────────────
function BengaluruMapSetup() {
  const map = useMap()
  useEffect(() => {
    map.setMaxBounds(BENGALURU_BOUNDS)
    map.setMinZoom(10)
  }, [])
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
  const [officers, setOfficers] = useState<Officer[]>([])
  const [wsStatus, setWsStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting')
  const [activeTab, setActiveTab] = useState<'incidents' | 'critical' | 'intercept' | 'vehicles'>('incidents')
  const [predictedRoutes, setPredictedRoutes] = useState<Record<string, { lat: number; lng: number }[]>>({})
  const wsRef = useRef<WebSocket | null>(null)

  // Build tracked vehicle list from critical alerts + demo data
  const trackedVehicles = criticalAlerts.length > 0
    ? criticalAlerts.map(a => ({
      id: `crit-${a.vehicle_id}`,
      plate: a.license_plate,
      make: a.make,
      model: a.model,
      caseType: a.case_type,
      latitude: a.location.latitude,
      longitude: a.location.longitude,
      color: CASE_COLORS[a.case_type] || '#F85149',
    }))
    : DEMO_TRACKED_VEHICLES

  // ── Fetch initial data ──────────────────────────────────────────────────────
  useEffect(() => {
    Promise.all([
      fetch(`${API}/api/v1/incidents?limit=50`).then(r => r.json()),
      fetch(`${API}/api/v1/officers`).then(r => r.json()).catch(() => [])
    ]).then(([incData, offData]) => {
      setIncidents(incData)
      // Use demo officers if backend returns empty list
      setOfficers(Array.isArray(offData) && offData.length > 0 ? offData : DEMO_OFFICERS)
    }).catch(() => {
      setOfficers(DEMO_OFFICERS)
    })
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
      } else if (data.type === 'OFFICER_LOCATION_UPDATE') {
        setOfficers(prev => {
          const idx = prev.findIndex(o => o.officer_id === data.officer_id)
          if (idx >= 0) {
            const next = [...prev]
            next[idx] = data as Officer
            return next
          }
          return [...prev, data as Officer]
        })
      }
    }

    ws.onclose = () => {
      setWsStatus('disconnected')
      setTimeout(connectWs, 3000) // auto-reconnect
    }
  }, [])

  useEffect(() => { connectWs(); return () => wsRef.current?.close() }, [])

  // ── Route Prediction ────────────────────────────────────────────────────────
  useEffect(() => {
    trackedVehicles.forEach(v => {
      // Only predict for non-demo vehicles (IDs starting with 'crit-')
      if (v.id.startsWith('crit-') && !predictedRoutes[v.id]) {
        const vehicleId = v.id.replace('crit-', '')
        fetch(`${API}/api/v1/vehicles/critical/${vehicleId}/predicted-route`)
          .then(r => r.json())
          .then(coords => {
            if (Array.isArray(coords) && coords.length > 0) {
              setPredictedRoutes(prev => ({ ...prev, [v.id]: coords }))
            }
          }).catch(err => console.error('Prediction fetch error:', err))
      }
    })
  }, [trackedVehicles, predictedRoutes])

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
          <style>{`
            @keyframes vehiclePulse {
              0%,100% { opacity:0.5; transform:scale(1); }
              50%      { opacity:0.1; transform:scale(1.5); }
            }
          `}</style>
          <MapContainer
            center={BENGALURU_CENTER}
            zoom={BENGALURU_ZOOM}
            style={{ width: '100%', height: '100%' }}
            zoomControl={true}
            maxBounds={BENGALURU_BOUNDS}
            maxBoundsViscosity={1.0}
          >
            {/* @ts-ignore */}
            {Object.entries(predictedRoutes).map(([vid, coords]) => {
              const vehicle = trackedVehicles.find(v => v.id === vid)
              return (
                <Polyline
                  key={`route-${vid}`}
                  positions={coords.map(c => [c.lat, c.lng] as [number, number])}
                  color={vehicle?.color || '#58A6FF'}
                  dashArray="10, 10"
                  weight={3}
                  opacity={0.7}
                />
              )
            })}
            {/* @ts-ignore */}
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> | Bengaluru Police Command'
              maxZoom={19}
            />
            {/* @ts-ignore */}
            <BengaluruMapSetup />

            {/* @ts-ignore */}
            {incidents.map(inc => (
              <Marker
                key={inc.id}
                position={[inc.latitude, inc.longitude]}
                icon={makeIcon(
                  inc.status === 'CLEARED' ? '#3D444D' : (INCIDENT_COLORS[(inc.incident_type || inc.type || '')] || '#58A6FF'),
                  inc.status === 'ACTIVE' ? 16 : 10
                )}
              >
                <Popup>
                  <div style={{ background: '#161B22', color: '#C9D1D9', padding: 8, borderRadius: 6, minWidth: 190 }}>
                    <b style={{ color: INCIDENT_COLORS[(inc.incident_type || inc.type || '')] || '#58A6FF' }}>
                      {incidentLabel(inc)}
                    </b>
                    <div style={{ fontSize: 11, marginTop: 4, color: '#8B949E' }}>📷 {inc.camera_id}</div>
                    <div style={{ fontSize: 11, color: '#8B949E' }}>Conf: {((inc.confidence || 0) * 100).toFixed(0)}%</div>
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

            {/* @ts-ignore */}
            {trackedVehicles.map(v => (
              <Marker
                key={v.id}
                position={[v.latitude, v.longitude]}
                icon={makeVehicleIcon(v.color)}
              >
                <Popup>
                  <div style={{ background: '#161B22', color: '#C9D1D9', padding: 10, borderRadius: 6, minWidth: 200 }}>
                    <b style={{ color: v.color }}>🚗 TRACKED VEHICLE</b>
                    <div style={{ fontSize: 14, fontWeight: 700, color: '#E6EDF3', marginTop: 4 }}>{v.plate}</div>
                    <div style={{ fontSize: 11, color: '#8B949E' }}>{v.make} {v.model}</div>
                    <div style={{ fontSize: 11, marginTop: 4 }}>
                      <span style={{ color: v.color, background: v.color + '22', padding: '2px 6px', borderRadius: 8 }}>
                        {v.caseType.replace(/_/g, ' ')}
                      </span>
                    </div>
                    <div style={{ marginTop: 8, fontSize: 11, color: '#F85149', fontWeight: 600 }}>⚠ INTERCEPT REQUIRED</div>
                  </div>
                </Popup>
              </Marker>
            ))}

            {/* @ts-ignore */}
            {officers.map(o => (
              <Marker
                key={`off-${o.officer_id}`}
                position={[o.latitude, o.longitude]}
                icon={makeOfficerIcon(o.on_duty, o.heading ?? 0)}
              >
                <Popup>
                  <div style={{ background: '#161B22', color: '#C9D1D9', padding: 10, borderRadius: 6, minWidth: 190 }}>
                    <b style={{ color: o.on_duty ? '#58A6FF' : '#8B949E' }}>🚔 Officer {o.officer_id}</b>
                    <div style={{ fontSize: 11, color: '#8B949E', marginTop: 4 }}>
                      Status: <span style={{ color: o.on_duty ? '#3FB950' : '#F85149' }}>{o.on_duty ? 'ON DUTY' : 'OFF DUTY'}</span>
                    </div>
                    <div style={{ fontSize: 11, color: '#8B949E' }}>Speed: {Math.round((o.speed_mps ?? 0) * 3.6)} km/h</div>
                    <div style={{ fontSize: 11, color: '#8B949E' }}>Heading: {o.heading ?? 0}°</div>
                    <div style={{ fontSize: 10, color: '#484F58', marginTop: 4 }}>{o.last_updated ? fmtTime(o.last_updated) : ''}</div>
                  </div>
                </Popup>
              </Marker>
            ))}
          </MapContainer>

          {/* Map legend */}
          <div style={{ position: 'absolute', bottom: 12, left: 12, background: '#161B22EE', border: '1px solid #21262D', borderRadius: 8, padding: '10px 14px', zIndex: 1000, fontSize: 11, minWidth: 170 }}>
            <div style={{ fontWeight: 700, color: '#E6EDF3', marginBottom: 6, fontSize: 12 }}>📍 Bengaluru Command</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
              <span style={{ fontSize: 14 }}>🚔</span>
              <span style={{ color: '#58A6FF' }}>Police Officer</span>
              <span style={{ color: '#484F58', marginLeft: 'auto' }}>{officers.filter(o => o.on_duty).length} active</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
              <span style={{ fontSize: 14 }}>🚗</span>
              <span style={{ color: '#E3B341' }}>Tracked Vehicle</span>
              <span style={{ color: '#484F58', marginLeft: 'auto' }}>{trackedVehicles.length}</span>
            </div>
            {Object.entries(INCIDENT_COLORS).map(([k, v]) => (
              <div key={k} style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
                <div style={{ width: 8, height: 8, borderRadius: '50%', background: v, flexShrink: 0 }} />
                <span style={{ color: '#8B949E' }}>{k.replace(/_/g, ' ')}</span>
              </div>
            ))}
          </div>

          {/* City label */}
          <div style={{ position: 'absolute', top: 12, left: '50%', transform: 'translateX(-50%)', background: '#161B22CC', border: '1px solid #30363D', borderRadius: 20, padding: '4px 14px', zIndex: 1000, fontSize: 11, color: '#8B949E', pointerEvents: 'none' }}>
            🏙️ Bengaluru City — Live Surveillance
          </div>
        </div>

        {/* ── Right panel ── */}
        <div style={{ width: 380, display: 'flex', flexDirection: 'column', background: '#161B22', borderLeft: '1px solid #21262D', overflow: 'hidden' }}>

          {/* Tabs */}
          <div style={{ display: 'flex', borderBottom: '1px solid #21262D', flexShrink: 0 }}>
            {([
              ['incidents', '🚦 Incidents', incidents.filter(i => i.status === 'ACTIVE').length],
              ['critical', '🚨 Critical', criticalAlerts.length],
              ['intercept', '⚡ Intercept', interceptAlerts.length],
              ['vehicles', '🚗 Tracked', trackedVehicles.length],
            ] as const).map(([tab, label, count]) => (
              <button key={tab} onClick={() => setActiveTab(tab as any)}
                style={{ flex: 1, padding: '10px 2px', background: activeTab === tab ? '#0D1117' : 'transparent', border: 'none', borderBottom: activeTab === tab ? '2px solid #58A6FF' : '2px solid transparent', color: activeTab === tab ? '#E6EDF3' : '#8B949E', cursor: 'pointer', fontSize: 11, fontFamily: 'inherit', fontWeight: activeTab === tab ? 600 : 400 }}>
                {label}
                <span style={{ marginLeft: 3, fontSize: 10, background: '#21262D', borderRadius: 10, padding: '1px 5px' }}>{count}</span>
              </button>
            ))}
          </div>

          {/* Officers bar */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 10px', background: '#0D1117', borderBottom: '1px solid #21262D', flexShrink: 0 }}>
            <span style={{ fontSize: 11, color: '#8B949E' }}>🚔 Officers:</span>
            {officers.slice(0, 6).map(o => (
              <span key={o.officer_id} style={{ fontSize: 10, padding: '1px 6px', borderRadius: 8, background: o.on_duty ? '#58A6FF22' : '#21262D', color: o.on_duty ? '#58A6FF' : '#484F58', border: `1px solid ${o.on_duty ? '#58A6FF44' : '#30363D'}` }}>
                {o.officer_id.split('-').pop()}
              </span>
            ))}
            <span style={{ marginLeft: 'auto', fontSize: 10, color: '#3FB950' }}>{officers.filter(o => o.on_duty).length} on duty</span>
          </div>

          {/* Tab content */}
          <div style={{ flex: 1, overflowY: 'auto', padding: 8 }}>
            {activeTab === 'incidents' && incidents.length === 0 && <EmptyState label="No incidents detected" />}
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
            {activeTab === 'vehicles' && trackedVehicles.map(v => (
              <TrackedVehicleCard key={v.id} vehicle={v} />
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

const TrackedVehicleCard: React.FC<{ vehicle: typeof DEMO_TRACKED_VEHICLES[0] }> = ({ vehicle }) => (
  <div style={{ background: '#0D1117', border: `1px solid ${vehicle.color}44`, borderRadius: 8, padding: '10px 12px', marginBottom: 6 }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
      <div>
        <span style={{ fontSize: 11, fontWeight: 700, color: vehicle.color, background: vehicle.color + '22', padding: '2px 7px', borderRadius: 10 }}>
          🚗 {vehicle.caseType.replace(/_/g, ' ')}
        </span>
        <div style={{ fontSize: 14, fontWeight: 700, color: '#E6EDF3', marginTop: 4 }}>{vehicle.plate}</div>
        <div style={{ fontSize: 11, color: '#8B949E' }}>{vehicle.make} {vehicle.model}</div>
        <div style={{ fontSize: 11, color: '#8B949E', marginTop: 2 }}>📍 {vehicle.latitude.toFixed(4)}, {vehicle.longitude.toFixed(4)}</div>
      </div>
      <span style={{ fontSize: 10, padding: '2px 7px', background: '#F8514922', color: '#F85149', borderRadius: 10, border: '1px solid #F8514944', whiteSpace: 'nowrap' }}>⚠ INTERCEPT</span>
    </div>
  </div>
)

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
