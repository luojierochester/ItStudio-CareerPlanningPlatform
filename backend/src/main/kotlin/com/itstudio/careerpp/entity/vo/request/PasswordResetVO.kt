package com.itstudio.careerpp.entity.vo.request

import jakarta.validation.constraints.Email
import org.hibernate.validator.constraints.Length

data class PasswordResetVO(
    @param:Email
    val email: String = "",
    @param:Length(min = 6, max = 6)
    val code: String? = null,
    @param:Length(min = 6, max = 20)
    val password: String = "",
)