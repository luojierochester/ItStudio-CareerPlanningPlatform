import React, { useEffect, useRef, useState } from 'react';
import * as echarts from 'echarts';
import { resumeApi } from '../api/resume';
import { fetchDashboard, fetchMatchedJobs } from '../api/mock';
import type { DashboardData, MatchedJob } from '../api/types';

const Home: React.FC = () => {
    const [dashboard, setDashboard] = useState<DashboardData | null>(null);
    const [jobs, setJobs] = useState<MatchedJob[]>([]);
    const [loading, setLoading] = useState(true);
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
                // 后端未启动或未上传简历时降级到 Mock
                [d, j] = await Promise.all([fetchDashboard(), fetchMatchedJobs()]);
            }
            if (cancelled) return;
            setDashboard(d);
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

    // 组件卸载时销毁 chart
    useEffect(() => {
        return () => { chartInstance.current?.dispose(); };
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
                {/* 竞争力评分卡 */}
                <div className="glass-panel" style={{ padding: '24px' }}>
                    <h3 style={{ margin: '0 0 20px 0', color: '#1e293b' }}>全息竞争力</h3>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '12px' }}>
                        <span className="text-gradient" style={{ fontSize: '64px', fontWeight: 900, lineHeight: 1 }}>{dashboard?.score}</span>
                        <span style={{ fontSize: '14px', fontWeight: 700, color: '#64748b' }}>INDEX</span>
                    </div>
                    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '13px', fontWeight: 700, color: '#10b981', background: '#ecfdf5', padding: '4px 10px', borderRadius: '12px' }}>
                        ↗ {dashboard?.rank}
                    </div>
                </div>

                {/* 六维雷达图 */}
                <div className="glass-panel" style={{ padding: '24px', gridColumn: 'span 2', display: 'flex', flexDirection: 'column' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
                        <h3 style={{ margin: 0, color: '#1e293b' }}>六维能力拓扑图</h3>
                        <span style={{ padding: '4px 10px', background: 'rgba(14,165,233,0.1)', color: '#0ea5e9', borderRadius: '8px', fontSize: '12px', fontWeight: 700 }}>AI 分析</span>
                    </div>
                    <div ref={radarRef} style={{ flex: 1, minHeight: '260px' }} />
                </div>

                {/* AI 匹配岗位列表 */}
                <div className="glass-panel" style={{ padding: '24px', gridColumn: 'span 3' }}>
                    <h3 style={{ margin: '0 0 20px 0', color: '#1e293b' }}>AI 匹配序列</h3>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
                        {jobs.map(job => (
                            <div key={job.id} style={{ padding: '20px', background: '#ffffff', borderRadius: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', border: '1px solid #e2e8f0' }}>
                                <div>
                                    <h4 style={{ margin: '0 0 4px 0', fontSize: '16px', color: '#1e293b' }}>{job.title}</h4>
                                    <p style={{ margin: '0 0 8px 0', fontSize: '13px', color: '#64748b' }}>{job.company || ''}</p>
                                    <div style={{ display: 'flex', gap: '6px' }}>
                                        {job.tags.map(tag => <span key={tag} style={{ padding: '2px 8px', border: '1px solid #cbd5e1', borderRadius: '6px', fontSize: '11px', color: '#64748b' }}>{tag}</span>)}
                                    </div>
                                </div>
                                <span className="text-gradient" style={{ fontSize: '24px', fontWeight: 900 }}>{job.matchRate}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Home;