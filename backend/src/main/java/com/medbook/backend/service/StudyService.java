package com.medbook.backend.service;

import com.medbook.backend.model.Patient;
import com.medbook.backend.repository.PatientRepository;
import org.springframework.stereotype.Service;

import java.security.SecureRandom;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;

/**
 * Study enrolment: assigns each patient a group (A-D) and an anonymous study id.
 *
 * Assignment is "balanced random": the group with the fewest participants so
 * far is chosen, and ties are broken at random. This keeps the four groups the
 * same size (the plan is 30-50 volunteers each) while still being unpredictable.
 * The group is stored server-side and never changed afterwards.
 */
@Service
public class StudyService {

    public static final List<String> GROUPS = List.of("A", "B", "C", "D");

    public static String groupName(String group) {
        return switch (group == null ? "" : group) {
            case "A" -> "Control";
            case "B" -> "Points";
            case "C" -> "Discount";
            case "D" -> "Quality-gated";
            default -> "Unassigned";
        };
    }

    private static final String ID_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";

    private final PatientRepository patientRepository;
    private final SecureRandom random = new SecureRandom();

    public StudyService(PatientRepository patientRepository) {
        this.patientRepository = patientRepository;
    }

    /**
     * Fills in studyGroup / studyId on the patient if missing, WITHOUT saving
     * (the caller saves). Used at registration, where the caller persists the patient.
     */
    public synchronized void assignStudyFields(Patient patient) {
        if (patient.getStudyGroup() == null) {
            Map<String, Long> counts = new LinkedHashMap<>();
            for (String g : GROUPS) counts.put(g, patientRepository.countByStudyGroup(g));
            patient.setStudyGroup(pickGroup(counts, random));
        }
        if (patient.getStudyId() == null) {
            patient.setStudyId(newStudyId());
        }
    }

    /**
     * Makes sure an existing patient (e.g. a seeded demo account that registered
     * before the study module existed) is enrolled, and saves if anything changed.
     */
    public synchronized Patient ensureEnrolled(Patient patient) {
        if (patient.getStudyGroup() != null && patient.getStudyId() != null) {
            return patient;
        }
        assignStudyFields(patient);
        return patientRepository.save(patient);
    }

    /** Smallest group wins; ties are broken at random. Pure function, unit-tested. */
    public static String pickGroup(Map<String, Long> counts, Random rnd) {
        long min = Long.MAX_VALUE;
        for (String g : GROUPS) min = Math.min(min, counts.getOrDefault(g, 0L));
        java.util.ArrayList<String> candidates = new java.util.ArrayList<>();
        for (String g : GROUPS) {
            if (counts.getOrDefault(g, 0L) == min) candidates.add(g);
        }
        return candidates.get(rnd.nextInt(candidates.size()));
    }

    private String newStudyId() {
        String id;
        do {
            StringBuilder sb = new StringBuilder("P-");
            for (int i = 0; i < 6; i++) sb.append(ID_ALPHABET.charAt(random.nextInt(ID_ALPHABET.length())));
            id = sb.toString();
        } while (patientRepository.existsByStudyId(id));
        return id;
    }
}
