import { useEffect, useState, useCallback } from 'react';
import api from '../services/api';
import { Plus, Trash2, Edit2, Check, X, Video } from 'lucide-react';

interface Camera {
    id: number;
    name: string;
    source: string;
    location: string | null;
    status: string;
}

function Toast({ message, type, onClose }: { message: string; type: 'success' | 'error'; onClose: () => void }) {
    useEffect(() => { const t = setTimeout(onClose, 3500); return () => clearTimeout(t); }, [onClose]);
    return (
        <div className={`fixed top-6 right-6 z-50 ${type === 'success' ? 'bg-emerald-600' : 'bg-rose-600'} text-white px-5 py-3 rounded-xl shadow-2xl text-sm font-medium flex items-center gap-3`}>
            {type === 'success' ? '✅' : '❌'} {message}
            <button onClick={onClose} className="ml-2 opacity-70 hover:opacity-100 text-lg">×</button>
        </div>
    );
}

export default function CamerasPage() {
    const [cameras, setCameras] = useState<Camera[]>([]);
    const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
    const [showAdd, setShowAdd] = useState(false);
    const [editId, setEditId] = useState<number | null>(null);
    const [form, setForm] = useState({ name: '', source: '', location: '' });
    const [editForm, setEditForm] = useState({ name: '', source: '', location: '' });

    const [loading, setLoading] = useState(false);
    const [deleteModal, setDeleteModal] = useState<{ show: boolean; id: number | null }>({ show: false, id: null });

    const showToast = useCallback((message: string, type: 'success' | 'error') => setToast({ message, type }), []);

    const fetchCameras = useCallback(async () => {
        try {
            const r = await api.get('/api/cameras');
            setCameras(r.data);
        } catch (err) {
            console.error("Fetch cameras failed", err);
        }
    }, []);

    useEffect(() => { fetchCameras(); }, [fetchCameras]);

    const handleAdd = async () => {
        if (!form.name || !form.source) { showToast('請填寫名稱和來源', 'error'); return; }
        setLoading(true);
        try {
            const payload = {
                ...form,
                location: form.location.trim() || null
            };
            console.log("Adding camera:", payload);
            await api.post('/api/cameras', payload);
            showToast('鏡頭已新增！', 'success');
            setForm({ name: '', source: '', location: '' });
            setShowAdd(false);
            fetchCameras();
        } catch (err) {
            console.error("Add camera failed", err);
            showToast('新增失敗', 'error');
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async () => {
        if (!deleteModal.id) return;
        setLoading(true);
        try {
            await api.delete(`/api/cameras/${deleteModal.id}`);
            showToast('已刪除', 'success');
            setDeleteModal({ show: false, id: null });
            fetchCameras();
        } catch (err) {
            console.error("Delete camera failed", err);
            showToast('刪除失敗', 'error');
        } finally {
            setLoading(false);
        }
    };

    const startEdit = (cam: Camera) => {
        setEditId(cam.id);
        setEditForm({ name: cam.name, source: cam.source, location: cam.location || '' });
    };

    const handleEdit = async (id: number) => {
        try {
            await api.put(`/api/cameras/${id}`, editForm);
            showToast('已更新', 'success');
            setEditId(null);
            fetchCameras();
        } catch { showToast('更新失敗', 'error'); }
    };

    const exampleSources = [
        'rtsp://192.168.1.100:554/stream1',
        'rtsp://admin:password@192.168.1.101:554/live',
        'http://192.168.1.102:8080/video',
        '0  (本機第一支 Webcam)',
        '1  (本機第二支 Webcam)',
    ];

    return (
        <div className="p-8 h-full overflow-y-auto">
            {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}

            <div className="mb-8 flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white mb-2">鏡頭管理</h1>
                    <p className="text-zinc-400">新增、設定或刪除 IP 攝影機來源</p>
                </div>
                <button
                    onClick={() => setShowAdd(!showAdd)}
                    className="flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium text-white transition-colors"
                >
                    <Plus size={16} /> 新增鏡頭
                </button>
            </div>

            {/* 新增表單 */}
            {showAdd && (
                <div className="mb-6 rounded-xl bg-zinc-900 border border-indigo-500/30 p-6 space-y-4">
                    <h3 className="text-base font-semibold text-white">新增攝影機</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                        <div>
                            <label className="block text-xs font-medium text-zinc-400 mb-1.5">名稱 *</label>
                            <input
                                type="text" placeholder="例：走廊鏡頭"
                                value={form.name} onChange={e => setForm({ ...form, name: e.target.value })}
                                className="w-full bg-zinc-800 text-white text-sm rounded-lg px-3 py-2.5 border border-zinc-700 focus:outline-none focus:border-indigo-500"
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-medium text-zinc-400 mb-1.5">來源 (IP/RTSP/索引) *</label>
                            <input
                                type="text" placeholder="rtsp://192.168.1.x:554/... 或 0"
                                value={form.source} onChange={e => setForm({ ...form, source: e.target.value })}
                                className="w-full bg-zinc-800 text-white text-sm rounded-lg px-3 py-2.5 border border-zinc-700 focus:outline-none focus:border-indigo-500"
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-medium text-zinc-400 mb-1.5">位置 (選填)</label>
                            <input
                                type="text" placeholder="例：一樓走廊"
                                value={form.location} onChange={e => setForm({ ...form, location: e.target.value })}
                                className="w-full bg-zinc-800 text-white text-sm rounded-lg px-3 py-2.5 border border-zinc-700 focus:outline-none focus:border-indigo-500"
                            />
                        </div>
                    </div>
                    <div className="flex gap-3">
                        <button
                            type="button"
                            onClick={handleAdd}
                            disabled={loading}
                            className={`px-4 py-2 rounded-lg text-sm font-medium text-white transition-colors flex items-center gap-2 ${loading ? 'bg-indigo-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-500'}`}
                        >
                            {loading ? (
                                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            ) : (
                                <Check size={14} />
                            )}
                            {loading ? '處理中...' : '確認新增'}
                        </button>
                        <button onClick={() => setShowAdd(false)} className="px-4 py-2 bg-zinc-700 hover:bg-zinc-600 rounded-lg text-sm font-medium text-zinc-300 transition-colors flex items-center gap-2">
                            <X size={14} /> 取消
                        </button>
                    </div>
                    {/* 格式說明 */}
                    <details className="text-xs text-zinc-500 mt-2">
                        <summary className="cursor-pointer hover:text-zinc-300 transition-colors">📖 來源格式範例（點擊展開）</summary>
                        <ul className="mt-2 space-y-1 pl-4 list-disc">
                            {exampleSources.map(s => <li key={s} className="font-mono">{s}</li>)}
                        </ul>
                    </details>
                </div>
            )}

            {/* 鏡頭列表 */}
            {cameras.length === 0 ? (
                <div className="text-center py-20 text-zinc-500">
                    <Video size={48} className="mx-auto mb-4 opacity-30" />
                    <p className="text-sm">尚未設定任何攝影機</p>
                    <p className="text-xs mt-1">點擊右上角「新增鏡頭」開始設定</p>
                </div>
            ) : (
                <div className="space-y-3">
                    {cameras.map(cam => (
                        <div key={cam.id} className="rounded-xl bg-zinc-900 border border-zinc-800 p-5 flex items-center gap-6">
                            <div className="w-12 h-12 rounded-lg bg-zinc-800 flex items-center justify-center flex-shrink-0">
                                <Video size={22} className="text-indigo-400" />
                            </div>
                            {editId === cam.id ? (
                                <div className="flex-1 grid grid-cols-3 gap-3">
                                    <input value={editForm.name} onChange={e => setEditForm({ ...editForm, name: e.target.value })}
                                        className="bg-zinc-800 text-white text-sm rounded-lg px-3 py-2 border border-zinc-600 focus:border-indigo-500 focus:outline-none" placeholder="名稱" />
                                    <input value={editForm.source} onChange={e => setEditForm({ ...editForm, source: e.target.value })}
                                        className="bg-zinc-800 text-white text-sm rounded-lg px-3 py-2 border border-zinc-600 focus:border-indigo-500 focus:outline-none" placeholder="來源" />
                                    <input value={editForm.location} onChange={e => setEditForm({ ...editForm, location: e.target.value })}
                                        className="bg-zinc-800 text-white text-sm rounded-lg px-3 py-2 border border-zinc-600 focus:border-indigo-500 focus:outline-none" placeholder="位置" />
                                </div>
                            ) : (
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-3 mb-1">
                                        <span className="font-semibold text-white text-sm">{cam.name}</span>
                                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase transition-all ${cam.status === 'active' ? 'bg-emerald-500/20 text-emerald-400' :
                                                cam.status === 'connecting' ? 'bg-amber-500/20 text-amber-400 animate-pulse' :
                                                    'bg-zinc-700 text-zinc-400'
                                            }`}>
                                            {cam.status === 'active' ? 'LIVE' : cam.status === 'connecting' ? 'CONNECTING' : 'OFFLINE'}
                                        </span>
                                        {cam.location && <span className="text-xs text-zinc-500">📍 {cam.location}</span>}
                                    </div>
                                    <p className="text-xs text-zinc-500 font-mono truncate">{cam.source}</p>
                                </div>
                            )}
                            <div className="flex items-center gap-2 flex-shrink-0">
                                {editId === cam.id ? (
                                    <>
                                        <button onClick={() => handleEdit(cam.id)} className="p-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-white transition-colors"><Check size={15} /></button>
                                        <button onClick={() => setEditId(null)} className="p-2 bg-zinc-700 hover:bg-zinc-600 rounded-lg text-zinc-300 transition-colors"><X size={15} /></button>
                                    </>
                                ) : (
                                    <>
                                        <button onClick={() => startEdit(cam)} className="p-2 bg-zinc-800 hover:bg-indigo-500/20 rounded-lg text-zinc-400 hover:text-indigo-400 transition-colors"><Edit2 size={15} /></button>
                                        <button onClick={() => setDeleteModal({ show: true, id: cam.id })} className="p-2 bg-zinc-800 hover:bg-rose-500/20 rounded-lg text-zinc-400 hover:text-rose-400 transition-colors"><Trash2 size={15} /></button>
                                    </>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* 刪除確認 Modal */}
            {deleteModal.show && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
                    <div className="bg-zinc-900 border border-zinc-800 rounded-2xl w-full max-w-sm shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
                        <div className="p-6 text-center">
                            <div className="w-16 h-16 bg-rose-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
                                <Trash2 size={24} className="text-rose-500" />
                            </div>
                            <h3 className="text-xl font-bold text-white mb-2">確定要刪除嗎？</h3>
                            <p className="text-zinc-400 text-sm leading-relaxed">
                                刪除後該攝影機的所有相關設定與紀錄將會移除，且此操作無法復原。
                            </p>
                        </div>
                        <div className="flex border-t border-zinc-800">
                            <button
                                onClick={() => setDeleteModal({ show: false, id: null })}
                                className="flex-1 px-4 py-4 text-sm font-medium text-zinc-400 hover:bg-zinc-800 transition-colors"
                            >
                                取消
                            </button>
                            <button
                                onClick={handleDelete}
                                disabled={loading}
                                className="flex-1 px-4 py-4 text-sm font-bold text-rose-500 hover:bg-rose-500/5 transition-colors border-l border-zinc-800 flex items-center justify-center gap-2"
                            >
                                {loading && <div className="w-3 h-3 border-2 border-rose-500/30 border-t-rose-500 rounded-full animate-spin" />}
                                確定刪除
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
