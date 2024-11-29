import attrs
import cattrs
import pytest

from slack_github_tracker.handlers.slack import _interpret as interpret


class TestParsingMessage:
    def test_it_can_parse_a_message(self) -> None:
        body: dict[str, object] = {
            "token": "oBaw0jt6jmXl7HD8geO7qlAA",
            "team_id": "TS8HER95B",
            "team_domain": "myslack",
            "channel_id": "C090Z73QS0Y",
            "channel_name": "slack-app-play",
            "user_id": "US8Z4ESLL",
            "user_name": "delfick",
            "command": "/track_pr",
            "api_app_id": "A08V9SZMPF2",
            "text": "stuff",
            "is_enterprise_install": "false",
            "response_url": "https://hooks.slack.com/commands/TS8HER95B/8101191819973/BYn2EBedZXslXHwrKjr7fljK",
            "trigger_id": "8089503654311.890590854181.e23e5b2da9894a19f13784ce1a01cafc",
        }

        expected = interpret.Command(
            token="oBaw0jt6jmXl7HD8geO7qlAA",
            team_id="TS8HER95B",
            team_domain="myslack",
            channel_id="C090Z73QS0Y",
            channel_name="slack-app-play",
            user_id="US8Z4ESLL",
            user_name="delfick",
            command="/track_pr",
            api_app_id="A08V9SZMPF2",
            text="stuff",
            is_enterprise_install=False,
            response_url="https://hooks.slack.com/commands/TS8HER95B/8101191819973/BYn2EBedZXslXHwrKjr7fljK",
            trigger_id="8089503654311.890590854181.e23e5b2da9894a19f13784ce1a01cafc",
        )

        assert interpret.CommandDeserializer(interpret.Command).deserialize(body) == expected

        assert interpret.CommandDeserializer(interpret.Command).deserialize(
            {**body, "is_enterprise_install": "true"}
        ) == attrs.evolve(expected, is_enterprise_install=True)

    def test_it_can_fail_to_parse(self) -> None:
        body: dict[str, object] = {
            "token": "oBaw0jt6jmXl7HD8geO7qlAA",
            "team_id": "TS8HER95B",
            "team_domain": "myslack",
            "channel_id": "C090Z73QS0Y",
            "channel_name": "slack-app-play",
            "user_id": "US8Z4ESLL",
            "user_name": "delfick",
            "command": "/track_pr",
            "api_app_id": "A08V9SZMPF2",
            "text": "stuff",
            "is_enterprise_install": "nup",
            "response_url": "https://hooks.slack.com/commands/TS8HER95B/8101191819973/BYn2EBedZXslXHwrKjr7fljK",
            "trigger_id": "8089503654311.890590854181.e23e5b2da9894a19f13784ce1a01cafc",
        }

        with pytest.raises(cattrs.errors.ClassValidationError) as e:
            interpret.CommandDeserializer(interpret.Command).deserialize(body)

        assert e.value.message == "While structuring Command"
        assert str(e.value.group_exceptions()[0][0][0]) == "Failed to parse boolean from: 'nup'"
        assert (
            e.value.group_exceptions()[0][0][1]
            == "Structuring class Command @ attribute is_enterprise_install"
        )
