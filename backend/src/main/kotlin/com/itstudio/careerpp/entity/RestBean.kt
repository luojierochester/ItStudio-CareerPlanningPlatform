package com.itstudio.careerpp.entity

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

@Serializable
data class RestBean<T>(
    val code: Int,
    val data: T,
    val message: String
) {
    companion object {
        fun <T> success(data: T, message: String = "Success"): RestBean<T> {
            return RestBean(200, data, message)
        }

        // 针对无 data 返回的情况，统一使用 Any?
        fun success(message: String = "Success"): RestBean<Any?> {
            return RestBean(200, null, message)
        }

        fun <T> failure(code: Int = 401, data: T, message: String?): RestBean<T> {
            return RestBean(code, data, message ?: "Failure")
        }

        fun unauthenticated(message: String?) =
            failure(401, null, message)

        fun forbidden(message: String?) =
            failure(403, null, message)

        fun logoutFailed(message: String = ""): RestBean<Any?> {
            val formatMessage = if (message.isBlank()) "" else ": $message"
            return failure(400, null, "Logout Failed$formatMessage")
        }
    }
}

inline fun <reified T> RestBean<T>.toJsonString(): String {
    return Json.encodeToString(this)
}