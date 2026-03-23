package com.ski.monitor.entity;

import jakarta.persistence.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@Entity
@Table(name = "alerts")
public class Alert {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "task_id", nullable = false)
    private Long taskId;

    @Column(name = "alert_type", nullable = false, length = 50)
    private String alertType;

    @Column(length = 20)
    private String severity = "WARNING";

    @Column(columnDefinition = "TEXT")
    private String description;

    @Column(name = "position_x")
    private Float positionX;

    @Column(name = "position_y")
    private Float positionY;

    @Column(name = "created_at")
    private LocalDateTime createdAt = LocalDateTime.now();
}
