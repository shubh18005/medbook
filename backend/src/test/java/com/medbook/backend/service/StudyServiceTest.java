package com.medbook.backend.service;

import org.junit.jupiter.api.Test;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Random;

import static org.junit.jupiter.api.Assertions.*;

class StudyServiceTest {

    @Test
    void pickGroupChoosesTheSmallestGroup() {
        Map<String, Long> counts = new LinkedHashMap<>();
        counts.put("A", 5L); counts.put("B", 3L); counts.put("C", 4L); counts.put("D", 6L);
        assertEquals("B", StudyService.pickGroup(counts, new Random(1)));
    }

    @Test
    void assignmentStaysBalancedAndUsesAllGroups() {
        Map<String, Long> counts = new LinkedHashMap<>();
        for (String g : StudyService.GROUPS) counts.put(g, 0L);
        Random rnd = new Random(42);
        for (int i = 0; i < 203; i++) {
            String g = StudyService.pickGroup(counts, rnd);
            counts.put(g, counts.get(g) + 1);
        }
        long min = Long.MAX_VALUE, max = 0;
        for (long c : counts.values()) { min = Math.min(min, c); max = Math.max(max, c); }
        assertTrue(max - min <= 1, "groups differ by at most one participant: " + counts);
    }

    @Test
    void tiesAreBrokenAtRandom() {
        Map<String, Long> counts = new LinkedHashMap<>();
        for (String g : StudyService.GROUPS) counts.put(g, 0L);
        java.util.Set<String> seen = new java.util.HashSet<>();
        Random rnd = new Random(7);
        for (int i = 0; i < 50; i++) seen.add(StudyService.pickGroup(counts, rnd));
        assertEquals(4, seen.size());
    }

    @Test
    void groupNames() {
        assertEquals("Control", StudyService.groupName("A"));
        assertEquals("Quality-gated", StudyService.groupName("D"));
    }
}
