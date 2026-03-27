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
        when(videoRepository.selectById(1L)).thenReturn(video);

        doAnswer(inv -> {
            Task task = inv.getArgument(0);
            task.setId(10L);
            return 1;
        }).when(taskRepository).insert(any(Task.class));
        when(redisTemplate.opsForList()).thenReturn(listOperations);

        Task result = taskService.createTask(1L);

        assertThat(result.getId()).isEqualTo(10L);
        assertThat(result.getStatus()).isEqualTo("PENDING");

        ArgumentCaptor<String> msgCaptor = ArgumentCaptor.forClass(String.class);
        verify(listOperations).rightPush(eq("video:tasks"), msgCaptor.capture());
        assertThat(msgCaptor.getValue()).contains("\"taskId\":10").contains("\"videoId\":1");

        // video status should be updated to PROCESSING
        ArgumentCaptor<Video> videoCaptor = ArgumentCaptor.forClass(Video.class);
        verify(videoRepository).updateById(videoCaptor.capture());
        assertThat(videoCaptor.getValue().getStatus()).isEqualTo("PROCESSING");
    }

    @Test
    void createTask_throwsWhenVideoNotFound() {
        when(videoRepository.selectById(99L)).thenReturn(null);

        assertThatThrownBy(() -> taskService.createTask(99L))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("Video not found");
    }

    @Test
    void updateStatus_changesTaskStatus() {
        Task task = makeTask(1L, 1L, "PENDING");
        when(taskRepository.selectById(1L)).thenReturn(task);
        when(taskRepository.updateById(any(Task.class))).thenReturn(1);

        Task result = taskService.updateStatus(1L, "PROCESSING");

        assertThat(result.getStatus()).isEqualTo("PROCESSING");
    }

    @Test
    void updateStatus_returnsNull_whenTaskNotFound() {
        when(taskRepository.selectById(99L)).thenReturn(null);

        Task result = taskService.updateStatus(99L, "PROCESSING");

        assertThat(result).isNull();
    }

    @Test
    void updateResult_setsResultAndUpdatesVideoStatus() {
        Task task = makeTask(1L, 1L, "PROCESSING");
        Video video = makeVideo(1L, "/data/videos/test.mp4");

        when(taskRepository.selectById(1L)).thenReturn(task);
        when(taskRepository.updateById(any(Task.class))).thenReturn(1);
        when(videoRepository.selectById(1L)).thenReturn(video);
        when(videoRepository.updateById(any(Video.class))).thenReturn(1);

        Task result = taskService.updateResult(1L, "{\"summary\":\"ok\"}", "COMPLETED");

        assertThat(result.getStatus()).isEqualTo("COMPLETED");
        assertThat(result.getResult()).isEqualTo("{\"summary\":\"ok\"}");

        ArgumentCaptor<Video> videoCaptor = ArgumentCaptor.forClass(Video.class);
        verify(videoRepository).updateById(videoCaptor.capture());
        assertThat(videoCaptor.getValue().getStatus()).isEqualTo("ANALYZED");
    }

    @Test
    void updateResult_setsVideoToFailed_whenTaskFailed() {
        Task task = makeTask(1L, 1L, "PROCESSING");
        Video video = makeVideo(1L, "/data/videos/test.mp4");

        when(taskRepository.selectById(1L)).thenReturn(task);
        when(taskRepository.updateById(any(Task.class))).thenReturn(1);
        when(videoRepository.selectById(1L)).thenReturn(video);
        when(videoRepository.updateById(any(Video.class))).thenReturn(1);

        taskService.updateResult(1L, "{}", "FAILED");

        ArgumentCaptor<Video> videoCaptor = ArgumentCaptor.forClass(Video.class);
        verify(videoRepository).updateById(videoCaptor.capture());
        assertThat(videoCaptor.getValue().getStatus()).isEqualTo("FAILED");
    }

    @Test
    void listAll_returnsAllTasks() {
        when(taskRepository.selectList(null)).thenReturn(List.of(makeTask(1L, 1L, "PENDING"), makeTask(2L, 2L, "COMPLETED")));

        List<Task> result = taskService.listAll();

        assertThat(result).hasSize(2);
    }

    @Test
    void getAnnotatedVideoPath_returnsParsedPath() {
        Task task = makeTask(1L, 1L, "COMPLETED");
        task.setResult("{\"annotatedVideoPath\":\"/data/videos/annotated/task1.mp4\"}");
        when(taskRepository.selectById(1L)).thenReturn(task);

        assertThat(taskService.getAnnotatedVideoPath(1L))
                .contains("/data/videos/annotated/task1.mp4");
    }

    @Test
    void getLatestAnnotatedVideoPathByVideoId_returnsNewestAvailablePath() {
        Task latest = makeTask(3L, 1L, "COMPLETED");
        latest.setResult("{\"annotatedVideoPath\":\"\"}");
        Task older = makeTask(2L, 1L, "COMPLETED");
        older.setResult("{\"annotatedVideoPath\":\"/data/videos/annotated/task2.mp4\"}");
        when(taskRepository.selectList(any())).thenReturn(List.of(latest, older));

        assertThat(taskService.getLatestAnnotatedVideoPathByVideoId(1L))
                .contains("/data/videos/annotated/task2.mp4");
    }
}
