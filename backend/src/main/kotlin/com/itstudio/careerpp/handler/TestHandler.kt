package com.itstudio.careerpp.handler

import org.springframework.stereotype.Component
import org.springframework.web.reactive.socket.WebSocketHandler
import org.springframework.web.reactive.socket.WebSocketSession
import reactor.core.publisher.Mono


@Component
class TestHandler : WebSocketHandler {
    override fun handle(session: WebSocketSession): Mono<Void> {
        // ws://localhost:8080/ws/test
        val output = session.receive()
            .map { msg ->
                val userText = msg.payloadAsText
                session.textMessage("Kotlin springboot4 received: $userText")
            }
        
        return session.send(output)
    }
}
