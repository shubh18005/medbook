package com.medbook.backend.dto;

import java.util.List;
import java.util.Map;

public record StudyStatsDto(
        List<GroupStatsDto> groups,
        long totalFeedback,
        List<Integer> qualityHistogram,   // 5 buckets: [0,.2) [.2,.4) [.4,.6) [.6,.8) [.8,1]
        Map<String, Object> config) {
}
