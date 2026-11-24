package com.medbook.backend.service;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.function.Function;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Calls the LOCAL Python inference service (analysis/medbook_analysis/serve.py) to get the
 * polarity of a feedback text from the trained TF-IDF / DistilBERT aspect model.
 *
 * Returns +1 / 0 / -1, or null when the service is unavailable. {@link SentimentLexicon} then
 * falls back to the built-in word list, so feedback submission NEVER fails because of the model.
 * After a failure the client stays quiet for {@code cooldownMs} so a dead service does not add a
 * timeout to every submission.
 *
 * Privacy: the URL must point to this machine / the study network; patient text is never sent to a
 * third-party service.
 */
public class ModelSentimentClient implements Function<String, Integer> {

    private static final Pattern POLARITY = Pattern.compile("\"polarity\"\\s*:\\s*(-?\\d)");

    private final HttpClient http;
    private final URI uri;
    private final long timeoutMs;
    private final long cooldownMs;
    private volatile long retryAfter = 0;

    public ModelSentimentClient(String baseUrl, long timeoutMs, long cooldownMs) {
        String b = baseUrl.endsWith("/") ? baseUrl.substring(0, baseUrl.length() - 1) : baseUrl;
        this.uri = URI.create(b + "/polarity");
        this.timeoutMs = timeoutMs;
        this.cooldownMs = cooldownMs;
        this.http = HttpClient.newBuilder().connectTimeout(Duration.ofMillis(timeoutMs)).build();
    }

    @Override
    public Integer apply(String text) {
        if (System.currentTimeMillis() < retryAfter) return null;
        try {
            HttpRequest req = HttpRequest.newBuilder(uri)
                    .timeout(Duration.ofMillis(timeoutMs))
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString("{\"text\":\"" + jsonEscape(text) + "\"}"))
                    .build();
            HttpResponse<String> res = http.send(req, HttpResponse.BodyHandlers.ofString());
            if (res.statusCode() == 200) {
                Matcher m = POLARITY.matcher(res.body());
                if (m.find()) {
                    int p = Integer.parseInt(m.group(1));
                    return Integer.compare(p, 0);
                }
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        } catch (Exception ignored) {
            // fall through to cooldown + null
        }
        retryAfter = System.currentTimeMillis() + cooldownMs;
        return null;
    }

    static String jsonEscape(String s) {
        if (s == null) return "";
        StringBuilder sb = new StringBuilder(s.length() + 8);
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            switch (c) {
                case '"': sb.append("\\\""); break;
                case '\\': sb.append("\\\\"); break;
                case '\n': sb.append("\\n"); break;
                case '\r': sb.append("\\r"); break;
                case '\t': sb.append("\\t"); break;
                default:
                    if (c < 0x20) sb.append(String.format("\\u%04x", (int) c)); else sb.append(c);
            }
        }
        return sb.toString();
    }
}
