package com.medbook.backend.service;

import com.sun.net.httpserver.HttpServer;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;

import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;

import static org.junit.jupiter.api.Assertions.*;

/** Tests the optional trained-model hook with a fake local HTTP service (no Python needed). */
class ModelSentimentClientTest {

    private HttpServer server;

    @AfterEach
    void cleanUp() {
        if (server != null) server.stop(0);
        SentimentLexicon.setModelPolarity(null);   // never leak the hook into other tests
    }

    private String startFake(int status, String body) throws Exception {
        server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.createContext("/polarity", ex -> {
            byte[] b = body.getBytes(StandardCharsets.UTF_8);
            ex.sendResponseHeaders(status, b.length);
            ex.getResponseBody().write(b);
            ex.close();
        });
        server.start();
        return "http://127.0.0.1:" + server.getAddress().getPort();
    }

    @Test
    void usesModelAnswerWhenServiceIsUp() throws Exception {
        String url = startFake(200, "{\"polarity\": -1, \"aspects\": {}}");
        SentimentLexicon.setModelPolarity(new ModelSentimentClient(url, 1000, 1000));
        // The word list would say +1 ("good"), the fake model says -1: the model must win.
        assertEquals(-1, SentimentLexicon.polarity("good good good"));
    }

    @Test
    void fallsBackToWordListWhenServiceReturnsError() throws Exception {
        String url = startFake(500, "{}");
        SentimentLexicon.setModelPolarity(new ModelSentimentClient(url, 1000, 1000));
        assertEquals(1, SentimentLexicon.polarity("good good good"));
    }

    @Test
    void fallsBackToWordListWhenServiceIsDown() {
        SentimentLexicon.setModelPolarity(new ModelSentimentClient("http://127.0.0.1:9", 300, 30_000));
        assertEquals(-1, SentimentLexicon.polarity("the clinic was not clean"));
    }

    @Test
    void jsonEscapingKeepsRequestValid() {
        assertEquals("a\\\"b\\\\c\\nd", ModelSentimentClient.jsonEscape("a\"b\\c\nd"));
    }
}
