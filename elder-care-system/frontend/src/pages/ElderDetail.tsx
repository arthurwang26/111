import { useState, useEffect, useMemo, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    ArrowLeft, Home, Calendar, ShieldAlert, Activity,
    FileText, CheckCircle, AlertCircle, Clock, User, Upload, Camera, Edit3, X, Save
} from 'lucide-react';
import {
    BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
    Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import api from '../services/api';
import { useTranslation } from '../contexts/I18nContext';

interface ResidentDetail {
    id: number;
    name: string;
    room: string | null;
    family_line_id: string | null;
    created_at: string;
    has_embedding: boolean;
    recent_events: any[];
    abnormal_events: any[];
    daily_activities: any[];
}

function formatDate(dateStr: string) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return '—';
    return d.toLocaleDateString('zh-TW', { year: 'numeric', month: '2-digit', day: '2-digit' });
}

function formatDateTime(dateStr: string) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return '—';
    return d.toLocaleString('zh-TW', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
}

type ViewMode = 'daily' | 'weekly' | 'monthly';

export default function ElderDetailPage() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [data, setData] = useState<ResidentDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // 臉部上傳狀態 — 完全獨立，不受 fetchData 影響
    const [uploading, setUploading] = useState(false);
    const [uploadMsg, setUploadMsg] = useState<{ text: string; ok: boolean } | null>(null);
    const [embeddingReady, setEmbeddingReady] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // 編輯 Modal 狀態
    const [editOpen, setEditOpen] = useState(false);
    const [editName, setEditName] = useState('');
    const [editRoom, setEditRoom] = useState('');
    const [editLineId, setEditLineId] = useState('');
    const [saving, setSaving] = useState(false);
    const [editMsg, setEditMsg] = useState<string | null>(null);

    // 活動趨勢檢視模式
    const [viewMode, setViewMode] = useState<ViewMode>('daily');
    const { t } = useTranslation();

    const fetchData = async () => {
        try {
            const r = await api.get(`/api/residents/${id}`);
            setData(r.data);
            // 只在初次載入時設定 embeddingReady，上傳後由 handlePhotoUpload 單獨更新
            setEmbeddingReady(prev => prev ? prev : !!r.data.has_embedding);
            setError(null);
        } catch {
            setError('無法載入資料，請稍後再試。');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (id) {
            setLoading(true);
            setEmbeddingReady(false); // 重置，等 fetchData 設定
            fetchData();
        }
    }, [id]);

    const handlePhotoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file || !id) return;
        setUploading(true);
        setUploadMsg(null);
        try {
            const form = new FormData();
            form.append('photo', file);
            const r = await api.post(`/api/residents/${id}/photo`, form, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            // ✅ 上傳成功：直接設定為 true，且不讓 fetchData 覆蓋
            setEmbeddingReady(true);
            setData(prev => prev ? { ...prev, has_embedding: true } : prev);
            setUploadMsg({ text: r.data.message || t('detail.photo_success'), ok: true });
        } catch (err: any) {
            const detail = err?.response?.data?.detail || t('detail.photo_fail');
            setUploadMsg({ text: detail, ok: false });
        } finally {
            setUploading(false);
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    const openEdit = () => {
        if (!data) return;
        setEditName(data.name);
        setEditRoom(data.room || '');
        setEditLineId(data.family_line_id || '');
        setEditMsg(null);
        setEditOpen(true);
    };

    const handleSaveEdit = async () => {
        if (!id || !editName.trim()) return;
        setSaving(true);
        setEditMsg(null);
        try {
            const fd = new FormData();
            fd.append('name', editName.trim());
            fd.append('room', editRoom.trim());
            fd.append('family_line_id', editLineId.trim());
            await api.put(`/api/residents/${id}`, fd, { headers: { 'Content-Type': 'multipart/form-data' } });
            // 直接更新本地資料，不需重新整理
            setData(prev => prev ? { ...prev, name: editName.trim(), room: editRoom.trim() || null, family_line_id: editLineId.trim() || null } : prev);
            setEditOpen(false);
        } catch (err: any) {
            setEditMsg(err?.response?.data?.detail || t('detail.save_fail'));
        } finally {
            setSaving(false);
        }
    };

    // --- 活動趨勢 ---
    const allActivities = useMemo(() => {
        if (!data?.daily_activities) return [];
        return [...data.daily_activities].reverse();
    }, [data]);

    const dailyData = useMemo(() => allActivities.slice(-14).map((d: any) => ({
        date: formatDate(d.date).slice(5),
        '走路 (分)': d.walking_mins || 0,
        '坐著 (分)': d.sitting_mins || 0,
    })), [allActivities]);

    const weeklyData = useMemo(() => {
        const weeks: any[] = [];
        for (let i = 0; i < allActivities.length; i += 7) {
            const chunk = allActivities.slice(i, i + 7);
            weeks.push({
                date: `第${Math.floor(i / 7) + 1}週`,
                '走路 (分)': chunk.reduce((s: number, d: any) => s + (d.walking_mins || 0), 0),
                '坐著 (分)': chunk.reduce((s: number, d: any) => s + (d.sitting_mins || 0), 0),
            });
        }
        return weeks;
    }, [allActivities]);

    const monthlyData = useMemo(() => {
        const byMonth: Record<string, any> = {};
        allActivities.forEach((d: any) => {
            const dt = new Date(d.date);
            const key = `${dt.getFullYear()}/${String(dt.getMonth() + 1).padStart(2, '0')}`;
            if (!byMonth[key]) byMonth[key] = { date: key, '走路 (分)': 0, '坐著 (分)': 0 };
            byMonth[key]['走路 (分)'] += d.walking_mins || 0;
            byMonth[key]['坐著 (分)'] += d.sitting_mins || 0;
        });
        return Object.values(byMonth);
    }, [allActivities]);

    const chartData = viewMode === 'daily' ? dailyData : viewMode === 'weekly' ? weeklyData : monthlyData;

    if (loading) return (
        <div className="min-h-screen bg-[#09090b] flex items-center justify-center">
            <div className="flex flex-col items-center gap-4">
                <div className="h-12 w-12 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin"></div>
                <p className="text-zinc-500 font-medium">{t('detail.loading')}</p>
            </div>
        </div>
    );

    if (error || !data) return (
        <div className="min-h-screen bg-[#09090b] flex items-center justify-center p-8">
            <div className="max-w-md w-full text-center space-y-4">
                <AlertCircle className="mx-auto text-rose-500" size={48} />
                <h2 className="text-xl font-bold text-white">{error || t('detail.not_found')}</h2>
                <button onClick={() => navigate('/elders')} className="px-6 py-2 rounded-lg bg-zinc-800 text-white hover:bg-zinc-700 transition-colors">{t('detail.back_list')}</button>
            </div>
        </div>
    );

    return (
        <div className="p-8 max-w-7xl mx-auto space-y-8">
            {/* 編輯 Modal */}
            {editOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
                    <div className="bg-zinc-900 border border-zinc-700 rounded-2xl p-6 max-w-md w-full mx-4 shadow-2xl">
                        <div className="flex items-center justify-between mb-5">
                            <h3 className="text-lg font-bold text-white flex items-center gap-2">
                                <Edit3 size={18} className="text-indigo-400" />
                                {t('detail.edit_title')}
                            </h3>
                            <button onClick={() => setEditOpen(false)} className="text-zinc-500 hover:text-white transition-colors"><X size={20} /></button>
                        </div>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-xs font-medium text-zinc-400 mb-1">{t('elders.name')}</label>
                                <input value={editName} onChange={e => setEditName(e.target.value)}
                                    className="w-full rounded-lg bg-zinc-800 ring-1 ring-zinc-700 py-2.5 px-4 text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
                            </div>
                            <div>
                                <label className="block text-xs font-medium text-zinc-400 mb-1">{t('detail.lbl_room')}</label>
                                <input value={editRoom} onChange={e => setEditRoom(e.target.value)} placeholder={t('elders.room_ph')}
                                    className="w-full rounded-lg bg-zinc-800 ring-1 ring-zinc-700 py-2.5 px-4 text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 placeholder:text-zinc-600" />
                            </div>
                            <div>
                                <label className="block text-xs font-medium text-zinc-400 mb-1">{t('detail.line_id')}</label>
                                <input value={editLineId} onChange={e => setEditLineId(e.target.value)} placeholder="U3b98c..."
                                    className="w-full rounded-lg bg-zinc-800 ring-1 ring-zinc-700 py-2.5 px-4 text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 placeholder:text-zinc-600" />
                            </div>
                            {editMsg && <p className="text-xs text-rose-400 bg-rose-500/10 px-3 py-2 rounded-lg">{editMsg}</p>}
                        </div>
                        <div className="flex gap-3 mt-6">
                            <button onClick={handleSaveEdit} disabled={saving || !editName.trim()}
                                className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition-colors disabled:opacity-50">
                                {saving ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Save size={14} />}
                                {saving ? t('detail.saving') : t('detail.save_btn')}
                            </button>
                            <button onClick={() => setEditOpen(false)} disabled={saving}
                                className="flex-1 px-4 py-2.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 font-medium text-sm transition-colors">
                                {t('misc.cancel')}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <button onClick={() => navigate('/elders')}
                className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors group">
                <ArrowLeft size={18} className="group-hover:-translate-x-1 transition-transform" />
                {t('detail.back_name')}
            </button>

            {/* 個人資料卡 */}
            <div className="relative overflow-hidden rounded-3xl bg-zinc-900 ring-1 ring-white/10 p-8">
                <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/5 blur-[100px] rounded-full -mr-32 -mt-32 pointer-events-none"></div>
                <div className="relative flex flex-col md:flex-row gap-8 items-start">
                    <div className="h-28 w-28 rounded-2xl bg-gradient-to-br from-indigo-600 to-violet-700 flex items-center justify-center text-white font-bold text-5xl shadow-2xl shadow-indigo-500/20 flex-shrink-0">
                        {data.name[0]}
                    </div>

                    <div className="flex-1 min-w-0 space-y-4">
                        {/* 名稱 + 狀態標籤 + 編輯按鈕 */}
                        <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                            <h1 className="text-3xl font-extrabold text-white tracking-tight">{data.name}</h1>
                            {/* 雙重保障：DB 值 OR 本地上傳覆蓋 */}
                            <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider whitespace-nowrap ${(data.has_embedding || embeddingReady) ? 'bg-emerald-500/10 text-emerald-400 ring-1 ring-emerald-500/20' : 'bg-amber-500/10 text-amber-400 ring-1 ring-amber-500/20'}`}>
                                {(data.has_embedding || embeddingReady) ? <><CheckCircle size={12} /> {t('detail.face_ready')}</> : <><AlertCircle size={12} /> {t('detail.face_none')}</>}
                            </span>
                            <button onClick={openEdit}
                                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-zinc-800 hover:bg-zinc-700 text-zinc-300 hover:text-white transition-colors border border-zinc-700">
                                <Edit3 size={12} /> {t('detail.edit_btn')}
                            </button>
                        </div>

                        {/* 基本資訊格 */}
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                            {[
                                { icon: Home, label: t('detail.lbl_room'), value: data.room || t('detail.val_empty') },
                                { icon: Calendar, label: t('detail.lbl_reg_date'), value: formatDate(data.created_at) },
                                { icon: User, label: t('detail.lbl_sys_id'), value: `#${data.id}` },
                                { icon: Activity, label: t('detail.lbl_line'), value: data.family_line_id ? data.family_line_id.slice(0, 8) + '...' : t('detail.val_unset') },
                            ].map(({ icon: Icon, label, value }) => (
                                <div key={label} className="flex items-center gap-3 text-zinc-400">
                                    <div className="p-2 rounded-lg bg-white/5 flex-shrink-0"><Icon size={15} /></div>
                                    <div className="min-w-0">
                                        <p className="text-[10px] uppercase font-bold text-zinc-500">{label}</p>
                                        <p className="text-white font-medium text-sm truncate">{value}</p>
                                    </div>
                                </div>
                            ))}
                        </div>

                        {/* 臉部照片上傳 */}
                        <div className={`rounded-xl border p-4 ${embeddingReady ? 'border-zinc-700 bg-zinc-800/40' : 'border-amber-500/30 bg-amber-500/5'}`}>
                            <div className="flex items-center justify-between flex-wrap gap-3">
                                <div className="flex items-center gap-3">
                                    <Camera size={16} className={embeddingReady ? 'text-emerald-400' : 'text-amber-400'} />
                                    <div>
                                        <p className="text-sm font-medium text-white">
                                            {embeddingReady ? t('detail.photo_title_ready') : t('detail.photo_title_none')}
                                        </p>
                                        <p className="text-xs text-zinc-500">
                                            {embeddingReady ? t('detail.photo_desc_ready') : t('detail.photo_desc_none')}
                                        </p>
                                    </div>
                                </div>
                                <div>
                                    <input ref={fileInputRef} type="file" accept="image/*" className="hidden"
                                        onChange={handlePhotoUpload} id={`photo-upload-${id}`} />
                                    <label htmlFor={`photo-upload-${id}`}
                                        className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium cursor-pointer transition-colors ${uploading ? 'bg-zinc-600 text-zinc-400 cursor-not-allowed pointer-events-none' : embeddingReady ? 'bg-zinc-700 hover:bg-zinc-600 text-white' : 'bg-amber-500 hover:bg-amber-400 text-black'}`}>
                                        {uploading ? <div className="w-4 h-4 border-2 border-zinc-400/30 border-t-zinc-400 rounded-full animate-spin" /> : <Upload size={14} />}
                                        {uploading ? t('detail.photo_uploading') : embeddingReady ? t('detail.photo_reupload') : t('detail.photo_upload')}
                                    </label>
                                </div>
                            </div>
                            {uploadMsg && (
                                <div className={`mt-3 text-xs px-3 py-2 rounded-lg ${uploadMsg.ok ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'}`}>
                                    {uploadMsg.ok ? '✅' : '❌'} {uploadMsg.text}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* 活動趨勢 + 異常紀錄 */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                <div className="lg:col-span-8 space-y-8">
                    {/* 活動趨勢 */}
                    <div className="rounded-2xl bg-zinc-900 ring-1 ring-white/5 p-6 shadow-xl">
                        <div className="flex items-center justify-between mb-5">
                            <h3 className="text-lg font-bold text-white flex items-center gap-2">
                                <Activity className="text-indigo-400" size={20} />
                                {t('detail.trend_title')}
                            </h3>
                            <select value={viewMode} onChange={e => setViewMode(e.target.value as ViewMode)}
                                className="bg-zinc-800 text-white text-sm rounded-lg px-3 py-1.5 border border-zinc-700 focus:outline-none focus:border-indigo-500 cursor-pointer">
                                <option value="daily">{t('detail.view_daily')}</option>
                                <option value="weekly">{t('detail.view_weekly')}</option>
                                <option value="monthly">{t('detail.view_monthly')}</option>
                            </select>
                        </div>
                        <div className="h-[300px]">
                            {chartData.length > 0 ? (
                                viewMode === 'monthly' ? (
                                    <ResponsiveContainer width="100%" height="100%">
                                        <LineChart data={chartData}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
                                            <XAxis dataKey="date" stroke="#71717a" fontSize={11} tickLine={false} axisLine={false} />
                                            <YAxis stroke="#71717a" fontSize={11} tickLine={false} axisLine={false} unit="m" />
                                            <Tooltip contentStyle={{ backgroundColor: '#18181b', border: '1px solid #3f3f46', borderRadius: '8px' }} />
                                            <Legend />
                                            <Line type="monotone" dataKey="走路 (分)" stroke="#6366f1" strokeWidth={2} dot={{ r: 4 }} />
                                            <Line type="monotone" dataKey="坐著 (分)" stroke="#f59e0b" strokeWidth={2} dot={{ r: 4 }} />
                                        </LineChart>
                                    </ResponsiveContainer>
                                ) : (
                                    <ResponsiveContainer width="100%" height="100%">
                                        <BarChart data={chartData}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
                                            <XAxis dataKey="date" stroke="#71717a" fontSize={11} tickLine={false} axisLine={false} />
                                            <YAxis stroke="#71717a" fontSize={11} tickLine={false} axisLine={false} unit="m" />
                                            <Tooltip contentStyle={{ backgroundColor: '#18181b', border: '1px solid #3f3f46', borderRadius: '8px' }} />
                                            <Legend />
                                            <Bar dataKey="走路 (分)" fill="#6366f1" radius={[4, 4, 0, 0]} maxBarSize={30} />
                                            <Bar dataKey="坐著 (分)" fill="#f59e0b" radius={[4, 4, 0, 0]} maxBarSize={30} />
                                        </BarChart>
                                    </ResponsiveContainer>
                                )
                            ) : (
                                <div className="h-full flex flex-col items-center justify-center text-zinc-600 border-2 border-dashed border-zinc-800 rounded-xl">
                                    <FileText size={40} className="mb-3 opacity-20" />
                                    <p className="font-medium">{t('detail.trend_empty')}</p>
                                    <p className="text-sm mt-1">{t('detail.trend_empty_desc')}</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* 最近行為 */}
                    <div className="rounded-2xl bg-zinc-900 ring-1 ring-white/5 p-6 shadow-xl">
                        <h3 className="text-lg font-bold text-white mb-5 flex items-center gap-2">
                            <Clock className="text-indigo-400" size={20} />
                            {t('detail.recent_title')}
                        </h3>
                        <div className="space-y-3">
                            {(!data.recent_events || data.recent_events.length === 0) ? (
                                <p className="text-zinc-500 italic text-sm py-4">{t('detail.recent_empty')}</p>
                            ) : (
                                data.recent_events.slice(0, 10).map((event, idx) => (
                                    <div key={idx} className="flex items-center justify-between p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors">
                                        <div className="flex items-center gap-3">
                                            <div className="h-8 w-8 rounded-full bg-indigo-500/10 flex items-center justify-center flex-shrink-0">
                                                <Activity size={14} className="text-indigo-400" />
                                            </div>
                                            <p className="text-sm text-white">
                                                {t('detail.recent_doing')} <span className="text-indigo-400 capitalize">{event.activity_type}</span>
                                                {event.object_interaction && <span className="text-zinc-500 text-xs"> ({t('detail.recent_interact')} {event.object_interaction} {t('detail.recent_interact_end')})</span>}
                                            </p>
                                        </div>
                                        <span className="text-xs text-zinc-500 shrink-0 ml-2">{formatDateTime(event.timestamp).slice(11)}</span>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>

                {/* 異常事件側欄 */}
                <div className="lg:col-span-4">
                    <div className="rounded-2xl bg-zinc-900 ring-1 ring-rose-500/20 p-6 shadow-xl sticky top-8">
                        <h3 className="text-lg font-bold text-white mb-5 flex items-center gap-2">
                            <ShieldAlert className="text-rose-500" size={20} />
                            {t('detail.history_title')}
                        </h3>
                        <div className="space-y-4 overflow-y-auto max-h-[560px] pr-1">
                            {(!data.abnormal_events || data.abnormal_events.length === 0) ? (
                                <div className="text-center py-12">
                                    <CheckCircle size={36} className="mx-auto text-emerald-500/20 mb-3" />
                                    <p className="text-zinc-600 text-sm">{t('detail.history_empty')}</p>
                                </div>
                            ) : (
                                data.abnormal_events.map((event, idx) => (
                                    <div key={idx} className={`p-4 rounded-xl border ${event.level >= 3 ? 'bg-rose-500/5 border-rose-500/20' : 'bg-amber-500/5 border-amber-500/20'}`}>
                                        <div className="flex items-center justify-between mb-1.5">
                                            <span className={`text-[10px] font-black px-2 py-0.5 rounded-full uppercase ${event.level >= 3 ? 'bg-rose-500 text-white' : 'bg-amber-500 text-black'}`}>
                                                LV.{event.level} — {event.type}
                                            </span>
                                        </div>
                                        <p className="text-[11px] text-zinc-500 mb-1">{formatDateTime(event.timestamp)}</p>
                                        <p className="text-xs text-zinc-300 leading-relaxed">{event.description}</p>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
