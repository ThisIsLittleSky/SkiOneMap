package com.ski.monitor.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("tracking_results")
public class TrackingResult {

    @TableId(type = IdType.AUTO)
    private Long id;

    @TableField("tracking_task_id")
    private Long trackingTaskId;

    @TableField("camera_id")
    private Long cameraId;

    @TableField("video_id")
    private Long videoId;

    @TableField("found_at_frame")
    private Integer foundAtFrame;

    private Float confidence;

    @TableField("appearance_features")
    private String appearanceFeatures;

    @TableField("predicted_route")
    private String predictedRoute;

    @TableField("match_image_path")
    private String matchImagePath;

    @TableField("created_at")
    private LocalDateTime createdAt = LocalDateTime.now();
}
