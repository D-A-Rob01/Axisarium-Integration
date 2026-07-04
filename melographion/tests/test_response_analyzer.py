from melographion.response_analyzer import analyze_response


def test_response_analysis_marks_inferred_fields():
    result = analyze_response(
        "I remember a mirror in my childhood house. It landed in my chest with grief."
    )

    assert "grief" in result["emotional_tags"]
    assert "chest" in result["body_response"]
    assert result["memories"]
    assert "mirror" in result["extracted_symbols"]
