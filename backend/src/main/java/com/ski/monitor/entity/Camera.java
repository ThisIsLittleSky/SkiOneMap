package com.ski.monitor.entity;

import jakarta.persistence.*;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@Entity
@Table(name = "cameras")
public class Camera {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 100)
    private String name;

    @Column(length = 200)
    private String description;

    /** 摄像头在 3D 场景中的 X 坐标 */
    @Column(name = "pos_x")
    private Double posX = 0.0;

    /** 摄像头在 3D 场景中的 Y 坐标 */
    @Column(name = "pos_y")
    private Double posY = 0.0;

    /** 摄像头在 3D 场景中的 Z 坐标 */
    @Column(name = "pos_z")
    private Double posZ = 0.0;

    /** 摄像头状态: ONLINE / OFFLINE */
    @Column(length = 20)
    private String status = "ONLINE";

    @Column(name = "created_at")
    private LocalDateTime createdAt = LocalDateTime.now();
}
