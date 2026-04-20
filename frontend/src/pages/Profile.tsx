import React, { useEffect, useRef, useState } from 'react';
import { resumeApi } from '../api/resume';
import { fetchResumeDetail } from '../api/mock';
import { useAiChat } from '../hooks/useAiChat';
import type { ResumeDetail } from '../api/types';

const ACCEPTED_TYPES = '.pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document';

const Profile: React.FC = () => {
    const [currentStatus, setCurrentStatus] = useState<'upload' | 'parsing' | 'ready'>('upload');
    const [chatInput, setChatInput] = useState('');
    const [uploadError, setUploadError] = useState('');
    const fileInputRef = useRef<HTMLInputElement>(null);
    const chatEndRef = useRef<HTMLDivElement>(null);

    const [resumeData, setResumeData] = useState<ResumeDetail | null>(null);

    // ===== 核心：接入 useAiChat Hook =====
    const { messages, sendMessage, status, connect } = useAiChat();

    // 自动滚动到底部
    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleUpload = async (file: File) => {
        setUploadError('');
        setCurrentStatus('parsing');
        try {
            // 真实接口：上传并解析简历（后端提取文本 + 结构化解析）
            let parsed: ResumeDetail | null = null;
            try {
                parsed = await resumeApi.uploadAndParse(file);
            } catch {
                // 后端解析失败时 Mock 降级
                parsed = await fetchResumeDetail();
            }
            setResumeData(parsed);

            // 建立 WebSocket 连接（有简历）
            connect(true);

            setCurrentStatus('ready');
        } catch (e: any) {
            setUploadError(e.message || '上传失败，请稍后重试');
            setCurrentStatus('upload');
        }
    };

    const onFileSelected = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        e.target.value = '';
        handleUpload(file);
    };

    const handleSend = () => {
        if (!chatInput.trim()) return;
        sendMessage(chatInput);
        setChatInput('');
    };

    // 跳过上传，直接进入 AI 引导模式
    const skipToReady = () => {
        connect(false);
        setCurrentStatus('ready');
    };

    // WebSocket 连接状态标签
    const statusLabel: Record<string, string> = {
        idle: '未连接',
        connecting: '连接中…',
        connected: '已连接',
        disconnected: '已断开',
    };
    const statusColor: Record<string, string> = {
        idle: '#64748b',
        connecting: '#f59e0b',
        connected: '#10b981',
        disconnected: '#ef4444',
    };

    return (
        <div className="parser-workspace">

            {currentStatus === 'upload' && (
                <div className="upload-center glass-panel">
                    <div className="upload-icon">📄</div>
                    <h2>上传你的简历原件</h2>
                    <p>支持 PDF / Word 格式，或者直接跳过让 AI 从零开始引导你创建</p>
                    {uploadError && (
                        <p style={{ color: '#ef4444', fontSize: '14px', margin: '8px 0 0 0' }}>{uploadError}</p>
                    )}
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept={ACCEPTED_TYPES}
                        style={{ display: 'none' }}
                        onChange={onFileSelected}
                    />
                    <div className="action-buttons">
                        <button className="btn-primary" onClick={() => fileInputRef.current?.click()}>选择 PDF/Word 上传</button>
                        <button className="btn-outline" onClick={skipToReady}>没有简历？AI 帮我写</button>
                    </div>
                </div>
            )}

            {currentStatus === 'parsing' && (
                <div className="parsing-center glass-panel">
                    <div className="loader"></div>
                    <h3>AI 正在解构你的生涯轨迹...</h3>
                    <p className="text-muted">正在进行语义抽取与能力量化</p>
                </div>
            )}

            {currentStatus === 'ready' && (
                <div className="workspace-split">

                    <div className="left-preview glass-panel">
                        <div className="panel-header">
                            <span className="title">全息简历模型</span>
                            <span className="status-tag">实时同步中</span>
                        </div>

                        <div className="resume-paper">
                            {resumeData ? (
                                <>
                                    <header className="resume-head">
                                        <h1>{resumeData.name}</h1>
                                        <p className="target-role">意向岗位：{resumeData.targetRole}</p>
                                        <p className="text-muted">{resumeData.education}</p>
                                    </header>

                                    <section className="resume-section">
                                        <h3>核心技能矩阵</h3>
                                        <div className="skill-tags">
                                            {resumeData.skills.map(skill => (
                                                <span key={skill} className="skill-tag">{skill}</span>
                                            ))}
                                            <button className="add-skill-btn">+ AI 挖掘更多</button>
                                        </div>
                                    </section>

                                    <section className="resume-section">
                                        <h3>项目实战经历</h3>
                                        {resumeData.projects.map((proj, idx) => (
                                            <div key={idx} className="project-item highlight-warn">
                                                <div className="proj-head">
                                                    <h4>{proj.title}</h4>
                                                    <button className="ai-fix-btn">✨ AI 润色</button>
                                                </div>
                                                <p className="proj-desc">{proj.desc}</p>
                                            </div>
                                        ))}
                                    </section>
                                </>
                            ) : (
                                <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>
                                    <p>暂无简历数据，请先上传简历或让 AI 引导你创建</p>
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="right-copilot glass-panel">
                        <div className="panel-header">
                            <span className="title"><i className="ai-icon">✨</i> 简历辅导引擎</span>
                            <span style={{
                                fontSize: '12px',
                                fontWeight: 600,
                                color: statusColor[status],
                                background: `${statusColor[status]}18`,
                                padding: '4px 10px',
                                borderRadius: '12px',
                            }}>
                                {statusLabel[status]}
                            </span>
                        </div>

                        <div className="chat-flow">
                            {messages.length === 0 && (
                                <div className="chat-bubble ai-bubble">
                                    <div className="avatar">🤖</div>
                                    <div className="message-content">你好！我是你的 AI 简历辅导助手。有什么需要帮你优化的吗？✨</div>
                                </div>
                            )}
                            {messages.map((msg, index) => (
                                <div key={index} className={`chat-bubble ${msg.role === 'ai' ? 'ai-bubble' : 'user-bubble'}`}>
                                    <div className="avatar">{msg.role === 'ai' ? '🤖' : '🧑‍🎓'}</div>
                                    <div className="message-content">
                                        {msg.content}
                                        {msg.streaming && <span className="typing-cursor">▍</span>}
                                    </div>
                                </div>
                            ))}
                            <div ref={chatEndRef} />
                        </div>

                        <div className="chat-input-area">
                            <input
                                type="text"
                                value={chatInput}
                                onChange={(e) => setChatInput(e.target.value)}
                                onKeyDown={(e) => { if (e.key === 'Enter') handleSend(); }}
                                placeholder="告诉 AI 你的想法，比如：'我在学生会做过外联'..."
                            />
                            <button className="send-btn" onClick={handleSend}>发送</button>
                        </div>
                    </div>

                </div>
            )}
        </div>
    );
};

export default Profile;