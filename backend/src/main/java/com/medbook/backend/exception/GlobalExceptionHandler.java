package com.medbook.backend.exception;

import com.medbook.backend.dto.ErrorResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(ApiException.class)
    public ResponseEntity<ErrorResponse> handleApiException(ApiException ex) {
        String code = ex.getErrorCode() != null ? ex.getErrorCode() : ex.getMessage();
        return ResponseEntity.status(ex.getStatus()).body(new ErrorResponse(code, ex.getMessage()));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleGeneric(Exception ex) {
        log.error("Unhandled API exception", ex);
        return ResponseEntity.internalServerError()
                .body(new ErrorResponse("internal_error", "Something went wrong on the server."));
    }
}
