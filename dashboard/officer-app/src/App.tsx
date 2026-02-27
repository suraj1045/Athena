/**
 * Athena Officer App — Full MVP Implementation
 *
 * Features:
 *  - Real-time WebSocket connection to receive INTERCEPT_ALERT events
 *  - Map view showing officer position + alert vehicle markers
 *  - Scrollable alert list with vehicle details, distance, direction
 *  - Alert acknowledgement (sends back to backend)
 *  - GPS location update loop → POST /api/v1/officers/{id}/location
 *  - On-duty / off-duty toggle
 */

import React, { useCallback, useEffect, useRef, useState } from 'react'
import {
  Alert,
  Animated,
  FlatList,
  Platform,
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  Vibration,
  View,
} from 'react-native'
import MapView, { Marker, PROVIDER_DEFAULT } from 'react-native-maps'

// ── Config ─────────────────────────────────────────────────────────────────────
const API_BASE = 'http://localhost:8000'
// In production: use the server's LAN IP e.g. 'http://192.168.1.x:8000'

// ── Types ──────────────────────────────────────────────────────────────────────
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
  acknowledged?: boolean
}

interface OfficerLocation {
  latitude: number
  longitude: number
  heading: number
  speed_mps: number
}

// ── Demo officer identity (editable for demo) ──────────────────────────────────
const OFFICER_ID = 'OFF-001'
const OFFICER_NAME = 'Officer Rajan'

