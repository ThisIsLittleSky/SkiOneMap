package com.ski.monitor.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.ski.monitor.entity.Task;
import com.ski.monitor.entity.Video;
import com.ski.monitor.repository.TaskRepository;
import com.ski.monitor.repository.VideoRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Service
public class TaskService {

    private static final Logger log = LoggerFactory.getLogger(TaskService.class);

    private final TaskRepository taskRepository;
    private final VideoRepository videoRepository;
    private final StringRedisTemplate redisTemplate;
    private final ObjectMapper objectMapper = new ObjectMapper();

    private static final String TASK_QUEUE_KEY = "video:tasks";

    public TaskService(TaskRepository taskRepository,
                       VideoRepository videoRepository,
                       StringRedisTemplate redisTemplate) {
        this.taskRepository = taskRepository;
        this.videoRepository = videoRepository;
        this.redisTemplate = redisTemplate;
    }

    public Task createTask(Long videoId) {
        Video video = videoRepository.selectById(videoId);
        if (video == null) {
            throw new IllegalArgumentException("Video not found: " + videoId);
        }

        Task task = new Task();
        task.setVideoId(videoId);
        task.setStatus("PENDING");
        taskRepository.insert(task);

        String message = String.format(
                "{\"taskId\":%d,\"videoId\":%d,\"videoPath\":\"%s\"}",
                task.getId(), videoId, video.getFilepath().replace("\\", "/")
        );
        redisTemplate.opsForList().rightPush(TASK_QUEUE_KEY, message);
        log.info("Task {} dispatched to Redis queue for video {}", task.getId(), videoId);

        video.setStatus("PROCESSING");
        videoRepository.updateById(video);

        return task;
    }

    public Task getById(Long id) {
        return taskRepository.selectById(id);
    }

    public List<Task> getByVideoId(Long videoId) {
        return taskRepository.selectList(
                new QueryWrapper<Task>().eq("video_id", videoId).orderByDesc("created_at"));
    }

    public Task updateStatus(Long id, String status) {
        Task task = taskRepository.selectById(id);
        if (task != null) {
            task.setStatus(status);
            task.setUpdatedAt(LocalDateTime.now());
            taskRepository.updateById(task);
            return task;
        }
        return null;
    }

    public Task updateResult(Long id, String result, String status) {
        Task task = taskRepository.selectById(id);
        if (task != null) {
            task.setResult(result);
            task.setStatus(status);
            task.setUpdatedAt(LocalDateTime.now());
            taskRepository.updateById(task);

            if ("COMPLETED".equals(status) || "FAILED".equals(status)) {
                Video video = videoRepository.selectById(task.getVideoId());
                if (video != null) {
                    video.setStatus("COMPLETED".equals(status) ? "ANALYZED" : "FAILED");
                    videoRepository.updateById(video);
                }
            }
            return task;
        }
        return null;
    }

    public List<Task> listAll() {
        return taskRepository.selectList(null);
    }

    public Optional<String> getAnnotatedVideoPath(Long taskId) {
        Task task = taskRepository.selectById(taskId);
        if (task == null || task.getResult() == null || task.getResult().isBlank()) {
            return Optional.empty();
        }
        return extractAnnotatedVideoPath(task.getResult());
    }

    public Optional<String> getLatestAnnotatedVideoPathByVideoId(Long videoId) {
        List<Task> tasks = getByVideoId(videoId);
        for (Task task : tasks) {
            if (!"COMPLETED".equals(task.getStatus()) || task.getResult() == null || task.getResult().isBlank()) {
                continue;
            }
            Optional<String> path = extractAnnotatedVideoPath(task.getResult());
            if (path.isPresent()) {
                return path;
            }
        }
        return Optional.empty();
    }

    private Optional<String> extractAnnotatedVideoPath(String result) {
        try {
            JsonNode root = objectMapper.readTree(result);
            if (!root.has("annotatedVideoPath")) {
                return Optional.empty();
            }
            String path = root.get("annotatedVideoPath").asText("");
            return path == null || path.isBlank() ? Optional.empty() : Optional.of(path);
        } catch (Exception e) {
            log.warn("Failed to parse annotated video path from task result", e);
            return Optional.empty();
        }
    }
}
