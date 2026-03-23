import { useEffect, useState } from 'react';
import api from '../services/api';
import { useTranslation } from '../contexts/I18nContext';

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
    const [hasError, setHasError] = useState(false);

    // src 改變時重設錯誤，讓圖片重試
    useEffect(() => { setHasError(false); }, [src]);

    if (!src || hasError) {
        return (
            <div className="relative bg-zinc-950 aspect-video rounded-lg flex flex-col items-center justify-center border border-zinc-800 gap-2">
                <span className="text-zinc-600 text-sm font-medium">{name}</span>
                {hasError && src ? (
                    <span className="text-zinc-700 text-xs animate-pulse">連線中，請稍候...</span>
                ) : (
                    <span className="text-zinc-700 text-xs">OFFLINE</span>
                )}
            </div>
        );
    }
    return (
        <div
            onClick={onClick}
            className="relative bg-black aspect-video rounded-lg overflow-hidden cursor-pointer group border border-zinc-800 hover:border-indigo-500/50 transition-colors"
            title="點擊放大"
        >
            <img
                key={src}
                src={src}
                alt={name}
                className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                onError={() => {
                    // 3 秒後重試，而不是永久隱藏
                    setTimeout(() => setHasError(false), 3000);
                    setHasError(true);
                }}
            />
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
                {onClick !== undefined ? '🔍 Click / 點擊放大' : ''}
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
    const { t } = useTranslation();

    // 本機開發用 :8000，ngrok / 遠端存取直接用現在的 origin（不加 port）
    const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    const baseUrl = isLocal ? `http://${window.location.hostname}:8000` : window.location.origin;

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
                // 使用 functional update 確保只在真正是 null 時才設定第一台，避免閉包 bug 重設用戶的選擇
                if (cams.length > 0) {
                    setSelectedCamId(prev => prev === null ? cams[0].id : prev);
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

    // 當主攝影機切換時，主動呼叫後端讓 AI pipeline 跟著切換
    useEffect(() => {
        if (selectedCamId === null) return;
        const cam = cameras.find(c => c.id === selectedCamId);
        if (!cam || cam.status === 'offline') return;
        // 輕量化請求，告知後端切換 AI 來源（後端收到後 pipeline.update_source 會執行）
        const switchUrl = `${baseUrl}/video/stream?source=${encodeURIComponent(cam.source.trim())}&camera_id=${cam.id}&_switch=1`;
        const ctrl = new AbortController();
        fetch(switchUrl, { signal: ctrl.signal }).catch(() => {/* 忽略連線本身，只需要觸發切換 */});
        // 立即中斷連線，我們只需要讓後端處理一次 update_source
        setTimeout(() => ctrl.abort(), 300);
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedCamId]);

    const getStreamUrl = (cam?: Camera, isMain: boolean = false) => {
        if (!cam) return null;
        // 移除 offline 封鎖：讓系統嘗試連線，若真的連不上前端 onError 會自動隱藏 img
        const src = cam.source.trim();
        const endpoint = isMain ? '/video/stream' : '/video/proxy';
        return `${baseUrl}${endpoint}?source=${encodeURIComponent(src)}&camera_id=${cam.id}`;
    };

    const handleClearTestEvents = async () => {
        if (!window.confirm("確定要刪除所有「未指示別」與「測試」事件嗎？（已綁定長者的真實事件將保留）")) return;
        try {
            const res = await api.delete('/api/events/clear_test');
            setToast({ message: res.data.message || '已清除測試事件', type: 'success' });
            const eventsRes = await api.get('/api/events/abnormal');
            setEvents(eventsRes.data);
        } catch (err) {
            setToast({ message: '清除失敗', type: 'error' });
        }
    };

    const handleDeleteEvent = async (id: number) => {
        if (!window.confirm("確定要刪除這筆單一事件嗎？")) return;
        try {
            await api.delete(`/api/events/${id}`);
            setToast({ message: '事件已刪除', type: 'success' });
            setEvents(prev => prev.filter(e => e.id !== id));
        } catch (err) {
            setToast({ message: '刪除失敗', type: 'error' });
        }
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
                    <h1 className="text-2xl font-bold text-white mb-2">{t('dashboard.title')}</h1>
                    <p className="text-zinc-400">{t('dashboard.subtitle')}</p>
                </div>
                {/* Camera Selector Dropdown */}
                {cameras.length > 0 && (
                    <div className="flex items-center gap-3">
                        <label className="text-sm text-zinc-400">{t('dashboard.main_cam')}</label>
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
                                src={getStreamUrl(selectedCam, true) ?? undefined}
                                isMain
                                onClick={() => {
                                    const url = getStreamUrl(selectedCam, true);
                                    if (url) setModalCam({ src: url + `&_t=${Date.now()}`, name: selectedCam.name });
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
                            <h3 className="text-sm font-medium text-zinc-400 mb-1">{t('dashboard.active_res')}</h3>
                            <p className="text-3xl font-semibold text-white">{elders.length}</p>
                        </div>
                        <div className="rounded-xl bg-zinc-900 ring-1 ring-white/5 p-6">
                            <h3 className="text-sm font-medium text-zinc-400 mb-1">{t('dashboard.high_sev')}</h3>
                            <p className="text-3xl font-semibold text-rose-500">{events.filter(e => e.level === 3).length}</p>
                        </div>
                    </div>
                </div>

                {/* Event Timeline */}
                <div className="rounded-xl bg-zinc-900 ring-1 ring-white/5 flex flex-col h-[calc(100vh-12rem)]">
                    <div className="p-6 border-b border-white/5 flex items-center justify-between">
                        <h2 className="text-lg font-semibold text-white">{t('dashboard.timeline')}</h2>
                        <div className="flex items-center gap-2">
                            <button onClick={handleClearTestEvents} className="text-xs text-rose-400 hover:text-white bg-rose-500/10 hover:bg-rose-500/30 px-2 py-1.5 rounded transition-colors flex items-center gap-1">
                                🗑️ 清除測試事件
                            </button>
                            <span className="text-xs text-zinc-400 bg-zinc-800 px-2 py-1.5 rounded">{t('dashboard.live_up')}</span>
                        </div>
                    </div>
                    <div className="flex-1 overflow-y-auto p-6">
                        <div className="space-y-6">
                            {events.length === 0 ? (
                                <p className="text-center text-zinc-500 py-8">{t('dashboard.no_events')}</p>
                            ) : (
                                <div className="relative border-l border-zinc-700 ml-3 space-y-8">
                                    {events.map((event) => (
                                        <div key={event.id} className="relative pl-6 group">
                                            <span className={`absolute -left-[5px] top-1 w-2.5 h-2.5 rounded-full ring-4 ring-zinc-900 ${event.level === 3 ? 'bg-rose-500' : event.level === 2 ? 'bg-amber-500' : 'bg-indigo-500'}`} />
                                            <div className="flex flex-col gap-1">
                                                <div className="flex items-center justify-between">
                                                    <div className="flex items-center gap-2">
                                                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase ${event.level === 3 ? 'bg-rose-500/20 text-rose-400' : event.level === 2 ? 'bg-amber-500/20 text-amber-400' : 'bg-indigo-500/20 text-indigo-400'}`}>
                                                            {event.type}
                                                        </span>
                                                        <button 
                                                            onClick={() => handleDeleteEvent(event.id)} 
                                                            className="opacity-0 group-hover:opacity-100 transition-opacity text-zinc-500 hover:text-rose-400 text-xs px-1"
                                                            title="刪除此筆事件"
                                                        >
                                                            ✕
                                                        </button>
                                                    </div>
                                                    <span className="text-xs text-zinc-500">
                                                        {new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                    </span>
                                                </div>
                                                <h4 className="text-sm font-medium text-white mt-1">
                                                    {t('dashboard.resident')} <span className="font-semibold">{event.resident_name}</span>
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
