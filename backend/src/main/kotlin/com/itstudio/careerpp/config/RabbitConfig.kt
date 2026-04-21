package com.itstudio.careerpp.config

import kotlinx.serialization.json.Json
import kotlinx.serialization.serializer
import org.springframework.amqp.core.Message
import org.springframework.amqp.core.MessageProperties
import org.springframework.amqp.core.Queue
import org.springframework.amqp.rabbit.config.SimpleRabbitListenerContainerFactory
import org.springframework.amqp.rabbit.connection.ConnectionFactory
import org.springframework.amqp.rabbit.core.RabbitTemplate
import org.springframework.amqp.support.converter.AbstractMessageConverter
import org.springframework.amqp.support.converter.MessageConverter
import org.springframework.beans.factory.annotation.Qualifier
import org.springframework.boot.amqp.autoconfigure.SimpleRabbitListenerContainerFactoryConfigurer
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration

@Configuration
class RabbitConfig {

    @Bean
    fun mailQueue(): Queue = Queue("mail", true)  // durable=true，重启后队列不丢失

    @Bean
    fun messageConverter(@Qualifier("kotlinxSerializationJson") json: Json): MessageConverter =
        object : AbstractMessageConverter() {
            override fun createMessage(obj: Any, messageProperties: MessageProperties): Message {
                val serializer = json.serializersModule.serializer(obj::class.java)
                val jsonString = json.encodeToString(serializer, obj)

                val bytes = jsonString.toByteArray(Charsets.UTF_8)
                messageProperties.contentType = MessageProperties.CONTENT_TYPE_JSON
                messageProperties.contentLength = bytes.size.toLong()
                return Message(bytes, messageProperties)
            }

            override fun fromMessage(message: Message): Any {
                val content = String(message.body, Charsets.UTF_8)
                return content
            }
        }

    @Bean
    fun rabbitTemplate(
        connectionFactory: ConnectionFactory,
        messageConverter: MessageConverter
    ): RabbitTemplate {
        val rabbitTemplate = RabbitTemplate(connectionFactory)
        rabbitTemplate.messageConverter = messageConverter
        return rabbitTemplate
    }

    @Bean
    fun rabbitListenerContainerFactory(
        configurer: SimpleRabbitListenerContainerFactoryConfigurer,
        connectionFactory: ConnectionFactory,
        messageConverter: MessageConverter
    ): SimpleRabbitListenerContainerFactory {
        val factory = SimpleRabbitListenerContainerFactory()
        configurer.configure(factory, connectionFactory)
        factory.setMessageConverter(messageConverter)
        return factory
    }
}