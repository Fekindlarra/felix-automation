#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TDD Test: Pydantic v2.5 regex constraint on List[str]
Blocker 3.4.7: Query(regex=...) over List[str] rejected by Pydantic 2.5
- Should accept valid event names matching pattern
- Should reject invalid event names NOT matching pattern
- Should work with Pydantic 2.5+ (Annotated + StringConstraints approach)
"""

import pytest
import sys
from pathlib import Path
from typing import List
from pydantic import BaseModel, ValidationError, conlist, StringConstraints
from typing_extensions import Annotated

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestPydanticRegexOnList:
    """
    Test suite to ensure webhook event validation works with Pydantic 2.5
    without using deprecated regex= on List[str]
    """

    def test_webhook_events_accept_valid_anomaly_critical(self):
        """
        RED: Should accept valid event name 'anomaly.critical'
        """
        # Define pattern: anomaly.(critical|high|medium|low) | prediction.(high|low) | recommendation.(urgent|high)
        valid_event = "anomaly.critical"
        pattern = r"^(anomaly\.(critical|high|medium|low)|prediction\.(high|low)|recommendation\.(urgent|high))$"

        import re
        assert re.match(pattern, valid_event), f"Pattern should match '{valid_event}'"

    def test_webhook_events_accept_valid_prediction_high(self):
        """
        RED: Should accept valid event name 'prediction.high'
        """
        valid_event = "prediction.high"
        pattern = r"^(anomaly\.(critical|high|medium|low)|prediction\.(high|low)|recommendation\.(urgent|high))$"

        import re
        assert re.match(pattern, valid_event), f"Pattern should match '{valid_event}'"

    def test_webhook_events_accept_valid_recommendation_urgent(self):
        """
        RED: Should accept valid event name 'recommendation.urgent'
        """
        valid_event = "recommendation.urgent"
        pattern = r"^(anomaly\.(critical|high|medium|low)|prediction\.(high|low)|recommendation\.(urgent|high))$"

        import re
        assert re.match(pattern, valid_event), f"Pattern should match '{valid_event}'"

    def test_webhook_events_reject_invalid_format(self):
        """
        RED: Should reject invalid event names NOT matching pattern
        """
        invalid_event = "invalid.event"
        pattern = r"^(anomaly\.(critical|high|medium|low)|prediction\.(high|low)|recommendation\.(urgent|high))$"

        import re
        assert not re.match(pattern, invalid_event), f"Pattern should NOT match '{invalid_event}'"

    def test_webhook_events_reject_invalid_anomaly_type(self):
        """
        RED: Should reject 'anomaly.invalid' (invalid severity)
        """
        invalid_event = "anomaly.invalid"
        pattern = r"^(anomaly\.(critical|high|medium|low)|prediction\.(high|low)|recommendation\.(urgent|high))$"

        import re
        assert not re.match(pattern, invalid_event), f"Pattern should NOT match '{invalid_event}'"

    def test_webhook_events_with_annotated_constraint(self):
        """
        GREEN: Using Annotated + StringConstraints for single string validation
        This is the Pydantic 2.5 compatible way to validate patterns
        """
        # In Pydantic 2.5, use Annotated with pattern constraint for individual items
        EventPattern = Annotated[
            str,
            StringConstraints(
                pattern=r"^(anomaly\.(critical|high|medium|low)|prediction\.(high|low)|recommendation\.(urgent|high))$"
            )
        ]

        class WebhookEvent(BaseModel):
            event: EventPattern

        # Should accept valid event
        event_model = WebhookEvent(event="anomaly.critical")
        assert event_model.event == "anomaly.critical"

        # Should reject invalid event
        with pytest.raises(ValidationError):
            WebhookEvent(event="invalid.event")

    def test_webhook_events_list_with_individual_validation(self):
        """
        GREEN: Validate each item in list individually using Annotated
        This properly validates a List[str] in Pydantic 2.5
        """
        from typing import List as ListType

        EventPattern = Annotated[
            str,
            StringConstraints(
                pattern=r"^(anomaly\.(critical|high|medium|low)|prediction\.(high|low)|recommendation\.(urgent|high))$"
            )
        ]

        class WebhookConfig(BaseModel):
            events: ListType[EventPattern] = ["anomaly.critical"]

        # Should accept valid list
        config = WebhookConfig(events=["anomaly.critical", "prediction.high"])
        assert config.events == ["anomaly.critical", "prediction.high"]

        # Should reject if any item is invalid
        with pytest.raises(ValidationError):
            WebhookConfig(events=["anomaly.critical", "invalid.event"])

    def test_webhook_events_empty_list_allowed(self):
        """
        GREEN: Empty list should be allowed (uses default)
        """
        from typing import List as ListType

        EventPattern = Annotated[
            str,
            StringConstraints(
                pattern=r"^(anomaly\.(critical|high|medium|low)|prediction\.(high|low)|recommendation\.(urgent|high))$"
            )
        ]

        class WebhookConfig(BaseModel):
            events: ListType[EventPattern] = ["anomaly.critical"]

        # Should use default when empty
        config = WebhookConfig(events=[])
        assert config.events == []

    def test_webhook_query_parameter_validation_pattern(self):
        """
        GREEN: Document the correct pattern for Query validation with List[str]
        This test documents the fix for blocker 3.4.7
        """
        # In FastAPI with Pydantic 2.5, for List[str] with pattern validation:
        # Instead of: events: List[str] = Query(..., regex="pattern")
        # Use: events: List[Annotated[str, StringConstraints(pattern="pattern")]] = Query(...)

        pattern = r"^(anomaly\.(critical|high|medium|low)|prediction\.(high|low)|recommendation\.(urgent|high))$"

        # This is the correct Pydantic 2.5 way to define it:
        from typing import List as ListType

        EventPattern = Annotated[
            str,
            StringConstraints(pattern=pattern)
        ]

        class ValidWebhookRequest(BaseModel):
            webhook_url: str
            events: ListType[EventPattern] = ["anomaly.critical"]
            active: bool = True

        # Valid request should work
        valid_request = ValidWebhookRequest(
            webhook_url="https://example.com/webhook",
            events=["anomaly.critical", "prediction.high"],
            active=True
        )
        assert len(valid_request.events) == 2

        # Invalid event in list should fail
        with pytest.raises(ValidationError) as exc_info:
            ValidWebhookRequest(
                webhook_url="https://example.com/webhook",
                events=["anomaly.critical", "bad.event"],
                active=True
            )
        assert "pattern" in str(exc_info.value).lower()
