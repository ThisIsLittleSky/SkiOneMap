package com.ski.monitor.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("videos")
public class Video {

    @TableId(type = IdType.AUTO)
    private Long id;

    @TableField("user_id")
    private Long userId;

    @TableField("camera_id")
    private Long cameraId;

    private String filename;

    private String filepath;

    private Integer duration;

    private String status = "UPLOADED";

    @TableField("created_at")
    private LocalDateTime createdAt = LocalDateTime.now();
}
