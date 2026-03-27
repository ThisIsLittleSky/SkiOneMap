package com.ski.monitor.service;

import com.ski.monitor.entity.Alert;
import com.ski.monitor.repository.AlertRepository;
import com.ski.monitor.websocket.AlertWebSocketHandler;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.redis.core.ListOperations;
import org.springframework.data.redis.core.StringRedisTemplate;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class RedisSubscriberServiceTest {

    @Mock
    private StringRedisTemplate redisTemplate;

    @Mock
    private AlertWebSocketHandler webSocketHandler;

    @Mock
    private TaskService taskService;

    @Mock
    private AlertRepository alertRepository;

    @Mock
    private ListOperations<String, String> listOperations;

    @InjectMocks
    private RedisSubscriberService redisSubscriberService;

    @Test
    void consumeResults_doesNothing_whenQueueEmpty() throws Exception {
        when(redisTemplate.opsForList()).thenReturn(listOperations);
        when(listOperations.leftPop("ai:results")).thenReturn(null);

        redisSubscriberService.consumeResults();

        verifyNoInteractions(webSocketHandler, taskService, alertRepository);
    }

    @Test
    void consumeResults_handlesCompletedTask_savesAlertsAndBroadcasts() throws Exception {
        String message = """
                {
                  "taskId": 5,
                  "status": "COMPLETED",
                  "trackCount": 3,
                  "alertCount": 2,
                  "totalFrames": 300,
                  "liabilitySuggestion": "测试建议",
                  "annotatedVideoPath": "/data/videos/annotated/task5.mp4",
                  "annotatedVideoAvailable": true,
                  "alerts": [
                    {"alertType":"WRONG_WAY","severity":"WARNING","description":"逆行","positionX":10.0,"positionY":20.0},
                    {"alertType":"COLLISION_RISK","severity":"DANGER","description":"碰撞","positionX":50.0,"positionY":60.0}
                  ]
                }
                """;

        when(redisTemplate.opsForList()).thenReturn(listOperations);
        when(listOperations.leftPop("ai:results")).thenReturn(message);

        redisSubscriberService.consumeResults();

        // taskService.updateResult called with COMPLETED
        verify(taskService).updateResult(eq(5L), any(String.class), eq("COMPLETED"));

        // two alerts saved
        ArgumentCaptor<Alert> alertCaptor = ArgumentCaptor.forClass(Alert.class);
        verify(alertRepository, times(2)).insert(alertCaptor.capture());
        assertThat(alertCaptor.getAllValues().get(0).getAlertType()).isEqualTo("WRONG_WAY");
        assertThat(alertCaptor.getAllValues().get(1).getAlertType()).isEqualTo("COLLISION_RISK");
        assertThat(alertCaptor.getAllValues().get(1).getSeverity()).isEqualTo("DANGER");

        // broadcast called once
        verify(webSocketHandler, times(1)).broadcast(any(String.class));
    }

    @Test
    void consumeResults_handlesFailedTask_broadcastsAndUpdates() throws Exception {
        String message = "{\"taskId\":7,\"status\":\"FAILED\",\"error\":\"YOLO error\"}";

        when(redisTemplate.opsForList()).thenReturn(listOperations);
        when(listOperations.leftPop("ai:results")).thenReturn(message);

        redisSubscriberService.consumeResults();

        verify(taskService).updateResult(eq(7L), eq(message), eq("FAILED"));
        verify(webSocketHandler).broadcast(eq(message));
        verifyNoInteractions(alertRepository);
    }

    @Test
    void consumeResults_handlesProcessingStatus_updatesTaskOnly() throws Exception {
        String message = "{\"taskId\":3,\"status\":\"PROCESSING\"}";

        when(redisTemplate.opsForList()).thenReturn(listOperations);
        when(listOperations.leftPop("ai:results")).thenReturn(message);

        redisSubscriberService.consumeResults();

        verify(taskService).updateStatus(eq(3L), eq("PROCESSING"));
        verify(webSocketHandler).broadcast(eq(message));
        verifyNoInteractions(alertRepository);
    }

    @Test
    void consumeResults_handlesCompletedWithNoAlerts() throws Exception {
        String message = "{\"taskId\":8,\"status\":\"COMPLETED\",\"trackCount\":1,\"alertCount\":0,\"totalFrames\":100}";

        when(redisTemplate.opsForList()).thenReturn(listOperations);
        when(listOperations.leftPop("ai:results")).thenReturn(message);

        redisSubscriberService.consumeResults();

        verify(taskService).updateResult(eq(8L), any(String.class), eq("COMPLETED"));
        verifyNoInteractions(alertRepository);
        verify(webSocketHandler).broadcast(any(String.class));
    }

    @Test
    void consumeResults_handlesMalformedJson_doesNotThrow() throws Exception {
        when(redisTemplate.opsForList()).thenReturn(listOperations);
        when(listOperations.leftPop("ai:results")).thenReturn("NOT_JSON");

        // should not throw
        redisSubscriberService.consumeResults();

        verifyNoInteractions(taskService, alertRepository, webSocketHandler);
    }
}
