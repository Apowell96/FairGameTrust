"""Study datasets and labels used in supplementary statistical tables."""

from dataclasses import dataclass
from pathlib import Path

COSTS = (0.0, 0.25, 0.5, 1.0)
ROUNDS = tuple(range(1, 11))
GAMES_PER_CELL = 10
MODELS = ("claude-sonnet-4-6", "gpt-4o", "mistral-small-2603")


@dataclass(frozen=True)
class Dataset:
    key: str
    label: str
    directory: str
    language_codes: tuple
    horizon_known: bool

    def model_label(self, model):
        labels = {"claude-sonnet-4-6": "Claude Sonnet 4.6", "gpt-4o": "GPT-4o",
                  "mistral-small-2603": "Mistral Small 2603" if self.key == "chinese" else "Mistral Small 4"}
        return labels[model]

    def input_path(self, data_root):
        return Path(data_root)/self.directory


DATASETS = {
    "english_horizon_known": Dataset("english_horizon_known", "English - horizon known",
        "English/horizon_known", ("en",), True),
    "english_horizon_unknown": Dataset("english_horizon_unknown", "English - horizon unknown",
        "English/horizon_unknown", ("en",), False),
    "french": Dataset("french", "French", "French", ("fr",), True),
    "chinese": Dataset("chinese", "Chinese", "Chinese", ("cn", "zh", "zh-cn"), True),
}
