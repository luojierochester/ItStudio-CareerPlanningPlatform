package com.itstudio.careerpp.service.impl

import com.baomidou.mybatisplus.core.toolkit.Wrappers
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl
import com.itstudio.careerpp.entity.dto.Account
import com.itstudio.careerpp.entity.dto.UserFile
import com.itstudio.careerpp.mapper.UserFileMapper
import com.itstudio.careerpp.service.UserFileService
import org.springframework.stereotype.Service
import reactor.core.publisher.Mono
import java.util.*
import kotlin.reflect.KMutableProperty1

@Service
class UserFileServiceImpl : ServiceImpl<UserFileMapper, UserFile>(), UserFileService {

    /**
     * @return 保存成功返回UUID，失败返回Mono<Empty>
     */
    override fun saveFile(
        accountMono: Mono<Account>,
        fileType: KMutableProperty1<UserFile, UUID?>
    ): Mono<UUID> {
        return accountMono
            .flatMap { account ->
                existUserFileOne(account)
                    .flatMap {
                        if (it) {
                            Mono.just(true)
                        } else {
                            saveEmptyUserFile(account)
                        }
                    }
                    .filter { it }
                    .map {
                        val uuid = UUID.randomUUID()
                        this.ktUpdate()
                            .eq(UserFile::id, account.id!!)
                            .set(fileType, uuid)
                            .update()
                        return@map uuid
                    }
            }
    }

    /**
     * @return 返回文件名即UUID，不存在返回Mono<Empty>
     */
    override fun findFile(
        accountMono: Mono<Account>,
        fileType: KMutableProperty1<UserFile, UUID?>
    ): Mono<UUID> {
        return accountMono
            .filterWhen { existUserFileOne(it) }
            .flatMap { getUserFileById(it.id!!) }
            .mapNotNull { fileType.get(it) }
    }

    /**
     * @return 返回数据库中是否存在属于account的行
     */
    override fun exists(
        accountMono: Mono<Account>,
        fileType: KMutableProperty1<UserFile, UUID?>
    ): Mono<Boolean> {
        return accountMono
            .flatMap { existUserFileOne(it) }
    }


    private fun getUserFileById(id: Int): Mono<UserFile> =
        Mono.just(this.query().eq("id", id).one())

    private fun existUserFileOne(account: Account): Mono<Boolean> {
        return Mono.just(
            this.baseMapper.exists(
                Wrappers.query<UserFile>()
                    .eq("id", account.id!!)
            )
        )
    }

    private fun saveEmptyUserFile(account: Account): Mono<Boolean> =
        Mono.just(this.save(UserFile(account.id!!)))
}