import com.medbook.backend.service.*;
import java.nio.file.*; import java.util.*;
public class GateRun {
  public static void main(String[] a) throws Exception {
    boolean model = a.length > 1 && a[1].equals("model");
    if (model) SentimentLexicon.setModelPolarity(new ModelSentimentClient("http://127.0.0.1:8001", 3000, 1000));
    QualityScorer s = new QualityScorer(0.4,0.3,0.3,Double.parseDouble(a[2]));
    List<String> prev = new ArrayList<>();
    System.out.println("idx\tstars\tD\tU\tC\tQ\tpassed\twords\taspects");
    int i = 0;
    for (String line : Files.readAllLines(Path.of(a[0]))) {
      String[] p = line.split("\t", 2); int stars = Integer.parseInt(p[0]); String text = p[1];
      var r = s.evaluate(text, stars, prev); prev.add(text);
      System.out.println(i++ + "\t" + stars + "\t" + r.detail() + "\t" + r.uniqueness() + "\t" + r.consistency() + "\t" + r.quality() + "\t" + r.passed() + "\t" + r.words() + "\t" + r.aspectsMentioned());
    }
  }
}
