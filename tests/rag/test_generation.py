from types import SimpleNamespace

from rag.generation import generate_itinerary
from rag.retrieval import RetrievedChunk


def _fake_response(text, stop_reason="end_turn"):
    return SimpleNamespace(
        stop_reason=stop_reason,
        content=[SimpleNamespace(type="text", text=text)],
    )


def _fake_tool_use_response(tool_name, tool_input, tool_id="toolu_1"):
    return SimpleNamespace(
        stop_reason="tool_use",
        content=[SimpleNamespace(type="tool_use", id=tool_id, name=tool_name, input=tool_input)],
    )


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


def test_generate_itinerary_executes_tool_call_and_sends_followup_without_tools(mocker):
    mocker.patch("rag.generation.retrieve_guide_chunks", return_value=[])
    mocker.patch(
        "rag.generation.execute_tool_call",
        return_value={"found": True, "price": 199, "airlines": "LOT"},
    )

    first_response = _fake_tool_use_response(
        "search_flights",
        {"departure_city": "Warsaw", "destination_city": "Rome",
         "date_from": "2026-09-01", "date_to": "2026-09-05"},
    )
    final_response = _fake_response("Day 1: fly to Rome for 199 PLN on LOT.")

    fake_client = SimpleNamespace()
    fake_client.messages = SimpleNamespace(
        create=mocker.Mock(side_effect=[first_response, final_response])
    )
    mocker.patch("rag.generation.get_anthropic_client", return_value=fake_client)

    result = generate_itinerary(
        "Rome", 3, "Medium", "food", "Cultural",
        departure_city="Warsaw", date_from="2026-09-01", date_to="2026-09-05",
        tools=[{"name": "search_flights"}],
    )

    assert "Day 1: fly to Rome for 199 PLN on LOT." in result
    assert fake_client.messages.create.call_count == 2

    second_call_kwargs = fake_client.messages.create.call_args_list[1].kwargs
    assert "tools" not in second_call_kwargs

    tool_result_message = second_call_kwargs["messages"][-1]
    assert tool_result_message["role"] == "user"
    assert tool_result_message["content"][0]["type"] == "tool_result"
    assert tool_result_message["content"][0]["tool_use_id"] == "toolu_1"


def test_generate_itinerary_skips_tools_when_model_doesnt_need_them(mocker):
    mocker.patch("rag.generation.retrieve_guide_chunks", return_value=[])
    mock_execute_tool_call = mocker.patch("rag.generation.execute_tool_call")

    fake_client = SimpleNamespace()
    fake_client.messages = SimpleNamespace(
        create=mocker.Mock(return_value=_fake_response("A general itinerary."))
    )
    mocker.patch("rag.generation.get_anthropic_client", return_value=fake_client)

    result = generate_itinerary(
        "Rome", 3, "Medium", "food", "Cultural", tools=[{"name": "search_flights"}]
    )

    assert "A general itinerary." in result
    assert fake_client.messages.create.call_count == 1
    mock_execute_tool_call.assert_not_called()
