import unittest
import os
from types import SimpleNamespace
from src.fairgame_factory import FairGameFactory
from src.io_managers.io_manager import IoManager
from src.results_processing.results_processor import ResultsProcessor
from src.game_round import GameRound


### cretaing a fake game and fake agents to test the trust phase of the GameRound class without needing to set up the full game environment.
class FakeHistory:
    def __init__(self):
        self.rounds = {}
        self.updates = []

    def update_round(self, round_number, agent_name, data):
        self.updates.append((round_number, agent_name, data))

        if round_number not in self.rounds:
            self.rounds[round_number] = {}
        if agent_name not in self.rounds[round_number]:
            self.rounds[round_number][agent_name] = {}

        self.rounds[round_number][agent_name].update(data)


class FakeAgent:
    def __init__(self, name, responses=None):
        self.name = name
        self.responses = responses or []
        self.response_index = 0
        self.strategy_history = []
        self.score_history = []

    def execute_round(self, prompt):
        response = self.responses[self.response_index]
        self.response_index += 1
        return response

    def add_strategy(self, strategy):
        self.strategy_history.append(strategy)

    def last_strategy(self):
        return self.strategy_history[-1] if self.strategy_history else None

    def last_score(self):
        return self.score_history[-1] if self.score_history else None


class FakePayoffMatrix:
    def __init__(self):
        self.strategies = {
            "C": "Cooperate",
            "D": "Defect"
        }


### The test class for the GameRound trust phase
class FakeGame:
    def __init__(self, trust_enabled):
        self.current_round = 1
        self.agents_communicate = False
        self.language = "English"
        self.prompt_template = "dummy template"
        self.n_rounds = 5
        self.n_rounds_known = True
        self.payoff_matrix = FakePayoffMatrix()
        self.history = FakeHistory()
        self.trust_settings = {
            "enabled": trust_enabled,
            "actions": ["LOOK", "NO_LOOK"],
            "look_cost": 1,
            "history_scope": "full",
            "history_rounds": 1
        }

        self.agents = {
            "AgentA": FakeAgent("AgentA", responses=["LOOK", "Cooperate"]),
            "AgentB": FakeAgent("AgentB", responses=["NO_LOOK", "Defect"])
        }


