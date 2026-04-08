package com.itstudio.careerpp.mapper

import com.baomidou.mybatisplus.core.mapper.BaseMapper
import com.itstudio.careerpp.entity.dto.UserFile
import org.apache.ibatis.annotations.Mapper

@Mapper
interface UserFileMapper : BaseMapper<UserFile>