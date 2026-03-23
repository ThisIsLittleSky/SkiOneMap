package com.ski.monitor.controller;

import com.ski.monitor.service.AuthService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    /** 登录，返回 token。不提供注册接口，账号由管理员预置。 */
    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody Map<String, String> body) {
        String username = body.get("username");
        String password = body.get("password");
        if (username == null || password == null) {
            return ResponseEntity.badRequest().body(Map.of("error", "用户名和密码不能为空"));
        }
        String token = authService.login(username, password);
        if (token == null) {
            return ResponseEntity.status(401).body(Map.of("error", "用户名或密码错误"));
        }
        return ResponseEntity.ok(Map.of("token", token, "username", username));
    }

    /** 验证 token 是否有效。 */
    @GetMapping("/verify")
    public ResponseEntity<?> verify(@RequestHeader(value = "X-Auth-Token", required = false) String token) {
        String username = authService.verify(token);
        if (username == null) {
            return ResponseEntity.status(401).body(Map.of("error", "未登录或 token 已过期"));
        }
        return ResponseEntity.ok(Map.of("username", username, "valid", true));
    }

    /** 登出。 */
    @PostMapping("/logout")
    public ResponseEntity<?> logout(@RequestHeader(value = "X-Auth-Token", required = false) String token) {
        authService.logout(token);
        return ResponseEntity.ok(Map.of("message", "已登出"));
    }
}
