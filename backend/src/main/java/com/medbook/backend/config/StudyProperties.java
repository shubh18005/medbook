package com.medbook.backend.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/**
 * Tunable parameters of the feedback study, read from application.properties
 * (prefix "study."). The quality-gate weights, threshold and reward values are
 * "design parameters ... set on a small pilot" (synopsis Section 5.2.3), so
 * they live in configuration rather than being hard-coded.
 */
@Component
public class StudyProperties {

    private final double wDetail;
    private final double wUnique;
    private final double wConsistency;
    private final double threshold;
    private final int rewardPoints;
    private final int rewardDiscountPercent;
    private final String gatedRewardType;
    private final int maxTextLength;
    private final String sentimentModelUrl;

    public StudyProperties(
            @Value("${study.quality.w-detail:0.4}") double wDetail,
            @Value("${study.quality.w-unique:0.3}") double wUnique,
            @Value("${study.quality.w-consistency:0.3}") double wConsistency,
            @Value("${study.quality.threshold:0.75}") double threshold,
            @Value("${study.reward.points:50}") int rewardPoints,
            @Value("${study.reward.discount-percent:10}") int rewardDiscountPercent,
            @Value("${study.reward.group-d-type:points}") String gatedRewardType,
            @Value("${study.feedback.max-text-length:1000}") int maxTextLength,
            @Value("${study.sentiment.model-url:}") String sentimentModelUrl) {
        this.wDetail = wDetail;
        this.wUnique = wUnique;
        this.wConsistency = wConsistency;
        this.threshold = threshold;
        this.rewardPoints = rewardPoints;
        this.rewardDiscountPercent = rewardDiscountPercent;
        this.gatedRewardType = gatedRewardType;
        this.maxTextLength = maxTextLength;
        this.sentimentModelUrl = sentimentModelUrl == null ? "" : sentimentModelUrl.trim();
    }

    public double getWDetail() { return wDetail; }
    public double getWUnique() { return wUnique; }
    public double getWConsistency() { return wConsistency; }
    public double getThreshold() { return threshold; }
    public int getRewardPoints() { return rewardPoints; }
    public int getRewardDiscountPercent() { return rewardDiscountPercent; }
    public String getGatedRewardType() { return gatedRewardType; }
    public int getMaxTextLength() { return maxTextLength; }
    public String getSentimentModelUrl() { return sentimentModelUrl; }
}
