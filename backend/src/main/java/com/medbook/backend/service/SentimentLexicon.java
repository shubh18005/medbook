package com.medbook.backend.service;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.function.Function;

/**
 * A tiny English sentiment lexicon used ONLY for the "C" (rating-text
 * consistency) part of the quality score.
 *
 * This is deliberately a simple placeholder. The research plan replaces it
 * with the trained TF-IDF / DistilBERT model once those exist; keeping it
 * behind {@link #polarity(String)} means that swap touches one method.
 */
public final class SentimentLexicon {

    private SentimentLexicon() {}

    /**
     * Optional trained-model hook (see ModelSentimentClient). When set and it returns a value,
     * that value is used; when it is null or returns null, the word list below is used.
     */
    private static volatile Function<String, Integer> modelPolarity = null;

    public static void setModelPolarity(Function<String, Integer> f) { modelPolarity = f; }

    private static final Set<String> POSITIVE = new HashSet<>(Arrays.asList(
            "good", "great", "excellent", "amazing", "wonderful", "helpful", "polite", "friendly",
            "kind", "caring", "clean", "hygienic", "tidy", "quick", "fast", "smooth", "clear",
            "transparent", "professional", "satisfied", "happy", "best", "nice", "thorough",
            "attentive", "patient", "courteous", "pleasant", "comfortable", "supportive",
            "reasonable", "prompt", "cooperative", "spotless", "awesome", "fantastic", "perfect"));

    private static final Set<String> NEGATIVE = new HashSet<>(Arrays.asList(
            "bad", "poor", "terrible", "awful", "rude", "dirty", "unhygienic", "slow", "long",
            "delay", "delayed", "late", "crowded", "confusing", "expensive", "overpriced",
            "overcharged", "unhelpful", "careless", "dismissive", "rushed", "disappointed",
            "disappointing", "worst", "horrible", "smelly", "messy", "chaotic", "unprofessional",
            "ignored", "waste", "hidden", "uncomfortable", "pathetic", "worse", "unsatisfied",
            "unclear", "filthy", "disgusting", "negligent", "arrogant"));

    private static final Set<String> NEGATIONS = new HashSet<>(Arrays.asList(
            "not", "no", "never", "hardly", "without", "nothing"));

    /** Lower-cases, expands "n't", strips punctuation and splits into word tokens. */
    public static List<String> tokens(String text) {
        List<String> out = new ArrayList<>();
        if (text == null) return out;
        String t = text.toLowerCase(Locale.ROOT).replace("n't", " not").replace("n\u2019t", " not");
        StringBuilder cur = new StringBuilder();
        for (int i = 0; i < t.length(); i++) {
            char c = t.charAt(i);
            if (Character.isLetterOrDigit(c)) {
                cur.append(c);
            } else if (cur.length() > 0) {
                out.add(cur.toString());
                cur.setLength(0);
            }
        }
        if (cur.length() > 0) out.add(cur.toString());
        return out;
    }

    /**
     * Returns +1 (positive), 0 (neutral / no sentiment words / tie) or -1 (negative).
     * A negation word within the two preceding tokens flips a sentiment word
     * ("not clean" -> negative, "no delay" -> positive).
     */
    public static int polarity(String text) {
        Function<String, Integer> m = modelPolarity;
        if (m != null && text != null && !text.isBlank()) {
            try {
                Integer p = m.apply(text);
                if (p != null) return Integer.compare(p, 0);
            } catch (RuntimeException ignored) {
                // fall back to the word list
            }
        }
        return lexiconPolarity(text);
    }

    /** The original word-list rule (kept as the fallback and for tests). */
    public static int lexiconPolarity(String text) {
        List<String> toks = tokens(text);
        int pos = 0;
        int neg = 0;
        for (int i = 0; i < toks.size(); i++) {
            String w = toks.get(i);
            boolean isPos = POSITIVE.contains(w);
            boolean isNeg = NEGATIVE.contains(w);
            if (!isPos && !isNeg) continue;

            boolean negated = false;
            for (int j = Math.max(0, i - 2); j < i; j++) {
                if (NEGATIONS.contains(toks.get(j))) {
                    negated = true;
                    break;
                }
            }
            if (negated) {
                isPos = !isPos;
                isNeg = !isNeg;
            }
            if (isPos) pos++;
            if (isNeg) neg++;
        }
        return Integer.compare(pos, neg);
    }
}
