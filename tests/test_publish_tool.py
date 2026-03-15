import json
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tools


def test_publish_facebook_variant_without_token():
    payload = {
        "workspace_id": "ws_1",
        "variant_id": "var_1",
        "platform": "facebook",
        "publish_status": "published",
        "platform_post_id": "123_456",
    }

    with patch.object(tools.pb_client, "publish_facebook_variant", return_value=payload) as mock_publish:
        raw = tools.publish_facebook_variant("ws_1", "var_1")
        data = json.loads(raw)

    mock_publish.assert_called_once_with("ws_1", "var_1")
    assert data["publish_status"] == "published"
    assert data["platform_post_id"] == "123_456"


def test_publish_facebook_variant_with_token():
    payload = {
        "workspace_id": "ws_1",
        "variant_id": "var_1",
        "platform": "facebook",
        "publish_status": "published",
    }

    with patch.object(
        tools.pb_client,
        "publish_facebook_variant_with_token",
        return_value=payload,
    ) as mock_publish:
        raw = tools.publish_facebook_variant("ws_1", "var_1", "token_abc")
        data = json.loads(raw)

    mock_publish.assert_called_once_with("ws_1", "var_1", "token_abc")
    assert data["platform"] == "facebook"


def test_publish_facebook_variant_error_message():
    with patch.object(tools.pb_client, "publish_facebook_variant", side_effect=RuntimeError("boom")):
        raw = tools.publish_facebook_variant("ws_1", "var_1")

    assert raw.startswith("Error:")
    assert "boom" in raw