// ── Main App ───────────────────────────────────────────────────────────────────
const App: React.FC = () => {
  const [alerts, setAlerts] = useState<InterceptAlert[]>([])
  const [location, setLocation] = useState<OfficerLocation>({
    latitude: 12.9716,   // Bangalore default for demo
    longitude: 77.5946,
    heading: 0,
    speed_mps: 0,
  })
  const [onDuty, setOnDuty] = useState(true)
  const [wsStatus, setWsStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting')
  const [selectedAlert, setSelectedAlert] = useState<InterceptAlert | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const flashAnim = useRef(new Animated.Value(1)).current
  const mapRef = useRef<MapView>(null)

  // ── Flash animation for new alerts ──────────────────────────────────────────
  const triggerFlash = useCallback(() => {
    Animated.sequence([
      Animated.timing(flashAnim, { toValue: 0.3, duration: 150, useNativeDriver: true }),
      Animated.timing(flashAnim, { toValue: 1, duration: 150, useNativeDriver: true }),
      Animated.timing(flashAnim, { toValue: 0.3, duration: 150, useNativeDriver: true }),
      Animated.timing(flashAnim, { toValue: 1, duration: 200, useNativeDriver: true }),
    ]).start()
    Vibration.vibrate([0, 300, 100, 300])
  }, [flashAnim])

  // ── WebSocket ────────────────────────────────────────────────────────────────
  const connectWs = useCallback(() => {
    const wsUrl = `ws://localhost:8000/ws/officer/${OFFICER_ID}`
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => setWsStatus('connected')

    ws.onmessage = (e) => {
      const data = JSON.parse(e.data)
      if (data.type === 'INTERCEPT_ALERT') {
        const alert: InterceptAlert = {
          alert_id: data.alert_id,
          vehicle_plate: data.vehicle_plate,
          vehicle_make: data.vehicle_make,
          vehicle_model: data.vehicle_model,
          violation_type: data.violation_type,
          location: data.location,
          distance_m: data.distance_m,
          direction: data.direction,
          estimated_intercept_s: data.estimated_intercept_s,
        }
        setAlerts(prev => [alert, ...prev].slice(0, 20))
        setSelectedAlert(alert)
        triggerFlash()

        // Animate map to vehicle location
        mapRef.current?.animateToRegion({
          latitude: data.location.latitude,
          longitude: data.location.longitude,
          latitudeDelta: 0.01,
          longitudeDelta: 0.01,
        }, 800)
      }
    }

    ws.onclose = () => {
      setWsStatus('disconnected')
      setTimeout(connectWs, 3000)
    }
  }, [triggerFlash])

  useEffect(() => {
    connectWs()
    return () => wsRef.current?.close()
  }, [])

  // ── Location update loop ─────────────────────────────────────────────────────
  useEffect(() => {
    const push = () => {
      fetch(`${API_BASE}/api/v1/officers/${OFFICER_ID}/location`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          latitude: location.latitude,
          longitude: location.longitude,
          heading: location.heading,
          speed_mps: location.speed_mps,
          on_duty: onDuty,
        }),
      }).catch(() => { }) // best-effort
    }
    push()
    const interval = setInterval(push, 5000)
    return () => clearInterval(interval)
  }, [location, onDuty])

  // ── Acknowledge alert ────────────────────────────────────────────────────────
  const acknowledgeAlert = async (alertId: string) => {
    wsRef.current?.send(JSON.stringify({ type: 'ACKNOWLEDGE_ALERT', alert_id: alertId }))
    await fetch(`${API_BASE}/api/v1/alerts/${alertId}/acknowledge`, { method: 'POST' }).catch(() => { })
    setAlerts(prev => prev.map(a => a.alert_id === alertId ? { ...a, acknowledged: true } : a))
    if (selectedAlert?.alert_id === alertId) setSelectedAlert(null)
  }

  const wsBadgeColor = { connected: '#3FB950', connecting: '#E3B341', disconnected: '#F85149' }[wsStatus]

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#0D1117" />

      {/* ── Header ── */}
      <View style={styles.header}>
        <View>
          <Text style={styles.appTitle}>🏛️ ATHENA</Text>
          <Text style={styles.officerName}>{OFFICER_NAME} · {OFFICER_ID}</Text>
        </View>
        <View style={styles.headerRight}>
          <View style={[styles.wsBadge, { borderColor: wsBadgeColor + '44', backgroundColor: wsBadgeColor + '22' }]}>
            <View style={[styles.wsDot, { backgroundColor: wsBadgeColor }]} />
            <Text style={[styles.wsText, { color: wsBadgeColor }]}>{wsStatus.toUpperCase()}</Text>
          </View>
          <TouchableOpacity
            style={[styles.dutyBtn, { backgroundColor: onDuty ? '#238636' : '#3D444D' }]}
            onPress={() => setOnDuty(d => !d)}>
            <Text style={styles.dutyBtnText}>{onDuty ? '✅ ON DUTY' : '⭕ OFF DUTY'}</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* ── Stats bar ── */}
      <View style={styles.statsBar}>
        <StatChip label="Active Alerts" value={alerts.filter(a => !a.acknowledged).length} color="#F85149" />
        <StatChip label="Acknowledged" value={alerts.filter(a => a.acknowledged).length} color="#3FB950" />
        <StatChip label="Total Alerts" value={alerts.length} color="#58A6FF" />
      </View>

      {/* ── Map ── */}
      <Animated.View style={[styles.mapContainer, { opacity: flashAnim }]}>
        <MapView
          ref={mapRef}
          provider={PROVIDER_DEFAULT}
          style={styles.map}
          initialRegion={{
            latitude: location.latitude,
            longitude: location.longitude,
            latitudeDelta: 0.05,
            longitudeDelta: 0.05,
          }}
          showsUserLocation={false}
          showsCompass={false}
        >
          {/* Officer marker */}
          <Marker coordinate={{ latitude: location.latitude, longitude: location.longitude }}
            title={OFFICER_ID} description="Your location">
            <View style={styles.officerPin}>
              <Text style={{ fontSize: 18 }}>👮</Text>
            </View>
          </Marker>

          {/* Alert vehicle markers */}
          {alerts.filter(a => !a.acknowledged).map(a => (
            <Marker
              key={a.alert_id}
              coordinate={{ latitude: a.location.latitude, longitude: a.location.longitude }}
              title={a.vehicle_plate}
              description={`${a.distance_m.toFixed(0)}m ${a.direction}`}
              onPress={() => setSelectedAlert(a)}
            >
              <View style={[styles.vehiclePin, { borderColor: '#F85149' }]}>
                <Text style={{ fontSize: 16 }}>🚗</Text>
              </View>
            </Marker>
          ))}
        </MapView>

        {/* Map overlay: move officer pin for demo */}
        <TouchableOpacity style={styles.mapOverlayBtn}
          onPress={() => Alert.alert('Demo Tip', 'In production this uses expo-location GPS. For demo, location is pre-set to Bangalore.')}>
          <Text style={styles.mapOverlayBtnText}>📍 Mock GPS</Text>
        </TouchableOpacity>
      </Animated.View>

      {/* ── Active alert modal ── */}
      {selectedAlert && !selectedAlert.acknowledged && (
        <View style={styles.alertModal}>
          <View style={styles.alertModalHeader}>
            <Text style={styles.alertModalTitle}>⚡ INTERCEPT ALERT</Text>
            <TouchableOpacity onPress={() => setSelectedAlert(null)}>
              <Text style={styles.alertModalClose}>✕</Text>
            </TouchableOpacity>
          </View>
          <View style={styles.alertModalBody}>
            <Text style={styles.alertPlate}>{selectedAlert.vehicle_plate}</Text>
            <Text style={styles.alertMakeModel}>{selectedAlert.vehicle_make} {selectedAlert.vehicle_model}</Text>
            <Text style={styles.alertViolation}>{selectedAlert.violation_type.replace(/_/g, ' ')}</Text>
            <View style={styles.alertStats}>
              <AlertStat label="Distance" value={`${Math.round(selectedAlert.distance_m)}m`} />
              <AlertStat label="Direction" value={selectedAlert.direction} />
              <AlertStat label="ETA" value={`${Math.round(selectedAlert.estimated_intercept_s)}s`} />
            </View>
            <TouchableOpacity style={styles.ackBtn} onPress={() => acknowledgeAlert(selectedAlert.alert_id)}>
              <Text style={styles.ackBtnText}>✓ Acknowledge & Intercept</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {/* ── Alert history ── */}
      <View style={styles.historyContainer}>
        <Text style={styles.historyTitle}>SHIFT ALERTS</Text>
        <FlatList
          data={alerts}
          keyExtractor={a => a.alert_id}
          renderItem={({ item }) => <AlertHistoryRow alert={item} onAck={acknowledgeAlert} />}
          ListEmptyComponent={<Text style={styles.emptyText}>No alerts this shift</Text>}
        />
      </View>
    </SafeAreaView>
  )
}

