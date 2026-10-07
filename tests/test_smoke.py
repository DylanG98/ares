from ares_research.smoke import run_smoke


def test_artifacts_and_injected_error(tmp_path):
    result = run_smoke(tmp_path)
    assert result["pdf_extraction"] == "pass"
    assert result["injected_error_detected"][0]["severity"] == "material"
    assert result["real_agent_runs"].startswith("not_run")
    rerun = run_smoke(tmp_path)
    assert rerun["case_id"] == result["case_id"]
    assert len(list((tmp_path / "dossiers").iterdir())) == 1
