package com.itstudio.careerpp.entity.dto

import com.baomidou.mybatisplus.annotation.TableName
import java.util.*

@TableName("user_file")
data class UserFile(
    val id: Int = 1,
    var testFile: UUID? = null, 
)