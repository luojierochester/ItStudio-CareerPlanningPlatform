import React, { useState } from 'react';
import { Outlet, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { authApi } from '../api/auto';

const AppLayout: React.FC = () => {
    const [aiInput, setAiInput] = useState('');
    const [isThinking, setIsThinking] = useState(false);
    const location = useLocation();
    const navigate = useNavigate();

    // 从本地存储读取用户名，判断是否登录
    const savedUsername = localStorage.getItem('username');

    const triggerAI = () => {
        if (!aiInput.trim()) return;
        setIsThinking(true);
        setTimeout(() => {
            setIsThinking(false);
            setAiInput('');
        }, 2000);
    };

    return (
        <div className="glass-app-layout">

            <div className="ui-layer">
                {/* 加上 flex 布局，为了把用户信息挤到最底部 */}
                <aside className="glass-sidebar" style={{ display: 'flex', flexDirection: 'column' }}>

                    {/* === 上半部分：Logo 和 菜单 === */}
                    <div>
                        <div className="brand-logo">
                            <div className="logo-glow"></div>
                            <span className="logo-title text-gradient">雪雪职业AI</span>
                        </div>
                        <nav className="nav-menu">
                            <NavLink to="/" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} end>
                                <i className="icon">⎔</i><span>简历智算中心</span>
                            </NavLink>
                            <NavLink to="/panorama" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                                <i className="icon">⊚</i><span>全景解析舱</span>
                            </NavLink>
                        </nav>
                    </div>

                    {/* === 下半部分：用户卡片 / 登录入口 === */}
                    <div style={{ marginTop: 'auto', paddingTop: '24px', borderTop: '1px solid rgba(255,255,255,0.5)' }}>
                        {savedUsername ? (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '8px' }}>
                                <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: 'linear-gradient(135deg, #0ea5e9, #6366f1)', color: 'white', display: 'flex', justifyContent: 'center', alignItems: 'center', fontWeight: 800 }}>
                                    {savedUsername.charAt(0).toUpperCase()}
                                </div>
                                <div>
                                    <div style={{ fontSize: '14px', fontWeight: 700, color: '#1e293b' }}>{savedUsername}</div>
                                    <div
                                        style={{ fontSize: '12px', color: '#64748b', cursor: 'pointer', marginTop: '2px' }}
                                        onClick={async () => {
                                            try { await authApi.logout(); } catch { /* ignore */ }
                                            localStorage.removeItem('token');
                                            localStorage.removeItem('username');
                                            localStorage.removeItem('role');
                                            navigate('/login');
                                        }}
                                    >
                                        退出登录
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <button
                                onClick={() => navigate('/login')}
                                style={{ width: '100%', padding: '12px', borderRadius: '12px', border: '1px solid #0ea5e9', background: 'transparent', color: '#0ea5e9', fontWeight: 700, cursor: 'pointer' }}
                            >
                                前往登录
                            </button>
                        )}
                    </div>

                </aside>

                <main className="glass-main">
                    <Outlet />
                </main>
            </div>

            {/* 只有在非简历中心才显示底部全局对话框 */}
            {location.pathname !== '/' && (
                <div className="ai-omnibar-container">
                    <div className={`ai-omnibar ${isThinking ? 'thinking' : ''}`}>
                        <i className="ai-icon">✨</i>
                        <input
                            type="text"
                            value={aiInput}
                            onChange={(e) => setAiInput(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && triggerAI()}
                            placeholder="输入指令，例如：生成产品经理换岗路径..."
                        />
                        <button className="ai-send-btn" onClick={triggerAI}>↵ Enter</button>
                    </div>
                    <div className="omnibar-glow"></div>
                </div>
            )}
        </div>
    );
};

export default AppLayout;