package com.ski.monitor.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ski.monitor.entity.Alert;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface AlertRepository extends BaseMapper<Alert> {
}
