package com.ski.monitor.service;

import com.ski.monitor.entity.Video;
import com.ski.monitor.repository.VideoRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.junit.jupiter.api.io.TempDir;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.util.ReflectionTestUtils;

import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class VideoServiceTest {

    @Mock
    private VideoRepository videoRepository;

    @InjectMocks
    private VideoService videoService;

    @TempDir
    Path tempDir;

    @BeforeEach
    void setUp() {
        ReflectionTestUtils.setField(videoService, "storagePath", tempDir.toString());
    }

    @Test
    void uploadVideo_savesFileAndReturnsVideo() throws IOException {
        MockMultipartFile file = new MockMultipartFile(
                "file", "test.mp4", "video/mp4", "fake-video-content".getBytes()
        );

        Video saved = new Video();
        saved.setId(1L);
        saved.setFilename("test.mp4");
        saved.setStatus("UPLOADED");
        when(videoRepository.save(any(Video.class))).thenReturn(saved);

        Video result = videoService.uploadVideo(file, 1L);

        assertThat(result).isNotNull();
        assertThat(result.getId()).isEqualTo(1L);
        assertThat(result.getStatus()).isEqualTo("UPLOADED");
        verify(videoRepository, times(1)).save(any(Video.class));
    }

    @Test
    void uploadVideo_handlesFileWithoutExtension() throws IOException {
        MockMultipartFile file = new MockMultipartFile(
                "file", "videofile", "video/mp4", "content".getBytes()
        );

        Video saved = new Video();
        saved.setId(2L);
        saved.setFilename("videofile");
        saved.setStatus("UPLOADED");
        when(videoRepository.save(any(Video.class))).thenReturn(saved);

        Video result = videoService.uploadVideo(file, 1L);
        assertThat(result).isNotNull();
    }

    @Test
    void getById_returnsVideo_whenExists() {
        Video video = new Video();
        video.setId(1L);
        when(videoRepository.findById(1L)).thenReturn(Optional.of(video));

        Video result = videoService.getById(1L);

        assertThat(result).isNotNull();
        assertThat(result.getId()).isEqualTo(1L);
    }

    @Test
    void getById_returnsNull_whenNotExists() {
        when(videoRepository.findById(99L)).thenReturn(Optional.empty());

        Video result = videoService.getById(99L);

        assertThat(result).isNull();
    }

    @Test
    void listAll_returnsAllVideos() {
        Video v1 = new Video(); v1.setId(1L);
        Video v2 = new Video(); v2.setId(2L);
        when(videoRepository.findAll()).thenReturn(List.of(v1, v2));

        List<Video> result = videoService.listAll();

        assertThat(result).hasSize(2);
    }
}
