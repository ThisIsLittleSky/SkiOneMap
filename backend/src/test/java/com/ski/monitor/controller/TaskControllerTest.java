package com.ski.monitor.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.ski.monitor.entity.Alert;
import com.ski.monitor.entity.Task;
import com.ski.monitor.repository.AlertRepository;
import com.ski.monitor.service.TaskService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(TaskController.class)
class TaskControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private TaskService taskService;

    @MockBean
    private AlertRepository alertRepository;

    private Task makeTask(Long id, Long videoId, String status, String result) {
        Task t = new Task();
        t.setId(id);
        t.setVideoId(videoId);
        t.setStatus(status);
        t.setResult(result);
        t.setCreatedAt(LocalDateTime.now());
        t.setUpdatedAt(LocalDateTime.now());
        return t;
    }

    @Test
    void createTask_returnsTaskId_onSuccess() throws Exception {
        when(taskService.createTask(1L)).thenReturn(makeTask(10L, 1L, "PENDING", null));

        mockMvc.perform(post("/api/task/create")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(Map.of("videoId", 1L))))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.taskId").value(10))
                .andExpect(jsonPath("$.status").value("PENDING"));
    }

    @Test
    void createTask_returns400_whenVideoIdMissing() throws Exception {
        mockMvc.perform(post("/api/task/create")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error").exists());
    }

    @Test
    void createTask_returns404_whenVideoNotFound() throws Exception {
        when(taskService.createTask(99L)).thenThrow(new IllegalArgumentException("Video not found: 99"));

        mockMvc.perform(post("/api/task/create")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(Map.of("videoId", 99L))))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.error").value("Video not found: 99"));
    }

    @Test
    void getStatus_returnsTaskStatus() throws Exception {
        when(taskService.getById(1L)).thenReturn(makeTask(1L, 1L, "PROCESSING", null));

        mockMvc.perform(get("/api/task/1/status"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.taskId").value(1))
                .andExpect(jsonPath("$.status").value("PROCESSING"));
    }

    @Test
    void getStatus_returns404_whenNotFound() throws Exception {
        when(taskService.getById(99L)).thenReturn(null);

        mockMvc.perform(get("/api/task/99/status"))
                .andExpect(status().isNotFound());
    }

    @Test
    void getResult_returnsResult_whenCompleted() throws Exception {
        String resultJson = "{\"taskId\":1,\"status\":\"COMPLETED\",\"trackCount\":3}";
        when(taskService.getById(1L)).thenReturn(makeTask(1L, 1L, "COMPLETED", resultJson));

        mockMvc.perform(get("/api/task/1/result"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.taskId").value(1))
                .andExpect(jsonPath("$.status").value("COMPLETED"));
    }

    @Test
    void getTracks_returnsTracksAndAlerts_whenCompleted() throws Exception {
        String resultJson = "{\"trackCount\":2,\"totalFrames\":100,\"liabilitySuggestion\":\"测试建议\"}";
        when(taskService.getById(1L)).thenReturn(makeTask(1L, 1L, "COMPLETED", resultJson));

        Alert a = new Alert();
        a.setId(1L); a.setTaskId(1L);
        a.setAlertType("WRONG_WAY"); a.setSeverity("WARNING");
        a.setDescription("逆行"); a.setPositionX(10f); a.setPositionY(20f);
        when(alertRepository.findByTaskIdOrderByCreatedAtDesc(1L)).thenReturn(List.of(a));

        mockMvc.perform(get("/api/task/1/tracks"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.trackCount").value(2))
                .andExpect(jsonPath("$.liabilitySuggestion").value("测试建议"))
                .andExpect(jsonPath("$.alerts.length()").value(1))
                .andExpect(jsonPath("$.alerts[0].alertType").value("WRONG_WAY"));
    }

    @Test
    void getTracks_returnsPendingStatus_whenNotCompleted() throws Exception {
        when(taskService.getById(2L)).thenReturn(makeTask(2L, 1L, "PROCESSING", null));

        mockMvc.perform(get("/api/task/2/tracks"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("PROCESSING"));
    }

    @Test
    void listTasks_returnsAllTasks() throws Exception {
        when(taskService.listAll()).thenReturn(List.of(
                makeTask(1L, 1L, "COMPLETED", null),
                makeTask(2L, 2L, "PENDING", null)
        ));

        mockMvc.perform(get("/api/task/list"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()").value(2));
    }
}
