package com.ski.monitor.service;

import com.ski.monitor.entity.User;
import com.ski.monitor.repository.UserRepository;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.UUID;
import java.util.concurrent.TimeUnit;

@Service
public class AuthService {

    private static final String TOKEN_PREFIX = "auth:token:";
    private static final long TOKEN_EXPIRE_HOURS = 8;

    private final UserRepository userRepository;
    private final StringRedisTemplate redisTemplate;

    public AuthService(UserRepository userRepository, StringRedisTemplate redisTemplate) {
        this.userRepository = userRepository;
        this.redisTemplate = redisTemplate;
    }

    /**
     * 登录验证，成功返回 token，失败返回 null。
     * 密码支持明文和 MD5 两种存储方式（自动识别）。
     */
    public String login(String username, String password) {
        User user = userRepository.findByUsername(username).orElse(null);
        if (user == null) return null;

        boolean matched = user.getPassword().equals(password)
                || user.getPassword().equalsIgnoreCase(md5(password));
        if (!matched) return null;

        String token = UUID.randomUUID().toString().replace("-", "");
        redisTemplate.opsForValue().set(
                TOKEN_PREFIX + token,
                username,
                TOKEN_EXPIRE_HOURS,
                TimeUnit.HOURS
        );
        return token;
    }

    /** 验证 token 是否有效，返回用户名；无效返回 null。 */
    public String verify(String token) {
        if (token == null || token.isBlank()) return null;
        return redisTemplate.opsForValue().get(TOKEN_PREFIX + token);
    }

    /** 登出，删除 token。 */
    public void logout(String token) {
        if (token != null) redisTemplate.delete(TOKEN_PREFIX + token);
    }

    private static String md5(String input) {
        try {
            MessageDigest md = MessageDigest.getInstance("MD5");
            byte[] bytes = md.digest(input.getBytes(StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder();
            for (byte b : bytes) sb.append(String.format("%02x", b));
            return sb.toString();
        } catch (Exception e) {
            return "";
        }
    }
}
