package com.medbook.backend.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * One patient feedback submission (synopsis Table 6.2, "Feedback entity").
 *
 * Deliberately holds NO patient name/email/id - only the anonymised
 * {@code studyId} - so exports for analysis are pseudonymous. The unique
 * constraint on appointmentId enforces "one feedback per appointment".
 */
@Entity
@Table(name = "feedback")
@Data
@NoArgsConstructor
public class Feedback {

    @Id
    private String id;

    @Column(unique = true, nullable = false)
    private String appointmentId;

    private String studyId;
    private String studyGroup; // A | B | C | D
    private String doctorId;

    private Integer overallRating;      // 1..5
    private Integer ratingDoctor;       // optional 1..5
    private Integer ratingStaff;
    private Integer ratingWaiting;
    private Integer ratingCleanliness;
    private Integer ratingBilling;

    @Column(length = 2000)
    private String freeText;

    // Quality gate: Q = w1*D + w2*U + w3*C
    private Integer wordCount;
    private Integer aspectsMentioned;
    private Double detailScore;
    private Double uniquenessScore;
    private Double consistencyScore;
    private Double qualityScore;
    private Boolean gatePassed;

    // Reward outcome
    private String rewardType;      // none | points | discount
    private String rewardStatus;    // not_applicable | granted | withheld
    private Integer rewardPoints;
    private Integer rewardDiscountPercent;
    private String rewardCode;

    private String submittedAt;
}
