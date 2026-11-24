package com.medbook.backend.service;

import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/** Unit tests for the quality gate Q = w1*D + w2*U + w3*C (no Spring needed). */
class QualityScorerTest {

    // Same defaults as application.properties.
    private final QualityScorer scorer = new QualityScorer(0.4, 0.3, 0.3, 0.75);

    @Test
    void oneWordGoodIsWithheld() {
        QualityScorer.GateResult r = scorer.evaluate("good", 5, List.of());
        assertEquals(0.0, r.uniqueness(), 1e-9, "generic one-liner counts as a template");
        assertFalse(r.passed());
    }

    @Test
    void twoWordReviewDoesNotPass() {
        assertFalse(scorer.evaluate("nice doctor", 5, List.of()).passed());
    }

    @Test
    void repeatedWordSpamDoesNotPassEvenWhenNeutral() {
        // A neutral 3-star rating makes the consistency part full, so detail must carry the check.
        String spam = "ok ok ok ok ok ok ok ok ok ok ok ok ok ok ok ok ok ok ok ok";
        assertFalse(scorer.evaluate(spam, 3, List.of()).passed());
    }

    @Test
    void negativeButDetailedFeedbackIsNotPunished() {
        String text = "Waited over an hour, staff were rude. The doctor was fine though.";
        assertTrue(scorer.evaluate(text, 2, List.of()).passed(), "the gate checks effort, not sentiment");
    }

    @Test
    void ratingOnlyScoresZero() {
        QualityScorer.GateResult r = scorer.evaluate("", 4, List.of());
        assertEquals(0.0, r.quality(), 1e-9);
        assertFalse(r.passed());
    }

    @Test
    void detailedConsistentReviewPasses() {
        String text = "The doctor explained everything clearly and was very caring. "
                + "The staff were polite and the waiting time was short.";
        QualityScorer.GateResult r = scorer.evaluate(text, 5, List.of());
        assertTrue(r.aspectsMentioned() >= 3, "doctor, staff and waiting time are mentioned");
        assertEquals(1.0, r.uniqueness(), 1e-9);
        assertEquals(1.0, r.consistency(), 1e-9);
        assertTrue(r.passed());
    }

    @Test
    void shortButSpecificReviewPasses() {
        assertTrue(scorer.evaluate("Doctor was good and staff polite", 5, List.of()).passed());
    }

    @Test
    void exactDuplicateIsNotUnique() {
        String text = "Doctor was very helpful and the clinic was clean";
        QualityScorer.GateResult r = scorer.evaluate(text, 5, List.of("doctor was VERY helpful, and the clinic was clean!"));
        assertEquals(0.0, r.uniqueness(), 1e-9);
    }

    @Test
    void nearCopyIsNotUnique() {
        String earlier = "the doctor listened carefully explained the treatment and the staff were polite throughout";
        String copy = earlier + " today";
        assertEquals(0.0, scorer.evaluate(copy, 5, List.of(earlier)).uniqueness(), 1e-9);
    }

    @Test
    void differentTextIsUnique() {
        QualityScorer.GateResult r = scorer.evaluate("Billing was clear and quick", 5,
                List.of("The washroom was dirty and the queue was long"));
        assertEquals(1.0, r.uniqueness(), 1e-9);
    }

    @Test
    void ratingTextMismatchLowersConsistency() {
        // 5 stars but a clearly negative text
        assertEquals(0.0, QualityScorer.consistency("terrible rude staff and a dirty clinic", 5), 1e-9);
        // mixed text vs a 3-star rating: partial agreement
        assertEquals(0.5, QualityScorer.consistency("Doctor was great but the clinic was dirty and the wait was long", 3), 1e-9);
    }

    @Test
    void negationFlipsSentiment() {
        assertEquals(-1, SentimentLexicon.polarity("the clinic was not clean"));
        assertEquals(1, SentimentLexicon.polarity("there was no delay at all"));
        assertEquals(-1, SentimentLexicon.polarity("the doctor wasn't helpful"));
        assertEquals(0, SentimentLexicon.polarity("I came on Tuesday"));
    }

    @Test
    void aspectDetection() {
        assertEquals(5, QualityScorer.aspectsMentioned(
                "doctor was kind, nurse was polite, long wait, clean washroom, fair bill"));
        assertEquals(0, QualityScorer.aspectsMentioned("it was fine overall"));
    }

    @Test
    void weightsMustSumToOne() {
        assertThrows(IllegalArgumentException.class, () -> new QualityScorer(0.5, 0.3, 0.3, 0.7));
        assertThrows(IllegalArgumentException.class, () -> new QualityScorer(-0.1, 0.6, 0.5, 0.7));
    }

    @Test
    void qualityIsWeightedSumOfParts() {
        QualityScorer.GateResult r = scorer.evaluate("Doctor was good and staff polite", 5, List.of());
        double expected = 0.4 * r.detail() + 0.3 * r.uniqueness() + 0.3 * r.consistency();
        assertEquals(expected, r.quality(), 1e-3);
    }
}
