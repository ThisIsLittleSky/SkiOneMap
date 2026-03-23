package com.ski.monitor.service;

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

@Service
public class TaskService {

    private static final Logger log = LoggerFactory.getLogger(TaskService.class);

    private final TaskRepository taskRepository;
    private final VideoRepository videoRepository;
    private final StringRedisTemplate redisTemplate;

    private static final String TASK_QUEUE_KEY = "video:tasks";

    public TaskService(TaskRepository taskRepository,
                       VideoRepository videoRepository,
                       StringRedisTemplate redisTemplate) {
        this.taskRepository = taskRepository;
        this.videoRepository = videoRepository;
        this.redisTemplate = redisTemplate;
    }

    public Task createTask(Long videoId) {
        Video video = videoRepository.findById(videoId).orElse(null);
        if (video == null) {
            throw new IllegalArgumentException("Video not found: " + videoId);
        }

        Task task = new Task();
        task.setVideoId(videoId);
        task.setStatus("PENDING");
        task = taskRepository.save(task);

        String message = String.format(
                "{\"taskId\":%d,\"videoId\":%d,\"videoPath\":\"%s\"}",
                task.getId(), videoId, video.getFilepath().replace("\\", "/")
        );
        redisTemplate.opsForList().rightPush(TASK_QUEUE_KEY, message);
        log.info("Task {} dispatched to Redis queue for video {}", task.getId(), videoId);

        video.setStatus("PROCESSING");
        videoRepository.save(video);

        return task;
    }

    public Task getById(Long id) {
        return taskRepository.findById(id).orElse(null);
    }

    public List<Task> getByVideoId(Long videoId) {
        return taskRepository.findByVideoIdOrderByCreatedAtDesc(videoId);
    }

    public Task updateStatus(Long id, String status) {
        Task task = taskRepository.findById(id).orElse(null);
        if (task != null) {
            task.setStatus(status);
            task.setUpdatedAt(LocalDateTime.now());
            return taskRepository.save(task);
        }
        return null;
    }

    public Task updateResult(Long id, String result, String status) {
        Task task = taskRepository.findById(id).orElse(null);
        if (task != null) {
            task.setResult(result);
            task.setStatus(status);
            task.setUpdatedAt(LocalDateTime.now());
            task = taskRepository.save(task);

            if ("COMPLETED".equals(status) || "FAILED".equals(status)) {
                Video video = videoRepository.findById(task.getVideoId()).orElse(null);
                if (video != null) {
                    video.setStatus("COMPLETED".equals(status) ? "ANALYZED" : "FAILED");
                    videoRepository.save(video);
                }
            }
            return task;
        }
        return null;
    }

    public List<Task> listAll() {
        return taskRepository.findAll();
    }
}
