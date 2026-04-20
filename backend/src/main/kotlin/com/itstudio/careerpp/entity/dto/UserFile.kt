package com.itstudio.careerpp.entity.dto

import com.baomidou.mybatisplus.annotation.TableName
import java.util.*

@TableName("user_file")
data class UserFile(
    val id: Int? = null,
    var testFile: UUID? = null,
    var resumeFile: UUID? = null,  // 简历文件 UUID
)