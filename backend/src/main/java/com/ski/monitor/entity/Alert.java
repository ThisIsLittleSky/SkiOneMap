package com.ski.monitor.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("alerts")
public class Alert {

    @TableId(type = IdType.AUTO)
    private Long id;

    @TableField("task_id")
    private Long taskId;

    @TableField("alert_type")
    private String alertType;

    private String severity = "WARNING";

    private String description;

    @TableField("position_x")
    private Float positionX;

    @TableField("position_y")
    private Float positionY;

    @TableField("created_at")
    private LocalDateTime createdAt = LocalDateTime.now();
}
