/* ===== 通用响应包装 ===== */
export interface RestBean<T> {
    code: number;
    message: string;
    data: T;
}

/* ===== Auth 模块 ===== */
export interface LoginResponse {
    username: string;
    role: string;
    token: string;
    expire: string;
}

export interface ReloginResponse {
    token: string;
    expire: string;
}

export interface RegisterPayload {
    email: string;
    code: string;
    username: string;
    password: string;
}

export interface ResetPayload {
    email: string;
    code: string;
    password: string;
}

/* ===== AI Chat 模块 ===== */
export interface NewChatResponse {
    uuid: string;
}

/* ===== Chat 消息 ===== */
export interface ChatMessage {
    role: 'user' | 'ai';
    content: string;
    /** 正在流式接收中 */
    streaming?: boolean;
}

/* ===== Dashboard ===== */
export interface DashboardData {
    score: number;
    rank: string;
    radar: { dimension: string; value: number }[];
}

/* ===== AI 雷达维度评分（后端 7 字段 JSON） ===== */
export interface RadarScore {
    professionalSkill: number;
    projectExperience: number;
    communication: number;
    stressResistance: number;
    learningAbility: number;
    innovation: number;
    totalScore: number;
}

/* ===== 岗位详情弹窗数据 ===== */
export interface JobDetailData {
    jobTitle: string;
    location: Record<string, number>;
    workHours: string;
    scoring: {
        skills: string[];
        certRequirements: string[];
        internScore: number;
        communicationScore: number;
        stressScore: number;
        learningScore: number;
        innovationScore: number;
        totalScore: number;
    };
    salary: string;
}

/* ===== 岗位匹配 ===== */
export interface MatchedJob {
    id: string | number;
    title: string;
    company?: string;
    matchRate: string;
    sim?: number;
    tags: string[];
    explanation?: {
        matchedSkills: string[];
        missingSkills: string[];
        reasons: string[];
        strengths: string[];
        suggestions: string[];
    };
}

/* ===== 简历解析 ===== */
export interface ResumeDetail {
    name: string;
    targetRole: string;
    education: string;
    skills: string[];
    projects: { title: string; desc: string }[];
}
