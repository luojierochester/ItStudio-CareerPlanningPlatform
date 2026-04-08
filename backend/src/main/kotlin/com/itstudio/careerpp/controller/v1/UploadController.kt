package com.itstudio.careerpp.controller.v1

import com.itstudio.careerpp.entity.RestBean
import com.itstudio.careerpp.service.v1.FileUploadService
import org.slf4j.LoggerFactory
import org.springframework.http.MediaType
import org.springframework.http.codec.multipart.FilePart
import org.springframework.validation.annotation.Validated
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RequestPart
import org.springframework.web.bind.annotation.RestController
import org.springframework.web.server.ServerWebExchange
import reactor.core.publisher.Mono

@Validated
@RestController
@RequestMapping("/api/v1/upload")
class UploadController(
    private val fileUploadService: FileUploadService
) {
    private val logger = LoggerFactory.getLogger(this::class.java)

    @PostMapping("/file", consumes = [MediaType.MULTIPART_FORM_DATA_VALUE])
    fun uploadFile(
        exchange: ServerWebExchange,
        @RequestPart("file") file: FilePart,
        @RequestPart("type") type: String
    ): Mono<RestBean<Any?>> {
        logger.info("Uploading file with type $type")
        val authorization = exchange.request.headers.getFirst("Authorization")
        return RestBean.just(fileUploadService.saveFile(file, authorization))
    }
}