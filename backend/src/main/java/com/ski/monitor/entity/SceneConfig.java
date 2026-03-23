package com.ski.monitor.entity;

import jakarta.persistence.*;
import lombok.Data;

/**
 * 场地配置：存储 3D 场景的四角经纬度及其他全局设置，单条记录（id=1）。
 */
@Data
@Entity
@Table(name = "scene_config")
public class SceneConfig {

    @Id
    private Long id = 1L;

    /** 场地名称 */
    @Column(length = 100)
    private String sceneName = "崇礼滑雪场";

    // 四角经纬度
    @Column(name = "lat_nw") private Double latNW;
    @Column(name = "lng_nw") private Double lngNW;
    @Column(name = "lat_ne") private Double latNE;
    @Column(name = "lng_ne") private Double lngNE;
    @Column(name = "lat_sw") private Double latSW;
    @Column(name = "lng_sw") private Double lngSW;
    @Column(name = "lat_se") private Double latSE;
    @Column(name = "lng_se") private Double lngSE;

    /** 天气城市编码 */
    @Column(name = "weather_city_code", length = 20)
    private String weatherCityCode = "101090301";
}
