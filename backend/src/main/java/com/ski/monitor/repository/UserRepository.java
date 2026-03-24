package com.ski.monitor.repository;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ski.monitor.entity.User;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface UserRepository extends BaseMapper<User> {
}
