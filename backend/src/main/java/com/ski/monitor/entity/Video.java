package com.ski.monitor.entity;

import jakarta.persistence.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@Entity
@Table(name = "videos")
public class Video {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false)
    private Long userId;

    @Column(nullable = false)
    private String filename;

    @Column(nullable = false, length = 500)
    private String filepath;

    private Integer duration;

    @Column(length = 20)
    private String status = "UPLOADED";

    @Column(name = "created_at")
    private LocalDateTime createdAt = LocalDateTime.now();
}
