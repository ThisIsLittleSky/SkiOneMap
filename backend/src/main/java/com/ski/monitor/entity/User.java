package com.ski.monitor.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("users")
public class User {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String username;

    private String password;

    private String role = "USER";

    @TableField("created_at")
    private LocalDateTime createdAt = LocalDateTime.now();
}
