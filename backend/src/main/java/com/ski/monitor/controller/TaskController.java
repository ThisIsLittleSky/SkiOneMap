package com.ski.monitor.controller;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.ski.monitor.entity.Alert;
import com.ski.monitor.entity.Task;
import com.ski.monitor.repository.AlertRepository;
import com.ski.monitor.service.TaskService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

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
            List<Alert> alerts = alertRepository.findByTaskIdOrderByCreatedAtDesc(id);
            return ResponseEntity.ok(Map.of(
                    "taskId", id,
                    "status", task.getStatus(),
                    "trackCount", root.has("trackCount") ? root.get("trackCount").asInt() : 0,
                    "totalFrames", root.has("totalFrames") ? root.get("totalFrames").asInt() : 0,
                    "liabilitySuggestion", root.has("liabilitySuggestion") ? root.get("liabilitySuggestion").asText() : "",
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
}
