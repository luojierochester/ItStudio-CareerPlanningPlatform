package com.itstudio.careerpp.utils

import com.auth0.jwt.JWT
import com.auth0.jwt.JWTVerifier
import com.auth0.jwt.algorithms.Algorithm
import com.auth0.jwt.interfaces.DecodedJWT
import org.springframework.beans.factory.annotation.Value
import org.springframework.data.redis.core.StringRedisTemplate
import org.springframework.security.core.userdetails.User
import org.springframework.security.core.userdetails.UserDetails
import org.springframework.stereotype.Component
import java.util.*
import java.util.concurrent.TimeUnit

@Component
class JwtUtils(
    @param:Value($$"${spring.security.jwt.key}")
    private val key: String,

    @param:Value($$"${spring.security.jwt.expire-hours}")
    private val expireHours: Int,

    private val template: StringRedisTemplate,
    private val algorithm: Algorithm = Algorithm.HMAC256(key),
    private val jwtVerifier: JWTVerifier = JWT.require(algorithm).build()
) {
    fun invalidateJwt(headerToken: String?): Boolean {
        val token = this.convertToToken(headerToken) ?: return false
        try {
            val jwt = jwtVerifier.verify(token)
            val id = jwt.id
            return deleteToken(id, jwt.expiresAt)
        } catch (e: Exception) {
            println(e.message)
            return false
        }
    }

    private fun deleteToken(uuid: String, time: Date): Boolean {
        val now = Date()
        val expire = (time.time - now.time).coerceAtLeast(0)
        template.opsForValue().set(
            Const.JWT_BLACK_LIST + uuid,
            "deleted",
            expire,
            TimeUnit.MILLISECONDS
        )
        return true
    }

    private fun isInvalidToken(uuid: String): Boolean =
        template.hasKey(Const.JWT_BLACK_LIST + uuid) ?: false

    fun resolveJwt(headerToken: String?): DecodedJWT? {
        val token = convertToToken(headerToken) ?: return null
        try {
            val decodedJWT = jwtVerifier.verify(token)
            if (this.isInvalidToken(decodedJWT.id)) return null
            val expiresAt = decodedJWT.expiresAt
            
            return if (Date().after(expiresAt)) null
            else decodedJWT
            
        } catch (e: Exception) {
            println(e.message)
            return null
        }
    }

    fun createJwt(
        details: UserDetails,
        id: Int,
        username: String
    ): String {
        return JWT.create()
            .withJWTId(UUID.randomUUID().toString())
            .withClaim("id", id)
            .withClaim("username", username)
            .withClaim(
                "authorities",
                details.authorities.map { it.authority }.toList()
            )
            .withExpiresAt(expiresTime())
            .withIssuedAt(Date())
            .sign(algorithm)
    }

    fun toUser(jwt: DecodedJWT): UserDetails {
        val claims = jwt.claims
        return User
            .withUsername(claims["username"]!!.asString())
            .password("********")
            .authorities(*(claims["authorities"]!!.asArray(String::class.java)))
            .build()
    }

    fun toId(jwt: DecodedJWT) = jwt.claims["id"]?.asInt() ?: -1

    fun expiresTime(): Date {
        val cal = Calendar.getInstance()
        cal.add(Calendar.HOUR, expireHours)
        return cal.time
    }

    fun convertToToken(headerToken: String?): String? =
        headerToken?.replace("Bearer ", "")
}