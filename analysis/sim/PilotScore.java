import com.medbook.backend.service.*;
import java.nio.file.*; import java.util.*;

/** Scores a simulated pilot with the REAL backend classes (QualityScorer, SentimentLexicon, RewardService).
 *  Input TSV: studyId, group, stars, text.  Output: CSV in the same format as GET /api/feedback/export. */
public class PilotScore {
  static String q(String s){ return "\"" + s.replace("\"","\"\"") + "\""; }
  public static void main(String[] a) throws Exception {
    double theta = Double.parseDouble(a[2]);
    if (a.length > 3 && !a[3].isEmpty()) SentimentLexicon.setModelPolarity(new ModelSentimentClient(a[3], 3000, 1000));
    QualityScorer s = new QualityScorer(0.4, 0.3, 0.3, theta);
    RewardService rw = new RewardService(50, 10, "points");
    List<String> prev = new ArrayList<>(); StringBuilder out = new StringBuilder();
    out.append("studyId,group,doctorId,submittedAt,overallRating,ratingDoctor,ratingStaff,ratingWaiting,ratingCleanliness,ratingBilling,freeText,wordCount,aspectsMentioned,detailD,uniquenessU,consistencyC,qualityQ,gatePassed,rewardType,rewardStatus\n");
    for (String line : Files.readAllLines(Path.of(a[0]))) {
      String[] p = line.split("\t", 4); String text = p.length > 3 ? p[3] : "";
      var r = s.evaluate(text, Integer.parseInt(p[2]), prev); if (!text.isBlank()) prev.add(text);
      var o = rw.decide(p[1], r.passed());
      out.append(String.join(",", p[0], p[1], "1", "2026-11-19T10:00:00", p[2], "", "", "", "", "", q(text), "" + r.words(), "" + r.aspectsMentioned(),
        "" + r.detail(), "" + r.uniqueness(), "" + r.consistency(), "" + r.quality(), "" + r.passed(), o.type(), o.status())).append("\n");
    }
    Files.writeString(Path.of(a[1]), out.toString());
  }
}
