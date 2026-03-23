package com.ski.monitor.repository;

import com.ski.monitor.entity.Alert;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface AlertRepository extends JpaRepository<Alert, Long> {
    List<Alert> findByTaskIdOrderByCreatedAtDesc(Long taskId);
}
