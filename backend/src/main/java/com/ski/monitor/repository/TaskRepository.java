package com.ski.monitor.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ski.monitor.entity.Task;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface TaskRepository extends BaseMapper<Task> {
}
