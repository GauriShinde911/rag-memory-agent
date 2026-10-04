import pytest
from app.tools.calculator import calculator
from app.tools.executor import python_executor
from app.tools.logger import logged, current_turn_tools, global_tool_store


def test_calculator_valid_expressions():
    assert calculator.invoke({"expression": "(16*4) + 3**2"}) == "73"
    assert calculator.invoke({"expression": "sqrt(144)"}) == "12"
    assert calculator.invoke({"expression": "abs(-42)"}) == "42"
    assert calculator.invoke({"expression": "10 / 2"}) == "5"


def test_calculator_blocks_unsafe_code():
    with pytest.raises(Exception):
        calculator.invoke({"expression": "__import__('os').system('echo pwned')"})

    with pytest.raises(Exception):
        calculator.invoke({"expression": "open('/etc/passwd').read()"})

    with pytest.raises(Exception):
        calculator.invoke({"expression": "eval('2+2')"})


def test_python_executor_success():
    res = python_executor.invoke({"code": "print(sum(range(1, 11)))"})
    assert res == "55"


def test_python_executor_timeout():
    with pytest.raises(Exception) as excinfo:
        python_executor.invoke({"code": "import time; time.sleep(6)"})
    assert "timed out" in str(excinfo.value).lower()


def test_request_scoped_tool_logging():
    global_tool_store.clear()

    # Outside turn context
    res = calculator.invoke({"expression": "10 + 5"})
    assert res == "15"
    assert global_tool_store.total_calls == 1

    # Inside turn context
    turn_log = []
    token = current_turn_tools.set(turn_log)
    try:
        calculator.invoke({"expression": "2 * 3"})
        python_executor.invoke({"code": "print('hello')"})

        assert len(turn_log) == 2
        assert turn_log[0]["tool"] == "calculator"
        assert turn_log[0]["success"] is True
        assert turn_log[1]["tool"] == "python_executor"
        assert turn_log[1]["success"] is True
    finally:
        current_turn_tools.reset(token)

    # After turn context, next call should not be in turn_log
    calculator.invoke({"expression": "4 * 4"})
    assert len(turn_log) == 2  # Still 2!
    assert global_tool_store.total_calls == 4
