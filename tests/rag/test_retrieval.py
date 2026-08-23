from rag.retrieval import retrieve_guide_chunks


class _FakeCursor:
    def __init__(self, rows):
        self._rows = rows
        self.executed_params = None

    def execute(self, sql, params):
        self.executed_params = params

    def fetchall(self):
        return self._rows

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


class _FakeConnection:
    def __init__(self, rows):
        self._cursor = _FakeCursor(rows)

    def cursor(self):
        return self._cursor

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


def test_retrieve_guide_chunks_returns_sorted_mapped_results(mocker):
    rows = [
        ("Rome", "Eat", "https://en.wikivoyage.org/wiki/Rome", "Great trattorias.", 0.10),
        ("Rome", "See", "https://en.wikivoyage.org/wiki/Rome", "The Colosseum.", 0.25),
    ]
    fake_conn = _FakeConnection(rows)

    mocker.patch("rag.retrieval.embed_texts", return_value=[[0.1, 0.2, 0.3]])
    mocker.patch("rag.retrieval.get_connection", return_value=fake_conn)

    results = retrieve_guide_chunks("food in Rome", k=2)

    assert [r.distance for r in results] == [0.10, 0.25]
    assert results[0].city == "Rome"
    assert results[0].section_title == "Eat"
    assert results[0].text == "Great trattorias."
    assert fake_conn._cursor.executed_params["k"] == 2


def test_retrieve_guide_chunks_returns_empty_when_no_matches(mocker):
    fake_conn = _FakeConnection(rows=[])

    mocker.patch("rag.retrieval.embed_texts", return_value=[[0.1, 0.2, 0.3]])
    mocker.patch("rag.retrieval.get_connection", return_value=fake_conn)

    results = retrieve_guide_chunks("a destination with no ingested guide data")

    assert results == []
