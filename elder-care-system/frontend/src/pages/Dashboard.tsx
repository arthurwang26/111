import { useEffect, useState, useCallback } from 'react';
import api from '../services/api';

interface Camera {
    id: number;
    name: string;
    source: string;
    location: string | null;
    status: string;
}

function Toast({ message, type, onClose }: { message: string; type: 'success' | 'error' | 'info'; onClose: () => void }) {
    useEffect(() => { const t = setTimeout(onClose, 4000); return () => clearTimeout(t); }, [onClose]);
    const colors = { success: 'bg-emerald-600', error: 'bg-rose-600', info: 'bg-indigo-600' };
    return (
        <div className={`fixed top-6 right-6 z-50 ${colors[type]} text-white px-5 py-3 rounded-xl shadow-2xl text-sm font-medium flex items-center gap-3`}>
            {type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'} {message}
            <button onClick={onClose} className="ml-2 opacity-70 hover:opacity-100 text-lg">×</button>
        </div>
    );
}

// Fullscreen modal for enlarged camera
function CameraModal({ src, name, onClose }: { src: string; name: string; onClose: () => void }) {
    useEffect(() => {
        const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
        window.addEventListener('keydown', handler);
        return () => window.removeEventListener('keydown', handler);
    }, [onClose]);
    return (
        <div className="fixed inset-0 z-50 bg-black/90 flex flex-col items-center justify-center" onClick={onClose}>
            <div className="absolute top-4 right-4 flex items-center gap-3">
                <span className="text-white font-semibold text-sm">{name}</span>
                <button onClick={onClose} className="text-zinc-400 hover:text-white text-2xl leading-none">×</button>
            </div>
            <div className="w-full max-w-5xl px-6" onClick={e => e.stopPropagation()}>
                <img src={src} alt={name} className="w-full rounded-xl shadow-2xl" onError={(e) => {
                    e.currentTarget.style.display = 'none';
                }} />
                <div className="mt-3 text-center text-zinc-500 text-xs">按 ESC 或點擊背景關閉</div>
            </div>
        </div>
    );
}

// Single camera tile
function CamTile({ name, src, isMain, onClick }: { name: string; src?: string; isMain?: boolean; onClick: () => void }) {
    if (!src) {
        return (
            <div className="relative bg-zinc-950 aspect-video rounded-lg flex items-center justify-center border border-zinc-800">
                <span className="text-zinc-600 text-sm font-medium">{name} - OFFLINE</span>
            </div>
        );
    }
    return (
        <div
            onClick={onClick}
            className="relative bg-black aspect-video rounded-lg overflow-hidden cursor-pointer group border border-zinc-800 hover:border-indigo-500/50 transition-colors"
            title="點擊放大"
        >
            <img src={src} alt={name} className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                onError={(e) => { e.currentTarget.style.display = 'none'; }} />
            <div className="absolute top-3 left-3 flex gap-2">
                {isMain && (
                    <span className="px-2 py-1 rounded bg-red-500/80 text-white text-[10px] font-bold flex items-center shadow-lg">
                        <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse mr-1.5"></span>
                        LIVE
                    </span>
                )}
                <span className="px-2 py-1 rounded bg-black/60 text-white text-[10px] font-medium">{name}</span>
            </div>
            <div className="absolute bottom-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity bg-black/60 rounded px-2 py-0.5 text-[10px] text-zinc-300">
                🔍 點擊放大
            </div>
        </div>
    );
}

export default function Dashboard() {
    const [events, setEvents] = useState<any[]>([]);
    const [elders, setElders] = useState<any[]>([]);
    const [cameras, setCameras] = useState<Camera[]>([]);
    const [selectedCamId, setSelectedCamId] = useState<number | null>(null);
    const [modalCam, setModalCam] = useState<{ src: string; name: string } | null>(null);
    const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);

    const showToast = useCallback((message: string, type: 'success' | 'error' | 'info' = 'info') => setToast({ message, type }), []);

    const baseUrl = `http://${window.location.hostname}:8000`;

    useEffect(() => {
        const fetchAll = async () => {
            try {
                const [residentsRes, eventsRes, camRes] = await Promise.all([
                    api.get('/api/residents'),
                    api.get('/api/events/abnormal'),
                    api.get('/api/cameras'),
                ]);
                setElders(residentsRes.data);
                setEvents(eventsRes.data);
                const cams: Camera[] = camRes.data;
                setCameras(cams);
                // Default to first camera
                if (cams.length > 0 && selectedCamId === null) {
                    setSelectedCamId(cams[0].id);
                }
            } catch (err) {
                console.error("Failed to fetch dashboard data");
            }
        };
        fetchAll();
        const interval = setInterval(fetchAll, 5000);
        return () => clearInterval(interval);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const getStreamUrl = (cam?: Camera) => {
        if (!cam) return null;
        const src = cam.source.trim();
        // Always route through backend to ensure Ngrok/Public access works 
        // and to keep the AI processing focused on the currently viewed camera.
        return `${baseUrl}/video/stream?source=${encodeURIComponent(src)}`;
    };

    const selectedCam = cameras.find(c => c.id === selectedCamId);
    const otherCams = cameras.filter(c => c.id !== selectedCamId).slice(0, 3);

    // Fill up remaining slots with offline placeholders
    const offlineSlots = Math.max(0, 3 - otherCams.length);

    return (
        <div className="p-8 h-full overflow-y-auto">
            {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
            {modalCam && <CameraModal src={modalCam.src} name={modalCam.name} onClose={() => setModalCam(null)} />}

            <div className="mb-8 flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white mb-2">Live Monitor</h1>
                    <p className="text-zinc-400">Real-time anomaly detection streaming</p>
                </div>
                {/* Camera Selector Dropdown */}
                {cameras.length > 0 && (
                    <div className="flex items-center gap-3">
                        <label className="text-sm text-zinc-400">主畫面：</label>
                        <select
                            value={selectedCamId ?? ''}
                            onChange={e => setSelectedCamId(Number(e.target.value))}
                            className="bg-zinc-800 text-white text-sm rounded-lg px-3 py-2 border border-zinc-700 focus:outline-none focus:border-indigo-500 cursor-pointer"
                        >
                            {cameras.map(c => (
                                <option key={c.id} value={c.id}>{c.name} {c.location ? `— ${c.location}` : ''}</option>
                            ))}
                        </select>
                    </div>
                )}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 space-y-6">
                    <div className="grid grid-cols-2 gap-2 rounded-xl overflow-hidden bg-zinc-900 p-2 ring-1 ring-white/10">
                        {/* Main (selected) camera */}
                        {selectedCam ? (
                            <CamTile
                                name={`${selectedCam.name} (Main)`}
                                src={getStreamUrl(selectedCam) ?? undefined}
                                isMain
                                onClick={() => {
                                    const url = getStreamUrl(selectedCam);
                                    if (url) setModalCam({ src: url, name: selectedCam.name });
                                }}
                            />
                        ) : (
                            <div className="relative bg-black aspect-video rounded-lg overflow-hidden">
                                <img src={`${baseUrl}/video/stream`} alt="CAM 1"
                                    className="w-full h-full object-cover"
                                    onError={(e) => { e.currentTarget.style.display = 'none'; }} />
                                <div className="absolute top-3 left-3">
                                    <span className="px-2 py-1 rounded bg-red-500/80 text-white text-[10px] font-bold flex items-center">
                                        <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse mr-1.5"></span>
                                        CAM 1 (Main)
                                    </span>
                                </div>
                            </div>
                        )}

                        {/* Other cameras */}
                        {otherCams.map(cam => (
                            <CamTile
                                key={cam.id}
                                name={cam.name}
                                src={getStreamUrl(cam) ?? undefined}
                                onClick={() => {
                                    const url = getStreamUrl(cam);
                                    if (url) setModalCam({ src: url, name: cam.name });
                                }}
                            />
                        ))}

                        {/* Offline placeholder slots */}
                        {Array.from({ length: offlineSlots }).map((_, i) => (
                            <div key={`offline-${i}`} className="relative bg-zinc-950 aspect-video rounded-lg flex items-center justify-center border border-zinc-800">
                                <span className="text-zinc-600 text-sm font-medium">CAM {(otherCams.length + i + 2)} - OFFLINE</span>
                            </div>
                        ))}
                    </div>


                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div className="rounded-xl bg-zinc-900 ring-1 ring-white/5 p-6">
                            <h3 className="text-sm font-medium text-zinc-400 mb-1">Active Residents</h3>
                            <p className="text-3xl font-semibold text-white">{elders.length}</p>
                        </div>
                        <div className="rounded-xl bg-zinc-900 ring-1 ring-white/5 p-6">
                            <h3 className="text-sm font-medium text-zinc-400 mb-1">High Severity Anomalies (L3)</h3>
                            <p className="text-3xl font-semibold text-rose-500">{events.filter(e => e.level === 3).length}</p>
                        </div>
                    </div>
                </div>

                {/* Event Timeline */}
                <div className="rounded-xl bg-zinc-900 ring-1 ring-white/5 flex flex-col h-[calc(100vh-12rem)]">
                    <div className="p-6 border-b border-white/5 flex items-center justify-between">
                        <h2 className="text-lg font-semibold text-white">Event Timeline</h2>
                        <span className="text-xs text-zinc-400 bg-zinc-800 px-2 py-1 rounded">Live Updates</span>
                    </div>
                    <div className="flex-1 overflow-y-auto p-6">
                        <div className="space-y-6">
                            {events.length === 0 ? (
                                <p className="text-center text-zinc-500 py-8">No recent events.</p>
                            ) : (
                                <div className="relative border-l border-zinc-700 ml-3 space-y-8">
                                    {events.map((event) => (
                                        <div key={event.id} className="relative pl-6">
                                            <span className={`absolute -left-[5px] top-1 w-2.5 h-2.5 rounded-full ring-4 ring-zinc-900 ${event.level === 3 ? 'bg-rose-500' : event.level === 2 ? 'bg-amber-500' : 'bg-indigo-500'}`} />
                                            <div className="flex flex-col gap-1">
                                                <div className="flex items-center justify-between">
                                                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase ${event.level === 3 ? 'bg-rose-500/20 text-rose-400' : event.level === 2 ? 'bg-amber-500/20 text-amber-400' : 'bg-indigo-500/20 text-indigo-400'}`}>
                                                        {event.type}
                                                    </span>
                                                    <span className="text-xs text-zinc-500">
                                                        {new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                    </span>
                                                </div>
                                                <h4 className="text-sm font-medium text-white mt-1">
                                                    Resident: <span className="font-semibold">{event.resident_name}</span>
                                                </h4>
                                                <p className="text-sm text-zinc-400 leading-snug">{event.description}</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
