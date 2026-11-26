"""Read game CSVs and validate decisions, metadata, payoffs and monitoring costs."""

import ast
from dataclasses import dataclass
from pathlib import Path
import re
import unicodedata

import numpy as np
import pandas as pd

from .io import sha256
from .settings import COSTS, GAMES_PER_CELL, MODELS, ROUNDS

PAYOFFS = {
    ("OptionA", "OptionA"): (6.0, 6.0),
    ("OptionA", "OptionB"): (0.0, 10.0),
    ("OptionB", "OptionA"): (10.0, 0.0),
    ("OptionB", "OptionB"): (2.0, 2.0),
}


@dataclass
class LoadedData:
    rounds: pd.DataFrame
    input_hashes: dict


def parse_bool(value):
    token = str(value).strip().casefold()
    if token not in ("true", "false"):
        raise ValueError(f"Expected True or False, got {value!r}")
    return token == "true"


def parse_list(value, name):
    try:
        values = ast.literal_eval(str(value))
    except (ValueError, SyntaxError) as error:
        raise ValueError(f"Invalid list in {name}") from error
    if not isinstance(values, list) or len(values) != len(ROUNDS):
        raise ValueError(f"{name} must contain exactly ten entries")
    return values


def normalize_strategy(value):
    token = re.sub(r"\s+", "", unicodedata.normalize("NFKC", str(value))).casefold()
    options = {"optiona": "OptionA", "optionb": "OptionB", "选项a": "OptionA", "选项b": "OptionB"}
    if token not in options:
        raise ValueError(f"Unknown strategy {value!r}")
    return options[token]


def require_close(actual, expected, name):
    actual = np.asarray(actual, dtype=float)
    if not np.isfinite(actual).all() or not np.allclose(actual, expected, rtol=0, atol=1e-10):
        raise ValueError(f"{name} disagrees with the recorded game decisions")


def decode_game(row, cost, iteration, dataset, source):
    """Decode one independent game into twenty agent/round observations."""
    if str(row["language"]).strip().casefold() not in dataset.language_codes:
        raise ValueError(f"Unexpected language in {source}")
    if parse_bool(row["n_rounds_is_known"]) != dataset.horizon_known:
        raise ValueError(f"Unexpected horizon metadata in {source}")
    for field in ("played_rounds", "max_rounds"):
        require_close(float(row[field]), 10, field)
    if parse_bool(row["agents_communicate"]):
        raise ValueError("This analysis requires games without communication")
    model = str(row["agent1_llm"]).strip()
    if model not in MODELS or str(row["agent2_llm"]).strip() != model:
        raise ValueError(f"Unsupported model pairing in {source}")
    if "look_cost" in row:
        require_close(float(row["look_cost"]), cost, "monitoring cost")
    fields = {}
    for agent in (1, 2):
        if str(row[f"agent{agent}_personality"]).strip().casefold() != "none":
            raise ValueError("This analysis requires neutral personalities")
        require_close(float(row[f"agent{agent}_knows_opponent_with_prob"]), 0, "baseline visibility")
        for field in ("strategies", "scores", "trust_actions", "trust_costs"):
            name = f"agent{agent}_{field}"
            fields[name] = parse_list(row[name], name)
        actions = [str(x).strip().upper() for x in fields[f"agent{agent}_trust_actions"]]
        if not set(actions).issubset({"LOOK", "NO_LOOK"}):
            raise ValueError(f"Invalid LOOK action in {source}")
        fields[f"agent{agent}_trust_actions"] = actions
        for suffix, expected in {
            "total_trust_cost": np.asarray(fields[f"agent{agent}_trust_costs"], dtype=float).sum(),
            "look_count": actions.count("LOOK"), "no_look_count": actions.count("NO_LOOK"),
            "look_ratio": actions.count("LOOK")/10,
        }.items():
            if f"agent{agent}_{suffix}" in row:
                require_close(float(row[f"agent{agent}_{suffix}"]), expected, suffix)
    game_id = f"{dataset.key}/{cost:g}/{model}/{iteration}"
    records = []
    for index, round_number in enumerate(ROUNDS):
        strategies = tuple(normalize_strategy(fields[f"agent{a}_strategies"][index]) for a in (1, 2))
        for agent, payoff in zip((1, 2), PAYOFFS[strategies]):
            looked = fields[f"agent{agent}_trust_actions"][index] == "LOOK"
            charge = float(fields[f"agent{agent}_trust_costs"][index])
            penalty = float(fields[f"agent{agent}_scores"][index])
            require_close(charge, cost if looked else 0, "round monitoring charge")
            require_close(penalty, payoff+charge, "round recorded penalty")
            records.append(dict(dataset=dataset.key, game_id=game_id, model=model, cost=cost,
                iteration=iteration, agent=f"agent{agent}", round=round_number,
                cooperated=int(strategies[agent-1] == "OptionB"), looked=int(looked),
                recorded_penalty=penalty, monitoring_charge=charge, source_file=source))
    return records


def load_dataset(data_root, dataset):
    """Load the four included costs; source game files are never modified."""
    data_root = Path(data_root).resolve()
    directory = dataset.input_path(data_root)
    if not directory.is_dir():
        raise ValueError(f"Dataset folder does not exist: {directory}")
    for folder in directory.iterdir():
        if folder.is_dir():
            try:
                value = float(folder.name)
            except ValueError:
                continue
            if not np.isfinite(value) or value not in (*COSTS, .75):
                raise ValueError(f"Unexpected monitoring-cost folder {folder.name}")
    records, hashes, seen = [], {}, set()
    for cost in COSTS:
        paths = sorted((directory/f"{cost:g}").glob("*/results_Prisoner_dilemma_trust_*.csv"))
        if not paths:
            raise ValueError(f"No game CSVs for {dataset.label}, monitoring cost {cost:g}")
        for path in paths:
            match = re.fullmatch(r"results_Prisoner_dilemma_trust_(\d+)\.csv", path.name)
            if match is None:
                raise ValueError(f"Invalid game filename {path.name}")
            frame = pd.read_csv(path)
            if len(frame) != 1:
                raise ValueError(f"Expected one game in {path}")
            source = path.relative_to(data_root).as_posix()
            try:
                decoded = decode_game(frame.iloc[0].to_dict(), cost, int(match.group(1)), dataset, source)
            except KeyError as error:
                raise ValueError(f"Missing column {error} in {source}") from error
            game_id = decoded[0]["game_id"]
            if game_id in seen:
                raise ValueError(f"Duplicate independent game {game_id}")
            seen.add(game_id)
            records.extend(decoded)
            hashes[source] = sha256(path)
    rounds = pd.DataFrame(records).sort_values(["cost", "model", "iteration", "agent", "round"]).reset_index(drop=True)
    counts = rounds.groupby(["model", "cost"]).game_id.nunique()
    expected = {(model, cost) for model in MODELS for cost in COSTS}
    if set(counts.index) != expected or not counts.eq(GAMES_PER_CELL).all():
        raise ValueError("Expected ten independent games per model and monitoring cost")
    if len(rounds) != 2400 or rounds.duplicated(["game_id", "agent", "round"]).any():
        raise ValueError("Expected 120 complete, distinct two-agent ten-round games")
    return LoadedData(rounds, hashes)
