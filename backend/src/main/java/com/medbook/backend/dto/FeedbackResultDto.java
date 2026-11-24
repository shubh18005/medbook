package com.medbook.backend.dto;

/**
 * What a PATIENT sees about one of their submissions. The quality score Q and
 * its components are intentionally not included, so the gate can't be tuned against.
 */
public record FeedbackResultDto(
        String appointmentId,
        String doctorName,
        String visitDate,
        String submittedAt,
        int overallRating,
        String rewardType,       // none | points | discount
        String rewardStatus,     // not_applicable | granted | withheld
        int rewardPoints,
        int rewardDiscountPercent,
        String rewardCode,
        String message) {
}
