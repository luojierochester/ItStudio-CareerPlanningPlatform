package com.itstudio.careerpp.entity.vo.response

import com.itstudio.careerpp.utils.DateUtils.getCurrentDateTime
import kotlinx.datetime.LocalDateTime
import kotlinx.serialization.Serializable

@Serializable
data class AuthorizeVO(
    val username: String = "",
    val role: String = "",
    val token: String = "",
    val expire: LocalDateTime = getCurrentDateTime(),
)