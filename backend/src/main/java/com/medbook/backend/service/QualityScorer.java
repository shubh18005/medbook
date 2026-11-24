package com.medbook.backend.service;

import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * Quality gate (synopsis Section 5.2.3):
 *
 *     Q = w1*D + w2*U + w3*C,   w1 + w2 + w3 = 1
 *
 *  D in [0,1]  detail        - text length (distinct words) and number of aspects mentioned
 *  U in {0,1}  uniqueness    - 1 if the text is not a duplicate / template of earlier submissions
 *  C in [0,1]  consistency   - agreement between star rating and polarity of the text
 *
 * In group D the reward is released only when Q >= theta. Weights and theta
 * are design parameters to be tuned on the pilot (see application.properties).
 *
 * Plain Java on purpose (no Spring types) so it can be unit-tested directly.
 */
public class QualityScorer {

    /** Result of one evaluation. All scores are rounded to 4 decimals. */
    public record GateResult(double detail, double uniqueness, double consistency,
                             double quality, boolean passed, int words, int aspectsMentioned) {}

    /** Generic one-liners that count as "template" feedback (U = 0). Compared after normalisation. */
    private static final Set<String> GENERIC = new HashSet<>(Arrays.asList(
            "good", "very good", "nice", "very nice", "ok", "okay", "fine", "excellent", "great",
            "best", "bad", "worst", "average", "nice doctor", "good doctor", "great doctor",
            "best doctor", "good service", "nice service", "all good", "everything is good",
            "thank you", "thanks", "na", "nil", "none", "no comments", "no comment", "test",
            "testing", "good experience", "nice experience", "satisfied", "very satisfied"));

    private static final double TEMPLATE_SIMILARITY = 0.9;
    private static final double WORDS_FOR_FULL_DETAIL = 20.0;
    private static final double ASPECTS_FOR_FULL_DETAIL = 3.0;

    private final double wDetail;
    private final double wUnique;
    private final double wConsistency;
    private final double threshold;

    public QualityScorer(double wDetail, double wUnique, double wConsistency, double threshold) {
        if (wDetail < 0 || wUnique < 0 || wConsistency < 0) {
            throw new IllegalArgumentException("Quality-score weights must not be negative.");
        }
        if (Math.abs(wDetail + wUnique + wConsistency - 1.0) > 1e-6) {
            throw new IllegalArgumentException("Quality-score weights must sum to 1 (got "
                    + (wDetail + wUnique + wConsistency) + ").");
        }
        this.wDetail = wDetail;
        this.wUnique = wUnique;
        this.wConsistency = wConsistency;
        this.threshold = threshold;
    }

    public double getThreshold() { return threshold; }
    public double getWDetail() { return wDetail; }
    public double getWUnique() { return wUnique; }
    public double getWConsistency() { return wConsistency; }

    /**
     * @param freeText      the optional free text (may be null/blank)
     * @param overallRating 1..5 star rating
     * @param previousTexts free texts of earlier submissions, for the duplicate/template check
     */
    public GateResult evaluate(String freeText, int overallRating, List<String> previousTexts) {
        String text = freeText == null ? "" : freeText.trim();
        int words = SentimentLexicon.tokens(text).size();
        int aspects = aspectsMentioned(text);

        // Length counts DISTINCT words, so repeating one word 20 times earns no detail credit.
        int distinctWords = new HashSet<>(SentimentLexicon.tokens(text)).size();
        double d = detail(distinctWords, aspects);
        double u = uniqueness(text, previousTexts);
        double c = consistency(text, overallRating);

        double q = wDetail * d + wUnique * u + wConsistency * c;
        boolean passed = q + 1e-9 >= threshold;
        return new GateResult(round4(d), round4(u), round4(c), round4(q), passed, words, aspects);
    }

    // ---------------------------------------------------------------- D

