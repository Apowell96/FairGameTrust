# FAIRGAME-Trust: Investigating Trust Formation in Large Language Model Agents

FAIRGAME-Trust extends the FAIRGAME framework by introducing trust as an explicit decision-making process within repeated game-theoretic interactions. Rather than assuming agents have access to information about their opponents, agents must decide whether to incur a monitoring cost to observe previous behaviour or act based on trust alone.

The framework enables researchers to investigate how Large Language Model (LLM) agents develop, maintain, and revise trust during repeated interactions. By introducing a voluntary monitoring mechanism, FAIRGAME-Trust captures the trade-off between acquiring information and accepting uncertainty, providing a controlled environment for studying trust dynamics in AI systems.

Agents participate in repeated Prisoner's Dilemma games where they must first decide whether to inspect an opponent's previous actions before selecting their strategy. This allows researchers to analyse trust formation, monitoring behaviour, cooperation patterns, and information-seeking strategies across different models and experimental conditions.

The framework records trust decisions, monitoring costs, strategic choices, and game outcomes, providing a foundation for evaluating how trust emerges and evolves within multi-agent AI systems.

---

## Getting Started

See [QuickStart.md](QuickStart.md) for a complete walkthrough.

### Research Overview

Trust plays a fundamental role in repeated interactions between intelligent agents. In many real-world scenarios, agents must decide whether to verify information at a cost or act based on trust alone. While Large Language Models have been extensively evaluated on cooperation and strategic decision-making tasks, little work has explored how trust develops and evolves during repeated interactions.

FAIRGAME-Trust extends the FAIRGAME framework by introducing an explicit trust decision prior to strategic action selection. Before choosing a game action, agents must decide whether to incur a monitoring cost to inspect an opponent's previous behaviour. This creates a trade-off between acquiring information and preserving resources, allowing trust to emerge as an observable behavioural phenomenon.

The framework provides a controlled environment for studying trust formation, information-seeking behaviour, and cooperation dynamics in Large Language Model agents. By recording monitoring decisions, strategic choices, and game outcomes over repeated interactions, researchers can investigate how different models balance verification and trust under uncertainty.

---

## Trust Decision Process

Each round consists of two stages:

1. **Trust Decision**

   * `LOOK`: Pay a monitoring cost and observe an opponent's previous behaviour.
   * `NO_LOOK`: Avoid the monitoring cost and act without additional information.

2. **Strategic Decision**

   * Select a game action based on available information.

The interaction is repeated over multiple rounds, enabling the analysis of trust formation, trust maintenance, and changes in monitoring behaviour over time.

---

## Collected Metrics

FAIRGAME-Trust records:

* Trust decisions (`LOOK` / `NO_LOOK`)
* Monitoring costs incurred
* Strategic actions
* Individual round scores
* Cumulative scores
* Behavioural changes over time

These metrics can be used to analyse trust development, information-seeking behaviour, cooperation patterns, and decision-making under uncertainty.

## Novel Contribution

The original FAIRGAME framework focuses on evaluating strategic behaviour and behavioural consistency across different experimental conditions.

FAIRGAME-Trust extends this approach by introducing trust as a measurable behavioural variable. Agents are no longer assumed to possess complete information about previous interactions. Instead, they must actively decide whether to acquire information at a cost or act based on trust.

This modification transforms trust from an implicit assumption into an observable and quantifiable behaviour, enabling the study of trust formation and information-seeking strategies in Large Language Model agents.

## Repository Structure

```text
├── api.py                     # Flask API for local interaction and testing
├── main.py                    # Main entry point for running experiments
├── resources/
│   ├── game_configs/          # Experiment configuration files
│   ├── game_templates/        # Prompt templates
│   └── results/               # Experimental outputs
├── src/
│   ├── agents/                # Agent implementations
│   ├── analysis/              # Analysis and visualisation tools
│   ├── games/                 # Prisoner's Dilemma trust experiments
│   ├── llm_connectors/        # LLM provider integrations
│   └── utilities/             # Shared framework utilities
├── unit_tests/                # Automated test suite
└── docs/                      # Project documentation
```

---

## Trust Mechanism

Before making a strategic decision, agents are presented with two options:

* **LOOK** – Pay a monitoring cost to observe an opponent's previous behaviour.
* **NO_LOOK** – Avoid the monitoring cost and act without additional information.

Following this decision, agents select their game strategy. Repeated interactions allow researchers to observe how monitoring behaviour changes over time and whether agents transition from verification-based decision-making to trust-based decision-making.

---

## Requirements

Your project requires the following API keys within the `.env` file:

* `API_KEY_OPENAI`
* `API_KEY_MISTRAL`
* `API_KEY_ANTHROPIC`

Optional S3-compatible storage support:

* `S3_ENDPOINT`
* `S3_KEY`
* `S3_SECRET`
* `BUCKET_NAME`

---

## License

This project is licensed under the Apache License 2.0.

See the `LICENSE` file for details.

See the `LICENSE` file for details.
