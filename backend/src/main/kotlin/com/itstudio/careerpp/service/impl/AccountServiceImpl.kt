package com.itstudio.careerpp.service.impl

import com.baomidou.mybatisplus.core.toolkit.Wrappers
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl
import com.itstudio.careerpp.entity.dto.Account
import com.itstudio.careerpp.mapper.AccountMapper
import com.itstudio.careerpp.service.AccountService
import org.slf4j.LoggerFactory
import org.springframework.security.core.userdetails.User
import org.springframework.security.core.userdetails.UserDetails
import org.springframework.security.core.userdetails.UsernameNotFoundException
import org.springframework.stereotype.Service
import reactor.core.publisher.Mono

@Service
class AccountServiceImpl : ServiceImpl<AccountMapper, Account>(), AccountService {

    val logger = LoggerFactory.getLogger(this::class.java)!!

    override fun findByUsername(username: String): Mono<UserDetails> {
        return findAccountByName(username)
            .switchIfEmpty(Mono.error(UsernameNotFoundException("Account with name $username not found")))
            .map { account ->
                User.withUsername(username)
                    .password(account.password)
                    .roles(account.role)
                    .build()
            }
    }

    override fun findAccountByName(username: String): Mono<Account> {
        return Mono.fromCallable {
            logger.info("Find account with name $username")
            this.query()
                .eq("username", username)
                .one()
        }.flatMap { account ->
            Mono.just(account)
        }.switchIfEmpty(Mono.error(UsernameNotFoundException("Account with name $username not found")))
    }

    override fun findAccountByEmail(email: String): Mono<Account> {
        return Mono.fromCallable {
            logger.info("Find account with email $email")
            this.query()
                .eq("email", email)
                .one()
        }.flatMap { account ->
            Mono.just(account)
        }.switchIfEmpty(Mono.error(UsernameNotFoundException("Account with email $email not found")))
    }

    override fun findAccountByNameOrEmail(text: String): Mono<Account> {
        return findAccountByEmail(text)
            .onErrorResume { findAccountByName(text) }
    }

    override fun existAccountByName(username: String): Mono<Boolean> {
        return Mono.fromCallable {
            logger.info("Determine if name $username exists")
            this.baseMapper.exists(
                Wrappers.query<Account>()
                    .eq("username", username)
            )
        }
    }

    override fun existAccountByEmail(email: String): Mono<Boolean> {
        return Mono.fromCallable {
            logger.info("Determine if email $email exists")
            this.baseMapper.exists(
                Wrappers.query<Account>()
                    .eq("email", email)
            )
        }
    }

    override fun resetPasswordByEmail(email: String, encodedPassword: String): Mono<String> {
        return existAccountByEmail(email).flatMap { exists ->
            if (!exists) {
                return@flatMap Mono.just("account with the email does not exist.")
            }

            Mono.fromCallable {
                logger.info("Reset password by email $email")
                this.update()
                    .eq("email", email)
                    .set("password", encodedPassword)
                    .update()
            }.flatMap { success ->
                if (success) {
                    Mono.just("")
                } else {
                    Mono.just("something went wrong. Please contact the administrator.")
                }
            }
        }
    }
}