package com.itstudio.careerpp

import org.junit.jupiter.api.Test
import org.springframework.boot.test.context.SpringBootTest
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder

@SpringBootTest
class CareerppApplicationTests {

	@Test
	fun contextLoads() {
		println(BCryptPasswordEncoder().encode("123456"))
	}

}
