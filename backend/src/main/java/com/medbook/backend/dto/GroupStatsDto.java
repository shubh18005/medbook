package com.medbook.backend.dto;

import java.util.Map;

/** Study measures for one group (admin only). */
public record GroupStatsDto(
        String group,
        String name,
        long enrolled,          // patients assigned to the group
        long shown,             // ... who have at least one completed visit (checkpoint triggered)
        long responded,         // ... who submitted feedback at least once
        double responseRate,    // responded / shown, in percent (RQ1)
        long feedbackCount,
        double meanRating,      // RQ2
        double neutralShare,    // % of submissions with overall rating 3 (RQ2)
        double meanWords,
        double meanQuality,     // mean Q (RQ3)
        double lowEffortShare,  // % of submissions with Q below the threshold (RQ3)
        long rewardsGranted,
        long rewardsWithheld,
        Map<String, Double> meanAspect) {
}
