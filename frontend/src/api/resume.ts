import request from './request';
import type { ResumeDetail, DashboardData, MatchedJob } from './types';

export const resumeApi = {
    /**
     * POST /api/v1/resume/upload
     * 上传简历（PDF/Word）并获取结构化解析结果
     */
    uploadAndParse: (file: File) => {
        const fd = new FormData();
        fd.append('file', file);
        return request.post<any, ResumeDetail>('/v1/resume/upload', fd, {
            headers: { 'Content-Type': 'multipart/form-data' },
            timeout: 30000,
        });
    },

    /** GET /api/v1/resume/profile — 获取已解析的简历数据 */
    getProfile: () => request.get<any, ResumeDetail>('/v1/resume/profile'),

    /** GET /api/v1/resume/dashboard — 获取六维能力看板 */
    getDashboard: () => request.get<any, DashboardData>('/v1/resume/dashboard'),

    /** GET /api/v1/resume/recommend — 获取岗位推荐列表 */
    getRecommendations: (topn: number = 10) =>
        request.get<any, MatchedJob[]>('/v1/resume/recommend', { params: { topn } }),
};
