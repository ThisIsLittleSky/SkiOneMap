package com.ski.monitor.controller;

import com.ski.monitor.entity.Video;
import com.ski.monitor.service.AuthService;
import com.ski.monitor.service.TaskService;
import com.ski.monitor.service.VideoService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.web.servlet.MockMvc;

import java.time.LocalDateTime;
import java.util.Optional;
import java.util.List;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(VideoController.class)
class VideoControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private VideoService videoService;

    @MockBean
    private TaskService taskService;

    @MockBean
    private AuthService authService;

    private Video makeVideo(Long id, String filename, String status) {
        Video v = new Video();
        v.setId(id);
        v.setUserId(1L);
        v.setFilename(filename);
        v.setFilepath("/data/videos/" + filename);
        v.setStatus(status);
        v.setCreatedAt(LocalDateTime.now());
        return v;
    }

    @Test
    void upload_returnsVideoId_onSuccess() throws Exception {
        MockMultipartFile file = new MockMultipartFile(
                "file", "ski.mp4", "video/mp4", "fake".getBytes()
        );
        when(videoService.uploadVideo(any(), eq(1L))).thenReturn(makeVideo(1L, "ski.mp4", "UPLOADED"));

        mockMvc.perform(multipart("/api/video/upload").file(file))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(1))
                .andExpect(jsonPath("$.filename").value("ski.mp4"))
                .andExpect(jsonPath("$.status").value("UPLOADED"));
    }

    @Test
    void upload_returns500_whenIOException() throws Exception {
        MockMultipartFile file = new MockMultipartFile(
                "file", "bad.mp4", "video/mp4", "x".getBytes()
        );
        when(videoService.uploadVideo(any(), eq(1L))).thenThrow(new java.io.IOException("disk full"));

        mockMvc.perform(multipart("/api/video/upload").file(file))
                .andExpect(status().isInternalServerError())
                .andExpect(jsonPath("$.error").exists());
    }

    @Test
    void getVideo_returnsVideo_whenExists() throws Exception {
        when(videoService.getById(1L)).thenReturn(makeVideo(1L, "test.mp4", "UPLOADED"));

        mockMvc.perform(get("/api/video/1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(1))
                .andExpect(jsonPath("$.filename").value("test.mp4"));
    }

    @Test
    void getVideo_returns404_whenNotFound() throws Exception {
        when(videoService.getById(99L)).thenReturn(null);

        mockMvc.perform(get("/api/video/99"))
                .andExpect(status().isNotFound());
    }

    @Test
    void listAll_returnsVideoList() throws Exception {
        when(videoService.listAll()).thenReturn(List.of(
                makeVideo(1L, "a.mp4", "UPLOADED"),
                makeVideo(2L, "b.mp4", "ANALYZED")
        ));

        mockMvc.perform(get("/api/video/list"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()").value(2))
                .andExpect(jsonPath("$[0].id").value(1))
                .andExpect(jsonPath("$[1].status").value("ANALYZED"));
    }

    @Test
    void annotatedStream_returns404_whenNoAnnotatedVideo() throws Exception {
        when(videoService.getById(1L)).thenReturn(makeVideo(1L, "test.mp4", "ANALYZED"));
        when(taskService.getLatestAnnotatedVideoPathByVideoId(1L)).thenReturn(Optional.empty());

        mockMvc.perform(get("/api/video/1/annotated/stream"))
                .andExpect(status().isNotFound());
    }
}
