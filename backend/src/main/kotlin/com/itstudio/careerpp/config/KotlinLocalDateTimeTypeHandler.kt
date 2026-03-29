package com.itstudio.careerpp.config

import kotlinx.datetime.toJavaLocalDateTime
import kotlinx.datetime.toKotlinLocalDateTime
import org.apache.ibatis.type.BaseTypeHandler
import org.apache.ibatis.type.JdbcType
import org.apache.ibatis.type.MappedTypes
import java.sql.CallableStatement
import java.sql.PreparedStatement
import java.sql.ResultSet
import java.time.LocalDateTime as JavaLocalDateTime
import kotlinx.datetime.LocalDateTime as KotlinLocalDateTime

@MappedTypes(KotlinLocalDateTime::class)
class KotlinLocalDateTimeTypeHandler : BaseTypeHandler<KotlinLocalDateTime>() {

    override fun setNonNullParameter(ps: PreparedStatement, i: Int, parameter: KotlinLocalDateTime, jdbcType: JdbcType?) {
        ps.setObject(i, parameter.toJavaLocalDateTime())
    }

    override fun getNullableResult(rs: ResultSet, columnName: String): KotlinLocalDateTime? {
        return rs.getObject(columnName, JavaLocalDateTime::class.java)?.toKotlinLocalDateTime()
    }

    override fun getNullableResult(rs: ResultSet, columnIndex: Int): KotlinLocalDateTime? {
        return rs.getObject(columnIndex, JavaLocalDateTime::class.java)?.toKotlinLocalDateTime()
    }

    override fun getNullableResult(cs: CallableStatement, columnIndex: Int): KotlinLocalDateTime? {
        return cs.getObject(columnIndex, JavaLocalDateTime::class.java)?.toKotlinLocalDateTime()
    }
}