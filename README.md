# FAIRGAME-Trust: Investigating Trust Formation in Large Language Model Agents

FAIRGAME-Trust extends the FAIRGAME framework by introducing trust as an explicit decision-making process within repeated game-theoretic interactions. Rather than assuming agents have access to information about their opponents, agents must decide whether to incur a monitoring cost to observe previous behaviour or act based on trust alone.

The framework enables researchers to investigate how Large Language Model (LLM) agents develop, maintain, and revise trust during repeated interactions. By introducing a voluntary monitoring mechanism, FAIRGAME-Trust captures the trade-off between acquiring information and accepting uncertainty, providing a controlled environment for studying trust dynamics in AI systems.

Agents participate in repeated Prisoner's Dilemma games where they must first decide whether to inspect an opponent's previous actions before selecting their strategy. This allows researchers to analyse trust formation, monitoring behaviour, cooperation patterns, and information-seeking strategies across different models and experimental conditions.

The framework records trust decisions, monitoring costs, strategic choices, and game outcomes, providing a foundation for evaluating how trust emerges and evolves within multi-agent AI systems.

---

## Research Objectives

FAIRGAME-Trust has been designed to support research into:

* Trust formation in LLM agents
* Information-seeking behaviour under uncertainty
* Monitoring and verification strategies
* Cost-benefit trade-offs in decision-making
* Cooperation and trust dynamics in repeated interactions
* Behavioural differences across LLM providers
* Multi-agent AI systems and emergent behaviour

---

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
