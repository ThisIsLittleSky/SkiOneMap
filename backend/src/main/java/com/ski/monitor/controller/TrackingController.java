package com.ski.monitor.controller;

import com.ski.monitor.entity.Camera;
import com.ski.monitor.entity.TrackingPerson;
import com.ski.monitor.entity.TrackingResult;
import com.ski.monitor.entity.TrackingTask;
import com.ski.monitor.service.TrackingService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/tracking")
@RequiredArgsConstructor
public class TrackingController {

    private final TrackingService trackingService;

    @GetMapping("/persons/{videoId}")
    public ResponseEntity<List<TrackingPerson>> getVideoPersons(
            @PathVariable Long videoId,
            @RequestParam(value = "extract", defaultValue = "true") boolean extract) {
        List<TrackingPerson> persons;
        if (extract) {
            persons = trackingService.getVideoPersons(videoId);
        } else {
            persons = trackingService.getVideoPersonsRaw(videoId);
        }
        return ResponseEntity.ok(persons);
    }

    @PostMapping("/tasks")
    public ResponseEntity<TrackingTask> createTrackingTask(@RequestBody Map<String, Object> request) {
        Long videoId = Long.valueOf(request.get("videoId").toString());
        Integer targetTrackId = Integer.valueOf(request.get("targetTrackId").toString());
        @SuppressWarnings("unchecked")
        List<Object> rawCameraIds = (List<Object>) request.get("cameraIds");
        List<Long> cameraIds = rawCameraIds.stream()
            .map(id -> Long.valueOf(id.toString()))
            .toList();
        
        TrackingTask task = trackingService.createTrackingTask(videoId, targetTrackId, cameraIds);
        return ResponseEntity.ok(task);
    }

    @GetMapping("/tasks/{taskId}")
    public ResponseEntity<Map<String, Object>> getTrackingTask(@PathVariable Long taskId) {
        TrackingTask task = trackingService.getTrackingTask(taskId);
        if (task == null) {
            return ResponseEntity.notFound().build();
        }
        
        List<TrackingResult> results = trackingService.getTrackingResults(taskId);
        return ResponseEntity.ok(Map.of("task", task, "results", results));
    }

    @GetMapping("/cameras")
    public ResponseEntity<List<Camera>> getAllCameras() {
        List<Camera> cameras = trackingService.getAllCameras();
        return ResponseEntity.ok(cameras);
    }

    @PostMapping("/persons/batch")
    public ResponseEntity<Map<String, Object>> savePersonsBatch(@RequestBody List<TrackingPerson> persons) {
        persons.forEach(trackingService::savePerson);
        return ResponseEntity.ok(Map.of("status", "success", "count", persons.size()));
    }

    @GetMapping("/persons/{videoId}/{trackId}")
    public ResponseEntity<TrackingPerson> getPersonByTrack(@PathVariable Long videoId, @PathVariable Integer trackId) {
        TrackingPerson person = trackingService.getPersonByTrack(videoId, trackId);
        if (person == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(person);
    }

    @GetMapping("/internal/task/{taskId}")
    public ResponseEntity<Map<String, Object>> getTaskInternal(@PathVariable Long taskId) {
        TrackingTask task = trackingService.getTrackingTask(taskId);
        if (task == null) {
            return ResponseEntity.notFound().build();
        }
        
        List<Long> cameraIds = trackingService.getTaskCameraIds(taskId);
        return ResponseEntity.ok(Map.of(
            "videoId", task.getVideoId(),
            "targetTrackId", task.getTargetTrackId(),
            "cameraIds", cameraIds
        ));
    }

    @PostMapping("/results/batch")
    public ResponseEntity<Map<String, Object>> saveResultsBatch(@RequestBody Map<String, Object> request) {
        Long taskId = Long.valueOf(request.get("task_id").toString());
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> results = (List<Map<String, Object>>) request.get("results");
        
        results.forEach(r -> trackingService.saveResult(r));
        return ResponseEntity.ok(Map.of("status", "success", "count", results.size()));
    }

    @PutMapping("/tasks/{taskId}/status")
    public ResponseEntity<Map<String, Object>> updateTaskStatus(
        @PathVariable Long taskId, 
        @RequestBody Map<String, String> request
    ) {
        String status = request.get("status");
        trackingService.updateTaskStatus(taskId, status);
        return ResponseEntity.ok(Map.of("status", "success"));
    }

    @PostMapping("/search-by-color")
    public ResponseEntity<Map<String, Object>> searchByColor(@RequestBody Map<String, Object> request) {
        String color = (String) request.get("color");
        @SuppressWarnings("unchecked")
        List<Object> rawCameraIds = (List<Object>) request.get("cameraIds");
        List<Long> cameraIds = rawCameraIds.stream()
            .map(id -> Long.valueOf(id.toString()))
            .toList();

        List<TrackingPerson> persons = trackingService.searchPersonsByColor(color, cameraIds);
        return ResponseEntity.ok(Map.of("persons", persons, "count", persons.size(), "color", color));
    }
}
