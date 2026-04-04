package com.itstudio.careerpp.utils

import reactor.core.publisher.Mono

object Const {
    const val FLOW_LIMIT_ORDER = -101
    
    const val JWT_BLACK_LIST = "jwt:blacklist:"
    const val VERIFY_EMAIL_LIMIT = "verify:email:limit:"
    const val VERIFY_EMAIL_DATA = "verify:email:data:"

    const val FLOW_LIMIT_COUNTER = "flow:counter:"
    const val FLOW_LIMIT_BLOCK = "flow:block:"
    
    val INTERNAL_ERROR_MONO = Mono.just("something went wrong. Please contact the administrator.")
}