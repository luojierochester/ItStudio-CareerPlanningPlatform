package com.itstudio.careerpp.handler.v1

import com.itstudio.careerpp.utils.Const
import org.slf4j.LoggerFactory
import org.springframework.beans.factory.annotation.Value
import org.springframework.data.redis.core.ReactiveStringRedisTemplate
import org.springframework.stereotype.Component
import org.springframework.web.reactive.socket.CloseStatus
import org.springframework.web.reactive.socket.WebSocketHandler
import org.springframework.web.reactive.socket.WebSocketSession
import org.springframework.web.reactive.socket.client.ReactorNettyWebSocketClient
import org.springframework.web.util.UriComponentsBuilder
import reactor.core.publisher.Mono
import java.net.URI

@Component
class AiChatHandler(
    private val redisTemplate: ReactiveStringRedisTemplate,
    @Value("\${app.ai-chat.url:ws://localhost:8002}")
    private val aiChatUrl: String
) : WebSocketHandler {
    private val logger = LoggerFactory.getLogger(this::class.java)
    private val wsClient = ReactorNettyWebSocketClient()

    override fun handle(session: WebSocketSession): Mono<Void> {
        val queryParams = UriComponentsBuilder
            .fromUri(session.handshakeInfo.uri)
            .build()
            .queryParams
        val uuid = queryParams.getFirst("uuid") ?: ""
        val hasFile = queryParams.getFirst("has_file") ?: "false"
        val userId = queryParams.getFirst("user_id") ?: ""

        return redisTemplate.opsForValue()
            .getAndDelete("${Const.WS_CHAT_TICKET}$uuid")
            .switchIfEmpty(
                Mono
                    .defer { session.close(CloseStatus.POLICY_VIOLATION) }
                    .then(Mono.empty())
            )
            .flatMap { _ ->
                val aiUri = URI("$aiChatUrl/ws/v1/ai-chat?uuid=$uuid&has_file=$hasFile&user_id=$userId")
                logger.info("Proxying WebSocket to AI service: $aiUri")

                wsClient.execute(aiUri) { aiSession ->
                    val forward = aiSession.send(
                        session.receive().map { aiSession.textMessage(it.payloadAsText) }
                    )
                    val backward = session.send(
                        aiSession.receive().map { session.textMessage(it.payloadAsText) }
                    )
                    Mono.zip(forward, backward).then()
                }.onErrorResume { e ->
                    logger.error("Failed to connect to AI service: ${e.message}")
                    session.send(
                        Mono.just(session.textMessage("AI 服务暂时不可用，请稍后再试。"))
                    ).then(session.close(CloseStatus.SERVER_ERROR))
                }
            }
    }
}