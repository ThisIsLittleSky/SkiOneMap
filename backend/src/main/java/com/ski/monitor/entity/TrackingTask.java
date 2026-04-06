package com.ski.monitor.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("tracking_tasks")
public class TrackingTask {

    @TableId(type = IdType.AUTO)
    private Long id;

    @TableField("video_id")
    private Long videoId;

    @TableField("target_person_image")
    private String targetPersonImage;

    @TableField("target_track_id")
    private Integer targetTrackId;

    private String status = "PENDING";

    @TableField("created_at")
    private LocalDateTime createdAt = LocalDateTime.now();

    @TableField("updated_at")
    private LocalDateTime updatedAt = LocalDateTime.now();
}
