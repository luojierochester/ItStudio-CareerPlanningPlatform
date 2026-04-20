import { useCallback, useEffect, useRef, useState } from 'react';
import type { ChatMessage } from '../api/types';
import { chatApi } from '../api/chat';
import { getAccountIdFromToken } from '../utils/jwt';

/* ---------- 常量 ---------- */
// 开发环境走 Vite proxy（当前 host），生产环境直连后端 WS 地址
const WS_BASE = import.meta.env.PROD
    ? import.meta.env.VITE_WS_BASE_URL
    : `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}`;
const HEARTBEAT_INTERVAL = 30_000; // 30 s
const RECONNECT_BASE_DELAY = 2_000; // 首次重连延迟
const MAX_RECONNECT_DELAY = 30_000;
const MAX_RECONNECT_ATTEMPTS = 10;

export interface UseAiChatReturn {
    /** 完整的对话消息列表 */
    messages: ChatMessage[];
    /** 发送一条用户消息 */
    sendMessage: (text: string) => void;
    /** WebSocket 连接状态 */
    status: 'idle' | 'connecting' | 'connected' | 'disconnected';
    /** 手动断开连接 */
    disconnect: () => void;
    /** 手动(重新)连接 */
    connect: (hasFile?: boolean) => void;
}

export function useAiChat(): UseAiChatReturn {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [status, setStatus] = useState<'idle' | 'connecting' | 'connected' | 'disconnected'>('idle');

    const wsRef = useRef<WebSocket | null>(null);
    const heartbeatTimer = useRef<ReturnType<typeof setInterval> | null>(null);
    const reconnectAttempts = useRef(0);
    const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
    /** 标记是否由用户主动断开（主动断开不重连） */
    const intentionalClose = useRef(false);
    /** 保存 hasFile 状态用于重连 */
    const hasFileRef = useRef(false);

    /* ----- 心跳 ----- */
    const startHeartbeat = useCallback(() => {
        stopHeartbeat();
        heartbeatTimer.current = setInterval(() => {
            if (wsRef.current?.readyState === WebSocket.OPEN) {
                wsRef.current.send(JSON.stringify({ type: 'ping' }));
            }
        }, HEARTBEAT_INTERVAL);
    }, []);

    const stopHeartbeat = useCallback(() => {
        if (heartbeatTimer.current) {
            clearInterval(heartbeatTimer.current);
            heartbeatTimer.current = null;
        }
    }, []);

    /* ----- 核心连接 ----- */
    const connectWs = useCallback(async (hasFile: boolean = false) => {
        // 如果已经在连接或已连接，直接返回
        if (wsRef.current && wsRef.current.readyState <= WebSocket.OPEN) return;

        setStatus('connecting');
        intentionalClose.current = false;
        hasFileRef.current = hasFile;

        let uuid: string;
        try {
            // 后端 GET /api/v1/ai-chat/new-chat 返回 uuid（当前为 stub，可能为空）
            const res = await chatApi.newChat();
            uuid = typeof res === 'string' ? res : (res as any)?.uuid ?? '';
        } catch {
            // 后端未就绪时降级：使用随机 uuid（WS 会被后端拒绝，但不阻断 UI 流程）
            uuid = crypto.randomUUID();
        }

        // 获取用户 ID
        const userId = getAccountIdFromToken();
        console.log('👤 用户 ID:', userId);

        // 构建 WebSocket URL
        let wsUrl = `${WS_BASE}/ws/v1/ai-chat?uuid=${encodeURIComponent(uuid)}`;
        wsUrl += `&has_file=${hasFile}`;
        if (userId !== null) {
            wsUrl += `&user_id=${userId}`;
        } else {
            console.warn('⚠️ 未获取到用户 ID，可能未登录或 token 无效');
        }
        console.log('🔗 WebSocket URL:', wsUrl);

        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
            setStatus('connected');
            reconnectAttempts.current = 0;
            startHeartbeat();
        };

        ws.onmessage = (ev) => {
            const text: string = typeof ev.data === 'string' ? ev.data : '';
            if (!text || text === 'pong') return;

            setMessages((prev) => {
                const last = prev[prev.length - 1];
                // 如果上一条是正在流式接收的 AI 消息，继续拼接
                if (last && last.role === 'ai' && last.streaming) {
                    const updated = [...prev];
                    updated[updated.length - 1] = {
                        ...last,
                        content: last.content + text,
                    };
                    return updated;
                }
                // 新开一条 AI 流式消息
                return [...prev, { role: 'ai', content: text, streaming: true }];
            });
        };

        ws.onerror = () => {
            // onerror 之后会自动触发 onclose
        };

        ws.onclose = () => {
            stopHeartbeat();
            setStatus('disconnected');

            // 结束最后一条流式消息
            setMessages((prev) => {
                if (prev.length === 0) return prev;
                const last = prev[prev.length - 1];
                if (last.streaming) {
                    const updated = [...prev];
                    updated[updated.length - 1] = { ...last, streaming: false };
                    return updated;
                }
                return prev;
            });

            // 非主动断开 → 指数退避重连
            if (!intentionalClose.current && reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS) {
                const delay = Math.min(RECONNECT_BASE_DELAY * 2 ** reconnectAttempts.current, MAX_RECONNECT_DELAY);
                reconnectAttempts.current += 1;
                reconnectTimer.current = setTimeout(() => connectWs(hasFileRef.current), delay);
            }
        };
    }, [startHeartbeat, stopHeartbeat]);

    /* ----- 发送消息 ----- */
    const sendMessage = useCallback((text: string) => {
        if (!text.trim()) return;

        // 先把用户消息加入列表
        setMessages((prev) => {
            // 结束上一条未完成的流式 AI 消息（如果有的话）
            const cleaned = prev.map((m) => (m.streaming ? { ...m, streaming: false } : m));
            return [...cleaned, { role: 'user', content: text }];
        });

        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(text);
        } else {
            // WS 未连接时降级 Mock 回复
            setTimeout(() => {
                setMessages((prev) => [
                    ...prev,
                    { role: 'ai', content: '[ 连接已断开 ] 正在重连，请稍后重试…', streaming: false },
                ]);
            }, 300);
            // 尝试重连（使用保存的 hasFile 状态）
            connectWs(hasFileRef.current);
        }
    }, [connectWs]);

    /* ----- 主动断开 ----- */
    const disconnect = useCallback(() => {
        intentionalClose.current = true;
        if (reconnectTimer.current) {
            clearTimeout(reconnectTimer.current);
            reconnectTimer.current = null;
        }
        stopHeartbeat();
        wsRef.current?.close();
        wsRef.current = null;
        setStatus('disconnected');
    }, [stopHeartbeat]);

    /* ----- 组件卸载时清理 ----- */
    useEffect(() => {
        return () => {
            intentionalClose.current = true;
            if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
            stopHeartbeat();
            wsRef.current?.close();
        };
    }, [stopHeartbeat]);

    return {
        messages,
        sendMessage,
        status,
        disconnect,
        connect: connectWs,
    };
}
