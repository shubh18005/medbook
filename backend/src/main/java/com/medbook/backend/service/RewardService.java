package com.medbook.backend.service;

import java.security.SecureRandom;

/**
 * Reward engine (synopsis Section 5.2.2 / Table 5.1). Applies the participant's
 * study group rule:
 *
 *   A  Control        no reward
 *   B  Points         points on submission
 *   C  Discount       discount code on submission
 *   D  Quality-gated  points (or discount, see study.reward.group-d-type) only if the quality check passed
 *
 * All rewards are SIMULATED (virtual points / discount codes), as stated in the
 * study's limitations.
 */
public class RewardService {

    public record RewardOutcome(String type, String status, int points, int discountPercent, String code) {}

    public static final String STATUS_NOT_APPLICABLE = "not_applicable";
    public static final String STATUS_GRANTED = "granted";
    public static final String STATUS_WITHHELD = "withheld";

    private static final String CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";

    private final int points;
    private final int discountPercent;
    private final String gatedType; // "points" | "discount"
    private final SecureRandom random = new SecureRandom();

    public RewardService(int points, int discountPercent, String gatedType) {
        this.points = points;
        this.discountPercent = discountPercent;
        this.gatedType = "discount".equalsIgnoreCase(gatedType) ? "discount" : "points";
    }

    public int getPoints() { return points; }
    public int getDiscountPercent() { return discountPercent; }
    public String getGatedType() { return gatedType; }

    /** What the reward on offer is, as shown to the patient before they submit: none | points | discount | gated. */
    public String offerFor(String group) {
        if (group == null) return "none";
        return switch (group) {
            case "B" -> "points";
            case "C" -> "discount";
            case "D" -> "gated";
            default -> "none";
        };
    }

    public String offerText(String group) {
        return switch (offerFor(group)) {
            case "points" -> "Earn " + points + " points for sharing your feedback.";
            case "discount" -> "Get a " + discountPercent + "% discount code for sharing your feedback.";
            case "gated" -> "Share thoughtful, specific feedback to earn "
                    + ("discount".equals(gatedType) ? "a " + discountPercent + "% discount code" : points + " points")
                    + ". A quality check applies.";
            default -> "";
        };
    }

    public RewardOutcome decide(String group, boolean passedGate) {
        if (group == null) return none();
        return switch (group) {
            case "B" -> grantPoints();
            case "C" -> grantDiscount();
            case "D" -> {
                if (!passedGate) yield new RewardOutcome(gatedType, STATUS_WITHHELD, 0, 0, null);
                yield "discount".equals(gatedType) ? grantDiscount() : grantPoints();
            }
            default -> none();
        };
    }

    public String messageFor(String group, RewardOutcome r) {
        if (STATUS_GRANTED.equals(r.status())) {
            if ("discount".equals(r.type())) {
                return "Thank you! Your " + r.discountPercent() + "% discount code is " + r.code() + ".";
            }
            return "Thank you! " + r.points() + " points have been added to your account.";
        }
        if (STATUS_WITHHELD.equals(r.status())) {
            return "Thank you! Your feedback is recorded. It did not meet the quality check for the reward - "
                    + "specific details about your visit help next time.";
        }
        return "Thank you! Your feedback has been recorded.";
    }

    private RewardOutcome none() {
        return new RewardOutcome("none", STATUS_NOT_APPLICABLE, 0, 0, null);
    }

    private RewardOutcome grantPoints() {
        return new RewardOutcome("points", STATUS_GRANTED, points, 0, null);
    }

    private RewardOutcome grantDiscount() {
        return new RewardOutcome("discount", STATUS_GRANTED, 0, discountPercent, newCode());
    }

    private String newCode() {
        StringBuilder sb = new StringBuilder("MB-");
        for (int i = 0; i < 8; i++) sb.append(CODE_ALPHABET.charAt(random.nextInt(CODE_ALPHABET.length())));
        return sb.toString();
    }
}
