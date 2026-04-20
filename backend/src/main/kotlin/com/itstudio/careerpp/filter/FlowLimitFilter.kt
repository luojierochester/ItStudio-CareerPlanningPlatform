package com.itstudio.careerpp.filter

import com.itstudio.careerpp.entity.RestBean
import com.itstudio.careerpp.entity.RestBean.Companion.toJsonString
import com.itstudio.careerpp.utils.Const
import org.springframework.beans.factory.annotation.Value
import org.springframework.core.annotation.Order
import org.springframework.data.redis.core.ReactiveStringRedisTemplate
import org.springframework.http.HttpStatus
import org.springframework.http.MediaType
import org.springframework.stereotype.Component
import org.springframework.web.server.ServerWebExchange
import org.springframework.web.server.WebFilter
import org.springframework.web.server.WebFilterChain
import reactor.core.publisher.Mono
import java.time.Duration

@Component
@Order(Const.FLOW_LIMIT_ORDER)
class FlowLimitFilter(
    private val template: ReactiveStringRedisTemplate,

    @param:Value($$"${app.flow-limit.count}")
    private val limitCount: Int,
    @param:Value($$"${app.flow-limit.limit-time}")
    private val limitTime: Int,
    @param:Value($$"${app.flow-limit.ban-time}")
    private val expireTime: Int,
    
) : WebFilter {

    override fun filter(exchange: ServerWebExchange, chain: WebFilterChain): Mono<Void> {
        val address = exchange.request.remoteAddress?.address?.hostAddress ?: "unknown"

        return tryCount(address).flatMap { allowed ->
            if (allowed) {
                chain.filter(exchange)
            } else {
                writeBlockMessage(exchange)
            }
        }
    }

    private fun writeBlockMessage(exchange: ServerWebExchange): Mono<Void> {
        val response = exchange.response
        response.statusCode = HttpStatus.FORBIDDEN
        response.headers.contentType = MediaType.APPLICATION_JSON
        val buffer = response.bufferFactory()
            .wrap(RestBean.forbidden("Too many requests").toJsonString().toByteArray())
        return response.writeWith(Mono.just(buffer))
    }

    private fun tryCount(ip: String): Mono<Boolean> {
        val blockKey = Const.FLOW_LIMIT_BLOCK + ip
        val counterKey = Const.FLOW_LIMIT_COUNTER + ip

        return template.hasKey(blockKey).flatMap { isBlocked ->
            if (isBlocked) {
                Mono.just(false)
            } else {
                template.opsForValue().increment(counterKey).flatMap { count ->
                    if (count == 1L) {
                        template.expire(
                            counterKey,
                            Duration.ofSeconds(limitTime.toLong())
                        ).thenReturn(true)
                    } else if (count > limitCount) {
                        template.opsForValue()
                            .set(
                                blockKey,
                                "1",
                                Duration.ofSeconds(expireTime.toLong())
                            )
                            .thenReturn(false)
                    } else {
                        Mono.just(true)
                    }
                }
            }
        }
    }
}