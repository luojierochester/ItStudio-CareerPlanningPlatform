package com.itstudio.careerpp.controller.v1

import com.itstudio.careerpp.entity.dto.UserFile
import com.itstudio.careerpp.service.AccountService
import com.itstudio.careerpp.service.UserFileService
import com.itstudio.careerpp.utils.JwtUtils
import org.slf4j.LoggerFactory
import org.springframework.beans.factory.annotation.Value
import org.springframework.core.io.FileSystemResource
import org.springframework.core.io.buffer.DataBufferUtils
import org.springframework.http.HttpHeaders
import org.springframework.http.HttpStatus
import org.springframework.http.MediaType
import org.springframework.validation.annotation.Validated
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RequestParam
import org.springframework.web.bind.annotation.RestController
import org.springframework.web.server.ServerWebExchange
import reactor.core.publisher.Mono
import reactor.core.scheduler.Schedulers
import java.net.URLEncoder
import java.nio.charset.StandardCharsets
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths

@Validated
@RestController
@RequestMapping("/api/v1/download")
class DownloadController(
    private val jwtUtils: JwtUtils,
    private val accountService: AccountService,
    private val userFileService: UserFileService,
    @Value("\${app.file.direction}")
    private val fileDir: String
) {
    private val logger = LoggerFactory.getLogger(this::class.java)

    @GetMapping("/file")
    fun downloadFile(
        exchange: ServerWebExchange,
        @RequestParam(defaultValue = "resume") type: String
    ): Mono<Void> {
        val header = exchange.request.headers.getFirst(HttpHeaders.AUTHORIZATION)
        val username = jwtUtils.headerToUsername(header)
            ?: return respondStatus(exchange, HttpStatus.UNAUTHORIZED)

        val fileProperty = when (type) {
            "resume" -> UserFile::resumeFile
            else -> UserFile::testFile
        }

        return accountService.findAccountByNameOrEmail(username)
            .flatMap { account ->
                userFileService.findFile(Mono.just(account), fileProperty)
            }
            .flatMap { uuid ->
                Mono.defer {
                    val dir = Paths.get(fileDir)
                    if (!Files.exists(dir)) return@defer Mono.empty<Path>()
                    val file = Files.list(dir).use { stream ->
                        stream.filter { it.fileName.toString().startsWith(uuid.toString()) }
                            .findFirst().orElse(null)
                    }
                    if (file != null) Mono.just(file) else Mono.empty()
                }.subscribeOn(Schedulers.boundedElastic())
            }
            .flatMap { filePath -> serveFile(exchange, filePath) }
            .switchIfEmpty(respondStatus(exchange, HttpStatus.NOT_FOUND))
    }

    private fun serveFile(exchange: ServerWebExchange, filePath: Path): Mono<Void> {
        val fileName = filePath.fileName.toString()
        val contentType = when {
            fileName.endsWith(".pdf") -> MediaType.APPLICATION_PDF
            fileName.endsWith(".docx") -> MediaType.parseMediaType(
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            fileName.endsWith(".doc") -> MediaType.parseMediaType("application/msword")
            else -> MediaType.APPLICATION_OCTET_STREAM
        }

        val response = exchange.response
        response.headers.contentType = contentType
        response.headers.set(
            HttpHeaders.CONTENT_DISPOSITION,
            "attachment; filename=\"${URLEncoder.encode(fileName, StandardCharsets.UTF_8)}\""
        )

        logger.info("Serving file: $filePath")
        val resource = FileSystemResource(filePath)
        return DataBufferUtils.read(resource, response.bufferFactory(), 4096)
            .let { response.writeWith(it) }
    }

    private fun respondStatus(exchange: ServerWebExchange, status: HttpStatus): Mono<Void> {
        exchange.response.statusCode = status
        return exchange.response.setComplete()
    }
}