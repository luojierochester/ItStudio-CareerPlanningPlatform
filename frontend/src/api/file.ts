import request from './request';

export const fileApi = {
    /**
     * POST /api/v1/upload/file
     * multipart/form-data: file + type
     */
    upload: (file: File, type: string = 'resume') => {
        const fd = new FormData();
        fd.append('file', file);
        fd.append('type', type);
        return request.post<any, null>('/v1/upload/file', fd, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
    },

    /**
     * GET /api/v1/download/file
     * 以 Blob 方式下载（后端目前为 stub，先占位）
     */
    download: (type: string = 'resume') => {
        return request.get<any, Blob>('/v1/download/file', {
            params: { type },
            responseType: 'blob',
        });
    },
};
