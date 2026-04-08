package com.itstudio.careerpp.service

import com.baomidou.mybatisplus.extension.service.IService
import com.itstudio.careerpp.entity.dto.Account
import com.itstudio.careerpp.entity.dto.UserFile
import reactor.core.publisher.Mono
import java.util.*
import kotlin.reflect.KMutableProperty1

interface UserFileService : IService<UserFile> {
    fun saveFile(accountMono: Mono<Account>, fileType: KMutableProperty1<UserFile, UUID?>): Mono<UUID>
    fun findFile(accountMono: Mono<Account>, fileType: KMutableProperty1<UserFile, UUID?>): Mono<UUID>
    fun exists(accountMono: Mono<Account>, fileType: KMutableProperty1<UserFile, UUID?>): Mono<Boolean>
}