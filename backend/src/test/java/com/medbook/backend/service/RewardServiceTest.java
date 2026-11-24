package com.medbook.backend.service;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class RewardServiceTest {

    private final RewardService rewards = new RewardService(50, 10, "points");

    @Test
    void controlGroupGetsNothing() {
        RewardService.RewardOutcome r = rewards.decide("A", true);
        assertEquals("none", r.type());
        assertEquals(RewardService.STATUS_NOT_APPLICABLE, r.status());
        assertEquals(0, r.points());
    }

    @Test
    void pointsGroupIsRewardedRegardlessOfQuality() {
        for (boolean passed : new boolean[]{true, false}) {
            RewardService.RewardOutcome r = rewards.decide("B", passed);
            assertEquals("points", r.type());
            assertEquals(RewardService.STATUS_GRANTED, r.status());
            assertEquals(50, r.points());
        }
    }

    @Test
    void discountGroupGetsACode() {
        RewardService.RewardOutcome r = rewards.decide("C", false);
        assertEquals("discount", r.type());
        assertEquals(RewardService.STATUS_GRANTED, r.status());
        assertEquals(10, r.discountPercent());
        assertNotNull(r.code());
        assertTrue(r.code().startsWith("MB-"));
        assertEquals(11, r.code().length());
        assertNotEquals(r.code(), rewards.decide("C", false).code(), "codes should differ");
    }

    @Test
    void gatedGroupIsPaidOnlyWhenGatePassed() {
        assertEquals(RewardService.STATUS_GRANTED, rewards.decide("D", true).status());
        RewardService.RewardOutcome withheld = rewards.decide("D", false);
        assertEquals(RewardService.STATUS_WITHHELD, withheld.status());
        assertEquals(0, withheld.points());
        assertNull(withheld.code());
    }

    @Test
    void gatedGroupCanPayInDiscount() {
        RewardService asDiscount = new RewardService(50, 10, "discount");
        RewardService.RewardOutcome r = asDiscount.decide("D", true);
        assertEquals("discount", r.type());
        assertNotNull(r.code());
    }

    @Test
    void offerTexts() {
        assertEquals("none", rewards.offerFor("A"));
        assertEquals("points", rewards.offerFor("B"));
        assertEquals("discount", rewards.offerFor("C"));
        assertEquals("gated", rewards.offerFor("D"));
        assertEquals("", rewards.offerText("A"));
        assertTrue(rewards.offerText("B").contains("50 points"));
        assertTrue(rewards.offerText("C").contains("10%"));
        assertTrue(rewards.offerText("D").toLowerCase().contains("quality check"));
    }
}
