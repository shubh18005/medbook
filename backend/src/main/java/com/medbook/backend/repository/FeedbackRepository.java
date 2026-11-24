package com.medbook.backend.repository;

import com.medbook.backend.model.Feedback;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;

public interface FeedbackRepository extends JpaRepository<Feedback, String> {

    // One feedback per appointment.
    boolean existsByAppointmentId(String appointmentId);

    // A participant's own history, newest first (joined via the anonymous study id).
    List<Feedback> findByStudyIdOrderBySubmittedAtDesc(String studyId);

    // Used by the quality gate's duplicate / template check (the "U" component).
    @Query("select f.freeText from Feedback f where f.freeText is not null and f.freeText <> ''")
    List<String> findAllTexts();
}
