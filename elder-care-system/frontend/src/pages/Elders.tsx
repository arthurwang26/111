import { useState, useEffect } from 'react';
import { Users, Plus, Trash2, ChevronRight, Upload, AlertCircle, CheckCircle } from 'lucide-react';
import api from '../services/api';

type Elder = { id: number; name: string; created_at: string; has_embedding: boolean };

export default function EldersPage() {
    const [elders, setElders] = useState<Elder[]>([]);
    const [showForm, setShowForm] = useState(false);
    const [name, setName] = useState('');
    const [photo, setPhoto] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [msg, setMsg] = useState<{ type: 'ok' | 'err'; text: string } | null>(null);

    const fetchElders = async () => {
        try {
            const r = await api.get('/api/residents');
            setElders(r.data);
        } catch { setElders([]); }
    };

    useEffect(() => { fetchElders(); }, []);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!name.trim()) return;
        setLoading(true); setMsg(null);
        try {
            const fd = new FormData();
            fd.append('name', name);
            if (photo) fd.append('photo', photo);
            await api.post('/api/residents', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
            setMsg({ type: 'ok', text: `${name} 已成功登記！` });
            setName(''); setPhoto(null); setShowForm(false);
            fetchElders();
        } catch (err: any) {
            setMsg({ type: 'err', text: err.response?.data?.detail || '登記失敗，請重試' });
        } finally { setLoading(false); }
    };

    const handleDelete = async (id: number, elderName: string) => {
        if (!confirm(`確定要刪除長者「${elderName}」？`)) return;
        try {
            await api.delete(`/api/residents/${id}`);
            fetchElders();
        } catch { alert('刪除失敗'); }
    };

    return (
        <div className="p-8 max-w-5xl mx-auto">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-3">
                        <Users className="text-indigo-500" size={28} />
                        長者管理
                    </h1>
                    <p className="text-zinc-400 mt-1">共 {elders.length} 位長者已登記</p>
                </div>
                <button
                    onClick={() => { setShowForm(!showForm); setMsg(null); }}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium transition-colors"
                >
                    <Plus size={18} /> 新增長者
                </button>
            </div>

            {/* 新增表單 */}
            {showForm && (
                <div className="mb-8 rounded-xl bg-zinc-900 ring-1 ring-white/10 p-6">
                    <h2 className="text-lg font-semibold text-white mb-4">新增長者資料</h2>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-zinc-300 mb-1">姓名 *</label>
                            <input
                                type="text" required value={name} onChange={e => setName(e.target.value)}
                                className="w-full rounded-lg bg-zinc-800 border-0 ring-1 ring-zinc-700 py-2.5 px-4 text-white placeholder:text-zinc-500 focus:ring-2 focus:ring-indigo-500"
                                placeholder="例：王大明"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-zinc-300 mb-1">正面臉部照片（用於識別）</label>
                            <label className="flex items-center gap-3 cursor-pointer rounded-lg bg-zinc-800 ring-1 ring-zinc-700 py-2.5 px-4 hover:ring-indigo-500 transition-all">
                                <Upload size={18} className="text-zinc-400" />
                                <span className="text-sm text-zinc-400">{photo ? photo.name : '點擊上傳照片（JPG/PNG）'}</span>
                                <input type="file" accept="image/*" className="hidden" onChange={e => setPhoto(e.target.files?.[0] || null)} />
                            </label>
                        </div>
                        {msg && (
                            <div className={`flex items-center gap-2 p-3 rounded-lg text-sm ${msg.type === 'ok' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
                                }`}>
                                {msg.type === 'ok' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
                                {msg.text}
                            </div>
                        )}
                        <div className="flex gap-3">
                            <button type="submit" disabled={loading}
                                className="px-5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium disabled:opacity-50 transition-colors">
                                {loading ? '處理中...' : '確認登記'}
                            </button>
                            <button type="button" onClick={() => setShowForm(false)}
                                className="px-5 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 transition-colors">
                                取消
                            </button>
                        </div>
                    </form>
                </div>
            )}

            {/* 長者清單 */}
            <div className="space-y-3">
                {elders.length === 0 ? (
                    <div className="text-center py-16 text-zinc-500">
                        <Users size={48} className="mx-auto mb-4 opacity-30" />
                        <p>尚未登記任何長者，點擊「新增長者」開始。</p>
                    </div>
                ) : (
                    elders.map(elder => (
                        <div key={elder.id}
                            className="flex items-center justify-between p-5 rounded-xl bg-zinc-900 ring-1 ring-white/5 hover:ring-white/10 transition-all">
                            <div className="flex items-center gap-4">
                                <div className="h-12 w-12 rounded-full bg-indigo-500/20 flex items-center justify-center text-indigo-400 font-bold text-lg">
                                    {elder.name[0]}
                                </div>
                                <div>
                                    <p className="font-semibold text-white">{elder.name}</p>
                                    <div className="flex items-center gap-2 mt-0.5">
                                        <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full ${elder.has_embedding ? 'bg-emerald-500/15 text-emerald-400' : 'bg-amber-500/15 text-amber-400'
                                            }`}>
                                            {elder.has_embedding ? <><CheckCircle size={10} /> 臉部已設定</> : <>⚠ 未設定臉部</>}
                                        </span>
                                        <span className="text-xs text-zinc-500">
                                            登記日：{new Date(elder.created_at).toLocaleDateString('zh-TW')}
                                        </span>
                                    </div>
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={() => handleDelete(elder.id, elder.name)}
                                    className="p-2 rounded-lg text-zinc-500 hover:bg-red-500/10 hover:text-red-400 transition-colors">
                                    <Trash2 size={18} />
                                </button>
                                <ChevronRight size={18} className="text-zinc-600" />
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
