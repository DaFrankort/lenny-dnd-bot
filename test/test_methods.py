import time

import pytest

from methods import call_with_timeout


class TestMethods:
    @pytest.mark.parametrize(
        "sleep, timeout, success",
        [
            (1.0, 0.5, False),
            (0.5, 1.0, True),
            (1.5, 1.0, False),
        ],
    )
    def test_call_with_timeout(self, sleep: int, timeout: int, success: bool) -> None:
        def timeout_func(sleep: int) -> int:
            time.sleep(sleep)
            return True

        result = call_with_timeout(timeout=timeout, func=timeout_func, args=[sleep])

        if success:
            assert result == True
        else:
            assert result is None
