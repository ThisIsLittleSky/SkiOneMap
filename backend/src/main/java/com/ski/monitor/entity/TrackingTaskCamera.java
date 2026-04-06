package com.ski.monitor.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("tracking_task_cameras")
public class TrackingTaskCamera {

    @TableId(type = IdType.AUTO)
    private Long id;

    @TableField("tracking_task_id")
    private Long trackingTaskId;

    @TableField("camera_id")
    private Long cameraId;

    @TableField("created_at")
    private LocalDateTime createdAt = LocalDateTime.now();
}
