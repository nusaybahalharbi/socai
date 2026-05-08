"""Tests for ML feature engineering + heuristic fallback inference."""
from app.ml.features import alert_to_features, alert_to_vector, FEATURE_NAMES
from app.ml.inference import Classifier


def test_features_have_consistent_shape():
    a = {"severity": "high", "failed_login_count": 12, "command_line": "powershell -enc abc"}
    feats = alert_to_features(a)
    assert set(feats.keys()) == set(FEATURE_NAMES)
    vec = alert_to_vector(a)
    assert vec.shape == (1, len(FEATURE_NAMES))


def test_heuristic_flags_clear_threats():
    clf = Classifier()
    # force heuristic path
    clf.bundle = None
    label, conf, expl = clf.predict({
        "severity": "critical",
        "failed_login_count": 30,
        "command_line": "powershell.exe -enc abc",
        "is_off_hours": True,
    })
    assert label == "threat"
    assert conf >= 0.5
    assert expl["method"] == "heuristic"


def test_heuristic_flags_benign_as_fp():
    clf = Classifier()
    clf.bundle = None
    label, conf, expl = clf.predict({
        "severity": "low", "failed_login_count": 0,
        "command_line": "Get-Process",
        "is_off_hours": False,
    })
    assert label == "false_positive"