// ── Sub-components ─────────────────────────────────────────────────────────────
const StatChip: React.FC<{ label: string; value: number; color: string }> = ({ label, value, color }) => (
  <View style={[styles.statChip, { borderColor: color + '44' }]}>
    <Text style={[styles.statValue, { color }]}>{value}</Text>
    <Text style={styles.statLabel}>{label}</Text>
  </View>
)

const AlertStat: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <View style={styles.alertStatItem}>
    <Text style={styles.alertStatValue}>{value}</Text>
    <Text style={styles.alertStatLabel}>{label}</Text>
  </View>
)

const AlertHistoryRow: React.FC<{ alert: InterceptAlert; onAck: (id: string) => void }> = ({ alert, onAck }) => (
  <View style={[styles.historyRow, { borderLeftColor: alert.acknowledged ? '#3FB950' : '#F85149' }]}>
    <View style={{ flex: 1 }}>
      <Text style={styles.historyPlate}>{alert.vehicle_plate}</Text>
      <Text style={styles.historyDetail}>{alert.vehicle_make} {alert.vehicle_model} · {alert.violation_type.replace(/_/g, ' ')}</Text>
      <Text style={styles.historyMeta}>{Math.round(alert.distance_m)}m {alert.direction} · ~{Math.round(alert.estimated_intercept_s)}s</Text>
    </View>
    {!alert.acknowledged
      ? <TouchableOpacity style={styles.historyAckBtn} onPress={() => onAck(alert.alert_id)}>
        <Text style={styles.historyAckText}>ACK</Text>
      </TouchableOpacity>
      : <Text style={styles.acknowledgedBadge}>✓ ACK</Text>
    }
  </View>
)

