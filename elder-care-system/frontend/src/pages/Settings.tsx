import { useState, useCallback, useEffect } from 'react';
import api from '../services/api';
import { useTranslation } from '../contexts/I18nContext';
import {
    Settings, Zap, MessageCircle, Camera, Link2, RefreshCw,
    CheckCircle, XCircle, AlertTriangle, ExternalLink, Globe
} from 'lucide-react';

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

export default function SettingsPage() {
    const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);
    const [loading, setLoading] = useState<string | null>(null);
    const [healthResult, setHealthResult] = useState<{ ok: boolean; msg: string } | null>(null);
    const { t, lang, setLang } = useTranslation();

    const showToast = useCallback((message: string, type: 'success' | 'error' | 'info') => setToast({ message, type }), []);

    // Fetch current ngrok URL from backend
    useEffect(() => {
        api.get('/api/test/health').then(() => {
            // Backend is reachable
        }).catch(() => { });
    }, []);

    const runTest = async (key: string, label: string, apiPath: string) => {
        setLoading(key);
        try {
            const r = await api.post(apiPath);
            if (r.data.success) showToast(`✅ ${label} 成功！`, 'success');
            else showToast(`❌ ${label} 失敗`, 'error');
        } catch {
            showToast(`❌ ${label} 請求失敗`, 'error');
        } finally {
            setLoading(null);
        }
    };

    const checkHealth = async () => {
        setLoading('health');
        try {
            const r = await api.get('/api/test/health');
            setHealthResult({ ok: true, msg: r.data.message || 'API 連線正常！' });
            showToast('API 連線正常', 'success');
        } catch {
            setHealthResult({ ok: false, msg: 'API 無法連線' });
            showToast('API 無法連線', 'error');
        } finally {
            setLoading(null);
        }
    };

    const apiBase = (import.meta.env.VITE_API_URL || window.location.origin).replace(/\/$/, '');
    const frontendUrl = window.location.origin;

    // Language Support Hook
    const handleLangChange = (newLang: string) => {
        setLang(newLang as any);
        showToast(newLang === 'en' ? 'Language switched' : '語言已切換', 'success');
    };

    return (
        <div className="p-8 h-full overflow-y-auto w-full max-w-5xl">
            {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}

            <div className="mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-white mb-2 flex items-center gap-3">
                        <Settings size={26} className="text-indigo-400" />
                        {t('settings.title')}
                    </h1>
                    <p className="text-zinc-400">{t('settings.subtitle')}</p>
                </div>

                {/* 語言選單 */}
                <div className="flex items-center gap-3 bg-zinc-900 border border-zinc-700 px-4 py-2.5 rounded-xl">
                    <Globe size={18} className="text-zinc-400" />
                    <span className="text-sm text-zinc-300 font-medium">{t('settings.lang')}</span>
                    <select
                        value={lang}
                        onChange={(e) => handleLangChange(e.target.value)}
                        className="bg-zinc-800 text-sm text-white rounded-lg px-3 py-1.5 border border-zinc-700 focus:outline-none focus:border-indigo-500"
                    >
                        <option value="zh-TW">中文 (繁體)</option>
                        <option value="en">English (US)</option>
                    </select>
                </div>
            </div>

            {/* 公開分享網址 */}
            <div className="mb-6 rounded-xl bg-zinc-900 border border-zinc-800 p-6">
                <h2 className="text-base font-semibold text-white flex items-center gap-2 mb-4">
                    <Link2 size={18} className="text-indigo-400" />
                    公開分享網址（給同學使用）
                </h2>
                <div className="space-y-3">
                    <div className="rounded-lg bg-zinc-800 p-4">
                        <div className="text-xs text-zinc-400 mb-1">🖥️ 前端介面網址</div>
                        <div className="flex items-center gap-3">
                            <code className="text-indigo-300 text-sm flex-1 truncate">{frontendUrl}</code>
                            <a href={frontendUrl} target="_blank" rel="noopener noreferrer"
                                className="p-1.5 rounded bg-zinc-700 hover:bg-zinc-600 text-zinc-400 hover:text-white transition-colors">
                                <ExternalLink size={14} />
                            </a>
                        </div>
                    </div>
                    <div className="rounded-lg bg-zinc-800 p-4">
                        <div className="text-xs text-zinc-400 mb-1">🔌 後端 API 網址</div>
                        <div className="flex items-center gap-3">
                            <code className="text-emerald-300 text-sm flex-1 truncate">{apiBase}</code>
                            <a href={`${apiBase}/docs`} target="_blank" rel="noopener noreferrer"
                                className="p-1.5 rounded bg-zinc-700 hover:bg-zinc-600 text-zinc-400 hover:text-white transition-colors">
                                <ExternalLink size={14} />
                            </a>
                        </div>
                    </div>
                    <div className="rounded-lg bg-amber-500/10 border border-amber-500/20 p-4">
                        <div className="text-xs text-amber-400 mb-2 font-medium">📡 Ngrok 公開分享</div>
                        <p className="text-xs text-zinc-400 mb-3">
                            若要讓同學從外部網路訪問，請啟動 ngrok 並設定以下環境變數：
                        </p>
                        <code className="text-xs text-zinc-300 bg-zinc-900 px-3 py-2 rounded block">
                            NGROK_URL=https://xxxx.ngrok-free.app
                        </code>
                        <p className="text-xs text-zinc-500 mt-2">
                            設定後，LINE 通知的截圖連結也會自動使用此公開網址。
                        </p>
                    </div>
                </div>
            </div>

            {/* 系統測試控制台 */}
            <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-6">
                <h2 className="text-base font-semibold text-white flex items-center gap-2 mb-4">
                    <Zap size={18} className="text-yellow-400" />
                    系統測試控制台
                </h2>
                <p className="text-xs text-zinc-500 mb-5">
                    以下按鈕可測試各項系統功能是否正常運作，測試資料會記錄於資料庫中。
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {/* API 健康檢查 */}
                    <div className="rounded-xl bg-zinc-800 border border-zinc-700 p-5">
                        <div className="flex items-center justify-between mb-3">
                            <div>
                                <div className="text-sm font-medium text-white flex items-center gap-2">
                                    <RefreshCw size={16} className="text-blue-400" />
                                    API 連線檢查
                                </div>
                                <div className="text-xs text-zinc-500 mt-0.5">測試後端 API 是否可連線</div>
                            </div>
                            {healthResult && (
                                healthResult.ok
                                    ? <CheckCircle size={18} className="text-emerald-400 flex-shrink-0" />
                                    : <XCircle size={18} className="text-rose-400 flex-shrink-0" />
                            )}
                        </div>
                        {healthResult && (
                            <div className={`text-xs rounded px-3 py-1.5 mb-3 ${healthResult.ok ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'}`}>
                                {healthResult.msg}
                            </div>
                        )}
                        <button onClick={checkHealth} disabled={loading === 'health'}
                            className="w-full px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm font-medium transition-colors flex items-center justify-center gap-2">
                            {loading === 'health' && <div className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
                            {loading === 'health' ? '測試中...' : '立即檢查'}
                        </button>
                    </div>

                    {/* LINE 推播測試 */}
                    <div className="rounded-xl bg-zinc-800 border border-zinc-700 p-5">
                        <div className="mb-3">
                            <div className="text-sm font-medium text-white flex items-center gap-2">
                                <MessageCircle size={16} className="text-green-400" />
                                LINE 推播測試
                            </div>
                            <div className="text-xs text-zinc-500 mt-0.5">發送一則測試 LINE 訊息</div>
                        </div>
                        <button onClick={() => runTest('line', 'LINE 推播', '/api/test/line')} disabled={loading === 'line'}
                            className="w-full px-4 py-2 rounded-lg bg-green-600 hover:bg-green-500 disabled:opacity-50 text-white text-sm font-medium transition-colors flex items-center justify-center gap-2">
                            {loading === 'line' && <div className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
                            {loading === 'line' ? '傳送中...' : '傳送測試訊息'}
                        </button>
                    </div>

                    {/* 跌倒事件測試 */}
                    <div className="rounded-xl bg-zinc-800 border border-zinc-700 p-5">
                        <div className="mb-3">
                            <div className="text-sm font-medium text-white flex items-center gap-2">
                                <AlertTriangle size={16} className="text-rose-400" />
                                模擬跌倒事件
                            </div>
                            <div className="text-xs text-zinc-500 mt-0.5">建立一筆跌倒異常紀錄並 LINE 通知</div>
                        </div>
                        <button onClick={() => runTest('fall', '跌倒事件', '/api/test/fall')} disabled={loading === 'fall'}
                            className="w-full px-4 py-2 rounded-lg bg-rose-700 hover:bg-rose-600 disabled:opacity-50 text-white text-sm font-medium transition-colors flex items-center justify-center gap-2">
                            {loading === 'fall' && <div className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
                            {loading === 'fall' ? '建立中...' : '模擬跌倒事件'}
                        </button>
                    </div>

                    {/* 截圖測試 */}
                    <div className="rounded-xl bg-zinc-800 border border-zinc-700 p-5">
                        <div className="mb-3">
                            <div className="text-sm font-medium text-white flex items-center gap-2">
                                <Camera size={16} className="text-purple-400" />
                                模擬截圖事件
                            </div>
                            <div className="text-xs text-zinc-500 mt-0.5">截圖目前畫面並 LINE 傳送</div>
                        </div>
                        <button onClick={() => runTest('snapshot', '截圖事件', '/api/test/snapshot')} disabled={loading === 'snapshot'}
                            className="w-full px-4 py-2 rounded-lg bg-purple-700 hover:bg-purple-600 disabled:opacity-50 text-white text-sm font-medium transition-colors flex items-center justify-center gap-2">
                            {loading === 'snapshot' && <div className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
                            {loading === 'snapshot' ? '截圖中...' : '截圖並傳送 LINE'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
