from dnd import DNDData
from search import search_from_query


class TestDndData:
    dnd_data = DNDData()
    queries: list[str] = [
        "fireball",
        "dagger",
        "poisoned",
        "goblin",
        "initiative",
        "attack",
        "tough",
        "ABCDF",
    ]

    def test_dnddatalist_search(self):
        for query in self.queries:
            for data in self.dnd_data:
                no_error = True
                try:
                    data.search(query)
                except Exception:
                    no_error = False

                assert (
                    no_error
                ), f"{data.entries[0].object_type} DNDDataList failed search()"

    def test_search_from_query(self):
        for query in self.queries:
            no_error = True

            try:
                search_from_query(query, self.dnd_data)
            except Exception:
                no_error = False

            assert no_error, "search_from_query threw an error."
