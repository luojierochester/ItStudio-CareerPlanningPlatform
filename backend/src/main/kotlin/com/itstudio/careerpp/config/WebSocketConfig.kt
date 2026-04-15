package com.itstudio.careerpp.config

import com.itstudio.careerpp.handler.TestHandler
import com.itstudio.careerpp.handler.v1.AiChatHandler
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.web.reactive.HandlerMapping
import org.springframework.web.reactive.handler.SimpleUrlHandlerMapping
import org.springframework.web.reactive.socket.server.support.WebSocketHandlerAdapter

@Configuration
class WebSocketConfig(
    private val aiChatHandler: AiChatHandler,
    private val testHandler: TestHandler
) {
    @Bean
    fun handlerMapping(): HandlerMapping {
        val map = mapOf(
            "/ws/v1/ai-chat" to aiChatHandler,
            "/ws/test" to testHandler
        )
        val mapping = SimpleUrlHandlerMapping()
        mapping.urlMap = map
        mapping.order = 1
        return mapping
    }

    @Bean
    fun handlerAdapter(): WebSocketHandlerAdapter =
        WebSocketHandlerAdapter()
}