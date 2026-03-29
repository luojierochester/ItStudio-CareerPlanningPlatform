package com.itstudio.careerpp.controller

import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RestController
import reactor.core.publisher.Mono

@RestController
@RequestMapping("/api/test")
class TestController {

    @GetMapping("/hello")
    fun test(): Mono<String> = Mono.just("Hello Kotlin WebFlux!")
}