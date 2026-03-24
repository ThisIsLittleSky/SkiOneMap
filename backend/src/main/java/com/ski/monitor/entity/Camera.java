package com.ski.monitor.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("cameras")
public class Camera {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String name;

    private String description;

    @TableField("pos_x")
    private Double posX = 0.0;

    @TableField("pos_y")
    private Double posY = 0.0;

    @TableField("pos_z")
    private Double posZ = 0.0;

    private String status = "ONLINE";

    @TableField("created_at")
    private LocalDateTime createdAt = LocalDateTime.now();
}
