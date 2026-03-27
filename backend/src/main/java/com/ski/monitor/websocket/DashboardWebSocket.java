package com.ski.monitor.websocket;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import jakarta.websocket.OnClose;
import jakarta.websocket.OnError;
import jakarta.websocket.OnMessage;
import jakarta.websocket.OnOpen;
import jakarta.websocket.Session;
import jakarta.websocket.server.ServerEndpoint;
import java.io.IOException;
import java.util.concurrent.CopyOnWriteArraySet;

@ServerEndpoint("/ws/dashboard")
@Component
@Slf4j
public class DashboardWebSocket {

    private static int onlineCount = 0;
    private static CopyOnWriteArraySet<DashboardWebSocket> webSocketSet = new CopyOnWriteArraySet<>();
    private Session session;

    @OnOpen
    public void onOpen(Session session) {
        this.session = session;
        webSocketSet.add(this);
        addOnlineCount();
        log.info("大屏连接加入！当前在线大屏数为" + getOnlineCount());
    }

    @OnClose
    public void onClose() {
        webSocketSet.remove(this);
        subOnlineCount();
        log.info("大屏连接关闭！当前在线大屏数为" + getOnlineCount());
    }

    @OnMessage
    public void onMessage(String message, Session session) {
        log.info("收到大屏消息: {}", message);
    }

    @OnError
    public void onError(Session session, Throwable error) {
        log.error("大屏WebSocket发生错误");
        error.printStackTrace();
    }

    /**
     * 群发自定义消息，比如有新的 SOS 时，调用此方法通知所有大屏
     */
    public static void sendInfo(Object messageObject) {
        ObjectMapper mapper = new ObjectMapper();
        String message;
        try {
            message = mapper.writeValueAsString(messageObject);
        } catch (Exception e) {
            log.error("消息序列化失败", e);
            return;
        }

        for (DashboardWebSocket item : webSocketSet) {
            try {
                item.sendMessage(message);
            } catch (IOException e) {
                continue;
            }
        }
    }

    public void sendMessage(String message) throws IOException {
        this.session.getBasicRemote().sendText(message);
    }

    public static synchronized int getOnlineCount() {
        return onlineCount;
    }

    public static synchronized void addOnlineCount() {
        DashboardWebSocket.onlineCount++;
    }

    public static synchronized void subOnlineCount() {
        DashboardWebSocket.onlineCount--;
    }
}
