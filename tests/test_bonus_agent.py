"""Tests offline cho phần bonus của agent: giới hạn retry 429, rút gọn dữ liệu nhiễu, tách prompt."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
from agent import run_agent, SYSTEM_PROMPT, BONUS_EXTRA_RULES, MAX_RATE_LIMITED_ATTEMPTS
from bonus.tools import BonusTools
from status_tools import StatusTools
from test_lab import FakeProvider, tool_call, final


class BonusAgentExtrasTests(unittest.TestCase):
    def test_main_prompt_unchanged_for_status_tools(self):
        fake = FakeProvider([final()])
        run_agent('x', fake, StatusTools())
        self.assertEqual(fake.histories[0][0]['content'], SYSTEM_PROMPT)

    def test_bonus_prompt_gets_extra_rules(self):
        fake = FakeProvider([final()])
        run_agent('x', fake, BonusTools())
        system = fake.histories[0][0]['content']
        self.assertIn('DigitalOcean', system)
        self.assertTrue(system.endswith(BONUS_EXTRA_RULES))

    def test_persistent_429_is_capped(self):
        responses = [tool_call(f'v{i}', 'get_vercel_status', '{}') for i in range(5)] + [final('Vercel chưa biết')]
        fake = FakeProvider(responses)
        result = run_agent('x', fake, BonusTools(scenario='rate_limit_always'), max_steps=8)
        self.assertEqual(result['status'], 'completed')
        executed = [t for t in result['trace'] if t['event'] == 'tool' and t['name'] == 'get_vercel_status']
        blocked = [t for t in result['trace'] if t['event'] == 'tool_blocked']
        self.assertEqual(len(executed), MAX_RATE_LIMITED_ATTEMPTS)
        self.assertEqual(len(blocked), 5 - MAX_RATE_LIMITED_ATTEMPTS)
        # Call bị chặn vẫn nhận tool result gắn đúng ID.
        last_tool = fake.histories[4][-1]
        self.assertEqual(last_tool['tool_call_id'], 'v3')
        self.assertEqual(json.loads(last_tool['content'])['error'], 'RETRY_LIMIT_REACHED')

    def test_transient_429_still_retries(self):
        fake = FakeProvider([tool_call('a', 'get_vercel_status', '{}'), tool_call('b', 'get_vercel_status', '{}'), final()])
        result = run_agent('x', fake, BonusTools(scenario='rate_limit_once'), max_steps=5)
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(json.loads(fake.histories[2][-1]['content'])['provider'], 'vercel')

    def test_noise_is_compacted_before_model(self):
        fake = FakeProvider([tool_call('a', 'get_vercel_status', '{}'), final()])
        run_agent('x', fake, BonusTools(scenario='noisy'))
        sent = json.loads(fake.histories[1][-1]['content'])
        self.assertEqual(len(sent['distractors']), 3)
        self.assertEqual(sent['distractors_omitted_by_agent'], 157)
        self.assertEqual(sent['provider'], 'vercel')

    def test_fabricated_url_gets_one_revision(self):
        fake = FakeProvider([tool_call('a', 'get_vercel_status', '{}'),
                             final('Vercel: xem https://www.vercelstatus.com (giả định).'),
                             final('Vercel: xem https://www.vercel-status.com.')])
        result = run_agent('x', fake, BonusTools(), max_steps=5)
        self.assertEqual(result['status'], 'completed')
        events = [t for t in result['trace'] if t['event'] == 'validation_unverified_url']
        self.assertEqual(events[0]['urls'], ['https://www.vercelstatus.com'])
        self.assertNotIn('vercelstatus.com', result['answer'])

    def test_known_urls_pass_and_check_runs_once(self):
        # URL có trong tool result: không bị nhắc.
        fake = FakeProvider([tool_call('a', 'get_npm_status', '{}'), final('Nguồn: https://status.npmjs.org/')])
        result = run_agent('x', fake, BonusTools())
        self.assertFalse(any(t['event'].startswith('validation_unverified') for t in result['trace']))
        # Model giữ URL lạ sau khi bị nhắc: không lặp vô hạn, ghi trace persisted.
        fake = FakeProvider([final('https://fake.example/x'), final('https://fake.example/x')])
        result = run_agent('x', fake, BonusTools(), max_steps=5)
        self.assertEqual(result['status'], 'completed')
        self.assertTrue(any(t['event'] == 'validation_unverified_url_persisted' for t in result['trace']))

    def test_url_check_not_applied_to_main_tools(self):
        fake = FakeProvider([final('Xem https://fake.example/x')])
        result = run_agent('x', fake, StatusTools())
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(len(fake.histories), 1)


if __name__ == '__main__':
    unittest.main()
