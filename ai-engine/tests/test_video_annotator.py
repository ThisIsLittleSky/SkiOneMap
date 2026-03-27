from app.services.video_annotator import VideoAnnotator


def test_build_output_path_creates_annotated_name(tmp_path):
    annotator = VideoAnnotator()
    annotator.output_root = str(tmp_path / "annotated")
    video_path = tmp_path / "sample.mp4"
    video_path.write_bytes(b"video")

    output_path = annotator._build_output_path(str(video_path), 12)

    assert output_path.endswith("sample_task12_annotated.mp4")
    assert str(tmp_path / "annotated") in output_path


def test_build_track_indexes_groups_points_by_frame():
    annotator = VideoAnnotator()
    tracks = [
        {
            "trackId": 3,
            "className": "person",
            "points": [
                {"frame": 0, "x": 10, "y": 20, "width": 30, "height": 40, "confidence": 0.9},
                {"frame": 2, "x": 12, "y": 26, "width": 30, "height": 40, "confidence": 0.88},
            ],
        }
    ]

    points_by_frame, history_by_track = annotator._build_track_indexes(tracks)

    assert 0 in points_by_frame
    assert points_by_frame[0][0]["trackId"] == 3
    assert history_by_track[3][1]["frame"] == 2


def test_build_alert_index_keeps_alert_visible_for_hold_frames():
    annotator = VideoAnnotator()
    annotator.alert_hold_frames = 3
    alerts = [{"alertType": "OVERSPEED", "frame": 5, "positionX": 100, "positionY": 80}]

    alerts_by_frame = annotator._build_alert_index(alerts)

    assert 5 in alerts_by_frame
    assert 6 in alerts_by_frame
    assert 7 in alerts_by_frame
    assert 8 not in alerts_by_frame


def test_build_temp_output_path_appends_render_suffix(tmp_path):
    annotator = VideoAnnotator()
    output_path = tmp_path / "annotated.mp4"

    temp_path = annotator._build_temp_output_path(str(output_path))

    assert temp_path.endswith("annotated_render.mp4")
