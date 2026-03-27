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
