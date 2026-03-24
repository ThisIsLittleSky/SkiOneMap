package com.ski.monitor.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

@Data
@TableName("scene_config")
public class SceneConfig {

    @TableId(type = IdType.INPUT)
    private Long id = 1L;

    private String sceneName = "崇礼滑雪场";

    @TableField("lat_nw") private Double latNW;
    @TableField("lng_nw") private Double lngNW;
    @TableField("lat_ne") private Double latNE;
    @TableField("lng_ne") private Double lngNE;
    @TableField("lat_sw") private Double latSW;
    @TableField("lng_sw") private Double lngSW;
    @TableField("lat_se") private Double latSE;
    @TableField("lng_se") private Double lngSE;

    @TableField("weather_city_code")
    private String weatherCityCode = "101090301";
}
