package com.medbook.backend.dto;

import java.util.List;

/** Everything the patient portal needs for the feedback checkpoint, in one call. */
public record FeedbackStatusDto(
        String offer,            // none | points | discount | gated
        String offerText,
        boolean consentGiven,
        int maxTextLength,
        List<PendingFeedbackDto> pending,
        List<FeedbackResultDto> history,
        int totalPoints,
        List<DiscountDto> discounts) {
}
