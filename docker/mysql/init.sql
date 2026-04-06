CREATE DATABASE IF NOT EXISTS ski_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE ski_db;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'USER',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 摄像头表
CREATE TABLE IF NOT EXISTS cameras (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(255),
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 视频表
CREATE TABLE IF NOT EXISTS videos (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    camera_id BIGINT,
    filename VARCHAR(255) NOT NULL,
    filepath VARCHAR(500) NOT NULL,
    duration INT,
    status VARCHAR(20) DEFAULT 'UPLOADED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (camera_id) REFERENCES cameras(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 任务表
CREATE TABLE IF NOT EXISTS tasks (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    video_id BIGINT NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING',
    result TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 预警记录表
CREATE TABLE IF NOT EXISTS alerts (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_id BIGINT NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) DEFAULT 'WARNING',
    description TEXT,
    position_x FLOAT,
    position_y FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 滑雪事故求救记录表 (SOS)
CREATE TABLE IF NOT EXISTS `sos_record` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `timestamp` bigint(20) NOT NULL COMMENT '发生时间戳',
  `latitude` double DEFAULT NULL COMMENT '纬度',
  `longitude` double DEFAULT NULL COMMENT '经度',
  `mode` varchar(32) DEFAULT NULL COMMENT '模式(normal/sentinel)',
  `device` varchar(255) DEFAULT NULL COMMENT '设备UA信息',
  `status` int(11) DEFAULT '0' COMMENT '状态: 0-未处理, 1-已处理',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='滑雪事故求救记录表';

-- 插入默认管理员用户 (密码: admin123, 实际项目应使用加密密码)
INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'ADMIN')
ON DUPLICATE KEY UPDATE username = username;

-- 天眼追踪功能相关表

-- 追踪任务表
CREATE TABLE IF NOT EXISTS tracking_tasks (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    video_id BIGINT NOT NULL COMMENT '源视频ID',
    target_person_image VARCHAR(500) COMMENT '目标人员图像路径',
    target_track_id INT COMMENT '目标轨迹ID',
    status VARCHAR(20) DEFAULT 'PENDING' COMMENT 'PENDING/PROCESSING/COMPLETED/FAILED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='追踪任务表';

-- 视频中检测到的人员表
CREATE TABLE IF NOT EXISTS tracking_persons (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    video_id BIGINT NOT NULL COMMENT '视频ID',
    track_id INT NOT NULL COMMENT '轨迹ID',
    cropped_image_path VARCHAR(500) COMMENT '裁剪图像路径',
    dominant_color VARCHAR(50) COMMENT '主要衣服颜色(英文)',
    color_distribution TEXT COMMENT '颜色分布JSON',
    first_frame INT COMMENT '首次出现帧',
    last_frame INT COMMENT '最后出现帧',
    frame_count INT COMMENT '出现帧数',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos(id),
    INDEX idx_video_track (video_id, track_id),
    INDEX idx_dominant_color (dominant_color)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='视频中检测到的人员表';

-- 追踪结果表
CREATE TABLE IF NOT EXISTS tracking_results (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    tracking_task_id BIGINT NOT NULL COMMENT '追踪任务ID',
    camera_id BIGINT NOT NULL COMMENT '摄像头ID',
    video_id BIGINT NOT NULL COMMENT '匹配到的视频ID',
    found_at_frame INT COMMENT '发现帧位置',
    confidence FLOAT COMMENT '匹配置信度',
    appearance_features TEXT COMMENT '穿着特征描述',
    predicted_route TEXT COMMENT '预测路线',
    match_image_path VARCHAR(500) COMMENT '匹配图像路径',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tracking_task_id) REFERENCES tracking_tasks(id),
    FOREIGN KEY (camera_id) REFERENCES cameras(id),
    FOREIGN KEY (video_id) REFERENCES videos(id),
    INDEX idx_task (tracking_task_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='追踪结果表';

-- 追踪任务关联的摄像头表
CREATE TABLE IF NOT EXISTS tracking_task_cameras (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    tracking_task_id BIGINT NOT NULL COMMENT '追踪任务ID',
    camera_id BIGINT NOT NULL COMMENT '摄像头ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tracking_task_id) REFERENCES tracking_tasks(id),
    FOREIGN KEY (camera_id) REFERENCES cameras(id),
    UNIQUE KEY uk_task_camera (tracking_task_id, camera_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='追踪任务关联摄像头表';
