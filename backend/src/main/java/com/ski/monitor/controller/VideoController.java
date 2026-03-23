package com.ski.monitor.controller;

import com.ski.monitor.entity.Video;
import com.ski.monitor.service.VideoService;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/video")
public class VideoController {

    private final VideoService videoService;

    public VideoController(VideoService videoService) {
        this.videoService = videoService;
    }

    @PostMapping("/upload")
    public ResponseEntity<?> upload(@RequestParam("file") MultipartFile file) {
        try {
            // MVP: use default userId = 1
            Video video = videoService.uploadVideo(file, 1L);
            return ResponseEntity.ok(Map.of(
                    "id", video.getId(),
                    "filename", video.getFilename(),
                    "status", video.getStatus()
            ));
        } catch (IOException e) {
            return ResponseEntity.internalServerError()
                    .body(Map.of("error", "Failed to upload video: " + e.getMessage()));
        }
    }

    @GetMapping("/{id}")
    public ResponseEntity<?> getVideo(@PathVariable Long id) {
        Video video = videoService.getById(id);
        if (video == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(video);
    }

    @GetMapping("/list")
    public ResponseEntity<List<Video>> listAll() {
        return ResponseEntity.ok(videoService.listAll());
    }

    /**
     * 视频流接口，支持 HTTP Range 请求，供前端 video 标签播放/拖拽定位。
     */
    @GetMapping("/{id}/stream")
    public ResponseEntity<Resource> streamVideo(
            @PathVariable Long id,
            HttpServletRequest request) throws IOException {

        Video video = videoService.getById(id);
        if (video == null) {
            return ResponseEntity.notFound().build();
        }

        Path filePath = Paths.get(video.getFilepath());
        if (!Files.exists(filePath)) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).build();
        }

        Resource resource = new FileSystemResource(filePath);
        long fileSize = Files.size(filePath);
        String rangeHeader = request.getHeader(HttpHeaders.RANGE);

        String contentType = Files.probeContentType(filePath);
        if (contentType == null) {
            contentType = "video/mp4";
        }

        if (rangeHeader == null) {
            return ResponseEntity.ok()
                    .contentType(MediaType.parseMediaType(contentType))
                    .contentLength(fileSize)
                    .header(HttpHeaders.ACCEPT_RANGES, "bytes")
                    .body(resource);
        }

        // 解析 Range: bytes=start-end
        String rangeValue = rangeHeader.replace("bytes=", "");
        String[] parts = rangeValue.split("-");
        long start = Long.parseLong(parts[0]);
        long end = parts.length > 1 && !parts[1].isEmpty()
                ? Long.parseLong(parts[1])
                : fileSize - 1;
        end = Math.min(end, fileSize - 1);
        long contentLength = end - start + 1;

        return ResponseEntity.status(HttpStatus.PARTIAL_CONTENT)
                .contentType(MediaType.parseMediaType(contentType))
                .header(HttpHeaders.CONTENT_RANGE, "bytes " + start + "-" + end + "/" + fileSize)
                .header(HttpHeaders.ACCEPT_RANGES, "bytes")
                .contentLength(contentLength)
                .body(new RangeResource(filePath, start, contentLength));
    }
}
