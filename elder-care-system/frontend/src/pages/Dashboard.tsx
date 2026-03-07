import { useEffect, useState } from 'react';
import api from '../services/api';

export default function Dashboard() {
    const [events, setEvents] = useState<any[]>([]);
    const [elders, setElders] = useState<any[]>([]);

    useEffect(() => {
        const fetchDashboardData = async () => {
            try {
                const [residentsRes, eventsRes] = await Promise.all([
                    api.get('/api/residents'),
                    api.get('/api/events/abnormal'),
                ]);
                setElders(residentsRes.data);
                setEvents(eventsRes.data);
            } catch (err) {
                console.error("Failed to fetch dashboard data");
            }
        };

        fetchDashboardData();
        // Poll for new events every 5 seconds
        const interval = setInterval(fetchDashboardData, 5000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="p-8 h-full overflow-y-auto">
            <div className="mb-8">
                <h1 className="text-2xl font-bold text-white mb-2">Live Monitor</h1>
                <p className="text-zinc-400">Real-time anomaly detection streaming</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Main Video Area */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="grid grid-cols-2 gap-2 rounded-xl overflow-hidden bg-zinc-900 p-2 ring-1 ring-white/10">
                        {/* Cam 1 - Active */}
                        <div className="relative bg-black aspect-video rounded-lg overflow-hidden group">
                            <img
                                src={`http://${window.location.hostname}:8000/video/stream`}
                                alt="Live Camera Feed 1"
                                className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                                onError={(e) => { e.currentTarget.style.display = 'none'; }}
                            />
                            <div className="absolute top-3 left-3 flex gap-2">
                                <span className="px-2 py-1 rounded bg-red-500/80 text-white text-[10px] font-bold flex items-center shadow-lg">
                                    <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse mr-1.5"></span>
                                    CAM 1 (Main)
                                </span>
                            </div>
                        </div>

                        {/* Cam 2 - Offline */}
                        <div className="relative bg-zinc-950 aspect-video rounded-lg flex items-center justify-center border border-zinc-800">
                            <span className="text-zinc-600 text-sm font-medium">CAM 2 - OFFLINE</span>
                        </div>

                        {/* Cam 3 - Offline */}
                        <div className="relative bg-zinc-950 aspect-video rounded-lg flex items-center justify-center border border-zinc-800">
                            <span className="text-zinc-600 text-sm font-medium">CAM 3 - OFFLINE</span>
                        </div>

                        {/* Cam 4 - Offline */}
                        <div className="relative bg-zinc-950 aspect-video rounded-lg flex items-center justify-center border border-zinc-800">
                            <span className="text-zinc-600 text-sm font-medium">CAM 4 - OFFLINE</span>
                        </div>
                    </div>

                    <div className="rounded-xl bg-zinc-900 border border-white/5 p-6">
                        <h3 className="text-lg font-semibold text-white mb-4">系統測試控制台 (System Tests)</h3>
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                            <button
                                onClick={async () => {
                                    try {
                                        await api.post('/api/test/line');
                                        alert('LINE 測試訊息已發送！');
                                    } catch (err) { alert('發送失敗'); }
                                }}
                                className="px-4 py-3 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium text-white transition-colors"
                            >
                                🔔 測試 LINE 推播
                            </button>
                            <button
                                onClick={async () => {
                                    try {
                                        const r = await api.post('/api/test/fall');
                                        if (r.data.success) alert('模擬跌倒事件已觸發！');
                                        else alert('錯誤: ' + r.data.message);
                                    } catch (err) { alert('事件觸發失敗'); }
                                }}
                                className="px-4 py-3 bg-rose-600 hover:bg-rose-500 rounded-lg text-sm font-medium text-white transition-colors"
                            >
                                🚨 模擬跌倒事件
                            </button>
                            <button
                                onClick={async () => {
                                    try {
                                        const r = await api.post('/api/test/snapshot');
                                        if (r.data.success) alert('模擬異常截圖已觸發！');
                                        else alert('錯誤: ' + r.data.message);
                                    } catch (err) { alert('觸發失敗'); }
                                }}
                                className="px-4 py-3 bg-amber-600 hover:bg-amber-500 rounded-lg text-sm font-medium text-white transition-colors"
                            >
                                📸 模擬異常截圖
                            </button>
                            <button
                                onClick={async () => {
                                    try {
                                        const r = await api.get('/api/test/health');
                                        if (r.data.success) alert(r.data.message);
                                    } catch (err) { alert('連線失敗'); }
                                }}
                                className="px-4 py-3 bg-emerald-600 hover:bg-emerald-500 rounded-lg text-sm font-medium text-white transition-colors"
                            >
                                📡 API 連線檢查
                            </button>
                        </div>
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

                {/* Side Panel: Event Log / Timeline */}
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
                                            {/* dot */}
                                            <span className={`absolute -left-[5px] top-1 w-2.5 h-2.5 rounded-full ring-4 ring-zinc-900 ${event.level === 3 ? 'bg-rose-500' : event.level === 2 ? 'bg-amber-500' : 'bg-indigo-500'
                                                }`} />
                                            <div className="flex flex-col gap-1">
                                                <div className="flex items-center justify-between">
                                                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase ${event.level === 3 ? 'bg-rose-500/20 text-rose-400' :
                                                        event.level === 2 ? 'bg-amber-500/20 text-amber-400' :
                                                            'bg-indigo-500/20 text-indigo-400'
                                                        }`}>
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
                                                {/* Snapshot placeholder for Level 3 */}
                                                {event.level === 3 && event.snapshot_path && (
                                                    <button className="mt-2 text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1">
                                                        📸 View Snapshot / Video Clip
                                                    </button>
                                                )}
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
