import { useState, useEffect } from 'react';
import { Activity, Search, AlertTriangle, Flame, Info, CheckCircle, ExternalLink } from 'lucide-react';
import api from '../services/api';
import { useTranslation } from '../contexts/I18nContext';

type Event = {
    id: number; type: string; level: number;
    description: string; timestamp: string; resident_name: string;
    snapshot_path?: string; is_resolved: number;
};

const SEVERITY_STYLE: Record<number, string> = {
    3: 'bg-rose-500/15 text-rose-400 border-rose-500/20',
    2: 'bg-amber-500/15 text-amber-400 border-amber-500/20',
    1: 'bg-indigo-500/15 text-indigo-400 border-indigo-500/20',
};

const SEVERITY_ICON = {
    3: <Flame size={14} />,
    2: <AlertTriangle size={14} />,
    1: <Info size={14} />,
};

export default function LogsPage() {
    const [events, setEvents] = useState<Event[]>([]);
    const [filter, setFilter] = useState<'ALL' | 3 | 2 | 1>('ALL');
    const [showResolved, setShowResolved] = useState(false);
    const [search, setSearch] = useState('');
    const { t } = useTranslation();

    const fetchEvents = async () => {
        try {
            const r = await api.get('/api/events/abnormal?limit=200');
            setEvents(r.data);
        } catch { setEvents([]); }
    };

    useEffect(() => {
        fetchEvents();
        const t = setInterval(fetchEvents, 10000);
        return () => clearInterval(t);
    }, []);

    const handleResolve = async (id: number) => {
        try {
            await api.patch(`/api/events/${id}/resolve`);
            fetchEvents();
        } catch { alert(t('logs.update_fail')); }
    };

    const getSnapshotUrl = (path?: string) => {
        if (!path) return null;
        // 假設後端存的是絕對路徑，我們只需取最後的檔案名稱
        const filename = path.split(/[\\/]/).pop();
        return `http://${window.location.hostname}:8000/static/snapshots/${filename}`;
    };

    const filtered = events.filter(e => {
        if (!showResolved && e.is_resolved === 1) return false;
        if (filter !== 'ALL' && e.level !== filter) return false;
        if (search && !e.description.includes(search)) return false;
        return true;
    });

    return (
        <div className="p-8 max-w-5xl mx-auto">
            <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-3">
                    <Activity className="text-rose-400" size={28} />
                    <div>
                        <h1 className="text-2xl font-bold text-white">{t('logs.title')}</h1>
                        <p className="text-zinc-400 mt-0.5">{t('logs.pending')}{events.filter(e => !e.is_resolved).length} {t('logs.count')}</p>
                    </div>
                </div>
                <label className="flex items-center gap-2 cursor-pointer bg-zinc-900 px-3 py-2 rounded-lg ring-1 ring-white/5">
                    <input type="checkbox" checked={showResolved} onChange={e => setShowResolved(e.target.checked)} className="rounded bg-zinc-800 border-zinc-700 text-indigo-500" />
                    <span className="text-sm text-zinc-300">{t('logs.show_resolved')}</span>
                </label>
            </div>

            {/* 篩選列 */}
            <div className="flex flex-wrap items-center gap-3 mb-6">
                <div className="relative flex-1 min-w-48">
                    <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
                    <input
                        value={search} onChange={e => setSearch(e.target.value)}
                        placeholder={t('logs.search')}
                        className="w-full pl-9 pr-4 py-2 rounded-lg bg-zinc-800 ring-1 ring-zinc-700 text-white text-sm placeholder:text-zinc-500 focus:ring-indigo-500 focus:outline-none"
                    />
                </div>
                {(['ALL', 3, 2, 1] as const).map(s => (
                    <button key={s} onClick={() => setFilter(s)}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${filter === s ? 'bg-indigo-600 text-white' : 'bg-zinc-800 text-zinc-400 hover:text-white'
                            }`}>
                        {s === 'ALL' ? t('logs.all_levels') : `Level ${s}`}
                    </button>
                ))}
            </div>

            {/* 事件列表 */}
            <div className="space-y-4">
                {filtered.length === 0 ? (
                    <div className="text-center py-16 text-zinc-500">
                        <Activity size={48} className="mx-auto mb-4 opacity-30" />
                        <p>{t('logs.empty')}</p>
                    </div>
                ) : (
                    filtered.map(event => (
                        <div key={event.id}
                            className={`p-5 rounded-xl bg-zinc-900 border transition-opacity ${event.is_resolved ? 'opacity-50 ring-1 ring-emerald-500/20' : 'ring-1 ring-white/5'
                                } ${SEVERITY_STYLE[event.level] || 'border-transparent'}`}>

                            <div className="flex items-start justify-between gap-4">
                                <div className="flex flex-col gap-2">
                                    <div className="flex items-center gap-2">
                                        <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold ${SEVERITY_STYLE[event.level]}`}>
                                            {SEVERITY_ICON[event.level as keyof typeof SEVERITY_ICON]}
                                            {event.type}
                                        </span>
                                        {event.is_resolved === 1 && (
                                            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold bg-emerald-500/10 text-emerald-400">
                                                <CheckCircle size={12} /> {t('logs.resolved')}
                                            </span>
                                        )}
                                    </div>
                                    <span className="text-xs text-zinc-500">
                                        {new Date(event.timestamp).toLocaleString('zh-TW')}
                                    </span>
                                </div>

                                {!event.is_resolved && (
                                    <button
                                        onClick={() => handleResolve(event.id)}
                                        className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600 hover:text-white text-xs font-bold transition-all"
                                    >
                                        <CheckCircle size={14} /> {t('logs.mark_resolved')}
                                    </button>
                                )}
                            </div>

                            <div className="mt-4 flex flex-col md:flex-row gap-5">
                                <div className="flex-1">
                                    <p className="text-sm text-zinc-300 whitespace-pre-line leading-relaxed">{event.description}</p>
                                </div>
                                {event.snapshot_path && (
                                    <div className="flex-shrink-0 w-full md:w-64">
                                        <div className="relative group rounded-lg overflow-hidden ring-1 ring-white/10">
                                            <img
                                                src={getSnapshotUrl(event.snapshot_path) || ''}
                                                alt="Fall Snapshot"
                                                className="w-full h-36 object-cover bg-zinc-800"
                                                onError={(e) => (e.currentTarget.style.display = 'none')}
                                            />
                                            <a
                                                href={getSnapshotUrl(event.snapshot_path) || ''}
                                                target="_blank"
                                                className="absolute inset-0 bg-black/50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                                            >
                                                <ExternalLink size={20} className="text-white" />
                                            </a>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
