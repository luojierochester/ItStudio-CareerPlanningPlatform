package com.itstudio.careerpp.service.v1

import com.itstudio.careerpp.entity.dto.UserFile
import com.itstudio.careerpp.entity.vo.response.*
import com.itstudio.careerpp.service.AccountService
import com.itstudio.careerpp.service.UserFileService
import com.itstudio.careerpp.utils.Const
import com.itstudio.careerpp.utils.JwtUtils
import org.apache.pdfbox.Loader
import org.apache.pdfbox.text.PDFTextStripper
import org.apache.poi.xwpf.usermodel.XWPFDocument
import org.slf4j.LoggerFactory
import org.springframework.beans.factory.annotation.Value
import org.springframework.core.ParameterizedTypeReference
import org.springframework.core.io.buffer.DataBufferUtils
import org.springframework.data.redis.core.ReactiveStringRedisTemplate
import org.springframework.http.MediaType
import org.springframework.http.codec.multipart.FilePart
import org.springframework.stereotype.Service
import org.springframework.web.reactive.function.client.WebClient
import reactor.core.publisher.Mono
import reactor.core.scheduler.Schedulers
import java.io.ByteArrayInputStream
import java.nio.file.Files
import java.nio.file.Paths
import java.util.*

@Service
class ResumeService(
    private val jwtUtils: JwtUtils,
    private val redisTemplate: ReactiveStringRedisTemplate,
    private val userFileService: UserFileService,
    private val accountService: AccountService,
    @Value("\${app.file.direction}")
    private val fileDir: String,
    @Value("\${app.algorithm.url:http://localhost:8001}")
    private val algorithmUrl: String
) {
    private val logger = LoggerFactory.getLogger(this::class.java)
    private val webClient = WebClient.create()

    // ==================== Public API ====================

    /**
     * 上传简历文件 → 保存到磁盘 → 提取文本 → 缓存到 Redis → 返回结构化解析结果
     */
    fun uploadAndParse(file: FilePart, header: String?): Mono<ResumeParseVO> {
        val extension = file.filename().substringAfterLast(".", "").lowercase()
        val username = jwtUtils.headerToUsername(header)
            ?: return Mono.error(RuntimeException("Invalid token"))

        return accountService.findAccountByNameOrEmail(username)
            .flatMap { account ->
                val accountId = account.id ?: return@flatMap Mono.error(RuntimeException("Account ID is null"))

                // 使用 UserFileService 生成 UUID 并保存到数据库
                userFileService.saveFile(Mono.just(account), UserFile::resumeFile)
                    .flatMap { uuid ->
                        DataBufferUtils.join(file.content())
                            .flatMap { dataBuffer ->
                                val bytes = ByteArray(dataBuffer.readableByteCount())
                                dataBuffer.read(bytes)
                                DataBufferUtils.release(dataBuffer)

                                // 保存文件 + 提取文本（阻塞 IO，切到弹性线程池）
                                Mono.fromCallable {
                                    val dirPath = Paths.get(fileDir)
                                    if (!Files.exists(dirPath)) Files.createDirectories(dirPath)
                                    // 使用 UUID 作为文件名
                                    Files.write(dirPath.resolve("$uuid.$extension"), bytes)
                                    extractText(bytes, extension)
                                }.subscribeOn(Schedulers.boundedElastic())
                            }
                            .flatMap { rawText ->
                                // 缓存原文到 Redis（使用 accountId 作为键）
                                redisTemplate.opsForValue()
                                    .set("${Const.RESUME_TEXT_CACHE}$accountId", rawText)
                                    .thenReturn(rawText)
                            }
                            .map { parseResumeText(it) }
                    }
            }
    }

    /**
     * 获取已缓存的简历结构化数据
     */
    fun getProfile(header: String?): Mono<ResumeParseVO> {
        val accountId = getAccountIdFromHeader(header)
            ?: return Mono.error(RuntimeException("Invalid token"))
        return redisTemplate.opsForValue()
            .get("${Const.RESUME_TEXT_CACHE}$accountId")
            .map { parseResumeText(it) }
    }

    /**
     * 更新简历的某个部分（由 AI 调用）
     */
    fun updateResume(header: String?, updateRequest: Map<String, Any>): Mono<ResumeParseVO> {
        val accountId = getAccountIdFromHeader(header)
            ?: return Mono.error(RuntimeException("Invalid token"))

        val action = updateRequest["action"] as? String ?: return Mono.error(RuntimeException("Missing action"))
        val section = updateRequest["section"] as? String ?: return Mono.error(RuntimeException("Missing section"))
        val content = updateRequest["content"]

        return redisTemplate.opsForValue()
            .get("${Const.RESUME_TEXT_CACHE}$accountId")
            .defaultIfEmpty("")
            .flatMap { rawText ->
                val currentResume = if (rawText.isNotEmpty()) parseResumeText(rawText) else ResumeParseVO()
                val updatedResume = applyResumeUpdate(currentResume, action, section, content)

                // 将更新后的简历转换回文本格式并缓存
                val updatedText = resumeToText(updatedResume)
                redisTemplate.opsForValue()
                    .set("${Const.RESUME_TEXT_CACHE}$accountId", updatedText)
                    .thenReturn(updatedResume)
            }
    }

    /**
     * 应用简历更新
     */
    private fun applyResumeUpdate(resume: ResumeParseVO, action: String, section: String, content: Any?): ResumeParseVO {
        return when (section) {
            "name" -> resume.copy(name = content as? String ?: resume.name)
            "targetRole" -> resume.copy(targetRole = content as? String ?: resume.targetRole)
            "education" -> resume.copy(education = content as? String ?: resume.education)
            "skills" -> {
                val newSkills = when (content) {
                    is List<*> -> content.filterIsInstance<String>()
                    is String -> listOf(content)
                    else -> emptyList()
                }
                when (action) {
                    "add" -> resume.copy(skills = (resume.skills + newSkills).distinct())
                    "update" -> resume.copy(skills = newSkills)
                    "delete" -> resume.copy(skills = resume.skills.filter { it !in newSkills })
                    else -> resume
                }
            }
            "projects" -> {
                when (action) {
                    "add" -> {
                        val newProject = when (content) {
                            is Map<*, *> -> ProjectItem(
                                title = content["title"] as? String ?: "",
                                desc = content["desc"] as? String ?: ""
                            )
                            else -> null
                        }
                        if (newProject != null) {
                            resume.copy(projects = resume.projects + newProject)
                        } else resume
                    }
                    "update" -> {
                        val projectList = when (content) {
                            is List<*> -> content.mapNotNull { item ->
                                (item as? Map<*, *>)?.let {
                                    ProjectItem(
                                        title = it["title"] as? String ?: "",
                                        desc = it["desc"] as? String ?: ""
                                    )
                                }
                            }
                            else -> emptyList()
                        }
                        resume.copy(projects = projectList)
                    }
                    "delete" -> {
                        val titleToDelete = (content as? Map<*, *>)?.get("title") as? String
                        resume.copy(projects = resume.projects.filter { it.title != titleToDelete })
                    }
                    else -> resume
                }
            }
            else -> resume
        }
    }

    /**
     * 将简历对象转换为文本格式（用于缓存）
     */
    private fun resumeToText(resume: ResumeParseVO): String {
        val sb = StringBuilder()
        if (resume.name.isNotEmpty()) sb.append("姓名：${resume.name}\n")
        if (resume.targetRole.isNotEmpty()) sb.append("求职意向：${resume.targetRole}\n")
        if (resume.education.isNotEmpty()) sb.append("教育背景：${resume.education}\n")
        if (resume.skills.isNotEmpty()) {
            sb.append("\n技能：\n")
            resume.skills.forEach { sb.append("- $it\n") }
        }
        if (resume.projects.isNotEmpty()) {
            sb.append("\n项目经历：\n")
            resume.projects.forEach { project ->
                sb.append("\n${project.title}\n")
                sb.append("${project.desc}\n")
            }
        }
        return sb.toString()
    }

    /**
     * 获取能力看板数据（优先走 algorithm 服务，降级走本地关键词提取）
     */
    fun getDashboard(header: String?): Mono<DashboardVO> {
        val accountId = getAccountIdFromHeader(header)
            ?: return Mono.error(RuntimeException("Invalid token"))
        return redisTemplate.opsForValue()
            .get("${Const.RESUME_TEXT_CACHE}$accountId")
            .flatMap { rawText ->
                callAlgorithm(rawText, 20, 5)
                    .map { response -> computeDashboard(rawText, response) }
                    .onErrorResume {
                        logger.warn("Algorithm unavailable, falling back to local: ${it.message}")
                        Mono.just(computeLocalDashboard(rawText))
                    }
            }
            .switchIfEmpty(Mono.just(computeLocalDashboard("")))
    }

    /**
     * 获取岗位推荐列表（依赖 algorithm 服务）
     */
    fun getRecommendations(header: String?, topn: Int): Mono<List<JobMatchVO>> {
        val accountId = getAccountIdFromHeader(header)
            ?: return Mono.error(RuntimeException("Invalid token"))
        return redisTemplate.opsForValue()
            .get("${Const.RESUME_TEXT_CACHE}$accountId")
            .flatMap { rawText ->
                callAlgorithm(rawText, topn * 3, topn)
                    .map { response -> extractJobMatches(response) }
                    .onErrorResume {
                        logger.warn("Algorithm unavailable: ${it.message}")
                        Mono.just(emptyList())
                    }
            }
            .defaultIfEmpty(emptyList())
    }

    // ==================== JWT Helper ====================

    private fun getAccountIdFromHeader(header: String?): Int? {
        val jwt = jwtUtils.resolveJwt(header) ?: return null
        return jwtUtils.toId(jwt)
    }

    // ==================== Text Extraction ====================

    private fun extractText(bytes: ByteArray, extension: String): String {
        return try {
            when (extension) {
                "pdf" -> extractFromPdf(bytes)
                "docx" -> extractFromDocx(bytes)
                else -> String(bytes, Charsets.UTF_8)
            }
        } catch (e: Exception) {
            logger.warn("Text extraction failed for .$extension: ${e.message}")
            ""
        }
    }

    private fun extractFromPdf(bytes: ByteArray): String {
        val doc = Loader.loadPDF(bytes)
        val text = PDFTextStripper().getText(doc)
        doc.close()
        return text
    }

    private fun extractFromDocx(bytes: ByteArray): String {
        val doc = XWPFDocument(ByteArrayInputStream(bytes))
        val text = doc.paragraphs.joinToString("\n") { it.text }
        doc.close()
        return text
    }

    // ==================== Resume Parsing (Regex) ====================

    private fun parseResumeText(text: String): ResumeParseVO {
        val lines = text.split("\n").map { it.trim() }.filter { it.isNotBlank() }
        return ResumeParseVO(
            name = extractName(lines),
            targetRole = extractTargetRole(lines),
            education = extractEducation(lines),
            skills = extractSkills(text),
            projects = extractProjects(lines)
        )
    }

    private fun extractName(lines: List<String>): String {
        val namePattern = Regex("^[\\u4e00-\\u9fa5]{2,4}$")
        return lines.firstOrNull { namePattern.matches(it) }
            ?: lines.firstOrNull()?.take(10) ?: ""
    }

    private fun extractTargetRole(lines: List<String>): String {
        val keywords = listOf("求职意向", "期望岗位", "目标职位", "应聘职位", "意向岗位", "期望职位")
        for (line in lines) {
            for (kw in keywords) {
                if (line.contains(kw)) {
                    return line.replace(Regex(".*$kw[：:\\s]*"), "").trim()
                }
            }
        }
        return ""
    }

    private fun extractEducation(lines: List<String>): String {
        val keywords = listOf("大学", "学院", "本科", "硕士", "博士", "学士", "MBA", "University")
        return lines.firstOrNull { line -> keywords.any { line.contains(it, ignoreCase = true) } } ?: ""
    }

    companion object {
        val SKILL_KEYWORDS = listOf(
            "Python", "Java", "Kotlin", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust", "Swift",
            "React", "Vue", "Angular", "Node.js", "Spring", "Spring Boot", "Django", "Flask", "FastAPI",
            "MySQL", "PostgreSQL", "MongoDB", "Redis", "Elasticsearch", "SQLite",
            "Docker", "Kubernetes", "Git", "Linux", "AWS", "Azure", "GCP",
            "PyTorch", "TensorFlow", "Scikit-learn", "Pandas", "NumPy",
            "HTML", "CSS", "SQL", "Hadoop", "Spark", "Flink", "Kafka", "RabbitMQ",
            "微服务", "机器学习", "深度学习", "自然语言处理", "计算机视觉", "数据分析"
        )
    }

    private fun extractSkills(text: String): List<String> =
        SKILL_KEYWORDS.filter { text.contains(it, ignoreCase = true) }

    private fun extractProjects(lines: List<String>): List<ProjectItem> {
        val projects = mutableListOf<ProjectItem>()
        var inSection = false
        var title = ""
        val desc = StringBuilder()
        val sectionStart = listOf("项目经历", "项目经验", "项目实践", "参与项目")
        val sectionEnd = listOf("教育背景", "教育经历", "工作经历", "工作经验", "技能", "自我评价", "荣誉", "证书", "获奖")

        for (line in lines) {
            if (sectionStart.any { line.contains(it) }) { inSection = true; continue }
            if (inSection && sectionEnd.any { line.contains(it) }) {
                if (title.isNotBlank()) projects.add(ProjectItem(title, desc.toString().trim()))
                break
            }
            if (!inSection) continue

            // 短行视为项目标题，长行视为描述
            if (line.length <= 30
                && !line.startsWith("负责") && !line.startsWith("参与")
                && !line.startsWith("使用") && !line.startsWith("-")
                && !line.startsWith("•") && !line.startsWith("·")
            ) {
                if (title.isNotBlank()) projects.add(ProjectItem(title, desc.toString().trim()))
                title = line
                desc.clear()
            } else {
                if (desc.isNotEmpty()) desc.append(" ")
                desc.append(line)
            }
        }
        if (title.isNotBlank() && inSection) {
            projects.add(ProjectItem(title, desc.toString().trim()))
        }
        return projects
    }

    // ==================== Algorithm Client ====================

    private fun callAlgorithm(resumeText: String, recallK: Int, topn: Int): Mono<Map<String, Any?>> {
        return webClient.post()
            .uri("$algorithmUrl/api/recommend")
            .contentType(MediaType.APPLICATION_JSON)
            .bodyValue(
                mapOf(
                    "resume_text" to resumeText,
                    "recall_k" to recallK,
                    "topn" to topn
                )
            )
            .retrieve()
            .bodyToMono(object : ParameterizedTypeReference<Map<String, Any?>>() {})
    }

    // ==================== Dashboard Computation ====================

    @Suppress("UNCHECKED_CAST")
    private fun computeDashboard(rawText: String, algorithmResponse: Map<String, Any?>): DashboardVO {
        val data = algorithmResponse["data"] as? List<Map<String, Any?>>
        if (data.isNullOrEmpty()) return computeLocalDashboard(rawText)

        val first = data.first()
        val hasInternship = (first["has_internship"] as? Number)?.toInt() == 1
        val hasProject = (first["has_project"] as? Number)?.toInt() == 1
        val hasCompetition = (first["has_competition"] as? Number)?.toInt() == 1
        val hasLearning = (first["has_learning_evidence"] as? Number)?.toInt() == 1
        val hasCommunication = (first["has_communication_evidence"] as? Number)?.toInt() == 1
        val hasPressure = (first["has_pressure_evidence"] as? Number)?.toInt() == 1

        val avgSim = data.mapNotNull { (it["sim"] as? Number)?.toDouble() }
            .average().takeIf { !it.isNaN() } ?: 0.5
        val skillScore = minOf((avgSim * 120).toInt(), 98)

        val radar = listOf(
            RadarItem("专业技能", skillScore),
            RadarItem("项目经验", if (hasProject) 85 else 30),
            RadarItem("竞赛成果", if (hasCompetition) 78 else 25),
            RadarItem("实习经历", if (hasInternship) 80 else 20),
            RadarItem("沟通表达", if (hasCommunication) 88 else 35),
            RadarItem("抗压能力", if (hasPressure) 75 else 30)
        )

        val score = radar.sumOf { it.value } / radar.size
        return DashboardVO(score, computeRank(score), radar)
    }

    private fun computeLocalDashboard(rawText: String): DashboardVO {
        val text = rawText.lowercase()
        val hasInternship = text.contains("实习") || text.contains("intern")
        val hasProject = text.contains("项目")
        val hasCompetition = text.contains("竞赛") || text.contains("蓝桥杯") || text.contains("acm")
        val hasCommunication = text.contains("沟通") || text.contains("团队") || text.contains("协作")
        val hasPressure = text.contains("抗压") || text.contains("高强度")

        val skillCount = SKILL_KEYWORDS.count { rawText.contains(it, ignoreCase = true) }
        val skillScore = minOf(30 + skillCount * 6, 98)

        val radar = listOf(
            RadarItem("专业技能", skillScore),
            RadarItem("项目经验", if (hasProject) 85 else 30),
            RadarItem("竞赛成果", if (hasCompetition) 78 else 25),
            RadarItem("实习经历", if (hasInternship) 80 else 20),
            RadarItem("沟通表达", if (hasCommunication) 88 else 35),
            RadarItem("抗压能力", if (hasPressure) 75 else 30)
        )

        val score = radar.sumOf { it.value } / radar.size
        return DashboardVO(score, computeRank(score), radar)
    }

    private fun computeRank(score: Int): String = when {
        score >= 85 -> "超越 95% 竞争者"
        score >= 75 -> "超越 85% 竞争者"
        score >= 60 -> "超越 70% 竞争者"
        score >= 45 -> "超越 50% 竞争者"
        else -> "超越 30% 竞争者"
    }

    // ==================== Job Match Extraction ====================

    @Suppress("UNCHECKED_CAST")
    private fun extractJobMatches(algorithmResponse: Map<String, Any?>): List<JobMatchVO> {
        val data = algorithmResponse["data"] as? List<Map<String, Any?>> ?: return emptyList()
        return data.mapIndexed { index, job ->
            val explanation = job["explanation"] as? Map<String, Any?>
            val sim = (job["sim"] as? Number)?.toDouble() ?: 0.0
            JobMatchVO(
                id = (job["job_id"] as? String) ?: "${index + 1}",
                title = (job["title"] as? String) ?: "未知岗位",
                matchRate = "${(sim * 100).toInt()}%",
                sim = sim,
                tags = (explanation?.get("matched_skills") as? List<String>) ?: emptyList(),
                explanation = explanation?.let {
                    JobExplanation(
                        matchedSkills = (it["matched_skills"] as? List<String>) ?: emptyList(),
                        missingSkills = (it["missing_skills"] as? List<String>) ?: emptyList(),
                        reasons = (it["reasons"] as? List<String>) ?: emptyList(),
                        strengths = (it["strengths"] as? List<String>) ?: emptyList(),
                        suggestions = (it["suggestions"] as? List<String>) ?: emptyList()
                    )
                }
            )
        }
    }
}
