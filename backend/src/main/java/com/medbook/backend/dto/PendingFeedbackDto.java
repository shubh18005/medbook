package com.medbook.backend.dto;

/** A completed consultation that is still waiting for the patient's feedback. */
public record PendingFeedbackDto(
        String appointmentId,
        String doctorName,
        String specialty,
        String date,
        String time) {
}
