"""Pure-logic tests for the Stream Deck controller — no hardware,
no socketio, no PIL required (BUTTONS/key_visuals are import-safe)."""

import unittest

from main import BUTTONS, key_visuals, press_payload


class LayoutTest(unittest.TestCase):
    def test_fifteen_keys(self):
        self.assertEqual(len(BUTTONS), 15)

    def test_historical_positions_unchanged(self):
        # muscle memory: keys 0-6 keep their payloads
        payloads = [press_payload(i) for i in range(7)]
        self.assertEqual(payloads[0], {"home_score_change": 1})
        self.assertEqual(payloads[1], {"away_score_change": 1})
        self.assertEqual(payloads[2], {"start_timer": True})
        self.assertEqual(payloads[3], {"stop_timer": True})
        self.assertEqual(payloads[4], {"timeout_home": True})
        self.assertEqual(payloads[5], {"timeout_away": True})
        self.assertEqual(payloads[6], {"side_change": True})

    def test_new_actions_mapped(self):
        used = [press_payload(i) for i in range(15)]
        for action in ({"referee_whistle": True}, {"technical_timeout": True},
                       {"next_period": True}, {"home_score_change": -1},
                       {"away_score_change": -1}, {"passive_home": True},
                       {"passive_away": True}, {"passive_pass": True}):
            self.assertIn(action, used)

    def test_every_key_has_label_and_action(self):
        for btn in BUTTONS:
            self.assertTrue(btn["label"])
            self.assertIsInstance(btn["press"], dict)


class VisualsTest(unittest.TestCase):
    def test_colors_from_state(self):
        s = {"home_color": "#0af", "away_color": "#f33"}
        self.assertEqual(key_visuals(s, 0), ("Home +1", "#0af", False))
        self.assertEqual(key_visuals(s, 1), ("Away +1", "#f33", False))

    def test_missing_state_keys_do_not_raise(self):
        # scorebug payload may evolve — no KeyErrors (#4)
        label, color, dot = key_visuals({}, 7)
        self.assertEqual((label, color, dot), ("Whistle\n(2:8)", None, False))

    def test_dots(self):
        running = {"running": True, "passive_team": "away"}
        self.assertTrue(key_visuals(running, 3)[2])   # stop: running
        self.assertFalse(key_visuals(running, 2)[2])  # start: no dot
        self.assertTrue(key_visuals(running, 13)[2])  # passive away armed
        self.assertFalse(key_visuals(running, 12)[2])  # passive home off
        self.assertTrue(key_visuals(running, 14)[2])   # pass -1: any passive

    def test_signature_is_hashable(self):
        {key_visuals({"running": True}, i) for i in range(15)}


if __name__ == "__main__":
    unittest.main()
