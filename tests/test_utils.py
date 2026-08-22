import sys
import os

# Allow imports from the app/ package when running tests directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.utils import strip_json_fences, is_forwarded_message, timestamped_filename

def test_strip_json_fences_removes_fenced_json():
    raw = '```json\n[{"sender": "Steam"}]\n```'
    result = strip_json_fences(raw)
    assert result == '[{"sender": "Steam"}]'


def test_strip_json_fences_leaves_plain_json_unchanged():
    raw = '[{"sender": "Steam"}]'
    result = strip_json_fences(raw)
    assert result == '[{"sender": "Steam"}]'


def test_strip_json_fences_handles_fence_without_json_label():
    raw = '```\n[{"sender": "Steam"}]\n```'
    result = strip_json_fences(raw)
    assert result == '[{"sender": "Steam"}]'


def test_is_forwarded_message_detects_forward_marker():
    label = "Unread Manjit Baishya Recent changes to your Steam account 09:18 Forwarded message - From: Steam Support"
    assert is_forwarded_message(label) is True


def test_is_forwarded_message_returns_false_for_native_email():
    label = "Unread Microsoft account team New sign-in detected 13:02 Microsoft account New sign-in detected"
    assert is_forwarded_message(label) is False


def test_timestamped_filename_has_correct_format():
    filename = timestamped_filename("digest", "md")
    assert filename.startswith("digest_")
    assert filename.endswith(".md")

    # e.g. "digest_20260822_143000.md" 
    assert len(filename) == len("digest_") + 15 + len(".md")