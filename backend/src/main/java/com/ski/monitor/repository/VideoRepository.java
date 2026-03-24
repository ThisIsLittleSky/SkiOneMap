package com.ski.monitor.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ski.monitor.entity.Video;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface VideoRepository extends BaseMapper<Video> {
}
