import request from './request';
import type { LoginResponse, ReloginResponse, RegisterPayload, ResetPayload } from './types';

export const authApi = {
    /**
     * POST /api/v1/auth/login
     * 后端 SecurityConfig 使用 exchange.formData 解析，必须以 URL-encoded 表单提交
     */
    login: (data: { username: string; password: string }) => {
        const params = new URLSearchParams();
        params.append('username', data.username);
        params.append('password', data.password);
        return request.post<any, LoginResponse>('/v1/auth/login', params, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        });
    },

    /** GET /api/v1/auth/logout */
    logout: () => request.get('/v1/auth/logout'),

    /** GET /api/v1/auth/ask-code?email=xxx&type=register|reset */
    askCode: (email: string, type: 'register' | 'reset') =>
        request.get('/v1/auth/ask-code', { params: { email, type } }),

    /** POST /api/v1/auth/register */
    register: (data: RegisterPayload) => request.post('/v1/auth/register', data),

    /** POST /api/v1/auth/reset */
    reset: (data: ResetPayload) => request.post('/v1/auth/reset', data),

    /** GET /api/v1/auth/relogin — 刷新 Token */
    relogin: () => request.get<any, ReloginResponse>('/v1/auth/relogin'),
};
