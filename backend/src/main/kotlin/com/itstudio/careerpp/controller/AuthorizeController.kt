package com.itstudio.careerpp.controller

import com.itstudio.careerpp.entity.RestBean
import com.itstudio.careerpp.entity.vo.request.EmailRegisterVO
import com.itstudio.careerpp.entity.vo.request.PasswordResetVO
import com.itstudio.careerpp.service.AccountService
import jakarta.validation.Valid
import jakarta.validation.constraints.Email
import jakarta.validation.constraints.NotBlank
import jakarta.validation.constraints.Pattern
import org.slf4j.LoggerFactory
import org.springframework.validation.annotation.Validated
import org.springframework.web.bind.annotation.*
import org.springframework.web.server.ServerWebExchange
import reactor.core.publisher.Mono

@Validated
@RestController
@RequestMapping("/api/auth")
class AuthorizeController(
    private val service: AccountService
) {
    private val logger = LoggerFactory.getLogger(this::class.java)

    @GetMapping("/ask-code")
    fun askVerifyCode(
        @RequestParam @NotBlank @Email email: String,
        @RequestParam @Pattern(regexp = "(register|reset)") type: String,
        exchange: ServerWebExchange
    ): Mono<RestBean<Any?>> {
        logger.info("Trying to ask code")
        val ip = exchange.request.remoteAddress?.address?.hostAddress ?: "unknown"
        return service.askEmailVerifyCode(type, email, ip)
            .map { messageHandler(it) }
    }

    @PostMapping("/register")
    fun emailRegister(@RequestBody @Valid vo: EmailRegisterVO): Mono<RestBean<Any?>> {
        logger.info("Trying to register")
        return service.registerEmailAccount(vo)
            .map { messageHandler(it) }
    }

    @PostMapping("/reset")
    fun emailResetPassword(@RequestBody @Valid vo: PasswordResetVO): Mono<RestBean<Any?>> {
        logger.info("Trying to reset password")
        return service.resetEmailAccountPassword(vo)
            .map { messageHandler(it) }
    }

    @GetMapping("/logout")
    fun logout(exchange: ServerWebExchange): Mono<RestBean<Any?>> {
        logger.info("Trying to logout")
        val authorization = exchange.request.headers.getFirst("Authorization")
        return Mono.fromCallable { service.invalidateJwt(authorization) }
            .map { success ->
                if (success) RestBean.success()
                else RestBean.logoutFailed()
            }
    }

    private fun messageHandler(wrongMessage: String): RestBean<Any?> {
        return if (wrongMessage.isBlank()) {
            RestBean.success()
        } else {
            RestBean.failure(400, null, wrongMessage)
        }
    }
}