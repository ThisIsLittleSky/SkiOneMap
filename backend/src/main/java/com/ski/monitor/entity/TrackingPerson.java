package com.ski.monitor.entity;

import com.baomidou.mybatisplus.annotation.*;
import com.fasterxml.jackson.annotation.JsonAlias;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("tracking_persons")
public class TrackingPerson {

    @TableId(type = IdType.AUTO)
    private Long id;

    @TableField("video_id")
    @JsonAlias("video_id")
    private Long videoId;

    @TableField("track_id")
    @JsonAlias("track_id")
    private Integer trackId;

    @TableField("cropped_image_path")
    @JsonAlias("cropped_image_path")
    private String croppedImagePath;

    @TableField("first_frame")
    @JsonAlias("first_frame")
    private Integer firstFrame;

    @TableField("last_frame")
    @JsonAlias("last_frame")
    private Integer lastFrame;

    @TableField("frame_count")
    @JsonAlias("frame_count")
    private Integer frameCount;

    @TableField("dominant_color")
    @JsonAlias("dominant_color")
    private String dominantColor;

    @TableField("color_distribution")
    @JsonAlias("color_distribution")
    private String colorDistribution;

    @TableField("created_at")
    private LocalDateTime createdAt = LocalDateTime.now();
}
