import { useState } from 'react';
import { Outlet, Navigate, useNavigate, NavLink } from 'react-router-dom';
import { ShieldCheck, Video, Users, Activity, LogOut, Settings, Camera, Menu, X } from 'lucide-react';

export default function Layout() {
    const navigate = useNavigate();
    const token = localStorage.getItem('token');
    const [sidebarOpen, setSidebarOpen] = useState(true);

    if (!token) {
        return <Navigate to="/login" replace />;
    }

    const handleLogout = () => {
        localStorage.removeItem('token');
        navigate('/login');
    };

    const navItem = (to: string, Icon: any, label: string) => (
        <NavLink to={to} end={to === '/'}
            className={({ isActive }) =>
                `flex items-center px-3 py-2.5 rounded-lg transition-all duration-200 group ${isActive
                    ? 'bg-indigo-500/10 text-indigo-400 font-medium'
                    : 'text-zinc-400 hover:bg-zinc-800/50 hover:text-white'
                } ${!sidebarOpen ? 'justify-center' : ''}`
            }
            title={!sidebarOpen ? label : undefined}
        >
            <Icon className={`flex-shrink-0 transition-all duration-200 ${sidebarOpen ? 'mr-3' : ''}`} size={20} />
            <span className={`transition-all duration-200 overflow-hidden whitespace-nowrap ${sidebarOpen ? 'opacity-100 max-w-xs' : 'opacity-0 max-w-0'}`}>
                {label}
            </span>
        </NavLink>
    );

    return (
        <div className="flex h-screen overflow-hidden bg-zinc-950 text-white">
            {/* 側邊欄 */}
            <aside className={`flex-shrink-0 border-r border-zinc-800 bg-zinc-900/50 flex flex-col transition-all duration-300 ease-in-out overflow-hidden ${sidebarOpen ? 'w-56' : 'w-14'}`}>
                {/* 頂部 Logo + 漢堡按鈕 */}
                <div className="flex h-16 items-center border-b border-zinc-800 bg-zinc-950 px-3 gap-2">
                    <button
                        onClick={() => setSidebarOpen(!sidebarOpen)}
                        className="p-2 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors flex-shrink-0"
                        title={sidebarOpen ? '收合選單' : '展開選單'}
                    >
                        {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
                    </button>
                    <div className={`flex items-center gap-2 overflow-hidden transition-all duration-200 ${sidebarOpen ? 'opacity-100 max-w-xs' : 'opacity-0 max-w-0'}`}>
                        <ShieldCheck className="text-indigo-500 flex-shrink-0" size={22} />
                        <span className="text-sm font-bold tracking-tight leading-tight whitespace-nowrap">長照視覺監控系統</span>
                    </div>
                </div>

                <nav className="flex-1 overflow-y-auto py-4 px-2 space-y-1">
                    {navItem('/', Video, '即時監控')}
                    {navItem('/elders', Users, '長者管理')}
                    {navItem('/logs', Activity, '異常記錄')}
                    {navItem('/cameras', Camera, '鏡頭管理')}
                    {navItem('/settings', Settings, '系統設定')}
                </nav>

                <div className="p-2 border-t border-zinc-800 bg-zinc-950">
                    <button
                        onClick={handleLogout}
                        className={`flex w-full items-center px-3 py-2.5 rounded-lg text-zinc-400 hover:bg-red-500/10 hover:text-red-400 transition-colors ${!sidebarOpen ? 'justify-center' : ''}`}
                        title={!sidebarOpen ? '登出' : undefined}
                    >
                        <LogOut className={`flex-shrink-0 ${sidebarOpen ? 'mr-3' : ''}`} size={20} />
                        <span className={`transition-all duration-200 overflow-hidden whitespace-nowrap ${sidebarOpen ? 'opacity-100 max-w-xs' : 'opacity-0 max-w-0'}`}>
                            登出
                        </span>
                    </button>
                </div>
            </aside>

            {/* 主內容 */}
            <main className="flex-1 overflow-y-auto min-w-0">
                <Outlet />
            </main>
        </div>
    );
}
