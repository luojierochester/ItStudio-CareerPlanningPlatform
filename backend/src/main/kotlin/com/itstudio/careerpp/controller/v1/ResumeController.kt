package com.itstudio.careerpp.controller.v1

import com.itstudio.careerpp.entity.RestBean
import com.itstudio.careerpp.service.v1.ResumeService
import org.slf4j.LoggerFactory
import org.springframework.http.HttpHeaders
import org.springframework.http.MediaType
import org.springframework.http.codec.multipart.FilePart
import org.springframework.validation.annotation.Validated
import org.springframework.web.bind.annotation.*
import org.springframework.web.server.ServerWebExchange
import reactor.core.publisher.Mono

@Validated
@RestController
@RequestMapping("/api/v1/resume")
class ResumeController(
    private val resumeService: ResumeService
) {
    private val logger = LoggerFactory.getLogger(this::class.java)

    /**
     * POST /api/v1/resume/upload
     * 上传简历文件（PDF/Word），提取文本并返回结构化解析结果
     */
    @PostMapping("/upload", consumes = [MediaType.MULTIPART_FORM_DATA_VALUE])
    fun uploadAndParse(
        exchange: ServerWebExchange,
        @RequestPart("file") file: FilePart
    ): Mono<RestBean<Any?>> {
        val header = exchange.request.headers.getFirst(HttpHeaders.AUTHORIZATION)
        logger.info("Resume upload and parse")
        return resumeService.uploadAndParse(file, header)
            .map { RestBean.success<Any?>(it) }
            .onErrorResume { e ->
                logger.warn("Resume upload failed: ${e.message}")
                Mono.just(RestBean.failure(500, null, e.message))
            }
    }

    /**
     * GET /api/v1/resume/profile
     * 获取已缓存的简历结构化数据
     */
    @GetMapping("/profile")
    fun getProfile(exchange: ServerWebExchange): Mono<RestBean<Any?>> {
        val header = exchange.request.headers.getFirst(HttpHeaders.AUTHORIZATION)
        return resumeService.getProfile(header)
            .map { RestBean.success<Any?>(it) }
            .defaultIfEmpty(RestBean.failure(404, null, "请先上传简历"))
    }

    /**
     * POST /api/v1/resume/update
     * 更新简历的某个部分（由 AI 调用）
     */
    @PostMapping("/update")
    fun updateResume(
        exchange: ServerWebExchange,
        @RequestBody updateRequest: Map<String, Any>
    ): Mono<RestBean<Any?>> {
        val header = exchange.request.headers.getFirst(HttpHeaders.AUTHORIZATION)
        logger.info("Resume update request: $updateRequest")
        return resumeService.updateResume(header, updateRequest)
            .map { RestBean.success<Any?>(it) }
            .onErrorResume { e ->
                logger.warn("Resume update failed: ${e.message}")
                Mono.just(RestBean.failure(500, null, e.message))
            }
    }

    /**
     * GET /api/v1/resume/dashboard
     * 获取六维能力看板数据
     */
    @GetMapping("/dashboard")
    fun getDashboard(exchange: ServerWebExchange): Mono<RestBean<Any?>> {
        val header = exchange.request.headers.getFirst(HttpHeaders.AUTHORIZATION)
        return resumeService.getDashboard(header)
            .map { RestBean.success<Any?>(it) }
            .defaultIfEmpty(RestBean.failure(404, null, "请先上传简历"))
    }

    /**
     * GET /api/v1/resume/recommend?topn=10
     * 获取岗位推荐列表（调用 algorithm 服务）
     */
    @GetMapping("/recommend")
    fun getRecommend(
        exchange: ServerWebExchange,
        @RequestParam(defaultValue = "10") topn: Int
    ): Mono<RestBean<Any?>> {
        val header = exchange.request.headers.getFirst(HttpHeaders.AUTHORIZATION)
        return resumeService.getRecommendations(header, topn)
            .map { RestBean.success<Any?>(it) }
            .defaultIfEmpty(RestBean.failure(404, null, "请先上传简历"))
    }
}
