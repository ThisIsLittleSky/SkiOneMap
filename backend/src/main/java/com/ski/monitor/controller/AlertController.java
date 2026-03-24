package com.ski.monitor.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.ski.monitor.entity.Alert;
import com.ski.monitor.repository.AlertRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/alert")
public class AlertController {

    private final AlertRepository alertRepository;

    public AlertController(AlertRepository alertRepository) {
        this.alertRepository = alertRepository;
    }

    @GetMapping("/list")
    public ResponseEntity<List<Alert>> listAll() {
        return ResponseEntity.ok(alertRepository.selectList(null));
    }

    @GetMapping("/task/{taskId}")
    public ResponseEntity<List<Alert>> listByTask(@PathVariable Long taskId) {
        return ResponseEntity.ok(alertRepository.selectList(
                new QueryWrapper<Alert>().eq("task_id", taskId).orderByDesc("created_at")));
    }
}
