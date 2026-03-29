package com.itstudio.careerpp.entity.dto

import com.baomidou.mybatisplus.annotation.IdType
import com.baomidou.mybatisplus.annotation.TableId
import com.baomidou.mybatisplus.annotation.TableName
import com.github.sor2171.backend.entity.DataCopy
import kotlinx.datetime.LocalDateTime
import kotlinx.serialization.Serializable

@Serializable
@TableName("account")
data class Account(
    @TableId(type = IdType.AUTO)
    val id: Int? = null,
    val username: String = "",
    val password: String = "",
    val email: String = "",
    val role: String = "",
    val registerTime: LocalDateTime? = null
) : DataCopy