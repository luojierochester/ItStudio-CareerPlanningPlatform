import request from './request';

export const chatApi = {
    /**
     * GET /api/v1/ai-chat/new-chat
     * 后端在 Redis 写入 chat_ticket:$uuid，返回 uuid 用于 WebSocket 握手
     */
    newChat: () => request.get<any, string>('/v1/ai-chat/new-chat'),
};
