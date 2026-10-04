import pytest
from app.eval.runner import compute_metrics


def test_eval_metrics_computation_on_canned_data():
    """Verify exact calculation of Hit@4, MRR, stale fact rate, tool success and tool selection."""
    # Canned rows simulating test scenarios:
    # 4 probe turns:
    #   Turn 1: Hit (rank 1 -> rr=1.0)
    #   Turn 2: Hit (rank 2 -> rr=0.5)
    #   Turn 3: Miss (rank None -> rr=0.0)
    #   Turn 4: Hit (rank 1 -> rr=1.0)
    # Expected Hit@4 = 3/4 = 0.75
    # Expected MRR = (1.0 + 0.5 + 0.0 + 1.0) / 4 = 2.5 / 4 = 0.625

    # Stale probe:
    #   Turn A: stale_retrieved = False
    #   Turn B: stale_retrieved = True
    # Expected stale rate = 1/2 = 0.5

    # Tool selection:
    #   Turn X: tool_selected = True
    #   Turn Y: tool_selected = False
    # Expected tool selection = 1/2 = 0.5

    # Tool calls:
    #   Call 1: success = True
    #   Call 2: success = True
    #   Call 3: success = False
    # Expected tool success rate = 2/3 = 0.6667

    canned_rows = [
        {"retrieval_hit": True, "rr": 1.0, "stale_retrieved": None, "tool_selected": None},
        {"retrieval_hit": True, "rr": 0.5, "stale_retrieved": None, "tool_selected": None},
        {"retrieval_hit": False, "rr": 0.0, "stale_retrieved": None, "tool_selected": None},
        {"retrieval_hit": True, "rr": 1.0, "stale_retrieved": None, "tool_selected": None},
        {"retrieval_hit": None, "rr": 0.0, "stale_retrieved": False, "tool_selected": None},
        {"retrieval_hit": None, "rr": 0.0, "stale_retrieved": True, "tool_selected": None},
        {"retrieval_hit": None, "rr": 0.0, "stale_retrieved": None, "tool_selected": True},
        {"retrieval_hit": None, "rr": 0.0, "stale_retrieved": None, "tool_selected": False},
    ]

    canned_tools = [
        {"tool": "calculator", "success": True},
        {"tool": "web_search", "success": True},
        {"tool": "python_executor", "success": False},
    ]

    metrics = compute_metrics(canned_rows, canned_tools)

    assert metrics["hit_at_4"] == 0.75
    assert metrics["mrr"] == 0.625
    assert metrics["stale_count"] == 1
    assert metrics["stale_total"] == 2
    assert metrics["stale_fact_rate"] == 0.5
    assert metrics["tool_call_success_rate"] == 0.6667
    assert metrics["tool_selection_accuracy"] == 0.5

    # Verify summary table contains all 5 formatted metrics
    summary = metrics["summary_table"]
    assert len(summary) == 5
    assert "75%" in summary[0]["value"]
    assert "0.62" in summary[1]["value"]
    assert "1/2" in summary[2]["value"]
    assert "67%" in summary[3]["value"]
    assert "50%" in summary[4]["value"]
