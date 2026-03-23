package com.ski.monitor.controller;

import com.ski.monitor.entity.Camera;
import com.ski.monitor.entity.SceneConfig;
import com.ski.monitor.repository.CameraRepository;
import com.ski.monitor.repository.SceneConfigRepository;
import com.ski.monitor.service.TaskService;
import com.ski.monitor.service.VideoService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/scene")
public class SceneController {

    private final CameraRepository cameraRepository;
    private final SceneConfigRepository sceneConfigRepository;
    private final VideoService videoService;
    private final TaskService taskService;

    public SceneController(CameraRepository cameraRepository,
                           SceneConfigRepository sceneConfigRepository,
                           VideoService videoService,
                           TaskService taskService) {
        this.cameraRepository = cameraRepository;
        this.sceneConfigRepository = sceneConfigRepository;
        this.videoService = videoService;
        this.taskService = taskService;
    }

    // ── 场地配置 ──────────────────────────────────────────────

    @GetMapping("/config")
    public ResponseEntity<SceneConfig> getConfig() {
        SceneConfig cfg = sceneConfigRepository.findById(1L)
                .orElseGet(() -> sceneConfigRepository.save(new SceneConfig()));
        return ResponseEntity.ok(cfg);
    }

    @PutMapping("/config")
    public ResponseEntity<SceneConfig> saveConfig(@RequestBody SceneConfig config) {
        config.setId(1L);
        return ResponseEntity.ok(sceneConfigRepository.save(config));
    }

    // ── 摄像头 CRUD ───────────────────────────────────────────

    @GetMapping("/cameras")
    public ResponseEntity<List<Camera>> listCameras() {
        return ResponseEntity.ok(cameraRepository.findAll());
    }

    @PostMapping("/cameras")
    public ResponseEntity<Camera> addCamera(@RequestBody Camera camera) {
        camera.setId(null);
        return ResponseEntity.ok(cameraRepository.save(camera));
    }

    @PutMapping("/cameras/{id}")
    public ResponseEntity<?> updateCamera(@PathVariable Long id, @RequestBody Camera camera) {
        if (!cameraRepository.existsById(id)) return ResponseEntity.notFound().build();
        camera.setId(id);
        return ResponseEntity.ok(cameraRepository.save(camera));
    }

    @DeleteMapping("/cameras/{id}")
    public ResponseEntity<?> deleteCamera(@PathVariable Long id) {
        cameraRepository.deleteById(id);
        return ResponseEntity.ok(Map.of("message", "deleted"));
    }

    // ── 向摄像头上传视频并触发分析 ────────────────────────────

    @PostMapping("/cameras/{id}/upload")
    public ResponseEntity<?> uploadAndAnalyze(
            @PathVariable Long id,
            @RequestParam("file") MultipartFile file) {
        Camera camera = cameraRepository.findById(id).orElse(null);
        if (camera == null) return ResponseEntity.notFound().build();
        try {
            var video = videoService.uploadVideo(file, 1L);
            var task = taskService.createTask(video.getId());
            return ResponseEntity.ok(Map.of(
                    "videoId", video.getId(),
                    "taskId", task.getId(),
                    "cameraId", id,
                    "cameraName", camera.getName(),
                    "status", task.getStatus()
            ));
        } catch (IOException e) {
            return ResponseEntity.internalServerError().body(Map.of("error", e.getMessage()));
        }
    }
}
