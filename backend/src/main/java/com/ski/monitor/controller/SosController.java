package com.ski.monitor.controller;

import com.ski.monitor.entity.SosRecord;
import com.ski.monitor.repository.SosRecordMapper;
import com.ski.monitor.websocket.DashboardWebSocket;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDateTime;

@RestController
@RequestMapping("/api/sos")
@Slf4j
public class SosController {

    @Autowired
    private SosRecordMapper sosRecordMapper;

    @PostMapping
    public String receiveSos(@RequestBody SosRecord record) {
        log.info("收到SOS求救信号: {}", record);
        
        // 1. 设置默认值并入库保存
        record.setStatus(0); // 未处理
        record.setCreateTime(LocalDateTime.now());
        sosRecordMapper.insert(record);

        // 2. 将此求救记录通过WebSocket实时推送到智慧大屏
        // 大屏端可以连接 ws://lzzt.cc:8085/ws/dashboard 接收该推送
        DashboardWebSocket.sendInfo(record);

        return "SOS received";
    }
}