// ── Styles ─────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0D1117' },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 12, borderBottomWidth: 1, borderBottomColor: '#21262D', backgroundColor: '#161B22' },
  appTitle: { fontSize: 18, fontWeight: '800', color: '#58A6FF', letterSpacing: 2 },
  officerName: { fontSize: 11, color: '#8B949E', marginTop: 2 },
  headerRight: { flexDirection: 'row', gap: 8, alignItems: 'center' },
  wsBadge: { flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: 8, paddingVertical: 4, borderRadius: 12, borderWidth: 1 },
  wsDot: { width: 6, height: 6, borderRadius: 3 },
  wsText: { fontSize: 9, fontWeight: '700' },
  dutyBtn: { paddingHorizontal: 10, paddingVertical: 5, borderRadius: 8 },
  dutyBtnText: { fontSize: 10, color: '#fff', fontWeight: '600' },
  statsBar: { flexDirection: 'row', gap: 8, padding: 8, backgroundColor: '#161B22', borderBottomWidth: 1, borderBottomColor: '#21262D' },
  statChip: { flex: 1, alignItems: 'center', padding: 6, borderRadius: 8, borderWidth: 1, backgroundColor: '#0D1117' },
  statValue: { fontSize: 20, fontWeight: '700' },
  statLabel: { fontSize: 9, color: '#8B949E', marginTop: 1 },
  mapContainer: { height: 220 },
  map: { flex: 1 },
  officerPin: { width: 36, height: 36, borderRadius: 18, backgroundColor: '#1F6FEB22', borderWidth: 2, borderColor: '#58A6FF', alignItems: 'center', justifyContent: 'center' },
  vehiclePin: { width: 34, height: 34, borderRadius: 17, backgroundColor: '#F8514922', borderWidth: 2, alignItems: 'center', justifyContent: 'center' },
  mapOverlayBtn: { position: 'absolute', bottom: 8, right: 8, backgroundColor: '#161B22CC', paddingHorizontal: 10, paddingVertical: 5, borderRadius: 12, borderWidth: 1, borderColor: '#21262D' },
  mapOverlayBtnText: { color: '#8B949E', fontSize: 11 },
  alertModal: { margin: 8, backgroundColor: '#161B22', borderRadius: 12, borderWidth: 1, borderColor: '#F85149' },
  alertModalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 12, borderBottomWidth: 1, borderBottomColor: '#21262D' },
  alertModalTitle: { fontSize: 12, fontWeight: '700', color: '#F85149', letterSpacing: 1 },
  alertModalClose: { color: '#8B949E', fontSize: 16 },
  alertModalBody: { padding: 12 },
  alertPlate: { fontSize: 28, fontWeight: '800', color: '#E6EDF3', letterSpacing: 3 },
  alertMakeModel: { fontSize: 13, color: '#8B949E', marginTop: 2 },
  alertViolation: { fontSize: 12, color: '#E3B341', marginTop: 4, fontWeight: '600' },
  alertStats: { flexDirection: 'row', gap: 12, marginTop: 12, marginBottom: 12 },
  alertStatItem: { flex: 1, alignItems: 'center', backgroundColor: '#0D1117', borderRadius: 8, padding: 8, borderWidth: 1, borderColor: '#21262D' },
  alertStatValue: { fontSize: 18, fontWeight: '700', color: '#58A6FF' },
  alertStatLabel: { fontSize: 10, color: '#8B949E', marginTop: 2 },
  ackBtn: { backgroundColor: '#238636', padding: 12, borderRadius: 10, alignItems: 'center' },
  ackBtnText: { color: '#fff', fontWeight: '700', fontSize: 14 },
  historyContainer: { flex: 1, margin: 8 },
  historyTitle: { fontSize: 10, fontWeight: '700', color: '#484F58', letterSpacing: 2, marginBottom: 6 },
  historyRow: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#161B22', borderRadius: 8, padding: 10, marginBottom: 4, borderLeftWidth: 3 },
  historyPlate: { fontSize: 14, fontWeight: '700', color: '#E6EDF3' },
  historyDetail: { fontSize: 11, color: '#8B949E', marginTop: 1 },
  historyMeta: { fontSize: 10, color: '#484F58', marginTop: 1 },
  historyAckBtn: { backgroundColor: '#1F6FEB', paddingHorizontal: 10, paddingVertical: 5, borderRadius: 6 },
  historyAckText: { color: '#fff', fontSize: 10, fontWeight: '700' },
  acknowledgedBadge: { color: '#3FB950', fontSize: 11, fontWeight: '600' },
  emptyText: { textAlign: 'center', color: '#484F58', marginTop: 20, fontSize: 13 },
})

export default App
