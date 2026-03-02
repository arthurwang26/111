import { useEffect, useState } from 'react';
import api from '../services/api';

export default function Dashboard() {
    const [events, setEvents] = useState<any[]>([]);
    const [elders, setElders] = useState<any[]>([]);

    useEffect(() => {
        const fetchDashboardData = async () => {
            try {
                const [eldersRes, eventsRes] = await Promise.all([
                    api.get('/api/elders'),
                    api.get('/api/events'),
                ]);
                setElders(eldersRes.data);
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
                    <div className="rounded-xl overflow-hidden bg-black aspect-video ring-1 ring-white/10 relative">
                        <img
                            src={`http://${window.location.hostname}:8000/video/stream`}
                            alt="Live Camera Feed"
                            className="w-full h-full object-contain"
                        />
                        <div className="absolute top-4 left-4 flex gap-2">
                            <span className="px-2.5 py-1 rounded-md bg-red-500/80 text-white text-xs font-medium backdrop-blur-sm flex items-center">
                                <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse mr-1.5"></span>
                                LIVE
                            </span>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div className="rounded-xl bg-zinc-900 ring-1 ring-white/5 p-6">
                            <h3 className="text-sm font-medium text-zinc-400 mb-1">Active Elders</h3>
                            <p className="text-3xl font-semibold text-white">{elders.length}</p>
                        </div>
                        <div className="rounded-xl bg-zinc-900 ring-1 ring-white/5 p-6">
                            <h3 className="text-sm font-medium text-zinc-400 mb-1">Recent Anomalies</h3>
                            <p className="text-3xl font-semibold text-rose-500">{events.filter(e => e.severity === 'HIGH').length}</p>
                        </div>
                    </div>
                </div>

                {/* Side Panel: Event Log */}
                <div className="rounded-xl bg-zinc-900 ring-1 ring-white/5 flex flex-col h-[calc(100vh-12rem)]">
                    <div className="p-6 border-b border-white/5">
                        <h2 className="text-lg font-semibold text-white">Event Log</h2>
                    </div>

                    <div className="flex-1 overflow-y-auto p-4 space-y-4">
                        {events.length === 0 ? (
                            <p className="text-center text-zinc-500 py-8">No recent events.</p>
                        ) : (
                            events.map((event) => (
                                <div key={event.id} className="p-4 rounded-lg bg-zinc-800/50 border border-white/5">
                                    <div className="flex justify-between items-start mb-2">
                                        <span className={`px-2 py-0.5 rounded text-xs font-semibold ${event.type === 'FALL' ? 'bg-rose-500/20 text-rose-400' : 'bg-amber-500/20 text-amber-400'
                                            }`}>
                                            {event.type}
                                        </span>
                                        <span className="text-xs text-zinc-500">
                                            {new Date(event.timestamp).toLocaleTimeString()}
                                        </span>
                                    </div>
                                    <p className="text-sm text-zinc-300">{event.description}</p>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
