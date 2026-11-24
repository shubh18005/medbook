package com.medbook.backend.controller;

import com.medbook.backend.config.StudyProperties;
import com.medbook.backend.dto.*;
import com.medbook.backend.exception.ApiException;
import com.medbook.backend.model.Appointment;
import com.medbook.backend.model.Feedback;
import com.medbook.backend.model.Patient;
import com.medbook.backend.repository.AppointmentRepository;
import com.medbook.backend.repository.FeedbackRepository;
import com.medbook.backend.repository.PatientRepository;
import com.medbook.backend.security.AuthUtil;
import com.medbook.backend.service.QualityScorer;
import com.medbook.backend.service.RewardService;
import com.medbook.backend.service.StudyService;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/**
 * Feedback checkpoint, reward engine and quality gate (synopsis Chapter 5 / 6.2).
 *
 *   GET  /api/feedback/status  patient  - pending checkpoints, reward on offer, own history
 *   POST /api/feedback         patient  - submit feedback for a completed appointment
 *   GET  /api/feedback/stats   admin    - group-wise study measures (RQ1-RQ3)
 *   GET  /api/feedback/export  admin    - anonymised CSV for the Python analysis pipeline
 */
@RestController
@RequestMapping("/api/feedback")
public class FeedbackController {

    private static final List<String> ASPECT_KEYS = List.of("doctor", "staff", "waiting", "cleanliness", "billing");

    private final FeedbackRepository feedbackRepository;
    private final AppointmentRepository appointmentRepository;
    private final PatientRepository patientRepository;
    private final StudyService studyService;
    private final QualityScorer qualityScorer;
    private final RewardService rewardService;
    private final StudyProperties props;

    public FeedbackController(FeedbackRepository feedbackRepository,
                              AppointmentRepository appointmentRepository,
                              PatientRepository patientRepository,
                              StudyService studyService,
                              QualityScorer qualityScorer,
                              RewardService rewardService,
                              StudyProperties props) {
        this.feedbackRepository = feedbackRepository;
        this.appointmentRepository = appointmentRepository;
        this.patientRepository = patientRepository;
        this.studyService = studyService;
        this.qualityScorer = qualityScorer;
        this.rewardService = rewardService;
        this.props = props;
    }

    // ------------------------------------------------------------------ patient: status

    @GetMapping("/status")
    public FeedbackStatusDto status() {
        Patient patient = requirePatient();
        String studyId = patient.getStudyId();
        String group = patient.getStudyGroup();

        List<Feedback> mine = feedbackRepository.findByStudyIdOrderBySubmittedAtDesc(studyId);
        Set<String> answered = new HashSet<>();
        for (Feedback f : mine) answered.add(f.getAppointmentId());

        // The trigger: a completed consultation with no feedback yet.
        List<PendingFeedbackDto> pending = new ArrayList<>();
        for (Appointment a : appointmentRepository.findByPatientIdAndStatus(patient.getId(), "completed")) {
            if (!answered.contains(a.getId())) {
                pending.add(new PendingFeedbackDto(a.getId(), a.getDoctorName(), a.getSpecialty(), a.getDate(), a.getTime()));
            }
        }
        pending.sort((x, y) -> String.valueOf(y.date()).compareTo(String.valueOf(x.date())));

        List<FeedbackResultDto> history = new ArrayList<>();
        int totalPoints = 0;
        List<DiscountDto> discounts = new ArrayList<>();
        for (Feedback f : mine) {
            history.add(toResult(f));
            if (RewardService.STATUS_GRANTED.equals(f.getRewardStatus())) {
                if (f.getRewardPoints() != null) totalPoints += f.getRewardPoints();
                if ("discount".equals(f.getRewardType()) && f.getRewardCode() != null) {
                    discounts.add(new DiscountDto(f.getRewardCode(),
                            f.getRewardDiscountPercent() == null ? 0 : f.getRewardDiscountPercent()));
                }
            }
        }

        return new FeedbackStatusDto(
                rewardService.offerFor(group),
                rewardService.offerText(group),
                patient.getConsentAt() != null,
                props.getMaxTextLength(),
                pending, history, totalPoints, discounts);
    }

    // ------------------------------------------------------------------ patient: submit

