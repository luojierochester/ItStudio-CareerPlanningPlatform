package com.itstudio.careerpp.entity.vo.request

import jakarta.validation.constraints.Email
import jakarta.validation.constraints.Pattern
import org.hibernate.validator.constraints.Length

data class EmailRegisterVO(
    @param:Email
    val email: String = "",
    @param:Length(min = 6, max = 6)
    val code: String? = null,
    @param:Pattern(regexp = "^[a-zA-Z0-9\\u4e00-\\u9fa5]+$")
    @param:Length(min = 4, max = 16)
    val username: String = "",
    @param:Length(min = 6, max = 20)
    val password: String = "",
)