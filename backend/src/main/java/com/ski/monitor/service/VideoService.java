package com.ski.monitor.service;

import com.ski.monitor.entity.Video;
import com.ski.monitor.repository.VideoRepository;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.UUID;

@Service
public class VideoService {

    private final VideoRepository videoRepository;

    @Value("${app.video.storage-path}")
    private String storagePath;

    public VideoService(VideoRepository videoRepository) {
        this.videoRepository = videoRepository;
    }

    public Video uploadVideo(MultipartFile file, Long userId, Long cameraId) throws IOException {
        Path dir = Paths.get(storagePath).toAbsolutePath();
        if (!Files.exists(dir)) {
            Files.createDirectories(dir);
        }

        String originalFilename = file.getOriginalFilename();
        String ext = originalFilename != null && originalFilename.contains(".")
                ? originalFilename.substring(originalFilename.lastIndexOf("."))
                : ".mp4";
        String savedFilename = UUID.randomUUID() + ext;
        Path filePath = dir.resolve(savedFilename).toAbsolutePath();
        Files.copy(file.getInputStream(), filePath);

        Video video = new Video();
        video.setUserId(userId);
        video.setCameraId(cameraId);
        video.setFilename(originalFilename);
        video.setFilepath(filePath.toString());
        video.setStatus("UPLOADED");
        videoRepository.insert(video);
        return video;
    }

    public Video getById(Long id) {
        return videoRepository.selectById(id);
    }

    public List<Video> listAll() {
        return videoRepository.selectList(null);
    }

    public List<Video> searchByCameraId(Long cameraId) {
        return videoRepository.selectList(
            new com.baomidou.mybatisplus.core.conditions.query.QueryWrapper<Video>()
                .eq("camera_id", cameraId)
        );
    }
}
