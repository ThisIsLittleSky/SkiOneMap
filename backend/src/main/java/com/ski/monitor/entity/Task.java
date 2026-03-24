package com.ski.monitor.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("tasks")
public class Task {

    @TableId(type = IdType.AUTO)
    private Long id;

    @TableField("video_id")
    private Long videoId;

    private String status = "PENDING";

    private String result;

    @TableField("created_at")
    private LocalDateTime createdAt = LocalDateTime.now();

    @TableField("updated_at")
    private LocalDateTime updatedAt = LocalDateTime.now();
}
