import React, { useState, useEffect, useRef, useCallback } from 'react';

/* ===== 常量 ===== */
const LS_KEY = 'global-config';

const FONT_OPTIONS = [
    { value: "'Segoe UI', 'Microsoft YaHei', sans-serif", label: 'UI Sans-serif (现代无衬线)' },
    { value: "Helvetica, Arial, sans-serif", label: 'Helvetica (经典纯净)' },
    { value: "'Times New Roman', Times, serif", label: 'Times New Roman (衬线阅读)' },
    { value: "'Courier New', Courier, monospace", label: 'Courier Code (极客等宽)' },
];

interface Config {
    darkMode: boolean;
    accentColor: string;
    fontFamily: string;
    language: 'zh' | 'en';
}

const DEFAULT_CONFIG: Config = {
    darkMode: false,
    accentColor: '#0ea5e9',
    fontFamily: FONT_OPTIONS[0].value,
    language: 'zh',
};

/* ===== 读写 localStorage ===== */
function loadConfig(): Config {
    try {
        const raw = localStorage.getItem(LS_KEY);
        if (raw) return { ...DEFAULT_CONFIG, ...JSON.parse(raw) };
    } catch { /* ignore */ }
    return { ...DEFAULT_CONFIG };
}

function saveConfig(cfg: Config) {
    localStorage.setItem(LS_KEY, JSON.stringify(cfg));
}

/* ===== 注入全局 CSS 变量 & body class ===== */
function applyConfig(cfg: Config) {
    const root = document.documentElement;
    root.style.setProperty('--primary-color', cfg.accentColor);
    root.style.setProperty('--font-family', cfg.fontFamily);
    document.body.style.fontFamily = cfg.fontFamily;
    document.body.classList.toggle('dark-mode', cfg.darkMode);
    document.body.classList.toggle('light-mode', !cfg.darkMode);
}

/* ===== 组件 ===== */
const GlobalConfigFab: React.FC = () => {
    const [open, setOpen] = useState(false);
    const [config, setConfig] = useState<Config>(loadConfig);
    const wrapperRef = useRef<HTMLDivElement>(null);

    // 挂载时立即应用
    useEffect(() => { applyConfig(config); }, []);

    // 状态变化 → 持久化 + 注入
    const update = useCallback((patch: Partial<Config>) => {
        setConfig(prev => {
            const next = { ...prev, ...patch };
            saveConfig(next);
            applyConfig(next);
            if (patch.language) {
                console.log(`[GlobalConfig] Language switched to: ${next.language}`);
            }
            return next;
        });
    }, []);

    // 点击外部关闭面板
    useEffect(() => {
        const handler = (e: MouseEvent) => {
            if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
                setOpen(false);
            }
        };
        document.addEventListener('mousedown', handler);
        return () => document.removeEventListener('mousedown', handler);
    }, []);

    return (
        <div className="gcf-wrapper" ref={wrapperRef}>
            {/* ===== FAB 按钮 ===== */}
            <button
                className={`gcf-fab ${open ? 'gcf-fab--open' : ''}`}
                title="设置 / Settings"
                onClick={() => setOpen(v => !v)}
            >
                <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" strokeWidth="2" fill="none">
                    <circle cx="12" cy="12" r="3" />
                    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
                </svg>
            </button>

            {/* ===== 设置面板 ===== */}
            {open && (
                <div className="gcf-panel">
                    <h3 className="gcf-title">
                        {config.language === 'zh' ? '系统级 UI 定制' : 'System UI Config'}
                    </h3>

                    {/* 语言 */}
                    <div className="gcf-item">
                        <label className="gcf-label">🌐 {config.language === 'zh' ? '界面语言 (Language)' : 'Language (语言)'}</label>
                        <select
                            className="gcf-select"
                            value={config.language}
                            onChange={e => update({ language: e.target.value as 'zh' | 'en' })}
                        >
                            <option value="zh">🇨🇳 简体中文 (Chinese)</option>
                            <option value="en">🇺🇸 English (英文)</option>
                        </select>
                    </div>

                    {/* 深浅色模式 */}
                    <div className="gcf-item">
                        <label className="gcf-label">
                            {config.language === 'zh' ? '视觉引擎模式' : 'Visual Engine Mode'}
                        </label>
                        <div className="gcf-theme-switch" onClick={() => update({ darkMode: !config.darkMode })}>
                            <div className={`gcf-switch-bg ${config.darkMode ? '' : 'is-light'}`} />
                            <span className={`gcf-switch-label ${config.darkMode ? 'active' : ''}`}>🌙 {config.language === 'zh' ? '极客暗黑' : 'Dark'}</span>
                            <span className={`gcf-switch-label ${config.darkMode ? '' : 'active'}`}>☀️ {config.language === 'zh' ? '护眼明亮' : 'Light'}</span>
                        </div>
                    </div>

                    {/* 高亮色 */}
                    <div className="gcf-item">
                        <label className="gcf-label">
                            {config.language === 'zh' ? '神经突触高亮色' : 'Accent Color'}
                        </label>
                        <input
                            type="color"
                            className="gcf-color"
                            value={config.accentColor}
                            onChange={e => update({ accentColor: e.target.value })}
                        />
                    </div>

                    {/* 字体 */}
                    <div className="gcf-item">
                        <label className="gcf-label">
                            {config.language === 'zh' ? '全局渲染字体族' : 'Font Family'}
                        </label>
                        <select
                            className="gcf-select"
                            value={config.fontFamily}
                            onChange={e => update({ fontFamily: e.target.value })}
                        >
                            {FONT_OPTIONS.map(f => (
                                <option key={f.value} value={f.value}>{f.label}</option>
                            ))}
                        </select>
                    </div>
                </div>
            )}
        </div>
    );
};

export default GlobalConfigFab;
