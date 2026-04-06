package com.ski.monitor.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.ski.monitor.entity.*;
import com.ski.monitor.repository.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;

import java.util.*;

@Slf4j
@Service
@RequiredArgsConstructor
public class TrackingService {

    private final TrackingTaskRepository trackingTaskRepository;
    private final TrackingPersonRepository trackingPersonRepository;
    private final TrackingResultRepository trackingResultRepository;
    private final TrackingTaskCameraRepository trackingTaskCameraRepository;
    private final CameraRepository cameraRepository;
    private final VideoService videoService;
    private final RestTemplate restTemplate;

    @Value("${app.ai-engine.base-url:http://localhost:8001}")
    private String aiEngineUrl;

    public List<TrackingPerson> getVideoPersonsRaw(Long videoId) {
        return trackingPersonRepository.selectList(
            new QueryWrapper<TrackingPerson>().eq("video_id", videoId)
        );
    }

    public List<TrackingPerson> getVideoPersons(Long videoId) {
        List<TrackingPerson> persons = getVideoPersonsRaw(videoId);
        
        boolean needReExtract = persons.isEmpty()
            || persons.stream().anyMatch(p -> p.getCroppedImagePath() == null || p.getTrackId() == null);
        
        if (needReExtract) {
            if (!persons.isEmpty()) {
                trackingPersonRepository.delete(
                    new QueryWrapper<TrackingPerson>().eq("video_id", videoId)
                );
            }
            extractPersonsFromVideo(videoId);
            persons = getVideoPersonsRaw(videoId);
        }
        
        return persons;
    }

    @Transactional
    public TrackingTask createTrackingTask(Long videoId, Integer targetTrackId, List<Long> cameraIds) {
        TrackingTask task = new TrackingTask();
        task.setVideoId(videoId);
        task.setTargetTrackId(targetTrackId);
        task.setStatus("PENDING");
        trackingTaskRepository.insert(task);

        for (Long cameraId : cameraIds) {
            TrackingTaskCamera taskCamera = new TrackingTaskCamera();
            taskCamera.setTrackingTaskId(task.getId());
            taskCamera.setCameraId(cameraId);
            trackingTaskCameraRepository.insert(taskCamera);
        }

        executeTrackingAsync(task.getId());
        
        return task;
    }

    public TrackingTask getTrackingTask(Long taskId) {
        return trackingTaskRepository.selectById(taskId);
    }

    public List<TrackingResult> getTrackingResults(Long taskId) {
        return trackingResultRepository.selectList(
            new QueryWrapper<TrackingResult>().eq("tracking_task_id", taskId)
        );
    }

    public List<Camera> getAllCameras() {
        return cameraRepository.selectList(null);
    }

    public void savePerson(TrackingPerson person) {
        trackingPersonRepository.insert(person);
    }

    public TrackingPerson getPersonByTrack(Long videoId, Integer trackId) {
        return trackingPersonRepository.selectOne(
            new QueryWrapper<TrackingPerson>()
                .eq("video_id", videoId)
                .eq("track_id", trackId)
        );
    }

    public List<TrackingPerson> searchPersonsByColor(String color, List<Long> cameraIds) {
        List<Long> videoIds = new ArrayList<>();
        for (Long cameraId : cameraIds) {
            List<com.ski.monitor.entity.Video> videos = videoService.searchByCameraId(cameraId);
            for (com.ski.monitor.entity.Video v : videos) {
                videoIds.add(v.getId());
            }
        }
        if (videoIds.isEmpty()) {
            return Collections.emptyList();
        }
        return trackingPersonRepository.selectList(
            new QueryWrapper<TrackingPerson>()
                .eq("dominant_color", color)
                .in("video_id", videoIds)
        );
    }

    public List<Long> getTaskCameraIds(Long taskId) {
        List<TrackingTaskCamera> taskCameras = trackingTaskCameraRepository.selectList(
            new QueryWrapper<TrackingTaskCamera>().eq("tracking_task_id", taskId)
        );
        return taskCameras.stream().map(TrackingTaskCamera::getCameraId).toList();
    }

    public void saveResult(Map<String, Object> resultData) {
        TrackingResult result = new TrackingResult();
        result.setTrackingTaskId(Long.valueOf(resultData.get("tracking_task_id").toString()));
        result.setCameraId(Long.valueOf(resultData.get("camera_id").toString()));
        result.setVideoId(Long.valueOf(resultData.get("video_id").toString()));
        result.setFoundAtFrame((Integer) resultData.get("found_at_frame"));
        result.setConfidence(((Number) resultData.get("confidence")).floatValue());
        result.setAppearanceFeatures((String) resultData.get("appearance_features"));
        result.setPredictedRoute((String) resultData.get("predicted_route"));
        trackingResultRepository.insert(result);
    }

    public void updateTaskStatus(Long taskId, String status) {
        TrackingTask task = trackingTaskRepository.selectById(taskId);
        if (task != null) {
            task.setStatus(status);
            trackingTaskRepository.updateById(task);
        }
    }

    private void extractPersonsFromVideo(Long videoId) {
        try {
            String url = aiEngineUrl + "/ai/tracking/extract-persons";
            Map<String, Object> request = Map.of("video_id", videoId);
            restTemplate.postForObject(url, request, Map.class);
        } catch (Exception e) {
            log.error("Failed to extract persons from video {}", videoId, e);
        }
    }

    private void executeTrackingAsync(Long taskId) {
        new Thread(() -> {
            try {
                String url = aiEngineUrl + "/ai/tracking/execute";
                Map<String, Object> request = Map.of("task_id", taskId);
                restTemplate.postForObject(url, request, Map.class);
            } catch (Exception e) {
                log.error("Failed to execute tracking task {}", taskId, e);
                TrackingTask task = trackingTaskRepository.selectById(taskId);
                if (task != null) {
                    task.setStatus("FAILED");
                    trackingTaskRepository.updateById(task);
                }
            }
        }).start();
    }
}
