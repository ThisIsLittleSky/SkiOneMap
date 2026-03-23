package com.ski.monitor.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.ski.monitor.entity.Alert;
import com.ski.monitor.repository.AlertRepository;
import com.ski.monitor.websocket.AlertWebSocketHandler;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

@Service
@EnableScheduling
public class RedisSubscriberService {

    private static final Logger log = LoggerFactory.getLogger(RedisSubscriberService.class);

    private final StringRedisTemplate redisTemplate;
    private final AlertWebSocketHandler webSocketHandler;
    private final TaskService taskService;
    private final AlertRepository alertRepository;
    private final ObjectMapper objectMapper = new ObjectMapper();

    private static final String RESULT_QUEUE_KEY = "ai:results";

    public RedisSubscriberService(StringRedisTemplate redisTemplate,
                                   AlertWebSocketHandler webSocketHandler,
                                   TaskService taskService,
                                   AlertRepository alertRepository) {
        this.redisTemplate = redisTemplate;
        this.webSocketHandler = webSocketHandler;
        this.taskService = taskService;
        this.alertRepository = alertRepository;
    }

    @Scheduled(fixedDelay = 1000)
    public void consumeResults() {
        String message = redisTemplate.opsForList().leftPop(RESULT_QUEUE_KEY);
        if (message == null) {
            return;
        }

        try {
            JsonNode root = objectMapper.readTree(message);
            long taskId = root.get("taskId").asLong();
            String status = root.get("status").asText();

            if ("COMPLETED".equals(status)) {
                int alertCount = root.has("alertCount") ? root.get("alertCount").asInt() : 0;
                int trackCount = root.has("trackCount") ? root.get("trackCount").asInt() : 0;

                // 存储完整结果（去掉 tracks 大字段，只保留摘要和 alerts）
                String summary = buildSummary(root, taskId, trackCount, alertCount);
                taskService.updateResult(taskId, summary, "COMPLETED");

                if (root.has("alerts") && root.get("alerts").isArray()) {
                    for (JsonNode alertNode : root.get("alerts")) {
                        Alert alert = new Alert();
                        alert.setTaskId(taskId);
                        alert.setAlertType(alertNode.has("alertType") ? alertNode.get("alertType").asText() : "UNKNOWN");
                        alert.setSeverity(alertNode.has("severity") ? alertNode.get("severity").asText() : "WARNING");
                        alert.setDescription(alertNode.has("description") ? alertNode.get("description").asText() : "");
                        alert.setPositionX(alertNode.has("positionX") ? (float) alertNode.get("positionX").asDouble() : null);
                        alert.setPositionY(alertNode.has("positionY") ? (float) alertNode.get("positionY").asDouble() : null);
                        alertRepository.save(alert);
                    }
                }

                // 构造轻量 WebSocket 推送消息（不含完整 tracks 数组）
                String wsBroadcast = buildWsMessage(root, taskId, trackCount, alertCount);
                webSocketHandler.broadcast(wsBroadcast);
                log.info("Task {} completed: {} tracks, {} alerts", taskId, trackCount, alertCount);
            } else if ("FAILED".equals(status)) {
                String error = root.has("error") ? root.get("error").asText() : "Unknown error";
                taskService.updateResult(taskId, message, "FAILED");
                log.warn("Task {} failed: {}", taskId, error);
                webSocketHandler.broadcast(message);
            } else if ("PROCESSING".equals(status)) {
                taskService.updateStatus(taskId, "PROCESSING");
                log.info("Task {} is processing", taskId);
                webSocketHandler.broadcast(message);
            }

        } catch (Exception e) {
            log.error("Failed to process AI result message", e);
        }
    }

    private String buildSummary(JsonNode root, long taskId, int trackCount, int alertCount) {
        try {
            com.fasterxml.jackson.databind.node.ObjectNode node = objectMapper.createObjectNode();
            node.put("taskId", taskId);
            node.put("status", "COMPLETED");
            node.put("trackCount", trackCount);
            node.put("alertCount", alertCount);
            node.put("totalFrames", root.has("totalFrames") ? root.get("totalFrames").asInt() : 0);
            node.put("liabilitySuggestion",
                    root.has("liabilitySuggestion") ? root.get("liabilitySuggestion").asText() : "");
            if (root.has("alerts")) {
                node.set("alerts", root.get("alerts"));
            }
            return objectMapper.writeValueAsString(node);
        } catch (Exception e) {
            return String.format("{\"taskId\":%d,\"status\":\"COMPLETED\"}", taskId);
        }
    }

    private String buildWsMessage(JsonNode root, long taskId, int trackCount, int alertCount) {
        try {
            com.fasterxml.jackson.databind.node.ObjectNode node = objectMapper.createObjectNode();
            node.put("taskId", taskId);
            node.put("status", "COMPLETED");
            node.put("trackCount", trackCount);
            node.put("alertCount", alertCount);
            node.put("totalFrames", root.has("totalFrames") ? root.get("totalFrames").asInt() : 0);
            node.put("liabilitySuggestion",
                    root.has("liabilitySuggestion") ? root.get("liabilitySuggestion").asText() : "");
            if (root.has("alerts")) {
                node.set("alerts", root.get("alerts"));
            }
            return objectMapper.writeValueAsString(node);
        } catch (Exception e) {
            return String.format("{\"taskId\":%d,\"status\":\"COMPLETED\",\"trackCount\":%d,\"alertCount\":%d}",
                    taskId, trackCount, alertCount);
        }
    }
}
