import numpy as np

from app.services.yolo_processor import YOLOProcessor


class FakeBoxes:
    def __init__(self, ids, xywh, conf, cls):
        self.id = np.array(ids)
        self.xywh = np.array(xywh, dtype=float)
        self.conf = np.array(conf, dtype=float)
        self.cls = np.array(cls, dtype=float)

    def __len__(self):
        return len(self.id)


class FakeResult:
    def __init__(self, boxes):
        self.boxes = boxes


class FakeModel:
    def __init__(self, results):
        self.results = results
        self.names = {0: "person"}
        self.calls = []

    def track(self, source, **kwargs):
        self.calls.append({"source": source, **kwargs})
        return self.results


def test_build_track_kwargs_uses_explicit_tracker_and_person_class(tmp_path):
    processor = YOLOProcessor()
    processor.tracker_config = str(tmp_path / "ski_bytetrack.yaml")
    processor.conf_threshold = 0.22
    processor.iou_threshold = 0.48
    processor.target_classes = [0]

    kwargs = processor._build_track_kwargs()

    assert kwargs["tracker"] == str(tmp_path / "ski_bytetrack.yaml")
    assert kwargs["conf"] == 0.22
    assert kwargs["iou"] == 0.48
    assert kwargs["classes"] == [0]
    assert kwargs["persist"] is True
    assert kwargs["stream"] is True


def test_filter_tracks_removes_short_segments():
    processor = YOLOProcessor()
    processor.min_track_frames = 3
    tracks = [
        {"trackId": 1, "points": [{"frame": 0}, {"frame": 1}, {"frame": 2}]},
        {"trackId": 2, "points": [{"frame": 0}]},
    ]

    filtered = processor._filter_tracks(tracks)

    assert [track["trackId"] for track in filtered] == [1]


def test_point_in_polygon_detects_inside_and_outside():
    processor = YOLOProcessor()
    polygon = [(0, 0), (100, 0), (100, 100), (0, 100)]

    assert processor._point_in_polygon(50, 50, polygon) is True
    assert processor._point_in_polygon(150, 50, polygon) is False


def test_filter_tracks_by_roi_removes_edge_tracks():
    processor = YOLOProcessor()
    processor.slope_roi_keep_ratio = 0.6
    polygon = [(0, 0), (100, 0), (100, 100), (0, 100)]
    tracks = [
        {
            "trackId": 1,
            "className": "person",
            "points": [
                {"frame": 0, "x": 10, "y": 10},
                {"frame": 1, "x": 20, "y": 20},
                {"frame": 2, "x": 30, "y": 30},
            ],
        },
        {
            "trackId": 2,
            "className": "person",
            "points": [
                {"frame": 0, "x": 150, "y": 20},
                {"frame": 1, "x": 160, "y": 30},
                {"frame": 2, "x": 30, "y": 30},
            ],
        },
    ]

    filtered = processor._filter_tracks_by_roi(tracks, polygon)

    assert [track["trackId"] for track in filtered] == [1]


def test_merge_broken_tracks_merges_close_segments():
    processor = YOLOProcessor()
    processor.merge_gap_frames = 4
    processor.merge_distance_threshold = 30
    processor.merge_direction_threshold = 0.1
    tracks = [
        {
            "trackId": 1,
            "className": "person",
            "points": [
                {"frame": 0, "x": 10, "y": 10, "width": 20, "height": 40, "confidence": 0.9},
                {"frame": 1, "x": 12, "y": 14, "width": 20, "height": 40, "confidence": 0.9},
            ],
        },
        {
            "trackId": 8,
            "className": "person",
            "points": [
                {"frame": 3, "x": 16, "y": 20, "width": 20, "height": 40, "confidence": 0.88},
                {"frame": 4, "x": 18, "y": 24, "width": 20, "height": 40, "confidence": 0.88},
            ],
        },
    ]

    merged = processor._merge_broken_tracks(tracks)

    assert len(merged) == 1
    assert merged[0]["trackId"] == 1
    assert [point["frame"] for point in merged[0]["points"]] == [0, 1, 3, 4]


def test_merge_broken_tracks_keeps_far_segments_separate():
    processor = YOLOProcessor()
    processor.merge_gap_frames = 4
    processor.merge_distance_threshold = 25
    tracks = [
        {
            "trackId": 1,
            "className": "person",
            "points": [
                {"frame": 0, "x": 10, "y": 10, "width": 20, "height": 40, "confidence": 0.9},
                {"frame": 1, "x": 12, "y": 14, "width": 20, "height": 40, "confidence": 0.9},
            ],
        },
        {
            "trackId": 8,
            "className": "person",
            "points": [
                {"frame": 3, "x": 90, "y": 120, "width": 20, "height": 40, "confidence": 0.88},
                {"frame": 4, "x": 95, "y": 126, "width": 20, "height": 40, "confidence": 0.88},
            ],
        },
    ]

    merged = processor._merge_broken_tracks(tracks)

    assert len(merged) == 2


def test_merge_broken_tracks_keeps_opposite_direction_separate():
    processor = YOLOProcessor()
    processor.merge_gap_frames = 4
    processor.merge_distance_threshold = 60
    processor.merge_direction_threshold = 0.3
    tracks = [
        {
            "trackId": 1,
            "className": "person",
            "points": [
                {"frame": 0, "x": 10, "y": 10, "width": 20, "height": 40, "confidence": 0.9},
                {"frame": 1, "x": 12, "y": 16, "width": 20, "height": 40, "confidence": 0.9},
            ],
        },
        {
            "trackId": 8,
            "className": "person",
            "points": [
                {"frame": 3, "x": 14, "y": 20, "width": 20, "height": 40, "confidence": 0.88},
                {"frame": 4, "x": 12, "y": 14, "width": 20, "height": 40, "confidence": 0.88},
            ],
        },
    ]

    merged = processor._merge_broken_tracks(tracks)

    assert len(merged) == 2


def test_process_video_applies_tracking_kwargs_and_filters_short_tracks(tmp_path):
    video_path = tmp_path / "sample.mp4"
    video_path.write_bytes(b"video")

    results = [
        FakeResult(FakeBoxes([1, 2], [[10, 20, 30, 40], [100, 120, 20, 30]], [0.9, 0.85], [0, 0])),
        FakeResult(FakeBoxes([1], [[12, 24, 30, 40]], [0.91], [0])),
    ]
    fake_model = FakeModel(results)

    processor = YOLOProcessor()
    processor.model = fake_model
    processor.tracker_config = "custom_tracker.yaml"
    processor.target_classes = [0]
    processor.min_track_frames = 2
    processor._read_video_size = lambda _: (200, 200)
    processor.slope_roi = [(0.0, 0.0), (0.8, 0.0), (0.8, 1.0), (0.0, 1.0)]
    processor.slope_roi_keep_ratio = 0.6

    tracks = processor.process_video(str(video_path))

    assert len(tracks) == 1
    assert tracks[0]["trackId"] == 1
    assert len(tracks[0]["points"]) == 2
    assert fake_model.calls[0]["tracker"] == "custom_tracker.yaml"
    assert fake_model.calls[0]["classes"] == [0]
