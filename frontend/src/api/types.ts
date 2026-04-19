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
