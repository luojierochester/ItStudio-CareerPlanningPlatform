package com.itstudio.careerpp.listener

import org.springframework.amqp.rabbit.annotation.RabbitHandler
import org.springframework.amqp.rabbit.annotation.RabbitListener
import org.springframework.beans.factory.annotation.Value
import org.springframework.mail.MailSender
import org.springframework.mail.SimpleMailMessage
import org.springframework.stereotype.Component

@Component
@RabbitListener(queues = ["mail"])
class MailQueueListener(
    @param:Value("\${spring.mail.username}")
    private val username: String,

    private val sender: MailSender
) {
    @RabbitHandler
    fun senderMailMessage(data: Map<String, String>) {
        val email = data["email"] ?: return
        val code = data["code"] ?: return
        val type = data["type"] ?: return
        val message = when (type) {
            "register" -> createMailMessage(
                "Welcome to Our Service",
                "Thank you for registering! Your verification code is: $code"
                        + "\nThis code is valid for 3 minutes.",
                email
            )

            "reset" -> createMailMessage(
                "Password Reset Request",
                "You requested a password reset. Your verification code is: $code"
                        + "\nThis code is valid for 3 minutes.",
                email
            )

            else -> return
        }
        sender.send(message)
    }

    fun createMailMessage(title: String, content: String, to: String): SimpleMailMessage {
        val message = SimpleMailMessage()
        message.subject = title
        message.text = content
        message.from = username
        message.setTo(to)
        return message
    }
}