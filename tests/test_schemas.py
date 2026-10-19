# tests/test_schemas.py
import pytest
from pydantic import ValidationError

from backend.schemas import ResearchCreate


def test_valid_topic_is_accepted():
    body = ResearchCreate(topic="impact of war on markets")
    assert body.topic == "impact of war on markets"


def test_topic_is_trimmed():
    body = ResearchCreate(topic="  impact of war  ")
    assert body.topic == "impact of war"


def test_topic_at_maximum_length_is_accepted():
    body = ResearchCreate(topic="a" * 300)
    assert len(body.topic) == 300


def test_topic_over_maximum_length_is_rejected():
    with pytest.raises(ValidationError):
        ResearchCreate(topic="a" * 301)


def test_topic_under_minimum_length_is_rejected():
    with pytest.raises(ValidationError):
        ResearchCreate(topic="ab")


def test_blank_topic_is_rejected():
    # Passes the minimum length before trimming, then fails after it.
    with pytest.raises(ValidationError):
        ResearchCreate(topic="   ")


def test_missing_topic_is_rejected():
    with pytest.raises(ValidationError):
        ResearchCreate()