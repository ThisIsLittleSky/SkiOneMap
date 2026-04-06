package com.ski.monitor.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ski.monitor.entity.TrackingResult;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface TrackingResultRepository extends BaseMapper<TrackingResult> {
}
