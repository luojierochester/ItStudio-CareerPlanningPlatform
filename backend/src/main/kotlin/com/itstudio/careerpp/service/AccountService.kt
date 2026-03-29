package com.itstudio.careerpp.service

import com.baomidou.mybatisplus.extension.service.IService
import com.itstudio.careerpp.entity.dto.Account
import com.itstudio.careerpp.entity.vo.request.EmailRegisterVO
import com.itstudio.careerpp.entity.vo.request.PasswordResetVO
import org.springframework.security.core.userdetails.ReactiveUserDetailsService
import reactor.core.publisher.Mono

interface AccountService : IService<Account>, ReactiveUserDetailsService {
    fun findAccountByNameOrEmail(text: String): Mono<Account>
    fun askEmailVerifyCode(type: String, email: String, ip: String): Mono<String>
    fun registerEmailAccount(vo: EmailRegisterVO): Mono<String>
    fun resetEmailAccountPassword(vo: PasswordResetVO): Mono<String>
    fun invalidateJwt(headerToken: String?): Boolean
}