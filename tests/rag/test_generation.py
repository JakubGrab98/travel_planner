from types import SimpleNamespace

from rag.generation import generate_itinerary
from rag.retrieval import RetrievedChunk


def _fake_response(text):
    return SimpleNamespace(content=[SimpleNamespace(type="text", text=text)])


def test_generate_itinerary_grounds_response_in_retrieved_chunks(mocker):
    chunks = [
        RetrievedChunk(
            city="Rome",
            section_title="Eat",
            source_url="https://en.wikivoyage.org/wiki/Rome",
            text="Great trattorias near the center.",
            distance=0.1,
        )
    ]
    mocker.patch("rag.generation.retrieve_guide_chunks", return_value=chunks)

    fake_client = SimpleNamespace()
    fake_client.messages = SimpleNamespace(
        create=mocker.Mock(return_value=_fake_response("Day 1: eat at a trattoria."))
    )
    mocker.patch("rag.generation.get_anthropic_client", return_value=fake_client)

    result = generate_itinerary("Rome", 3, "Medium", "food", "Cultural")

    assert "Day 1: eat at a trattoria." in result
    call_kwargs = fake_client.messages.create.call_args.kwargs
    assert "Rome" in call_kwargs["messages"][0]["content"]
    assert "Great trattorias near the center." in call_kwargs["messages"][0]["content"]
    assert "tools" not in call_kwargs


def test_generate_itinerary_handles_no_retrieved_chunks_gracefully(mocker):
    mocker.patch("rag.generation.retrieve_guide_chunks", return_value=[])

    fake_client = SimpleNamespace()
    fake_client.messages = SimpleNamespace(
        create=mocker.Mock(return_value=_fake_response("A general itinerary for Lisbon."))
    )
    mocker.patch("rag.generation.get_anthropic_client", return_value=fake_client)

    result = generate_itinerary("Lisbon", 3, "Medium", "food", "Cultural")

    assert "A general itinerary for Lisbon." in result
    call_kwargs = fake_client.messages.create.call_args.kwargs
    assert "No local guide data available" in call_kwargs["messages"][0]["content"]
