"""실행 조건의 단일 출처와 Cloud 요청 반영을 확인한다."""

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from evalkit import config, run_cloud, run_local


class ExecutionConditionsTests(unittest.TestCase):
    def test_single_execution_conditions_file_controls_local_and_cloud(self):
        self.assertEqual(config.RUN_SETTINGS_PATH.name, "execution_conditions.json")
        self.assertFalse((config.CONFIG_DIR / "run_settings.json").exists())
        settings = config.load_run_settings()
        self.assertEqual(settings["options"]["num_predict"], 768)
        self.assertEqual(settings["cloud"]["repeats"], 1)
        self.assertTrue(settings["cloud"]["supports_temperature"])
        self.assertEqual(settings["cloud"]["fixed_temperature"], 0)
        self.assertEqual(config.chat_options()["num_predict"], 768)
        self.assertEqual(config.cloud_options()["max_output_tokens"], 768)
        self.assertEqual(config.cloud_options()["temperature"], 0)

    def test_cloud_request_uses_file_conditions(self):
        captured = {}

        class FakeResponses:
            def create(self, **kwargs):
                captured.update(kwargs)
                return SimpleNamespace(status="completed")

        fake_client = SimpleNamespace(responses=FakeResponses())
        with patch.object(run_cloud, "_get_client", return_value=fake_client):
            run_cloud.call_cloud("gpt-5.6-luna", "질문", config.cloud_options(), "unused")
        cloud = config.load_run_settings()["cloud"]
        self.assertEqual(captured["tools"], cloud["tools"])
        self.assertEqual(captured["tool_choice"], cloud["tool_choice"])
        self.assertEqual(captured["reasoning"], cloud["reasoning"])
        self.assertEqual(captured["store"], cloud["store"])
        self.assertEqual(captured["max_output_tokens"], 768)
        self.assertEqual(captured["temperature"], 0)

    def test_temperature_probe_sends_zero_without_writing_experiment_log(self):
        response = SimpleNamespace(
            status="completed",
            temperature=0.0,
            output_text="확인",
        )
        with (
            patch.object(run_cloud, "get_api_key", return_value="unused"),
            patch.object(run_cloud, "call_cloud", return_value=(response, 0.25)) as call,
            patch.object(run_cloud.recorder.RunLog, "append") as append,
        ):
            result = run_cloud.probe_temperature()

        call.assert_called_once_with(
            "gpt-5.6-luna",
            "확인이라고만 답해 주세요.",
            {"temperature": 0, "max_output_tokens": 16},
            "unused",
        )
        append.assert_not_called()
        self.assertTrue(result["accepted"])
        self.assertEqual(result["temperature"], 0.0)

    def test_local_runner_rejects_conditions_it_cannot_apply(self):
        settings = config.load_run_settings()
        settings["local_tools"] = [{"name": "search"}]
        with patch.object(config, "load_run_settings", return_value=settings):
            with self.assertRaises(SystemExit):
                run_local.run_all(dry_run=True, only_model="C", limit=1)


if __name__ == "__main__":
    unittest.main()
