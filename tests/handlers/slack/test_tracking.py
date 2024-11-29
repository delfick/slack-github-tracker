import pytest

from slack_github_tracker.handlers.slack import _tracking as tracking


class TestParsingTrackPRMessage:
    @pytest.fixture
    def base_body(self) -> dict[str, object]:
        return {
            "token": "oBaw0jt6jmXl7HD8geO7qlAA",
            "team_id": "TS8HER95B",
            "team_domain": "myslack",
            "channel_id": "C090Z73QS0Y",
            "channel_name": "slack-app-play",
            "user_id": "US8Z4ESLL",
            "user_name": "delfick",
            "command": "/track_pr",
            "api_app_id": "A08V9SZMPF2",
            "is_enterprise_install": "false",
            "response_url": "https://hooks.slack.com/commands/TS8HER95B/8101191819973/BYn2EBedZXslXHwrKjr7fljK",
            "trigger_id": "8089503654311.890590854181.e23e5b2da9894a19f13784ce1a01cafc",
        }

    def test_it_can_extract_github_url(self, base_body: dict[str, object]) -> None:
        body = {**base_body, "text": "https://github.com/delfick/test-for-github-webhooks/pull/2"}
        message = tracking.TrackPRMessageDeserializer().deserialize(body)
        assert message.pr_to_track == tracking.PR(
            organisation="delfick", repo="test-for-github-webhooks", pr_number=2
        )

    def test_it_can_extract_github_path(self, base_body: dict[str, object]) -> None:
        body = {**base_body, "text": "delfick/test-for-github-webhooks/pull/2"}
        message = tracking.TrackPRMessageDeserializer().deserialize(body)
        assert message.pr_to_track == tracking.PR(
            organisation="delfick", repo="test-for-github-webhooks", pr_number=2
        )

    def test_it_is_ok_with_extra_slashes(self, base_body: dict[str, object]) -> None:
        body = {**base_body, "text": "//delfick/test-for-github-webhooks/pull/2/"}
        message = tracking.TrackPRMessageDeserializer().deserialize(body)
        assert message.pr_to_track == tracking.PR(
            organisation="delfick", repo="test-for-github-webhooks", pr_number=2
        )

    def test_it_does_not_like_other_urls(self, base_body: dict[str, object]) -> None:
        body = {**base_body, "text": "https://gitlab.com/delfick/test-for-github-webhooks/pull/2/"}
        with pytest.raises(tracking.InvalidPR):
            tracking.TrackPRMessageDeserializer().deserialize(body)

    def test_it_does_not_like_non_pull_path(self, base_body: dict[str, object]) -> None:
        for invalid in (
            "https://github.com/delfick/test-for-github-webhooks/issue/2/",
            "/delfick/test-for-github-webhooks/issue/2/",
        ):
            body = {**base_body, "text": invalid}
            with pytest.raises(tracking.InvalidPR):
                tracking.TrackPRMessageDeserializer().deserialize(body)
