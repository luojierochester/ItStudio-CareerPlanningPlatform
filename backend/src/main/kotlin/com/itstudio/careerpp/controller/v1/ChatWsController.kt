package com.itstudio.careerpp.controller.v1

import com.itstudio.careerpp.entity.RestBean
import com.itstudio.careerpp.utils.Const
import org.slf4j.LoggerFactory
import org.springframework.data.redis.core.ReactiveStringRedisTemplate
import org.springframework.http.HttpHeaders
import org.springframework.validation.annotation.Validated
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RestController
import org.springframework.web.server.ServerWebExchange
import reactor.core.publisher.Mono
import java.time.Duration
import java.util.*

@Validated
@RestController
@RequestMapping("/api/v1/ai-chat")
class ChatWsController(
    private val redisTemplate: ReactiveStringRedisTemplate
) {
    private val logger = LoggerFactory.getLogger(this::class.java)

    @GetMapping("/new-chat")
    fun newWsChat(
        exchange: ServerWebExchange
    ): Mono<RestBean<Any?>> {
        val header = exchange.request.headers.getFirst(HttpHeaders.AUTHORIZATION)
        logger.info("Creating new chat session from $header")
        val uuid = UUID.randomUUID().toString()
        return redisTemplate.opsForValue()
            .set("${Const.WS_CHAT_TICKET}$uuid", "valid", Duration.ofMinutes(5))
            .then(Mono.just(RestBean.success<Any?>(uuid)))
    }
}