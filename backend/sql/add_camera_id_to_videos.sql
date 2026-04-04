-- 为 videos 表添加 camera_id 字段
-- 执行时间: 2026-04-04

USE ski_db;

-- 添加 camera_id 列
ALTER TABLE videos ADD COLUMN camera_id BIGINT AFTER user_id;

-- 添加外键约束
ALTER TABLE videos ADD CONSTRAINT fk_video_camera 
    FOREIGN KEY (camera_id) REFERENCES cameras(id);
