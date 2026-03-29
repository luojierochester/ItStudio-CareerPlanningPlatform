package com.itstudio.careerpp.exception

import com.itstudio.careerpp.entity.RestBean
import jakarta.validation.ValidationException
import org.slf4j.LoggerFactory
import org.springframework.web.bind.annotation.ExceptionHandler
import org.springframework.web.bind.annotation.RestControllerAdvice

@RestControllerAdvice
class ValidationController {

    private val log = LoggerFactory.getLogger(ValidationController::class.java)

    @ExceptionHandler(ValidationException::class)
    fun validationException(e: Exception): RestBean<out String?> {
        log.warn("Resolve [${e.javaClass.name}: ${e.message}]")
        return RestBean.failure(
            400,
            null,
            "parameter validation error"
        )
    }
}