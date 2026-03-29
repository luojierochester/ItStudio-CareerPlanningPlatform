package com.itstudio.careerpp.filter

import com.itstudio.careerpp.utils.JwtUtils
import org.springframework.http.HttpHeaders
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken
import org.springframework.security.core.context.ReactiveSecurityContextHolder
import org.springframework.stereotype.Component
import org.springframework.web.server.ServerWebExchange
import org.springframework.web.server.WebFilter
import org.springframework.web.server.WebFilterChain
import reactor.core.publisher.Mono

@Component
class JwtAuthorizeFilter(
    private val utils: JwtUtils
) : WebFilter {

    override fun filter(exchange: ServerWebExchange, chain: WebFilterChain): Mono<Void> {
        val authorization = exchange.request.headers.getFirst(HttpHeaders.AUTHORIZATION)
        val jwt = utils.resolveJwt(authorization)

        return if (jwt != null) {
            val user = utils.toUser(jwt)
            val authentication = UsernamePasswordAuthenticationToken(
                user,
                null,
                user.authorities
            )
            exchange.attributes["id"] = utils.toId(jwt)

            chain.filter(exchange)
                .contextWrite(ReactiveSecurityContextHolder.withAuthentication(authentication))
        } else {
            chain.filter(exchange)
        }
    }
}