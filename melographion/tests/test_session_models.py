import pytest

from melographion.models import MelographionSession, ObservationSet


def test_session_event_status_transitions_and_separate_observations():
    session = MelographionSession()
    event = session.add_event(song_id="track-1", prompt="Prompt")

    assert event.status == "pending_prompt"

    event.capture_response("Verbatim response")
    assert event.status == "response_captured"
    assert event.user_response_verbatim == "Verbatim response"

    inferred = ObservationSet(extracted_symbols=["mirror"], emotional_tags=["grief"])
    event.set_inferred_observations(inferred)
    assert event.status == "inference_pending"
    assert event.inferred_observations is not None
    assert event.reviewed_observations is None

    reviewed = inferred.model_copy(update={"review_note": "Accepted with caution."})
    event.review_observations(reviewed)
    assert event.status == "inference_reviewed"
    assert event.reviewed_observations is not None
    assert event.reviewed_observations.analysis_status == "reviewed"
    assert event.inferred_observations.analysis_status == "inferred"

    event.suggest_next_song(song_id="track-2", reasoning_public="Follow the mirror motif.")
    assert event.status == "next_song_suggested"
    assert event.next_song_id == "track-2"

    event.complete()
    assert event.status == "complete"


def test_verbatim_response_cannot_be_overwritten():
    session = MelographionSession()
    event = session.add_event(song_id="track-1", prompt="Prompt")
    event.capture_response("Original")

    with pytest.raises(ValueError):
        event.capture_response("Changed")

    with pytest.raises(ValueError):
        event.user_response_verbatim = "Changed"
