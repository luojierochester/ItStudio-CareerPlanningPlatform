package com.itstudio.careerpp.service.v1

import com.itstudio.careerpp.entity.dto.UserFile
import com.itstudio.careerpp.service.AccountService
import com.itstudio.careerpp.service.UserFileService
import com.itstudio.careerpp.utils.JwtUtils
import org.slf4j.LoggerFactory
import org.springframework.beans.factory.annotation.Value
import org.springframework.http.codec.multipart.FilePart
import org.springframework.stereotype.Service
import reactor.core.publisher.Mono
import java.nio.file.Paths

@Service
class FileUploadService(
    private val userFileService: UserFileService,
    private val accountService: AccountService,
    private val jwtUtils: JwtUtils,

    @Value($$"${app.file.direction}")
    private val fileDir: String
) {
    private val logger = LoggerFactory.getLogger(this::class.java)

    fun saveFile(file: FilePart, header: String?): Mono<String> {
        val extension = file.filename().substringAfterLast(".", "")
        val username = jwtUtils.headerToUsername(header)!!

        return accountService
            .findAccountByNameOrEmail(username)
            .flatMap { account ->
                userFileService.saveFile(
                    Mono.just(account),
                    UserFile::testFile
                )
                    .flatMap { uuid ->
                        val path = Paths.get("$fileDir/$uuid.$extension")
                        file.transferTo(path)
                            .then(Mono.just(""))
                            .onErrorResume { e ->
                                logger.warn(e.message)
                                Mono.just(e.message ?: "Unknown Error")
                            }
                    }
            }
    }
}