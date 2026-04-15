package com.itstudio.careerpp.entity

import kotlin.reflect.KClass
import kotlin.reflect.KProperty
import kotlin.reflect.full.createInstance
import kotlin.reflect.full.declaredMemberProperties
import kotlin.reflect.full.memberProperties
import kotlin.reflect.jvm.javaField

interface DataCopy {

    fun <T : Any> toAnotherObject(
        toClass: KClass<T>,
        otherProperties: Map<String, Any?>
    ): T {
        try {
            val voProperties = toClass.declaredMemberProperties
            val vo = toClass.createInstance()
            for (voProperty in voProperties)
                copyFieldData(voProperty, otherProperties, vo)
            return vo
        } catch (e: ReflectiveOperationException) {
            throw RuntimeException(
                "${toClass.simpleName} has no fields.",
                e
            )
        }
    }

    private fun copyFieldData(
        toProperty: KProperty<*>,
        otherProperties: Map<String, Any?>,
        another: Any
    ) {
        try {
            val thisProperty = this::class.memberProperties
                .firstOrNull { it.name == toProperty.name }

            val value =
                if (thisProperty != null) {
                    thisProperty.getter.call(this)
                } else if (otherProperties.containsKey(toProperty.name))
                    otherProperties[toProperty.name]
                else
                    throw RuntimeException(
                        "Property ${toProperty.name} not found."
                    )

            val field = toProperty.javaField!!
            field.isAccessible = true
            field.set(another, value)
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }
}