    @PostMapping
    public ResponseEntity<FeedbackResultDto> submit(@RequestBody SubmitFeedbackRequest req) {
        Patient patient = requirePatient();

        // ---- validation (never trust the client) ----
        if (req.appointmentId() == null || req.appointmentId().isBlank()) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "appointmentId is required.");
        }
        int overall = requireRating(req.overallRating(), "Overall rating");
        Integer rDoctor = optionalRating(req.ratingDoctor(), "Doctor rating");
        Integer rStaff = optionalRating(req.ratingStaff(), "Staff rating");
        Integer rWaiting = optionalRating(req.ratingWaiting(), "Waiting-time rating");
        Integer rClean = optionalRating(req.ratingCleanliness(), "Cleanliness rating");
        Integer rBilling = optionalRating(req.ratingBilling(), "Billing rating");

        String text = req.freeText() == null ? "" : req.freeText().trim();
        if (text.length() > props.getMaxTextLength()) {
            throw new ApiException(HttpStatus.BAD_REQUEST,
                    "Feedback text must be at most " + props.getMaxTextLength() + " characters.");
        }

        // ---- the appointment must be this patient's, and completed ----
        Appointment apt = appointmentRepository.findById(req.appointmentId())
                .orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND, "Appointment not found."));
        if (!patient.getId().equals(apt.getPatientId())) {
            throw new ApiException(HttpStatus.FORBIDDEN, "You can only give feedback on your own consultations.");
        }
        if (!"completed".equals(apt.getStatus())) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "Feedback can only be given for completed consultations.");
        }
        if (feedbackRepository.existsByAppointmentId(apt.getId())) {
            throw new ApiException(HttpStatus.CONFLICT, "Feedback has already been submitted for this consultation.");
        }

        // ---- informed consent (voluntary participation) ----
        if (patient.getConsentAt() == null) {
            if (!Boolean.TRUE.equals(req.consent())) {
                throw new ApiException(HttpStatus.BAD_REQUEST,
                        "Please give your consent to take part in the study before submitting.");
            }
            patient.setConsentAt(Instant.now().toString());
            patient = patientRepository.save(patient);
        }

        // ---- quality gate, then reward engine ----
        QualityScorer.GateResult gate = qualityScorer.evaluate(text, overall, feedbackRepository.findAllTexts());
        RewardService.RewardOutcome reward = rewardService.decide(patient.getStudyGroup(), gate.passed());

        Feedback f = new Feedback();
        f.setId("fb-" + UUID.randomUUID());
        f.setAppointmentId(apt.getId());
        f.setStudyId(patient.getStudyId());
        f.setStudyGroup(patient.getStudyGroup());
        f.setDoctorId(apt.getDoctorId());
        f.setOverallRating(overall);
        f.setRatingDoctor(rDoctor);
        f.setRatingStaff(rStaff);
        f.setRatingWaiting(rWaiting);
        f.setRatingCleanliness(rClean);
        f.setRatingBilling(rBilling);
        f.setFreeText(text.isEmpty() ? null : text);
        f.setWordCount(gate.words());
        f.setAspectsMentioned(gate.aspectsMentioned());
        f.setDetailScore(gate.detail());
        f.setUniquenessScore(gate.uniqueness());
        f.setConsistencyScore(gate.consistency());
        f.setQualityScore(gate.quality());
        f.setGatePassed(gate.passed());
        f.setRewardType(reward.type());
        f.setRewardStatus(reward.status());
        f.setRewardPoints(reward.points());
        f.setRewardDiscountPercent(reward.discountPercent());
        f.setRewardCode(reward.code());
        f.setSubmittedAt(Instant.now().toString());

        try {
            feedbackRepository.save(f);
        } catch (DataIntegrityViolationException e) {
            // Two simultaneous submits for the same appointment: the unique constraint wins.
            throw new ApiException(HttpStatus.CONFLICT, "Feedback has already been submitted for this consultation.");
        }

        return ResponseEntity.status(HttpStatus.CREATED).body(toResult(f, apt));
    }

    // ------------------------------------------------------------------ admin: stats

    @GetMapping("/stats")
    public StudyStatsDto stats() {
        requireAdmin();

        List<Patient> patients = patientRepository.findAll();
        Set<String> patientsWithCompletedVisit = new HashSet<>();
        for (Appointment a : appointmentRepository.findByStatus("completed")) {
            patientsWithCompletedVisit.add(a.getPatientId());
        }
        List<Feedback> all = feedbackRepository.findAll();

        double threshold = qualityScorer.getThreshold();
        List<GroupStatsDto> groups = new ArrayList<>();
        int[] histogram = new int[5];

        for (String g : StudyService.GROUPS) {
            long enrolled = 0;
            long shown = 0;
            for (Patient p : patients) {
                if (!g.equals(p.getStudyGroup())) continue;
                enrolled++;
                if (patientsWithCompletedVisit.contains(p.getId())) shown++;
            }

            List<Feedback> fs = new ArrayList<>();
            Set<String> respondents = new HashSet<>();
            for (Feedback f : all) {
                if (g.equals(f.getStudyGroup())) {
                    fs.add(f);
                    respondents.add(f.getStudyId());
                }
            }
            long responded = respondents.size();
            double responseRate = shown == 0 ? 0.0 : round2(100.0 * responded / shown);

            double sumRating = 0, sumWords = 0, sumQ = 0;
            long neutral = 0, low = 0, granted = 0, withheld = 0;
            Map<String, double[]> aspectAcc = new LinkedHashMap<>();
            for (String k : ASPECT_KEYS) aspectAcc.put(k, new double[]{0, 0}); // sum, count

            for (Feedback f : fs) {
                int rating = f.getOverallRating() == null ? 0 : f.getOverallRating();
                sumRating += rating;
                if (rating == 3) neutral++;
                sumWords += f.getWordCount() == null ? 0 : f.getWordCount();
                double q = f.getQualityScore() == null ? 0.0 : f.getQualityScore();
                sumQ += q;
                if (q < threshold) low++;
                if (RewardService.STATUS_GRANTED.equals(f.getRewardStatus())) granted++;
                if (RewardService.STATUS_WITHHELD.equals(f.getRewardStatus())) withheld++;
                histogram[Math.min(4, (int) (q * 5))]++;
                addAspect(aspectAcc, "doctor", f.getRatingDoctor());
                addAspect(aspectAcc, "staff", f.getRatingStaff());
                addAspect(aspectAcc, "waiting", f.getRatingWaiting());
                addAspect(aspectAcc, "cleanliness", f.getRatingCleanliness());
                addAspect(aspectAcc, "billing", f.getRatingBilling());
            }

            int n = fs.size();
            Map<String, Double> meanAspect = new LinkedHashMap<>();
            for (Map.Entry<String, double[]> e : aspectAcc.entrySet()) {
                double[] acc = e.getValue();
                meanAspect.put(e.getKey(), acc[1] == 0 ? 0.0 : round2(acc[0] / acc[1]));
            }

            groups.add(new GroupStatsDto(
                    g, StudyService.groupName(g), enrolled, shown, responded, responseRate, n,
                    n == 0 ? 0.0 : round2(sumRating / n),
                    n == 0 ? 0.0 : round2(100.0 * neutral / n),
                    n == 0 ? 0.0 : round2(sumWords / n),
                    n == 0 ? 0.0 : round2(sumQ / n),
                    n == 0 ? 0.0 : round2(100.0 * low / n),
                    granted, withheld, meanAspect));
        }

        List<Integer> hist = new ArrayList<>();
        for (int h : histogram) hist.add(h);

        Map<String, Object> config = new LinkedHashMap<>();
        config.put("wDetail", qualityScorer.getWDetail());
        config.put("wUnique", qualityScorer.getWUnique());
        config.put("wConsistency", qualityScorer.getWConsistency());
        config.put("threshold", qualityScorer.getThreshold());
        config.put("rewardPoints", rewardService.getPoints());
        config.put("rewardDiscountPercent", rewardService.getDiscountPercent());
        config.put("groupDRewardType", rewardService.getGatedType());

        return new StudyStatsDto(groups, all.size(), hist, config);
    }

    // ------------------------------------------------------------------ admin: export

    @GetMapping("/export")
    public ResponseEntity<String> export() {
        requireAdmin();

        List<Feedback> all = new ArrayList<>(feedbackRepository.findAll());
        all.sort((a, b) -> String.valueOf(a.getSubmittedAt()).compareTo(String.valueOf(b.getSubmittedAt())));

        StringBuilder sb = new StringBuilder();
        sb.append("studyId,group,doctorId,submittedAt,overallRating,ratingDoctor,ratingStaff,ratingWaiting,")
          .append("ratingCleanliness,ratingBilling,freeText,wordCount,aspectsMentioned,")
          .append("detailD,uniquenessU,consistencyC,qualityQ,gatePassed,rewardType,rewardStatus\n");
        for (Feedback f : all) {
            sb.append(csv(f.getStudyId())).append(',')
              .append(csv(f.getStudyGroup())).append(',')
              .append(csv(f.getDoctorId())).append(',')
              .append(csv(f.getSubmittedAt())).append(',')
              .append(csv(f.getOverallRating())).append(',')
              .append(csv(f.getRatingDoctor())).append(',')
              .append(csv(f.getRatingStaff())).append(',')
              .append(csv(f.getRatingWaiting())).append(',')
              .append(csv(f.getRatingCleanliness())).append(',')
              .append(csv(f.getRatingBilling())).append(',')
              .append(csv(f.getFreeText())).append(',')
              .append(csv(f.getWordCount())).append(',')
              .append(csv(f.getAspectsMentioned())).append(',')
              .append(csv(f.getDetailScore())).append(',')
              .append(csv(f.getUniquenessScore())).append(',')
              .append(csv(f.getConsistencyScore())).append(',')
              .append(csv(f.getQualityScore())).append(',')
              .append(csv(f.getGatePassed())).append(',')
              .append(csv(f.getRewardType())).append(',')
              .append(csv(f.getRewardStatus())).append('\n');
        }

        return ResponseEntity.ok()
                .header("Content-Type", "text/csv; charset=UTF-8")
                .header("Content-Disposition", "attachment; filename=\"medbook-feedback-export.csv\"")
                .body(sb.toString());
    }

    // ------------------------------------------------------------------ helpers

    private Patient requirePatient() {
        if (!"patient".equals(AuthUtil.currentRole())) {
            throw new ApiException(HttpStatus.FORBIDDEN, "You don't have permission to do that.");
        }
        Patient patient = patientRepository.findById(AuthUtil.currentUserId())
                .orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND, "Patient not found."));
        // Seeded / pre-existing patients are enrolled lazily on first use.
        return studyService.ensureEnrolled(patient);
    }

    private void requireAdmin() {
        if (!"admin".equals(AuthUtil.currentRole())) {
            throw new ApiException(HttpStatus.FORBIDDEN, "You don't have permission to do that.");
        }
    }

    private static int requireRating(Integer v, String label) {
        if (v == null || v < 1 || v > 5) {
            throw new ApiException(HttpStatus.BAD_REQUEST, label + " must be between 1 and 5.");
        }
        return v;
    }

    private static Integer optionalRating(Integer v, String label) {
        if (v == null || v == 0) return null; // 0 = "not rated"
        return requireRating(v, label);
    }

    private static void addAspect(Map<String, double[]> acc, String key, Integer value) {
        if (value == null) return;
        double[] a = acc.get(key);
        a[0] += value;
        a[1] += 1;
    }

    private static double round2(double x) {
        return Math.round(x * 100.0) / 100.0;
    }

    private FeedbackResultDto toResult(Feedback f) {
        Appointment apt = appointmentRepository.findById(f.getAppointmentId()).orElse(null);
        return toResult(f, apt);
    }

    private FeedbackResultDto toResult(Feedback f, Appointment apt) {
        RewardService.RewardOutcome r = new RewardService.RewardOutcome(
                f.getRewardType(), f.getRewardStatus(),
                f.getRewardPoints() == null ? 0 : f.getRewardPoints(),
                f.getRewardDiscountPercent() == null ? 0 : f.getRewardDiscountPercent(),
                f.getRewardCode());
        return new FeedbackResultDto(
                f.getAppointmentId(),
                apt == null ? null : apt.getDoctorName(),
                apt == null ? null : apt.getDate(),
                f.getSubmittedAt(),
                f.getOverallRating() == null ? 0 : f.getOverallRating(),
                f.getRewardType(), f.getRewardStatus(),
                r.points(), r.discountPercent(), f.getRewardCode(),
                rewardService.messageFor(f.getStudyGroup(), r));
    }

    /** CSV cell with quoting, and a leading apostrophe against spreadsheet formula injection. */
    static String csv(Object value) {
        if (value == null) return "";
        String s = String.valueOf(value);
        if (!s.isEmpty() && "=+-@\t\r".indexOf(s.charAt(0)) >= 0) s = "'" + s;
        if (s.contains(",") || s.contains("\"") || s.contains("\n") || s.contains("\r")) {
            s = "\"" + s.replace("\"", "\"\"") + "\"";
        }
        return s;
    }
}
