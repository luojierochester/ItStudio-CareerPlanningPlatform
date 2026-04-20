import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as echarts from 'echarts';
import { resumeApi } from '../api/resume';
import { fetchDashboard, fetchMatchedJobs } from '../api/mock';
import type { DashboardData, MatchedJob, RadarScore, JobDetailData } from '../api/types';

/* ===== 维度标签映射 ===== */
const DIMENSION_META: { key: keyof Omit<RadarScore, 'totalScore'>; label: string; icon: string }[] = [
    { key: 'professionalSkill', label: '专业技能', icon: '⚡' },
    { key: 'projectExperience', label: '项目经验', icon: '🚀' },
    { key: 'communication', label: '沟通表达', icon: '💬' },
    { key: 'stressResistance', label: '抗压能力', icon: '🛡️' },
    { key: 'learningAbility', label: '学习能力', icon: '📖' },
    { key: 'innovation', label: '创新能力', icon: '💡' },
];

/** 从 DashboardData.radar 构造 RadarScore（兼容已有后端） */
function toRadarScore(d: DashboardData): RadarScore {
    const map: Record<string, number> = {};
    d.radar.forEach(r => { map[r.dimension] = r.value; });
    return {
        professionalSkill: map['专业技能'] ?? 0,
        projectExperience: map['项目经验'] ?? map['竞赛成果'] ?? 0,
        communication: map['沟通表达'] ?? 0,
        stressResistance: map['抗压能力'] ?? 0,
        learningAbility: map['学习能力'] ?? 70,
        innovation: map['创新能力'] ?? 65,
        totalScore: d.score,
    };
}

/** 从 MatchedJob 构造 Mock 弹窗数据 */
function toJobDetail(job: MatchedJob): JobDetailData {
    return {
        jobTitle: job.title,
        location: { '超一线城市': 30, '一线城市': 30, '二线城市': 33.33, '三线城市': 6.67 },
        workHours: '标准工时制，9:00-18:00，午休 1-1.5 小时，周末双休。部分岗位需接受出差或项目驻场。',
        scoring: {
            skills: job.tags.length > 0 ? job.tags : ['Java', 'JavaScript', 'React'],
            certRequirements: [],
            internScore: 6,
            communicationScore: 8,
            stressScore: 7,
            learningScore: 9,
            innovationScore: 6,
            totalScore: job.sim ? +(job.sim * 10).toFixed(1) : 7.2,
        },
        salary: '实习岗位补贴约 2500-2700 元/月。正式岗位薪资需根据技能、经验、城市及公司规模面议。',
    };
}

/* ===== 进度条子组件 ===== */
const ScoreBar: React.FC<{ label: string; value: number; max?: number }> = ({ label, value, max = 10 }) => {
    const pct = Math.min((value / max) * 100, 100);
    return (
        <div className="jd-score-row">
            <span className="jd-score-label">{label}</span>
            <div className="jd-bar-track">
                <div className="jd-bar-fill" style={{ width: `${pct}%` }} />
            </div>
            <span className="jd-score-value">{value}<span style={{ opacity: 0.5 }}>/{max}</span></span>
        </div>
    );
};

