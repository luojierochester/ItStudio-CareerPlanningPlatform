import axios from 'axios';

// 1. 创建 Axios 实例
// 开发环境走 Vite proxy（相对路径 /api），生产环境直连后端真实地址
const isProd = import.meta.env.PROD;
const request = axios.create({
    baseURL: isProd ? `${import.meta.env.VITE_API_BASE_URL}/api` : '/api',
    timeout: 10000,
});

// 2. 请求拦截器：自动携带 Token
request.interceptors.request.use(
    (config) => {
        // 从本地存储拿 token
        const token = localStorage.getItem('token');
        // 如果有 token，就放到请求头里（完全符合 api.md 的 Bearer 规范）
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// 3. 响应拦截器：自动解包与全局报错
request.interceptors.response.use(
    (response) => {
        // 文件下载（blob）响应直接返回
        if (response.config.responseType === 'blob') {
            return response.data;
        }

        // 拦截部分不守规矩的特殊接口 (如你文档里提到的 /test)
        if (response.config.url?.includes('/test/')) {
            return response.data;
        }

        const res = response.data;

        // 核心：根据文档，code 为 200 才是成功
        if (res.code === 200) {
            // 直接把真实的 data 扔给组件，剥离外层包装
            return res.data;
        } else {
            // 业务报错（比如密码错误），可以在这里接 UI 库的 Toast 提示
            console.error('业务报错:', res.message);
            return Promise.reject(new Error(res.message || '请求失败'));
        }
    },
    (error) => {
        // HTTP 状态码报错处理 (比如 401 Token 过期)
        if (error.response?.status === 401) {
            console.error('身份验证失败，请重新登录');
            localStorage.removeItem('token');
            localStorage.removeItem('username');
            localStorage.removeItem('role');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

export default request;