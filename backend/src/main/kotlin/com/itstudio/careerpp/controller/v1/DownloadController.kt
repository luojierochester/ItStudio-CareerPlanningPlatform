package com.itstudio.careerpp.controller.v1

import com.itstudio.careerpp.entity.RestBean
import org.slf4j.LoggerFactory
import org.springframework.http.HttpHeaders
import org.springframework.validation.annotation.Validated
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RestController
import org.springframework.web.server.ServerWebExchange
import reactor.core.publisher.Mono

@Validated
@RestController
@RequestMapping("/api/v1/download")
class DownloadController(

) {
    private val logger = LoggerFactory.getLogger(this::class.java)

    @GetMapping("/file")
    fun downloadFile(
        exchange: ServerWebExchange
    ): Mono<RestBean<Any?>> {
        val header = exchange.request.headers.getFirst(HttpHeaders.AUTHORIZATION)
        logger.info("Downloading file from $header")
        return RestBean.just(Mono.just(""))
    }
}