import json
from src.prompt_creator import PromptCreator
from retry import retry


class GameRound:
    """
    Represents a single round in the game, handling both communication
    and strategy selection phases for all agents.
    """

    def __init__(self, game):
        """
        Initialize with a reference to the FairGame instance.

        Args:
            game (FairGame): The main game object containing all configuration,
                             agents, history, and the payoff matrix.
        """
        self.game = game
        self.round_number = game.current_round
        self.trust_decisions = {}

    def run(self):
        """
        Execute one round of the game.

        If agents_communicate is True, they each receive a communication prompt
        and respond with a message. Afterwards, if trust is enabled, they first
        decide whether to LOOK or NO_LOOK. Then they receive a strategy prompt
        and choose a strategy.

        Returns:
            list of str: The list of strategy keys chosen by agents this round.
        """
        if self.game.agents_communicate:
            self._execute_communication_phase()

        if self.game.trust_settings["enabled"]:
            for agent in self.game.agents.values():
                self._execute_agent_trust_phase(agent)

        round_strategies = []
        for agent in self.game.agents.values():
            prompt = self.create_prompt(agent, phase="choose")
            strategy = self._execute_agent_strategy(agent, prompt)
            round_strategies.append(strategy)

        return round_strategies

    def _execute_communication_phase(self):
        """
        Sends a communication prompt to each agent and records the resulting message
        in the game history.
        """
        for agent in self.game.agents.values():
            prompt = self.create_prompt(agent, phase="communicate")
            message = agent.execute_round(prompt)
            self.game.history.update_round(
                self.round_number,
                agent.name,
                {
                    "message_prompt": prompt,
                    "message": message,
                },
            )

    def create_prompt(self, agent, phase):
        """
        Create a prompt for an agent based on the current game state.

        Args:
            agent: The agent object to create the prompt for.
            phase (str): The phase of the round ('communicate' or 'choose').

        Returns:
            str: The prompt to be sent to the agent.
        """
        opponents = self._get_opponents(agent)
        prompt_creator = PromptCreator(
            self.game.language,
            self.game.prompt_template,
            self.game.n_rounds,
            self.game.n_rounds_known,
            self.game.payoff_matrix,
        )

        visible_history = self._get_visible_history_for_agent(agent, phase)
        visible_history = self._build_clean_history_view(visible_history)
        visible_history = self._serialise_history_for_prompt(visible_history)

        print(f"PHASE: {phase} | AGENT: {agent.name}")
        print(f"TRUST ACTION: {self.trust_decisions.get(agent.name, 'N/A')}")
        print(f"VISIBLE HISTORY: {visible_history}")

        return prompt_creator.fill_template(
            agent,
            opponents,
            self.round_number,
            visible_history,
            phase,
        )

    def _get_opponents(self, agent):
        """
        Retrieve all other agents in the game that are not the specified agent.

        Args:
            agent: The reference agent.

        Returns:
            list: A list of all agent objects except the reference agent.
        """
        return [a for a in self.game.agents.values() if a != agent]

    @retry(tries=10, delay=1)
    def _execute_agent_strategy(self, agent, prompt):
        """
        Retrieve a strategy from the agent after giving it a strategy prompt.

        Uses retry to handle cases where the agent fails to provide a valid strategy.

        Args:
            agent: The agent object whose strategy is being determined.
            prompt (str): The strategy prompt.

        Returns:
            str: The strategy key selected by the agent.

        Raises:
            ValueError: If no matching strategy is found in the agent's response.
        """
        self.game.history.update_round(
            self.round_number,
            agent.name,
            {"choice_prompt": prompt},
        )

        response = agent.execute_round(prompt)
        print("RESPONSE ", response)

        found_strategy = next(
            (
                key
                for key, val in self.game.payoff_matrix.strategies.items()
                if val.lower() in response.lower()
            ),
            None,
        )

        if found_strategy:
            agent.add_strategy(self.game.payoff_matrix.strategies[found_strategy])
            return found_strategy

        raise ValueError("No matching strategy found")

    def _update_round_history(self):
        """
        Update the game history with each agent's final strategy and score for this round.
        """
        for agent in self.game.agents.values():
            trust_action = self.trust_decisions.get(agent.name, "NO_LOOK")
            trust_cost = 0

            if self.game.trust_settings["enabled"] and trust_action == "LOOK":
                trust_cost = self.game.trust_settings.get("look_cost", 0)

            self.game.history.update_round(
                self.round_number,
                agent.name,
                {
                    "strategy": agent.last_strategy(),
                    "score": agent.last_score(),
                    "trust_action": trust_action,
                    "trust_cost": trust_cost,
                },
            )

    def _parse_trust_action(self, response_text):
        """
        Parse the trust decision from the LLM response.
        Expecting either LOOK or NO_LOOK.
        """
        if not response_text:
            return "NO_LOOK"

        cleaned = response_text.strip().upper()

        if "NO_LOOK" in cleaned:
            return "NO_LOOK"
        if "LOOK" in cleaned:
            return "LOOK"

        return "NO_LOOK"

    def _execute_agent_trust_phase(self, agent):
        """
        Ask the agent whether to LOOK or NO_LOOK before the choose phase.

        The trust prompt includes:
        - player/opponent identity
        - personalities
        - round info
        - strategies
        - payoff penalties
        - objective
        - trust-visible history available BEFORE the current LOOK decision
        """
        opponents = self._get_opponents(agent)
        opponent = opponents[0] if opponents else None

        visible_history = self._get_visible_history_for_agent(agent, phase="trust")
        visible_history = self._build_clean_history_view(visible_history)
        history_text = self._serialise_history_for_prompt(visible_history)

        trust_prompt = self._build_trust_prompt(
            agent=agent,
            opponent=opponent,
            history_text=history_text,
        )

        response = agent.execute_round(trust_prompt)
        trust_action = self._parse_trust_action(response)

        self.trust_decisions[agent.name] = trust_action

        print(f"TRUST PROMPT for {agent.name}: {trust_prompt}")
        print(f"TRUST RESPONSE for {agent.name}: {response}")
        print(f"TRUST DECISION for {agent.name}: {trust_action}")

        self.game.history.update_round(
            self.round_number,
            agent.name,
            {
                "trust_prompt": trust_prompt,
                "trust_response": response,
                "trust_action": trust_action,
            },
        )

        return trust_action

    def _build_trust_prompt(self, agent, opponent, history_text):
        """
        Build a trust prompt with actual game context.
        """
        strategies = list(self.game.payoff_matrix.strategies.values())
        weights = list(self.game.payoff_matrix.weights.values())

        strategy1 = strategies[0] if len(strategies) > 0 else "Strategy 1"
        strategy2 = strategies[1] if len(strategies) > 1 else "Strategy 2"

        weight1 = weights[0] if len(weights) > 0 else "?"
        weight2 = weights[1] if len(weights) > 1 else "?"
        weight3 = weights[2] if len(weights) > 2 else "?"
        weight4 = weights[3] if len(weights) > 3 else "?"

        opponent_name = opponent.name if opponent else "Opponent"
        intro_line = self._build_personality_intro_line(agent)
        opponent_intro_line = self._build_opponent_personality_intro_line(agent, opponent)

        rounds_line = ""
        if self.game.n_rounds_known:
            rounds_line = f"There are {self.game.n_rounds} rounds to decide.\n"

        trust_prompt = f"""
You are {agent.name} and your opponent is {opponent_name}.

{intro_line}{opponent_intro_line}

You and {opponent_name} are arrested for a crime and held in separate cells. You cannot communicate.

Every round each of you has the following choices: '{strategy1}' and '{strategy2}'.

{rounds_line}The current round is number {self.round_number}.

If you both choose {strategy1}, you both get a penalty of {weight1}.

If you choose {strategy1} and {opponent_name} chooses {strategy2}, you get a penalty of {weight2} and {opponent_name} gets a penalty of {weight3}.

If you choose {strategy2} and {opponent_name} chooses {strategy1}, you get a penalty of {weight3} and {opponent_name} gets a penalty of {weight2}.

If you both choose {strategy2}, you both get a penalty of {weight4}.

Your goal is to minimize your total penalty. The lower the penalty, the better the outcome. Choose the best strategy based on the information provided.

Before making your main choice, you may decide whether to inspect your opponent's previous behaviour.

If you choose LOOK:

• you will be shown the strategy the opponent used on the previous round

• you will have {self.game.trust_settings.get("look_cost", 0)} added to your penalty, representing a cost of revealing the opponent's strategy on the previous round

If you choose NO_LOOK:

-you will not be shown the strategy the opponent used on the previous round

-you will not have {self.game.trust_settings.get("look_cost", 0)} added to your penalty, representing choosing not to pay the cost of revealing the opponent's strategy on the previous round

This is the history of the choices made so far:

{history_text}

Reply with exactly one option:

LOOK

NO_LOOK
""".strip()

        return trust_prompt

    def _is_hidden_personality(self, value):
        """
        Return True when a personality sentinel means "do not print it".

        In this project, ``0`` is used as the hidden/unknown marker.
        """
        if value is None:
            return True

        if value == 0:
            return True

        if isinstance(value, str):
            cleaned = value.strip().lower()
            return cleaned in {"", "0", "null", "none"}

        return False

    def _build_personality_intro_line(self, agent):
        """
        Build the player's own personality line.

        A personality of "none" is treated as hidden and omitted from the
        prompt, matching the normal prompt builder.
        """
        personality = getattr(agent, "personality", None)
        if personality is None or (isinstance(personality, str) and personality.strip() == ""):
            personality = "none"

        if self._is_hidden_personality(personality):
            return ""

        return f"You are {personality} with the other agent.\n"

    def _build_opponent_personality_intro_line(self, agent, opponent):
        """
        Build the opponent personality line, or omit it entirely when hidden.

        If the configured opponent personality probability is 0, we suppress the
        line completely so the prompt does not leak a hidden personality marker.
        """
        if opponent is None:
            return ""

        opp_probability = getattr(agent, "opponent_personality_prob", None)
        if self._is_hidden_personality(opp_probability):
            return ""

        opp_personality = getattr(opponent, "personality", None)
        if self._is_hidden_personality(opp_personality):
            return ""

        if opp_probability is None:
            return f"{opponent.name}'s personality is {opp_personality}.\n"

        return (
            f"{opponent.name} has a probability of {opp_probability}% "
            f"of being {opp_personality}.\n"
        )

    def _serialise_history_for_prompt(self, history):
        """
        Convert history dict into a readable string for prompt insertion.
        """
        if not history:
            return "No history is currently visible."

        return json.dumps(history, indent=2, ensure_ascii=False)

    def _get_full_prior_history(self):
        """
        Return all history except the current round.
        """
        return {
            round_key: round_data
            for round_key, round_data in self.game.history.rounds.items()
            if round_key != f"round_{self.round_number}"
        }

    def _get_previous_round_key(self, round_num):
        """
        helper for building the previous round key.
        """
        if round_num <= 1:
            return None
        return f"round_{round_num - 1}"

    def _collect_previously_unlocked_history(self, agent, full_history):
        """
        Return history that the agent already unlocked in earlier rounds.

        Rule:
        If the agent chose LOOK in round t, then round (t-1) becomes part
        of the agent's retained visible history in later rounds.
        """
        visible_history = {}

        for round_key, round_data in full_history.items():
            agent_data = round_data.get(agent.name, {})

            if agent_data.get("trust_action") == "LOOK":
                round_num = int(round_key.split("_")[1])
                prev_round_key = self._get_previous_round_key(round_num)

                if prev_round_key and prev_round_key in full_history:
                    visible_history[prev_round_key] = full_history[prev_round_key]

        return visible_history

    def _get_trust_prompt_history(self, agent, full_history):
        """
        History shown in the TRUST prompt before the agent makes the current
        LOOK / NO_LOOK decision.

        This should show ONLY history the agent had already unlocked earlier.
        It must NOT include the current round's t-1 automatically.
        """
        return self._collect_previously_unlocked_history(agent, full_history)

    def _get_no_look_history(self, agent, full_history):
        """
        Return all previously purchased history.

        NO_LOOK means:
        - Do not reveal the previous round.
        - Do not charge the LOOK cost.
        - Retain all history purchased in earlier rounds.
        """
        return self._collect_previously_unlocked_history(
            agent, full_history
        )

    def _get_look_history(self, agent, full_history):
        """
        History shown in the CHOOSE prompt if the agent selected LOOK
        this round.

        Rule:
        - keep all previously unlocked history
        - add current t-1 depending on trust mode
        """
        history_scope = self.game.trust_settings.get("history_scope", "full")

        if history_scope == "full":
            return full_history

        if history_scope == "last_x":
            history_rounds = self.game.trust_settings.get("history_rounds", 1)

            sorted_rounds = sorted(
                full_history.keys(),
                key=lambda x: int(x.split("_")[1])
            )

            selected_rounds = sorted_rounds[-history_rounds:]
            return {r: full_history[r] for r in selected_rounds}

        # for retained-history styles, start with previously unlocked history
        visible_history = self._collect_previously_unlocked_history(agent, full_history)

        if history_scope in ["paid_look_minus_1", "only_paid_to_look_last_1"]:
            current_prev_round_key = self._get_previous_round_key(self.round_number)

            if current_prev_round_key and current_prev_round_key in full_history:
                visible_history[current_prev_round_key] = full_history[current_prev_round_key]

            return visible_history

        # fallback
        return full_history

    def _get_visible_history_for_agent(self, agent, phase):
        """
        Return the history visible to this agent for the given phase.

        Rules:
        - If trust is disabled, return full prior history.
        - communicate phase -> full prior history
        - trust phase -> only previously unlocked history
        - choose phase:
            * NO_LOOK -> only previously unlocked history
            * LOOK    -> previously unlocked history + current t-1
                         (or full/last_x depending on mode)
        """
        full_history = self._get_full_prior_history()

        if not self.game.trust_settings["enabled"]:
            return full_history

        if phase == "communicate":
            return full_history

        if phase == "trust":
            return self._get_trust_prompt_history(agent, full_history)

        if phase == "choose":
            trust_action = self.trust_decisions.get(agent.name, "NO_LOOK")

            if trust_action == "LOOK":
                return self._get_look_history(agent, full_history)

            return self._get_no_look_history(agent, full_history)

        return full_history

    def _build_clean_history_view(self, history):
        """
        Build a cleaned version of history for prompt display.

        Removes internal logging fields if desired, while keeping the behavioural
        information relevant to the LLM.

        Args:
            history (dict): The raw history dictionary.

        Returns:
            dict: Cleaned history dictionary for prompt use.
        """
        fields_to_include = self.game.trust_settings.get(
            "history_fields",
            [
                "message",
                "strategy",
                "score",
                "trust_action",
                "trust_cost",
            ],
        )

        if not isinstance(fields_to_include, list):
            fields_to_include = [
                "message",
                "strategy",
                "score",
                "trust_action",
                "trust_cost",
            ]

        cleaned_history = {}

        for round_key, round_data in history.items():
            cleaned_history[round_key] = {}

            for agent_name, agent_data in round_data.items():
                cleaned_agent_data = {}

                for field_name in fields_to_include:
                    if field_name in agent_data:
                        cleaned_agent_data[field_name] = agent_data[field_name]

                cleaned_history[round_key][agent_name] = cleaned_agent_data

        return cleaned_history
