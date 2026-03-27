package com.ski.monitor.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("sos_record")
public class SosRecord {
    @TableId(type = IdType.AUTO)
    private Long id;
    
    private Long timestamp;
    private Double latitude;
    private Double longitude;
    private String mode;
    private String device;
    
    // 0: 未处理, 1: 已处理
    private Integer status;
    
    private LocalDateTime createTime;
}
