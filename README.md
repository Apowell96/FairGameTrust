# FAIRGAME: a Framework for AI Agents Bias Recognition using Game Theory

FAIRGAME is a framework designed to simulate a diverse range of scenarios, from classic Game Theory models to real-world use cases, while identifying biases related to language, cultural traits, or gaming strategies. It enables comprehensive simulations involving AI agents with varying identities and personalities, quantifying the outcomes of their interactions and aligning them with desired results through game-theoretic principles. This makes FAIRGAME a versatile tool for testing and evaluating chatbot behavior, AI decision-making, and agent interactions in various contexts.

## Research Overview

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

## Code Repository Structure

The following tree shows the list of the repository's sections and their main contents:

```
└── apy.py             # Flask API for local testing and interaction
└── Dockerfile         # Containerization setup
└── main.py            # Entry point script to run the core application. It also provides an example of the input
└── resources/         # Static resources (JSON config files and templates)
└── results/           # Stores output results, logs, or evaluation metrics
└── src/               # Core source code: models, logic, and processing pipelines
└── unit_tests/        # Unit tests to verify the functionality of components
```

## Requirements

Your project needs the following keys in the .env file (an example is provided in .env.example):

- API_KEY_OPENAI to properly connect to OpenAI's API and models.
- API_KEY_MISTRAL to properly connect to Mistral's API and models.
- API_KEY_ANTHROPIC to properly connect to Anthropic's API and models.

Optionally, to enable saving results to an S3-compatible storage, you can also include:
- S3_ENDPOINT
- S3_KEY
- S3_SECRET
- BUCKET_NAME

## Governance and Contribution

The development and community management of this project follows the governance rules described in the [GOVERNANCE.md](GOVERNANCE.md) document.

At SOM Research Lab we are dedicated to creating and maintaining welcoming, inclusive, safe, and harassment-free development spaces. Anyone participating will be subject to and agrees to sign on to our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

This project is developed by the AI Readiness and Assessment (AIRA) group at Luxembourg Institute of Science and Technology (LIST) and part of the AI Sandbox (https://ai-sandbox.list.lu/). 
We are open to contributions from the community. Any comment is more than welcome! If you are interested in contributing to this project, please read the [CONTRIBUTING.md](CONTRIBUTING.md) file.