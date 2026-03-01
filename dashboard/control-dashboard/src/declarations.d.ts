/**
 * Module stubs — allows the TypeScript language server to work WITHOUT node_modules.
 * Vite resolves the real implementations at build/runtime after `npm install`.
 * These are ONLY used by the IDE type checker.
 */

/* ── JSX global ────────────────────────────────────────────────────────────── */
declare namespace JSX {
    interface Element { }
    interface IntrinsicElements {
        // Allow any HTML/custom tag with any attributes
        [tag: string]: {
            children?: unknown
            style?: Record<string, string | number | undefined>
            className?: string
            id?: string
            key?: string | number
            ref?: unknown
            onClick?: (e: MouseEvent) => void
            onChange?: (e: Event) => void
            [attr: string]: unknown
        }
    }
}

/* ── React namespace ───────────────────────────────────────────────────────── */
declare namespace React {
    type FC<P = {}> = (props: P & { children?: ReactNode }) => JSX.Element | null
    type ReactNode = JSX.Element | string | number | boolean | null | undefined
    type CSSProperties = Record<string, string | number | undefined>
    type HTMLAttributes<_T> = Record<string, unknown>
}

/* ── react ─────────────────────────────────────────────────────────────────── */
declare module 'react' {
    type ReactNode = JSX.Element | string | number | boolean | null | undefined
    type CSSProperties = Record<string, string | number | undefined>
    interface FC<P = {}> {
        (props: P & { children?: ReactNode }): JSX.Element | null
    }
    function useState<T>(init: T | (() => T)): [T, (v: T | ((prev: T) => T)) => void]
    function useEffect(fn: () => (() => void) | void, deps?: unknown[]): void
    function useRef<T>(init: T | null): { current: T | null }
    function useCallback<T extends (...args: unknown[]) => unknown>(fn: T, deps: unknown[]): T
    const StrictMode: FC<{ children?: ReactNode }>
}

/* ── react-dom/client ──────────────────────────────────────────────────────── */
declare module 'react-dom/client' {
    function createRoot(el: Element | null): { render(node: JSX.Element): void }
    export { createRoot }
}

/* ── leaflet — L namespace ─────────────────────────────────────────────────── */
declare namespace L {
    interface LatLng { lat: number; lng: number }
    interface LatLngBounds { isValid(): boolean }
    interface DivIcon { }
    interface Marker {
        addTo(map: MapInstance): this
        bindPopup(content: string): this
    }
    interface MapInstance {
        setMaxBounds(b: LatLngBounds): this
        setMinZoom(z: number): this
        fitBounds(b: LatLngBounds, opts?: object): this
        removeLayer(l: unknown): this
    }
    interface TileLayerInstance { addTo(map: MapInstance): void }
    function latLng(lat: number, lng: number): LatLng
    function latLngBounds(sw: LatLng, ne?: LatLng): LatLngBounds
    function latLngBounds(coords: [number, number][]): LatLngBounds
    function marker(pos: [number, number], opts?: object): Marker
    function divIcon(opts: object): DivIcon
    function map(el: string | HTMLElement, opts?: object): MapInstance
    function tileLayer(url: string, opts?: object): TileLayerInstance
    const control: (opts?: object) => unknown
}

/* ── leaflet module ────────────────────────────────────────────────────────── */
declare module 'leaflet' {
    export const latLng: typeof L.latLng
    export const latLngBounds: typeof L.latLngBounds
    export const marker: typeof L.marker
    export const divIcon: typeof L.divIcon
    export const map: typeof L.map
    export const tileLayer: typeof L.tileLayer
    export const control: typeof L.control
    export type LatLng = L.LatLng
    export type LatLngBounds = L.LatLngBounds
    export type Marker = L.Marker
    export type DivIcon = L.DivIcon
    export type Map = L.MapInstance
    const _default: typeof L
    export default _default
}

/* ── react-leaflet ─────────────────────────────────────────────────────────── */
declare module 'react-leaflet' {
    type LatLngTuple = [number, number]
    const MapContainer: React.FC<{
        center: LatLngTuple
        zoom: number
        style?: React.CSSProperties
        zoomControl?: boolean
        maxBounds?: L.LatLngBounds
        maxBoundsViscosity?: number
        children?: React.ReactNode
    }>
    const TileLayer: React.FC<{
        url: string
        attribution?: string
        maxZoom?: number
    }>
    const Marker: React.FC<{
        position: LatLngTuple
        icon?: L.DivIcon
        children?: React.ReactNode
    }>
    const Popup: React.FC<{ children?: React.ReactNode }>
    function useMap(): L.MapInstance
    export { MapContainer, TileLayer, Marker, Popup, useMap }
}

/* ── CSS side-effect imports ───────────────────────────────────────────────── */
declare module 'leaflet/dist/leaflet.css' { }
declare module '*.css' { }
