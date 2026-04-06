package com.ski.monitor.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ski.monitor.entity.TrackingPerson;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface TrackingPersonRepository extends BaseMapper<TrackingPerson> {
}
