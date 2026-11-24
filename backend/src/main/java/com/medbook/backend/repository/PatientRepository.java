package com.medbook.backend.repository;

import com.medbook.backend.model.Patient;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface PatientRepository extends JpaRepository<Patient, String> {
    Optional<Patient> findByEmail(String email);
    boolean existsByEmail(String email);

    // Feedback study: balanced group assignment and unique anonymous ids.
    long countByStudyGroup(String studyGroup);
    boolean existsByStudyId(String studyId);
}
