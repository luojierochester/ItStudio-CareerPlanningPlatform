package com.itstudio.careerpp.service

import com.baomidou.mybatisplus.extension.service.IService
import com.itstudio.careerpp.entity.dto.Account
import org.springframework.security.core.userdetails.ReactiveUserDetailsService
import reactor.core.publisher.Mono

interface AccountService : IService<Account>, ReactiveUserDetailsService {
    fun findAccountByNameOrEmail(text: String): Mono<Account>
    fun findAccountByName(username: String): Mono<Account>
    fun findAccountByEmail(email: String): Mono<Account>
    fun existAccountByName(username: String): Mono<Boolean>
    fun existAccountByEmail(email: String): Mono<Boolean>
    fun resetPasswordByEmail(email: String, encodedPassword: String): Mono<String>
}