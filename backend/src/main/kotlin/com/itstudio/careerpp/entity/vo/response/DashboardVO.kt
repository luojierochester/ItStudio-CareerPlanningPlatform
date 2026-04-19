package com.itstudio.careerpp.entity.vo.response

import kotlinx.serialization.Serializable

@Serializable
data class DashboardVO(
    val score: Int = 0,
    val rank: String = "",
    val radar: List<RadarItem> = emptyList()
)

@Serializable
data class RadarItem(
    val dimension: String = "",
    val value: Int = 0
)
