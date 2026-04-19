/**
 * 防御性 Mock 模块
 * 当后端尚未实现对应接口时，由前端提供高保真异步假数据，
 * 保证 UI 可以完整闭环跑通。
 */
import type { DashboardData, MatchedJob, ResumeDetail } from './types';

/** 模拟网络延迟 */
const delay = (ms: number = 600) => new Promise<void>((r) => setTimeout(r, ms));

/**
 * Mock: 全景解析舱 Dashboard 数据
 * 后端尚无 /v1/dashboard 或类似接口
 */
export async function fetchDashboard(): Promise<DashboardData> {
    await delay();
    return {
        score: 95,
        rank: '超越 92% 竞争者',
        radar: [
            { dimension: '专业技能', value: 92 },
            { dimension: '项目经验', value: 85 },
            { dimension: '竞赛成果', value: 78 },
            { dimension: '实习经历', value: 60 },
            { dimension: '沟通表达', value: 88 },
            { dimension: '抗压能力', value: 75 },
        ],
    };
}

/**
 * Mock: AI 匹配岗位列表
 * 后端尚无岗位推荐读取接口（algorithm 模块独立部署）
 */
export async function fetchMatchedJobs(): Promise<MatchedJob[]> {
    await delay(800);
    return [
        { id: 1, title: 'AI 大模型研究员', company: '百度 (Baidu)', matchRate: '98%', tags: ['算法', 'Python', 'PyTorch'] },
        { id: 2, title: '全栈开发工程师', company: '字节跳动 (ByteDance)', matchRate: '91%', tags: ['React', 'Spring', 'TypeScript'] },
        { id: 3, title: '数据分析师', company: '美团 (Meituan)', matchRate: '87%', tags: ['SQL', 'Python', 'Tableau'] },
        { id: 4, title: '后端开发工程师', company: '阿里巴巴 (Alibaba)', matchRate: '85%', tags: ['Java', 'Spring Boot', 'MySQL'] },
        { id: 5, title: '产品经理', company: '腾讯 (Tencent)', matchRate: '79%', tags: ['Axure', '用户调研', '数据分析'] },
        { id: 6, title: '前端开发工程师', company: '网易 (NetEase)', matchRate: '76%', tags: ['React', 'Vue', 'Node.js'] },
    ];
}

/**
 * Mock: 简历解析结果
 * 后端文件上传接口仅保存文件到磁盘，不返回解析后的简历结构化数据
 */
export async function fetchResumeDetail(): Promise<ResumeDetail> {
    await delay(1200);
    return {
        name: '张三',
        targetRole: 'AI 算法工程师',
        education: '某 985 高校 · 计算机科学与技术 · 本科 2024 届',
        skills: ['Python', 'PyTorch', 'React', 'Spring Boot', 'MySQL', 'Docker', 'Git'],
        projects: [
            { title: '基于大模型的智能简历评估系统', desc: '使用 LLM + RAG 技术对简历进行语义分析与评分，准确率提升 23%。' },
            { title: '校园招聘数据可视化平台', desc: '基于 React + ECharts 构建全栈数据看板，日均 PV 2000+。' },
        ],
    };
}
