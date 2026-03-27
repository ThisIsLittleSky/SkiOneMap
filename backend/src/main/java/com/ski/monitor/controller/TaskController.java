package com.ski.monitor.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.ski.monitor.entity.Alert;
import com.ski.monitor.entity.Task;
import com.ski.monitor.repository.AlertRepository;
import com.ski.monitor.service.TaskService;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@RestController
@RequestMapping("/api/task")
public class TaskController {

    private final TaskService taskService;
    private final AlertRepository alertRepository;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public TaskController(TaskService taskService, AlertRepository alertRepository) {
        this.taskService = taskService;
        this.alertRepository = alertRepository;
    }

    @PostMapping("/create")
    public ResponseEntity<?> createTask(@RequestBody Map<String, Long> body) {
        Long videoId = body.get("videoId");
        if (videoId == null) {
            return ResponseEntity.badRequest().body(Map.of("error", "videoId is required"));
        }
        try {
            Task task = taskService.createTask(videoId);
            return ResponseEntity.ok(Map.of(
                    "taskId", task.getId(),
                    "status", task.getStatus()
            ));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(404).body(Map.of("error", e.getMessage()));
        }
    }

    @GetMapping("/{id}/status")
    public ResponseEntity<?> getStatus(@PathVariable Long id) {
        Task task = taskService.getById(id);
        if (task == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(Map.of(
                "taskId", task.getId(),
                "status", task.getStatus()
        ));
    }

    @GetMapping("/{id}/result")
    public ResponseEntity<?> getResult(@PathVariable Long id) {
        Task task = taskService.getById(id);
        if (task == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(Map.of(
                "taskId", task.getId(),
                "status", task.getStatus(),
                "result", task.getResult() != null ? task.getResult() : ""
        ));
    }

    @GetMapping("/{id}/tracks")
    public ResponseEntity<?> getTracks(@PathVariable Long id) {
        Task task = taskService.getById(id);
        if (task == null) {
            return ResponseEntity.notFound().build();
        }
        if (!"COMPLETED".equals(task.getStatus()) || task.getResult() == null) {
            return ResponseEntity.ok(Map.of("taskId", id, "status", task.getStatus(), "tracks", List.of()));
        }
        try {
            JsonNode root = objectMapper.readTree(task.getResult());
            List<Alert> alerts = alertRepository.selectList(
                    new QueryWrapper<Alert>().eq("task_id", id).orderByDesc("created_at"));
            String annotatedVideoUrl = root.has("annotatedVideoAvailable") && root.get("annotatedVideoAvailable").asBoolean(false)
                    ? String.format("/api/task/%d/annotated/stream", id)
                    : "";
            return ResponseEntity.ok(Map.of(
                    "taskId", id,
                    "status", task.getStatus(),
                    "trackCount", root.has("trackCount") ? root.get("trackCount").asInt() : 0,
                    "totalFrames", root.has("totalFrames") ? root.get("totalFrames").asInt() : 0,
                    "liabilitySuggestion", root.has("liabilitySuggestion") ? root.get("liabilitySuggestion").asText() : "",
                    "annotatedVideoAvailable", root.has("annotatedVideoAvailable") && root.get("annotatedVideoAvailable").asBoolean(false),
                    "annotatedVideoUrl", annotatedVideoUrl,
                    "alerts", alerts
            ));
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body(Map.of("error", e.getMessage()));
        }
    }

    @GetMapping("/list")
    public ResponseEntity<?> listTasks() {
        return ResponseEntity.ok(taskService.listAll());
    }

    @GetMapping("/{id}/annotated/stream")
    public ResponseEntity<Resource> streamAnnotatedVideo(
            @PathVariable Long id,
            HttpServletRequest request) throws IOException {
        Optional<String> path = taskService.getAnnotatedVideoPath(id);
        if (path.isEmpty()) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).build();
        }
        return buildStreamResponse(Paths.get(path.get()), request);
    }

    private ResponseEntity<Resource> buildStreamResponse(Path filePath, HttpServletRequest request) throws IOException {
        if (!Files.exists(filePath)) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).build();
        }

        Resource resource = new FileSystemResource(filePath);
        long fileSize = Files.size(filePath);
        String rangeHeader = request.getHeader(HttpHeaders.RANGE);

        String contentType = Files.probeContentType(filePath);
        if (contentType == null) {
            contentType = "video/mp4";
        }

        if (rangeHeader == null) {
            return ResponseEntity.ok()
                    .contentType(MediaType.parseMediaType(contentType))
                    .contentLength(fileSize)
                    .header(HttpHeaders.ACCEPT_RANGES, "bytes")
                    .body(resource);
        }

        String rangeValue = rangeHeader.replace("bytes=", "");
        String[] parts = rangeValue.split("-");
        long start = Long.parseLong(parts[0]);
        long end = parts.length > 1 && !parts[1].isEmpty()
                ? Long.parseLong(parts[1])
                : fileSize - 1;
        end = Math.min(end, fileSize - 1);
        long contentLength = end - start + 1;

        return ResponseEntity.status(HttpStatus.PARTIAL_CONTENT)
                .contentType(MediaType.parseMediaType(contentType))
                .header(HttpHeaders.CONTENT_RANGE, "bytes " + start + "-" + end + "/" + fileSize)
                .header(HttpHeaders.ACCEPT_RANGES, "bytes")
                .contentLength(contentLength)
                .body(new RangeResource(filePath, start, contentLength));
    }
}
