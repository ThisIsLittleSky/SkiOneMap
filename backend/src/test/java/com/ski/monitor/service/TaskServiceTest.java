package com.ski.monitor.service;

import com.ski.monitor.entity.Task;
import com.ski.monitor.entity.Video;
import com.ski.monitor.repository.TaskRepository;
import com.ski.monitor.repository.VideoRepository;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.redis.core.ListOperations;
import org.springframework.data.redis.core.StringRedisTemplate;

import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class TaskServiceTest {

    @Mock
    private TaskRepository taskRepository;

    @Mock
    private VideoRepository videoRepository;

    @Mock
    private StringRedisTemplate redisTemplate;

    @Mock
    private ListOperations<String, String> listOperations;

    @InjectMocks
    private TaskService taskService;

    private Video makeVideo(Long id, String filepath) {
        Video v = new Video();
        v.setId(id);
        v.setFilepath(filepath);
        v.setStatus("UPLOADED");
        return v;
    }

    private Task makeTask(Long id, Long videoId, String status) {
        Task t = new Task();
        t.setId(id);
        t.setVideoId(videoId);
        t.setStatus(status);
        return t;
    }

    @Test
    void createTask_dispatchesToRedisAndSaves() {
        Video video = makeVideo(1L, "/data/videos/test.mp4");
        when(videoRepository.findById(1L)).thenReturn(Optional.of(video));

        Task saved = makeTask(10L, 1L, "PENDING");
        when(taskRepository.save(any(Task.class))).thenReturn(saved);
        when(redisTemplate.opsForList()).thenReturn(listOperations);
        when(videoRepository.save(any(Video.class))).thenReturn(video);

        Task result = taskService.createTask(1L);

        assertThat(result.getId()).isEqualTo(10L);
        assertThat(result.getStatus()).isEqualTo("PENDING");

        ArgumentCaptor<String> msgCaptor = ArgumentCaptor.forClass(String.class);
        verify(listOperations).rightPush(eq("video:tasks"), msgCaptor.capture());
        assertThat(msgCaptor.getValue()).contains("\"taskId\":10").contains("\"videoId\":1");

        // video status should be updated to PROCESSING
        ArgumentCaptor<Video> videoCaptor = ArgumentCaptor.forClass(Video.class);
        verify(videoRepository).save(videoCaptor.capture());
        assertThat(videoCaptor.getValue().getStatus()).isEqualTo("PROCESSING");
    }

    @Test
    void createTask_throwsWhenVideoNotFound() {
        when(videoRepository.findById(99L)).thenReturn(Optional.empty());

        assertThatThrownBy(() -> taskService.createTask(99L))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("Video not found");
    }

    @Test
    void updateStatus_changesTaskStatus() {
        Task task = makeTask(1L, 1L, "PENDING");
        when(taskRepository.findById(1L)).thenReturn(Optional.of(task));
        when(taskRepository.save(any(Task.class))).thenAnswer(inv -> inv.getArgument(0));

        Task result = taskService.updateStatus(1L, "PROCESSING");

        assertThat(result.getStatus()).isEqualTo("PROCESSING");
    }

    @Test
    void updateStatus_returnsNull_whenTaskNotFound() {
        when(taskRepository.findById(99L)).thenReturn(Optional.empty());

        Task result = taskService.updateStatus(99L, "PROCESSING");

        assertThat(result).isNull();
    }

    @Test
    void updateResult_setsResultAndUpdatesVideoStatus() {
        Task task = makeTask(1L, 1L, "PROCESSING");
        Video video = makeVideo(1L, "/data/videos/test.mp4");

        when(taskRepository.findById(1L)).thenReturn(Optional.of(task));
        when(taskRepository.save(any(Task.class))).thenAnswer(inv -> inv.getArgument(0));
        when(videoRepository.findById(1L)).thenReturn(Optional.of(video));
        when(videoRepository.save(any(Video.class))).thenReturn(video);

        Task result = taskService.updateResult(1L, "{\"summary\":\"ok\"}", "COMPLETED");

        assertThat(result.getStatus()).isEqualTo("COMPLETED");
        assertThat(result.getResult()).isEqualTo("{\"summary\":\"ok\"}");

        ArgumentCaptor<Video> videoCaptor = ArgumentCaptor.forClass(Video.class);
        verify(videoRepository).save(videoCaptor.capture());
        assertThat(videoCaptor.getValue().getStatus()).isEqualTo("ANALYZED");
    }

    @Test
    void updateResult_setsVideoToFailed_whenTaskFailed() {
        Task task = makeTask(1L, 1L, "PROCESSING");
        Video video = makeVideo(1L, "/data/videos/test.mp4");

        when(taskRepository.findById(1L)).thenReturn(Optional.of(task));
        when(taskRepository.save(any(Task.class))).thenAnswer(inv -> inv.getArgument(0));
        when(videoRepository.findById(1L)).thenReturn(Optional.of(video));
        when(videoRepository.save(any(Video.class))).thenReturn(video);

        taskService.updateResult(1L, "{}", "FAILED");

        ArgumentCaptor<Video> videoCaptor = ArgumentCaptor.forClass(Video.class);
        verify(videoRepository).save(videoCaptor.capture());
        assertThat(videoCaptor.getValue().getStatus()).isEqualTo("FAILED");
    }

    @Test
    void listAll_returnsAllTasks() {
        when(taskRepository.findAll()).thenReturn(List.of(makeTask(1L, 1L, "PENDING"), makeTask(2L, 2L, "COMPLETED")));

        List<Task> result = taskService.listAll();

        assertThat(result).hasSize(2);
    }
}