    static double detail(int words, int aspects) {
        double lengthPart = Math.min(words / WORDS_FOR_FULL_DETAIL, 1.0);
        double aspectPart = Math.min(aspects / ASPECTS_FOR_FULL_DETAIL, 1.0);
        return 0.5 * lengthPart + 0.5 * aspectPart;
    }

    /** Number of the five study aspects (doctor, staff, waiting, cleanliness, billing) the text touches. */
    public static int aspectsMentioned(String text) {
        List<String> toks = SentimentLexicon.tokens(text);
        int count = 0;
        for (AspectWords a : ASPECTS) {
            if (a.matches(toks)) count++;
        }
        return count;
    }

    private record AspectWords(Set<String> exact, List<String> stems) {
        boolean matches(List<String> tokens) {
            for (String t : tokens) {
                if (exact.contains(t)) return true;
                for (String s : stems) {
                    if (t.startsWith(s)) return true;
                }
            }
            return false;
        }
    }

    private static Set<String> set(String... words) {
        return new HashSet<>(Arrays.asList(words));
    }

    private static final List<AspectWords> ASPECTS = List.of(
            // doctor
            new AspectWords(set("dr", "listened", "treatment", "medicine", "medicines", "prescription", "checkup"),
                    List.of("doctor", "consult", "diagnos", "explain")),
            // staff
            new AspectWords(set("staff", "behaviour", "behavior", "polite", "rude", "helpful", "courteous", "attendant"),
                    List.of("nurs", "recept")),
            // waiting time
            new AspectWords(set("delay", "delayed", "slot", "late", "crowded"),
                    List.of("wait", "queue")),
            // cleanliness
            new AspectWords(set("dirty", "smell", "smelly", "tidy", "sanitary", "unhygienic", "filthy", "spotless", "messy"),
                    List.of("clean", "hygien", "wash", "toilet")),
            // billing
            new AspectWords(set("fee", "fees", "price", "prices", "cost", "payment", "pay", "paid", "charges",
                    "charge", "receipt", "expensive", "overcharged", "overpriced"),
                    List.of("bill")));

    // ---------------------------------------------------------------- U

    static String normalise(String text) {
        return String.join(" ", SentimentLexicon.tokens(text));
    }

    static double uniqueness(String text, List<String> previousTexts) {
        String norm = normalise(text);
        if (norm.isEmpty()) return 0.0;                 // nothing original was written
        if (GENERIC.contains(norm)) return 0.0;          // template one-liner

        Set<String> mine = new HashSet<>(SentimentLexicon.tokens(text));
        if (previousTexts != null) {
            for (String prev : previousTexts) {
                if (prev == null) continue;
                String pn = normalise(prev);
                if (pn.isEmpty()) continue;
                if (pn.equals(norm)) return 0.0;         // exact duplicate
                Set<String> theirs = new HashSet<>(SentimentLexicon.tokens(prev));
                if (jaccard(mine, theirs) >= TEMPLATE_SIMILARITY) return 0.0; // near-copy
            }
        }
        return 1.0;
    }

    private static double jaccard(Set<String> a, Set<String> b) {
        if (a.isEmpty() && b.isEmpty()) return 1.0;
        Set<String> inter = new HashSet<>(a);
        inter.retainAll(b);
        Set<String> union = new HashSet<>(a);
        union.addAll(b);
        return union.isEmpty() ? 0.0 : (double) inter.size() / union.size();
    }

    // ---------------------------------------------------------------- C

    static double consistency(String text, int overallRating) {
        if (text == null || text.isBlank()) return 0.0;   // nothing to compare the stars against
        int fromText = SentimentLexicon.polarity(text);
        int fromStars = overallRating >= 4 ? 1 : (overallRating == 3 ? 0 : -1);
        int diff = Math.abs(fromText - fromStars);
        return diff == 0 ? 1.0 : (diff == 1 ? 0.5 : 0.0);
    }

    private static double round4(double x) {
        return Math.round(x * 10000.0) / 10000.0;
    }
}
