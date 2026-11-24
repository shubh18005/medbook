package com.medbook.backend.config;

import com.medbook.backend.service.QualityScorer;
import com.medbook.backend.service.ModelSentimentClient;
import com.medbook.backend.service.RewardService;
import com.medbook.backend.service.SentimentLexicon;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/** Wires the plain-Java study services using the values in {@link StudyProperties}. */
@Configuration
public class StudyConfig {

    // Throws at startup if the weights don't sum to 1, so a bad config is caught immediately.
    @Bean
    public QualityScorer qualityScorer(StudyProperties p) {
        // Optional: use the trained aspect model (analysis/serve.py) for the C (consistency) part.
        // Empty URL = keep the built-in word list. If the service is down, the word list is used anyway.
        if (!p.getSentimentModelUrl().isEmpty()) {
            SentimentLexicon.setModelPolarity(new ModelSentimentClient(p.getSentimentModelUrl(), 1500, 30_000));
        }
        return new QualityScorer(p.getWDetail(), p.getWUnique(), p.getWConsistency(), p.getThreshold());
    }

    @Bean
    public RewardService rewardService(StudyProperties p) {
        return new RewardService(p.getRewardPoints(), p.getRewardDiscountPercent(), p.getGatedRewardType());
    }
}
