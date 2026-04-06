package com.ski.monitor.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ski.monitor.entity.TrackingTask;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface TrackingTaskRepository extends BaseMapper<TrackingTask> {
}
