package com.itstudio.careerpp.entity.vo.response

import kotlinx.serialization.Serializable

@Serializable
data class ResumeParseVO(
    val name: String = "",
    val targetRole: String = "",
    val education: String = "",
    val skills: List<String> = emptyList(),
    val projects: List<ProjectItem> = emptyList()
)

@Serializable
data class ProjectItem(
    val title: String = "",
    val desc: String = ""
)
