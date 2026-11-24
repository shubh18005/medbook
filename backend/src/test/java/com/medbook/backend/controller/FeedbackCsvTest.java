package com.medbook.backend.controller;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

class FeedbackCsvTest {

    @Test
    void plainValuesAreUnchanged() {
        assertEquals("hello", FeedbackController.csv("hello"));
        assertEquals("4", FeedbackController.csv(4));
        assertEquals("", FeedbackController.csv(null));
    }

    @Test
    void commasQuotesAndNewlinesAreQuoted() {
        assertEquals("\"a,b\"", FeedbackController.csv("a,b"));
        assertEquals("\"say \"\"hi\"\"\"", FeedbackController.csv("say \"hi\""));
        assertEquals("\"line1\nline2\"", FeedbackController.csv("line1\nline2"));
    }

    @Test
    void formulaInjectionIsNeutralised() {
        assertEquals("'=SUM(A1:A9)", FeedbackController.csv("=SUM(A1:A9)"));
        assertEquals("'+cmd", FeedbackController.csv("+cmd"));
        assertEquals("'@x", FeedbackController.csv("@x"));
    }
}
