import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
import app
from backend.debate.agent import prompt
from backend.debate.tools import DebateConfig
from test.test_activity import events


class ReplyToneTests(unittest.TestCase):
    def test_tones_change_voice_but_keep_roles_and_evidence_rules(self):
        config = DebateConfig(supported_player=1, opponent_player=2)
        for tone, marker in [('reasoned','REASONED'), ('roast','FULL ROAST')]:
            text = prompt('debate', config, {}, {}, tone)
            self.assertIn('Reply tone: '+marker, text)
            self.assertIn('You defend NBA player 2', text)
            self.assertIn('identical evidence, citation and uncertainty requirements', text)
            self.assertIn('overrides the tone of earlier conversation turns', text)