/* ===== 岗位详情弹窗 ===== */
const JobDetailModal: React.FC<{ detail: JobDetailData; onClose: () => void }> = ({ detail, onClose }) => {
    const locationEntries = Object.entries(detail.location).sort((a, b) => b[1] - a[1]);
    const maxLoc = Math.max(...locationEntries.map(e => e[1]), 1);
    const { scoring } = detail;

    return (
        <div className="jd-overlay" onClick={onClose}>
            <div className="jd-modal" onClick={e => e.stopPropagation()}>
                {/* 头部 */}
                <div className="jd-header">
                    <h2 className="jd-title">{detail.jobTitle}</h2>
                    <button className="jd-close" onClick={onClose}>✕</button>
                </div>

                <div className="jd-body">
                    {/* 综合评分 */}
                    <div className="jd-section">
                        <div className="jd-total-badge">
                            <span className="jd-total-num">{scoring.totalScore}</span>
                            <span className="jd-total-label">综合评分</span>
                        </div>
                    </div>

                    {/* 专业技能标签 */}
                    <div className="jd-section">
                        <h4 className="jd-section-title">⚡ 专业技能栈</h4>
                        <div className="jd-tags">
                            {scoring.skills.map(s => <span key={s} className="jd-tag">{s}</span>)}
                        </div>
                    </div>

                    {/* 能力评分 */}
                    <div className="jd-section">
                        <h4 className="jd-section-title">📊 能力维度评分</h4>
                        <ScoreBar label="实习能力" value={scoring.internScore} />
                        <ScoreBar label="沟通能力" value={scoring.communicationScore} />
                        <ScoreBar label="抗压能力" value={scoring.stressScore} />
                        <ScoreBar label="学习能力" value={scoring.learningScore} />
                        <ScoreBar label="创新能力" value={scoring.innovationScore} />
                    </div>

                    {/* 地理分布 */}
                    <div className="jd-section">
                        <h4 className="jd-section-title">📍 岗位地理分布</h4>
                        {locationEntries.map(([city, pct]) => (
                            <div key={city} className="jd-loc-row">
                                <span className="jd-loc-city">{city}</span>
                                <div className="jd-loc-track">
                                    <div className="jd-loc-fill" style={{ width: `${(pct / maxLoc) * 100}%` }} />
                                </div>
                                <span className="jd-loc-pct">{pct}%</span>
                            </div>
                        ))}
                    </div>

                    {/* 工作时间 */}
                    <div className="jd-section">
                        <h4 className="jd-section-title">🕐 工作时间</h4>
                        <p className="jd-text">{detail.workHours}</p>
                    </div>

                    {/* 薪资水平 */}
                    <div className="jd-section">
                        <h4 className="jd-section-title">💰 薪资水平</h4>
                        <p className="jd-text">{detail.salary}</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

/* ===== 主页面 ===== */
const Home: React.FC = () => {
    const [dashboard, setDashboard] = useState<DashboardData | null>(null);
    const [radarScore, setRadarScore] = useState<RadarScore | null>(null);
    const [jobs, setJobs] = useState<MatchedJob[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedJob, setSelectedJob] = useState<JobDetailData | null>(null);
    const radarRef = useRef<HTMLDivElement>(null);
    const chartInstance = useRef<echarts.ECharts | null>(null);

    // 优先真实 API，失败则 Mock 降级
    useEffect(() => {
        let cancelled = false;
        (async () => {
            let d: DashboardData;
            let j: MatchedJob[];
            try {
                [d, j] = await Promise.all([
                    resumeApi.getDashboard(),
                    resumeApi.getRecommendations(6),
                ]);
            } catch {
                [d, j] = await Promise.all([fetchDashboard(), fetchMatchedJobs()]);
            }
            if (cancelled) return;
            setDashboard(d);
            setRadarScore(toRadarScore(d));
            setJobs(j);
            setLoading(false);
        })();
        return () => { cancelled = true; };
    }, []);

    // 渲染 ECharts 雷达图
    useEffect(() => {
        if (!dashboard || !radarRef.current) return;

        if (!chartInstance.current) {
            chartInstance.current = echarts.init(radarRef.current);
        }
        const chart = chartInstance.current;

        chart.setOption({
            radar: {
                indicator: dashboard.radar.map((r) => ({ name: r.dimension, max: 100 })),
                shape: 'polygon',
                splitNumber: 4,
                axisName: { color: '#64748b', fontSize: 12, fontWeight: 600 },
                splitLine: { lineStyle: { color: 'rgba(203,213,225,0.4)' } },
                splitArea: { areaStyle: { color: ['rgba(14,165,233,0.02)', 'rgba(14,165,233,0.05)'] } },
                axisLine: { lineStyle: { color: 'rgba(203,213,225,0.4)' } },
            },
            series: [{
                type: 'radar',
                data: [{
                    value: dashboard.radar.map((r) => r.value),
                    name: '能力值',
                    areaStyle: { color: 'rgba(14,165,233,0.15)' },
                    lineStyle: { color: '#0ea5e9', width: 2 },
                    itemStyle: { color: '#0ea5e9' },
                    symbol: 'circle',
                    symbolSize: 6,
                }],
            }],
        });

        const onResize = () => chart.resize();
        window.addEventListener('resize', onResize);
        return () => {
            window.removeEventListener('resize', onResize);
        };
    }, [dashboard]);

    useEffect(() => {
        return () => { chartInstance.current?.dispose(); };
    }, []);

    const handleJobClick = useCallback((job: MatchedJob) => {
        setSelectedJob(toJobDetail(job));
    }, []);

    if (loading) {
        return (
            <div className="fade-in" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                <div className="loader"></div>
            </div>
        );
    }

    return (
        <div className="fade-in">
            <header style={{ marginBottom: '40px' }}>
                <h1 className="text-gradient" style={{ fontSize: '32px', margin: '0 0 8px 0' }}>欢迎探索你的无限可能</h1>
                <p style={{ color: '#64748b', margin: 0 }}>GLSL 底层引擎正在实时渲染 10,000+ 岗位知识图谱节点</p>
            </header>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px' }}>
                {/* 竞争力评分卡 — 总分 + 六维网格 */}
                <div className="glass-panel" style={{ padding: '24px' }}>
                    <h3 style={{ margin: '0 0 16px 0', color: '#1e293b' }}>全息竞争力</h3>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '16px' }}>
                        <span className="text-gradient" style={{ fontSize: '64px', fontWeight: 900, lineHeight: 1 }}>{radarScore?.totalScore ?? dashboard?.score}</span>
                        <span style={{ fontSize: '14px', fontWeight: 700, color: '#64748b' }}>INDEX</span>
                    </div>
                    {/* 六维数值网格 */}
                    {radarScore && (
                        <div className="radar-grid">
                            {DIMENSION_META.map(dm => (
                                <div key={dm.key} className="radar-grid-item">
                                    <span className="radar-grid-icon">{dm.icon}</span>
                                    <span className="radar-grid-val">{radarScore[dm.key]}</span>
                                    <span className="radar-grid-label">{dm.label}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* 六维雷达图 */}
                <div className="glass-panel" style={{ padding: '24px', gridColumn: 'span 2', display: 'flex', flexDirection: 'column' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
                        <h3 style={{ margin: 0, color: '#1e293b' }}>六维能力拓扑图</h3>
                        <span style={{ padding: '4px 10px', background: 'rgba(14,165,233,0.1)', color: '#0ea5e9', borderRadius: '8px', fontSize: '12px', fontWeight: 700 }}>AI 分析</span>
                    </div>
                    <div ref={radarRef} style={{ flex: 1, minHeight: '260px' }} />
                </div>

                {/* AI 匹配岗位列表 — 可点击 */}
                <div className="glass-panel" style={{ padding: '24px', gridColumn: 'span 3' }}>
                    <h3 style={{ margin: '0 0 20px 0', color: '#1e293b' }}>AI 匹配序列</h3>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
                        {jobs.map(job => (
                            <div
                                key={job.id}
                                className="job-card"
                                onClick={() => handleJobClick(job)}
                            >
                                <div>
                                    <h4 style={{ margin: '0 0 4px 0', fontSize: '16px', color: '#1e293b' }}>{job.title}</h4>
                                    <p style={{ margin: '0 0 8px 0', fontSize: '13px', color: '#64748b' }}>{job.company || ''}</p>
                                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                                        {job.tags.map(tag => <span key={tag} className="job-tag">{tag}</span>)}
                                    </div>
                                </div>
                                <span className="text-gradient" style={{ fontSize: '24px', fontWeight: 900, flexShrink: 0 }}>{job.matchRate}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* 岗位详情弹窗 */}
            {selectedJob && (
                <JobDetailModal detail={selectedJob} onClose={() => setSelectedJob(null)} />
            )}
        </div>
    );
};

export default Home;