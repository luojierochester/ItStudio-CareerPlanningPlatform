package com.itstudio.careerpp.handler.v1

import com.itstudio.careerpp.utils.Const
import org.springframework.data.redis.core.ReactiveStringRedisTemplate
import org.springframework.stereotype.Component
import org.springframework.web.reactive.socket.CloseStatus
import org.springframework.web.reactive.socket.WebSocketHandler
import org.springframework.web.reactive.socket.WebSocketSession
import org.springframework.web.util.UriComponentsBuilder
import reactor.core.publisher.Mono

@Component
class AiChatHandler(
    private val redisTemplate: ReactiveStringRedisTemplate
) : WebSocketHandler {
    override fun handle(session: WebSocketSession): Mono<Void> {
        // ws://localhost:8080/ws/v1/ai-chat?uuid=****
        val queryParams = UriComponentsBuilder
            .fromUri(session.handshakeInfo.uri)
            .build()
            .queryParams
        val uuid = queryParams.getFirst("uuid")
        return redisTemplate.opsForValue()
            .getAndDelete("${Const.WS_CHAT_TICKET}$uuid")
            .switchIfEmpty(
                Mono
                    .defer { session.close(CloseStatus.POLICY_VIOLATION) }
                    .then(Mono.empty())
            )
            .flatMap { _ ->
                val output = session.receive()
                    .map { msg ->
                        val userText = msg.payloadAsText
                        session.textMessage("AI 响应: $userText 的处理结果")
                    }
                session.send(output)
            }
    }
}