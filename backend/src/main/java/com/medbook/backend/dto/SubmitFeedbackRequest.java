package com.medbook.backend.dto;

/** Body of POST /api/feedback. Aspect ratings and free text are optional. */
public record SubmitFeedbackRequest(
        String appointmentId,
        Integer overallRating,
        Integer ratingDoctor,
        Integer ratingStaff,
        Integer ratingWaiting,
        Integer ratingCleanliness,
        Integer ratingBilling,
        String freeText,
        Boolean consent) {
}
