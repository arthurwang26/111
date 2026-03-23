import { useState, useEffect } from 'react';
import { Users, Plus, Trash2, ChevronRight, Upload, AlertCircle, CheckCircle, X } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import api from '../services/api';
import { useTranslation } from '../contexts/I18nContext';

type Elder = { id: number; name: string; room: string | null; created_at: string; has_embedding: boolean };

export default function EldersPage() {
    const [elders, setElders] = useState<Elder[]>([]);
    const [showForm, setShowForm] = useState(false);
    const [name, setName] = useState('');
    const [room, setRoom] = useState('');
    const [photo, setPhoto] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [msg, setMsg] = useState<{ type: 'ok' | 'err'; text: string } | null>(null);
    const [deleteModal, setDeleteModal] = useState<{ id: number; name: string } | null>(null);
    const [deleting, setDeleting] = useState(false);
    const { t } = useTranslation();

    const location = useLocation();

    const fetchElders = async () => {
        try {
            const r = await api.get('/api/residents');
            setElders(r.data);
        } catch { setElders([]); }
    };

    // 每次導覽回此頁都重新整理
    useEffect(() => { fetchElders(); }, [location.key]);

    // 使用者切換分頁回來時重新整理
    useEffect(() => {
        const onVisible = () => { if (document.visibilityState === 'visible') fetchElders(); };
        document.addEventListener('visibilitychange', onVisible);
        return () => document.removeEventListener('visibilitychange', onVisible);
    }, []);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!name.trim()) return;
        setLoading(true); setMsg(null);
        try {
            const fd = new FormData();
            fd.append('name', name);
            if (room.trim()) fd.append('room', room.trim());
            if (photo) fd.append('photo', photo);
            await api.post('/api/residents', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
            setMsg({ type: 'ok', text: `${name} 已成功登記！` });
            setName(''); setRoom(''); setPhoto(null); setShowForm(false);
            fetchElders();
        } catch (err: any) {
            setMsg({ type: 'err', text: err.response?.data?.detail || '登記失敗，請重試' });
        } finally { setLoading(false); }
    };

    const confirmDelete = async () => {
        if (!deleteModal) return;
        setDeleting(true);
        try {
            await api.delete(`/api/residents/${deleteModal.id}`);
            setDeleteModal(null);
            fetchElders();
        } catch {
            setDeleteModal(null);
            setMsg({ type: 'err', text: '刪除失敗，請重試' });
        } finally { setDeleting(false); }
    };

    return (
        <div className="p-8 max-w-5xl mx-auto">
            {/* 刪除確認 Modal */}
            {deleteModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
                    <div className="bg-zinc-900 border border-zinc-700 rounded-2xl p-6 max-w-sm w-full mx-4 shadow-2xl">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="p-2 rounded-lg bg-rose-500/10">
                                <Trash2 size={20} className="text-rose-400" />
                            </div>
                            <h3 className="text-lg font-bold text-white">確認刪除</h3>
                        </div>
                        <p className="text-zinc-400 text-sm mb-6">
                            確定要刪除長者「<span className="text-white font-semibold">{deleteModal.name}</span>」？
                            此操作無法復原，所有相關記錄也會一併刪除。
                        </p>
                        <div className="flex gap-3">
                            <button
                                onClick={confirmDelete}
                                disabled={deleting}
                                className="flex-1 px-4 py-2.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-medium text-sm transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                            >
                                {deleting && <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
                                {deleting ? '刪除中...' : '確認刪除'}
                            </button>
                            <button
                                onClick={() => setDeleteModal(null)}
                                disabled={deleting}
                                className="flex-1 px-4 py-2.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 font-medium text-sm transition-colors"
                            >
                                取消
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-3">
                        <Users className="text-indigo-500" size={28} />
                        {t('elders.title')}
                    </h1>
                    <p className="text-zinc-400 mt-1">{t('elders.subtitle').replace('{count}', elders.length.toString())}</p>
                </div>
                <button
                    onClick={() => { setShowForm(!showForm); setMsg(null); }}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium transition-colors"
                >
                    {showForm ? <X size={18} /> : <Plus size={18} />}
                    {showForm ? t('elders.cancel') : t('elders.add')}
                </button>
            </div>

            {/* 新增表單 */}
            {showForm && (
                <div className="mb-8 rounded-xl bg-zinc-900 ring-1 ring-white/10 p-6">
                    <h2 className="text-lg font-semibold text-white mb-4">{t('elders.form_title')}</h2>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-zinc-300 mb-1">{t('elders.name')}</label>
                                <input
                                    type="text" required value={name} onChange={e => setName(e.target.value)}
                                    className="w-full rounded-lg bg-zinc-800 border-0 ring-1 ring-zinc-700 py-2.5 px-4 text-white placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                    placeholder={t('elders.name_ph')}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-zinc-300 mb-1">{t('elders.room')}</label>
                                <input
                                    type="text" value={room} onChange={e => setRoom(e.target.value)}
                                    className="w-full rounded-lg bg-zinc-800 border-0 ring-1 ring-zinc-700 py-2.5 px-4 text-white placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                    placeholder={t('elders.room_ph')}
                                />
                            </div>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-zinc-300 mb-1">{t('elders.photo')}</label>
                            <label className="flex items-center gap-3 cursor-pointer rounded-lg bg-zinc-800 ring-1 ring-zinc-700 py-2.5 px-4 hover:ring-indigo-500 transition-all">
                                <Upload size={18} className="text-zinc-400" />
                                <span className="text-sm text-zinc-400">{photo ? photo.name : t('elders.upload')}</span>
                                <input type="file" accept="image/*" className="hidden" onChange={e => setPhoto(e.target.files?.[0] || null)} />
                            </label>
                        </div>
                        {msg && (
                            <div className={`flex items-center gap-2 p-3 rounded-lg text-sm ${msg.type === 'ok' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                                {msg.type === 'ok' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
                                {msg.text}
                            </div>
                        )}
                        <div className="flex gap-3">
                            <button type="submit" disabled={loading}
                                className="px-5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium disabled:opacity-50 transition-colors">
                                {loading ? t('elders.processing') : t('elders.submit')}
                            </button>
                            <button type="button" onClick={() => setShowForm(false)}
                                className="px-5 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 transition-colors">
                                {t('elders.cancel')}
                            </button>
                        </div>
                    </form>
                </div>
            )}

            {msg && !showForm && (
                <div className={`mb-4 flex items-center gap-2 p-3 rounded-lg text-sm ${msg.type === 'ok' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                    {msg.type === 'ok' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
                    {msg.text}
                </div>
            )}

            {/* 長者清單 */}
            <div className="space-y-3">
                {elders.length === 0 ? (
                    <div className="text-center py-16 text-zinc-500">
                        <Users size={48} className="mx-auto mb-4 opacity-30" />
                        <p>{t('elders.empty')}</p>
                    </div>
                ) : (
                    elders.map(elder => (
                        <div key={elder.id}
                            className="group relative p-5 rounded-xl bg-zinc-900 ring-1 ring-white/5 hover:ring-indigo-500/50 hover:bg-zinc-800/50 transition-all"
                        >
                            <Link to={`/elders/${elder.id}`} className="absolute inset-0 z-10" />
                            <div className="flex items-center justify-between relative z-20 pointer-events-none">
                                <div className="flex items-center gap-4">
                                    <div className="h-12 w-12 rounded-full bg-indigo-500/20 flex items-center justify-center text-indigo-400 font-bold text-lg">
                                        {elder.name[0]}
                                    </div>
                                    <div>
                                        <p className="font-semibold text-white group-hover:text-indigo-400 transition-colors">{elder.name}</p>
                                        <div className="flex items-center gap-2 mt-0.5">
                                            <span className={`inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full ${!!elder.has_embedding ? 'bg-emerald-500/15 text-emerald-400' : 'bg-amber-500/15 text-amber-400'}`}>
                                                {!!elder.has_embedding ? <><CheckCircle size={10} /> {t('elders.face_ready')}</> : <>⚠ {t('elders.face_none')}</>}
                                            </span>
                                            {elder.room && <span className="text-[10px] text-zinc-500">🏠 {elder.room}</span>}
                                            <span className="text-[10px] text-zinc-500">ID: #{elder.id}</span>
                                        </div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2 relative z-30 pointer-events-auto">
                                    <button
                                        onClick={(e) => { e.preventDefault(); e.stopPropagation(); setDeleteModal({ id: elder.id, name: elder.name }); }}
                                        className="p-2 rounded-lg text-zinc-500 hover:bg-red-500/10 hover:text-red-400 transition-colors"
                                        title={t('elders.del_btn')}
                                    >
                                        <Trash2 size={18} />
                                    </button>
                                    <ChevronRight size={18} className="text-zinc-600 group-hover:text-indigo-400" />
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
