package com.itstudio.careerpp.entity.vo.response

import kotlinx.serialization.Serializable

@Serializable
data class JobMatchVO(
    val id: String = "",
    val title: String = "",
    val matchRate: String = "",
    val sim: Double = 0.0,
    val tags: List<String> = emptyList(),
    val explanation: JobExplanation? = null
)

@Serializable
data class JobExplanation(
    val matchedSkills: List<String> = emptyList(),
    val missingSkills: List<String> = emptyList(),
    val reasons: List<String> = emptyList(),
    val strengths: List<String> = emptyList(),
    val suggestions: List<String> = emptyList()
)
