package com.itstudio.careerpp.service.impl

import com.baomidou.mybatisplus.core.toolkit.Wrappers
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl
import com.itstudio.careerpp.entity.dto.Account
import com.itstudio.careerpp.entity.vo.request.EmailRegisterVO
import com.itstudio.careerpp.entity.vo.request.PasswordResetVO
import com.itstudio.careerpp.mapper.AccountMapper
import com.itstudio.careerpp.service.AccountService
import com.itstudio.careerpp.utils.Const
import com.itstudio.careerpp.utils.DateUtils.getCurrentDateTime
import com.itstudio.careerpp.utils.FlowUtils
import com.itstudio.careerpp.utils.JwtUtils
import org.springframework.amqp.core.AmqpTemplate
import org.springframework.data.redis.core.ReactiveStringRedisTemplate
import org.springframework.security.core.userdetails.User
import org.springframework.security.core.userdetails.UserDetails
import org.springframework.security.core.userdetails.UsernameNotFoundException
import org.springframework.security.crypto.password.PasswordEncoder
import org.springframework.stereotype.Service
import reactor.core.publisher.Mono
import java.time.Duration

@Service
class AccountServiceImpl(
    private val utils: FlowUtils,
    private val jwtUtils: JwtUtils,
    private val amqpTemplate: AmqpTemplate,
    private val stringRedisTemplate: ReactiveStringRedisTemplate,
    private val encoder: PasswordEncoder

) : ServiceImpl<AccountMapper, Account>(), AccountService {

    override fun findByUsername(username: String): Mono<UserDetails> {
        return findAccountByNameOrEmail(username)
            .switchIfEmpty(Mono.error(UsernameNotFoundException("Account with name $username not found")))
            .map { account ->
                User.withUsername(username)
                    .password(account.password)
                    .roles(account.role)
                    .build()
            }
    }

    override fun findAccountByNameOrEmail(text: String): Mono<Account> {
        return Mono.fromCallable {
            this.query()
                .eq("username", text).or()
                .eq("email", text)
                .one()
        }.flatMap { account ->
            Mono.just(account)
        }
    }

    override fun askEmailVerifyCode(type: String, email: String, ip: String): Mono<String> {
        return verifyLimit(ip).flatMap { allowed ->
            if (allowed) {
                val code = (100000..999999).random().toString()
                val data = mapOf(
                    "type" to type,
                    "email" to email,
                    "code" to code
                )

                Mono.fromRunnable<Void> {
                    amqpTemplate.convertAndSend("mail", data)
                }.then(
                    stringRedisTemplate.opsForValue()
                        .set(
                            Const.VERIFY_EMAIL_DATA + email,
                            code,
                            Duration.ofMinutes(3)
                        )
                ).thenReturn("")
            } else {
                Mono.just("Request limit exceeded. Please try again later.")
            }
        }
    }

    override fun registerEmailAccount(vo: EmailRegisterVO): Mono<String> {
        val (email, code, username, password) = vo

        return verifyCode(email, code).flatMap { error ->
            if (!error.isBlank()) {
                return@flatMap Mono.just(error)
            }

            existAccountByEmail(email).flatMap { emailExists ->
                if (emailExists) {
                    return@flatMap Mono.just("account with the same email already exists.")
                }

                existAccountByUsername(username).flatMap { usernameExists ->
                    if (usernameExists) {
                        return@flatMap Mono.just("username already exists.")
                    }

                    val encodedPassword = encoder.encode(password)
                    val account = Account(
                        null,
                        username,
                        encodedPassword!!,
                        email,
                        "user",
                        getCurrentDateTime()
                    )

                    Mono.fromCallable { this.save(account) }
                        .flatMap { success ->
                            if (success) {
                                stringRedisTemplate.delete(Const.VERIFY_EMAIL_DATA + email)
                                    .thenReturn("")
                            } else {
                                Mono.just("something went wrong. Please contact the administrator.")
                            }
                        }
                }
            }
        }
    }

    override fun resetEmailAccountPassword(vo: PasswordResetVO): Mono<String> {
        val (email, code, password) = vo

        return verifyCode(email, code).flatMap { error ->
            if (!error.isBlank()) {
                return@flatMap Mono.just(error)
            }

            existAccountByEmail(email).flatMap { exists ->
                if (!exists) {
                    return@flatMap Mono.just("account with the email does not exist.")
                }

                val encodedPassword = encoder.encode(password)

                Mono.fromCallable {
                    this.update()
                        .eq("email", email)
                        .set("password", encodedPassword)
                        .update()
                }.flatMap { success ->
                    if (success) {
                        stringRedisTemplate.delete(Const.VERIFY_EMAIL_DATA + email)
                            .thenReturn("")
                    } else {
                        Mono.just("something went wrong. Please contact the administrator.")
                    }
                }
            }
        }
    }

    override fun invalidateJwt(headerToken: String?): Boolean {
        return jwtUtils.invalidateJwt(headerToken)
    }

    private fun existAccountByEmail(email: String): Mono<Boolean> {
        return Mono.fromCallable {
            this.baseMapper.exists(
                Wrappers.query<Account>()
                    .eq("email", email)
            )
        }
    }

    private fun existAccountByUsername(username: String): Mono<Boolean> {
        return Mono.fromCallable {
            this.baseMapper.exists(
                Wrappers.query<Account>()
                    .eq("username", username)
            )
        }
    }

    private fun verifyLimit(ip: String): Mono<Boolean> {
        val key = Const.VERIFY_EMAIL_LIMIT + ip
        return utils.limitOnceCheck(key, 60)
    }

    private fun verifyCode(email: String, receivedCode: String?): Mono<String> {
        return stringRedisTemplate.opsForValue()
            .get(Const.VERIFY_EMAIL_DATA + email)
            .flatMap { code ->
                when {
                    receivedCode == null || code != receivedCode ->
                        Mono.just("verify code is wrong.")

                    else -> Mono.just("")
                }
            }
            .switchIfEmpty(Mono.just("verify code has not been sent"))
    }
}