### the actual test class for the GameRound trust phase
class TestGameRoundTrust(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script_path = os.path.abspath(__file__)
        script_dir = os.path.dirname(script_path)
        cls.RESOURCES_PATH = script_dir

    def setUp(self):
        self.io_manager = IoManager(root_path=self.RESOURCES_PATH)
        self.game_factory = FairGameFactory()
        self.game_factory.set_io_manager(self.io_manager)
        self.processor = ResultsProcessor()
    
    
    def test_factory_create_games_with_trust_config(self):
        config = self.game_factory.load_config("Prisoner_dilemma_trust.json")
        self.game_factory.create_games(config)

        self.assertGreater(len(self.game_factory.games), 0)

        first_game = self.game_factory.games[0]
        self.assertTrue(first_game.trust_settings["enabled"])
        self.assertEqual(first_game.trust_settings["actions"], ["LOOK", "NO_LOOK"])
        self.assertEqual(first_game.trust_settings["look_cost"], 1)
        self.assertEqual(first_game.trust_settings["history_scope"], "full")
        self.assertEqual(first_game.trust_settings["history_rounds"], 1)
    
    def test_trust_phase_enabled_records_decisions(self):
        game = FakeGame(trust_enabled=True)
        round_obj = GameRound(game)
        round_obj.create_prompt = lambda agent, phase: "dummy choose prompt"

        round_obj.run()

        self.assertEqual(round_obj.trust_decisions["AgentA"], "LOOK")
        self.assertEqual(round_obj.trust_decisions["AgentB"], "NO_LOOK")

        agent_a_history = game.history.rounds[1]["AgentA"]
        agent_b_history = game.history.rounds[1]["AgentB"]

        self.assertEqual(agent_a_history["trust_action"], "LOOK")
        self.assertEqual(agent_b_history["trust_action"], "NO_LOOK")

    def test_trust_phase_disabled_does_not_record_decisions(self):
        game = FakeGame(trust_enabled=False)
        game.agents = {
            "AgentA": FakeAgent("AgentA", responses=["Cooperate"]),
            "AgentB": FakeAgent("AgentB", responses=["Defect"])
        }

        round_obj = GameRound(game)
        round_obj.create_prompt = lambda agent, phase: "dummy choose prompt"

        round_obj.run()

        self.assertEqual(round_obj.trust_decisions, {})

        agent_a_history = game.history.rounds.get(1, {}).get("AgentA", {})
        agent_b_history = game.history.rounds.get(1, {}).get("AgentB", {})

        self.assertNotIn("trust_action", agent_a_history)
        self.assertNotIn("trust_action", agent_b_history)

    def test_parse_trust_action_defaults_to_no_look(self):
        game = FakeGame(trust_enabled=True)
        round_obj = GameRound(game)

        self.assertEqual(round_obj._parse_trust_action("LOOK"), "LOOK")
        self.assertEqual(round_obj._parse_trust_action("NO_LOOK"), "NO_LOOK")
        self.assertEqual(round_obj._parse_trust_action("something else"), "NO_LOOK")
        self.assertEqual(round_obj._parse_trust_action(""), "NO_LOOK")

    def test_trust_prompt_hides_none_personality(self):
        game = FakeGame(trust_enabled=True)
        round_obj = GameRound(game)

        agent = SimpleNamespace(name="AgentA", personality="none", opponent_personality_prob=80)
        opponent = SimpleNamespace(name="AgentB", personality="cooperative")

        prompt = round_obj._build_trust_prompt(agent, opponent, history_text="No history")

        self.assertNotIn("You are none.", prompt)
        self.assertIn("You are AgentA and your opponent is AgentB.", prompt)
        
    def test_trust_config_runs_full_game_and_records_trust_fields(self):
        """
        End-to-end test:
        - load the trust config
        - create games through the factory
        - run the framework
        - inspect the first game
        - confirm 5 rounds were played
        - confirm trust fields exist in round history
        """
        config = self.game_factory.load_config("Prisoner_dilemma_trust.json")
        self.game_factory.create_games(config)
        self.assertGreater(len(self.game_factory.games), 0)

        self.game_factory.run_games()

        first_game = self.game_factory.games[0]

        # Check the game really ran 5 rounds
        self.assertEqual(len(first_game.history.rounds), 5)
        self.assertEqual(len(first_game.choices_made), 5)

        # Check trust settings are present on the game
        self.assertTrue(first_game.trust_settings["enabled"])
        self.assertEqual(first_game.trust_settings["look_cost"], 1)

        # Check each round contains trust + normal strategy fields for each agent
        for round_number, round_data in first_game.history.rounds.items():
            self.assertEqual(len(round_data), 2)  # two agents

            for agent_name, agent_data in round_data.items():
                self.assertIn("trust_action", agent_data)
                self.assertIn(agent_data["trust_action"], ["LOOK", "NO_LOOK"])

                self.assertIn("trust_cost", agent_data)
                self.assertIsInstance(agent_data["trust_cost"], int)

                self.assertIn("strategy", agent_data)
                self.assertIsNotNone(agent_data["strategy"])

                self.assertIn("score", agent_data)
                self.assertIsNotNone(agent_data["score"])
    
    
    def test_trust_results_are_in_processed_dataframe(self):
        """
        End-to-end test:
        - run the trust game
        - process results into a DataFrame
        - confirm trust columns are present
        - confirm the trust data is populated
        """
        results = self.game_factory.load_config_create_and_run_games("Prisoner_dilemma_trust.json")
        results_df = self.processor.process(results)

        self.assertGreater(len(results_df), 0)

        # Check trust-related columns exist
        self.assertIn("agent1_trust_actions", results_df.columns)
        self.assertIn("agent1_trust_costs", results_df.columns)
        self.assertIn("agent1_total_trust_cost", results_df.columns)
        self.assertIn("agent1_look_count", results_df.columns)
        self.assertIn("agent1_no_look_count", results_df.columns)
        self.assertIn("agent1_look_ratio", results_df.columns)

        self.assertIn("agent2_trust_actions", results_df.columns)
        self.assertIn("agent2_trust_costs", results_df.columns)
        self.assertIn("agent2_total_trust_cost", results_df.columns)
        self.assertIn("agent2_look_count", results_df.columns)
        self.assertIn("agent2_no_look_count", results_df.columns)
        self.assertIn("agent2_look_ratio", results_df.columns)

        first_row = results_df.iloc[0]

        # Check trust action lists are present and cover all 5 rounds
        self.assertEqual(len(first_row["agent1_trust_actions"]), 5)
        self.assertEqual(len(first_row["agent2_trust_actions"]), 5)

        self.assertEqual(len(first_row["agent1_trust_costs"]), 5)
        self.assertEqual(len(first_row["agent2_trust_costs"]), 5)

        # Check only LOOK / NO_LOOK values appear and ignore None values (in case of any missing data)
        agent1_actions = [action for action in first_row["agent1_trust_actions"] if action is not None]
        agent2_actions = [action for action in first_row["agent2_trust_actions"] if action is not None]

        self.assertGreater(len(agent1_actions), 0)
        self.assertGreater(len(agent2_actions), 0)

        for action in agent1_actions:
            self.assertIn(action, ["LOOK", "NO_LOOK"])

        for action in agent2_actions:
            self.assertIn(action, ["LOOK", "NO_LOOK"])
            
        # Check totals are numeric
        self.assertGreaterEqual(first_row["agent1_total_trust_cost"], 0)
        self.assertGreaterEqual(first_row["agent2_total_trust_cost"], 0)

        self.assertGreaterEqual(first_row["agent1_look_count"], 0)
        self.assertGreaterEqual(first_row["agent1_no_look_count"], 0)
        self.assertGreaterEqual(first_row["agent2_look_count"], 0)
        self.assertGreaterEqual(first_row["agent2_no_look_count"], 0)

        self.assertGreaterEqual(first_row["agent1_look_ratio"], 0)
        self.assertLessEqual(first_row["agent1_look_ratio"], 1)
        self.assertGreaterEqual(first_row["agent2_look_ratio"], 0)
        self.assertLessEqual(first_row["agent2_look_ratio"], 1)

if __name__ == "__main__":
    unittest.main()
