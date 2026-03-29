package com.itstudio.careerpp.utils

import jakarta.annotation.Resource
import org.springframework.data.redis.core.ReactiveStringRedisTemplate
import org.springframework.stereotype.Component
import reactor.core.publisher.Mono
import java.time.Duration

@Component
class FlowUtils(
    @Resource
    val template: ReactiveStringRedisTemplate
) {

    fun limitOnceCheck(key: String, blockTime: Int): Mono<Boolean> {
        return template.hasKey(key).flatMap { exists ->
            if (exists) {
                Mono.just(false)
            } else {
                template.opsForValue()
                    .set(key, "", Duration.ofSeconds(blockTime.toLong()))
                    .thenReturn(true)
            }
        }
    }
}