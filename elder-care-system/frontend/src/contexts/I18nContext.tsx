import React, { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';

type Language = 'zh-TW' | 'en';

type Translations = {
    [key in Language]: Record<string, string>;
};

// ========================
// 字典定義
// ========================
const translations: Translations = {
    'zh-TW': {
        // 共用 & 側邊欄
        'app.title': '高齡長照視覺監控系統',
        'nav.dashboard': '即時監控',
        'nav.elders': '長者管理',
        'nav.cameras': '鏡頭管理',
        'nav.logs': '異常事件',
        'nav.settings': '系統設定',
        'nav.logout': '登出系統',

        // 首頁
        'dashboard.title': '即時監控總覽',
        'dashboard.subtitle': '查看各區域攝影機即時畫面與異常事件',
        'dashboard.main_cam': '主畫面：',
        'dashboard.click_zoom': '🔍 點擊放大',
        'dashboard.active_res': '已登記長者人數',
        'dashboard.high_sev': '嚴重異常事件 (L3)',
        'dashboard.timeline': '異常事件時間軸',
        'dashboard.live_up': '即時更新中',
        'dashboard.no_events': '近期無任何異常事件。',
        'dashboard.resident': '相關人員：',

        // 長者管理
        'elders.title': '長者管理',
        'elders.subtitle': '共 {count} 位長者已登記',
        'elders.add': '新增長者',
        'elders.cancel': '取消',
        'elders.form_title': '新增長者資料',
        'elders.name': '姓名 *',
        'elders.name_ph': '例：王大明',
        'elders.room': '房號',
        'elders.room_ph': '例：101',
        'elders.photo': '正面臉部照片（用於識別）',
        'elders.upload': '點擊上傳照片（JPG/PNG）',
        'elders.submit': '確認登記',
        'elders.processing': '處理中...',
        'elders.del_confirm': '確認刪除',
        'elders.del_desc': '確定要刪除長者「{name}」？此操作無法復原，所有相關記錄也會一併刪除。',
        'elders.deleting': '刪除中...',
        'elders.empty': '尚未登記任何長者，點擊「新增長者」開始。',
        'elders.face_ready': '臉部識別已就緒',
        'elders.face_none': '未設定臉部資料',
        'elders.del_btn': '刪除長者',

        // 設定頁
        'settings.title': '系統設定',
        'settings.subtitle': '系統控制台、測試工具、分享網址與偏好',
        'settings.lang': '介面語言',
        'settings.test_api': 'API 連線檢查',
        'settings.test_line': 'LINE 推播測試',
        'settings.test_fall': '模擬跌倒事件',
        'settings.test_snapshot': '模擬截圖事件',
        'settings.public_url': '公開分享網址（給同學使用）',

        // 攝影機
        'cameras.title': '鏡頭管理',
        'cameras.subtitle': '新增、設定或刪除 IP 攝影機來源',
        'cameras.add': '新增鏡頭',
        'cameras.name': '名稱',
        'cameras.source': '來源',
        'cameras.location': '位置',
        'cameras.reconnect': '重新連線',
        'cameras.edit': '編輯設定',
        'cameras.delete': '移出鏡頭',
        'cameras.live': '正在連線',
        'cameras.connecting': '連線中',
        'cameras.offline': '離線',

        // ==================
        // 異常事件 (Logs)
        // ==================
        'logs.title': '異常事件記錄',
        'logs.pending': '待處理：',
        'logs.count': '筆',
        'logs.show_resolved': '顯示已處理事件',
        'logs.search': '搜尋事件描述...',
        'logs.all_levels': '全部層級',
        'logs.empty': '目前沒有符合條件的事件',
        'logs.resolved': '已處理',
        'logs.mark_resolved': '標註已處理',
        'logs.update_fail': '更新狀態失敗',

        // ==================
        // 長者詳情 (ElderDetail)
        // ==================
        'detail.loading': '載入長者詳情中...',
        'detail.not_found': '找不到該長者',
        'detail.back_list': '返回列表',
        'detail.back_name': '返回長者名單',

        'detail.edit_title': '修改長者資料',
        'detail.line_id': '家屬 LINE User ID',
        'detail.saving': '儲存中...',
        'detail.save_btn': '儲存變更',
        'detail.save_fail': '儲存失敗，請重試',
        'detail.fetch_fail': '無法載入資料，請稍後再試。',

        'detail.face_ready': '臉部辨識已就緒',
        'detail.face_none': '尚未設定臉部',
        'detail.edit_btn': '修改資料',

        'detail.lbl_room': '房號',
        'detail.lbl_reg_date': '登記日期',
        'detail.lbl_sys_id': '系統 ID',
        'detail.lbl_line': 'LINE ID',
        'detail.val_empty': '未填寫',
        'detail.val_unset': '未設定',

        'detail.photo_title_ready': '更換臉部識別照片',
        'detail.photo_title_none': '⚠️ 尚未設定臉部識別照片',
        'detail.photo_desc_ready': '已設定，可重新上傳以更新。',
        'detail.photo_desc_none': '請上傳正面清晰照片以啟用 AI 辨識。',
        'detail.photo_uploading': '上傳中...',
        'detail.photo_reupload': '重新上傳',
        'detail.photo_upload': '上傳照片',
        'detail.photo_success': '臉部照片更新成功！',
        'detail.photo_fail': '上傳失敗，請換一張清晰的正面照片',

        'detail.trend_title': '活動趨勢',
        'detail.view_daily': '📅 日視圖',
        'detail.view_weekly': '📆 週視圖',
        'detail.view_monthly': '🗓️ 月視圖',
        'detail.trend_empty': '目前尚無活動數據',
        'detail.trend_empty_desc': '系統將在辨識到長者後開始記錄',
        'detail.walk_min': '走路 (分)',
        'detail.sit_min': '坐著 (分)',

        'detail.recent_title': '最近行為紀錄',
        'detail.recent_empty': '尚無一般活動記錄',
        'detail.recent_doing': '正在',
        'detail.recent_interact': '與',
        'detail.recent_interact_end': '互動',

        'detail.history_title': '異常事件歷史',
        'detail.history_empty': '一切正常，無異常記錄',

        // 雜項
        'misc.success': '成功',
        'misc.error': '失敗',
        'misc.cancel': '取消',
        'misc.confirm': '確認',
        'misc.loading': '載入中...',
    },
    'en': {
        // Common & Sidebar
        'app.title': 'Elder Care Vision Monitor',
        'nav.dashboard': 'Live View',
        'nav.elders': 'Elders',
        'nav.cameras': 'Cameras',
        'nav.logs': 'Events',
        'nav.settings': 'Settings',
        'nav.logout': 'Logout',

        // Dashboard
        'dashboard.title': 'Live Monitoring Overview',
        'dashboard.subtitle': 'Monitor real-time feeds and anomalies across zones',
        'dashboard.main_cam': 'Main View:',
        'dashboard.click_zoom': '🔍 Click to Zoom',
        'dashboard.active_res': 'Registered Residents',
        'dashboard.high_sev': 'High Severity Anomalies (L3)',
        'dashboard.timeline': 'Event Timeline',
        'dashboard.live_up': 'Live Updates',
        'dashboard.no_events': 'No recent events.',
        'dashboard.resident': 'Resident:',

        // Elders
        'elders.title': 'Elder Management',
        'elders.subtitle': 'Total {count} elders registered',
        'elders.add': 'Add Elder',
        'elders.cancel': 'Cancel',
        'elders.form_title': 'Register New Elder',
        'elders.name': 'Name *',
        'elders.name_ph': 'e.g., John Doe',
        'elders.room': 'Room',
        'elders.room_ph': 'e.g., 101',
        'elders.photo': 'Frontal Face Photo (For ID)',
        'elders.upload': 'Click to upload (JPG/PNG)',
        'elders.submit': 'Register',
        'elders.processing': 'Processing...',
        'elders.del_confirm': 'Confirm Deletion',
        'elders.del_desc': 'Are you sure you want to delete elder "{name}"? This action cannot be undone, and all related records will be removed.',
        'elders.deleting': 'Deleting...',
        'elders.empty': 'No elders registered yet. Click "Add Elder" to start.',
        'elders.face_ready': 'Face ID Ready',
        'elders.face_none': 'No Face Data',
        'elders.del_btn': 'Delete Elder',

        // Settings
        'settings.title': 'System Settings',
        'settings.subtitle': 'Console, test tools, sharing URLs and preferences',
        'settings.lang': 'Interface Language',
        'settings.test_api': 'API Health Check',
        'settings.test_line': 'LINE Notification Test',
        'settings.test_fall': 'Simulate Fall Event',
        'settings.test_snapshot': 'Simulate Snapshot Event',
        'settings.public_url': 'Public Share URLs',

        // Cameras
        'cameras.title': 'Camera Management',
        'cameras.subtitle': 'Add, configure, or remove IP camera sources',
        'cameras.add': 'Add Camera',
        'cameras.name': 'Name',
        'cameras.source': 'Source',
        'cameras.location': 'Location',
        'cameras.reconnect': 'Reconnect',
        'cameras.edit': 'Edit',
        'cameras.delete': 'Remove',
        'cameras.live': 'LIVE',
        'cameras.connecting': 'CONNECTING',
        'cameras.offline': 'OFFLINE',

        // ==================
        // Events (Logs)
        // ==================
        'logs.title': 'Event Logs',
        'logs.pending': 'Pending: ',
        'logs.count': '',
        'logs.show_resolved': 'Show Resolved Events',
        'logs.search': 'Search event descriptions...',
        'logs.all_levels': 'All Levels',
        'logs.empty': 'No events match the criteria.',
        'logs.resolved': 'Resolved',
        'logs.mark_resolved': 'Mark as Resolved',
        'logs.update_fail': 'Failed to update status',

        // ==================
        // Elder Detail
        // ==================
        'detail.loading': 'Loading resident profile...',
        'detail.not_found': 'Resident not found',
        'detail.back_list': 'Back to List',
        'detail.back_name': 'Back to Residents',

        'detail.edit_title': 'Edit Profile',
        'detail.line_id': 'Family LINE User ID',
        'detail.saving': 'Saving...',
        'detail.save_btn': 'Save Changes',
        'detail.save_fail': 'Save failed, please try again',
        'detail.fetch_fail': 'Failed to load data, please try again later.',

        'detail.face_ready': 'Face ID Ready',
        'detail.face_none': 'No Face Configured',
        'detail.edit_btn': 'Edit Info',

        'detail.lbl_room': 'Room',
        'detail.lbl_reg_date': 'Reg Date',
        'detail.lbl_sys_id': 'System ID',
        'detail.lbl_line': 'LINE ID',
        'detail.val_empty': 'Empty',
        'detail.val_unset': 'Not Set',

        'detail.photo_title_ready': 'Change Face ID Photo',
        'detail.photo_title_none': '⚠️ No Face ID Photo Set',
        'detail.photo_desc_ready': 'Configured. Upload a new photo to update.',
        'detail.photo_desc_none': 'Upload a front-facing, clear photo to enable AI recognition.',
        'detail.photo_uploading': 'Uploading...',
        'detail.photo_reupload': 'Re-upload',
        'detail.photo_upload': 'Upload Photo',
        'detail.photo_success': 'Face photo updated successfully!',
        'detail.photo_fail': 'Upload failed, please try a clearer front-facing photo',

        'detail.trend_title': 'Activity Trends',
        'detail.view_daily': '📅 Daily',
        'detail.view_weekly': '📆 Weekly',
        'detail.view_monthly': '🗓️ Monthly',
        'detail.trend_empty': 'No activity data yet',
        'detail.trend_empty_desc': 'The system will record data once the resident is recognized.',
        'detail.walk_min': 'Walking (m)',
        'detail.sit_min': 'Sitting (m)',

        'detail.recent_title': 'Recent Behaviors',
        'detail.recent_empty': 'No general activities recorded.',
        'detail.recent_doing': '',
        'detail.recent_interact': 'interacted with',
        'detail.recent_interact_end': '',

        'detail.history_title': 'Abnormality History',
        'detail.history_empty': 'All good, no anomalies recorded.',

        // Misc
        'misc.success': 'Success',
        'misc.error': 'Error',
        'misc.cancel': 'Cancel',
        'misc.confirm': 'Confirm',
        'misc.loading': 'Loading...',
    }
};

// ========================
// Context Provider
// ========================
interface I18nContextProps {
    lang: Language;
    setLang: (lang: Language) => void;
    t: (key: string, fallback?: string) => string;
}

const I18nContext = createContext<I18nContextProps | undefined>(undefined);

export const I18nProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [lang, setLangState] = useState<Language>(
        (localStorage.getItem('appLang') as Language) || 'zh-TW'
    );

    const setLang = (newLang: Language) => {
        setLangState(newLang);
        localStorage.setItem('appLang', newLang);
    };

    const t = (key: string, fallback?: string): string => {
        return translations[lang][key] || fallback || key;
    };

    return (
        <I18nContext.Provider value={{ lang, setLang, t }}>
            {children}
        </I18nContext.Provider>
    );
};

export const useTranslation = () => {
    const context = useContext(I18nContext);
    if (context === undefined) {
        throw new Error('useTranslation must be used within an I18nProvider');
    }
    return context;
};
