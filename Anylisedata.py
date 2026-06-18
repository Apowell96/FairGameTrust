import pandas as pd
import ast  # safer than eval

# 1. load your file
df = pd.read_csv("resources/results/results_prisoner_dilemma_round_known_conventional.csv")

# 2. helper to turn "['OptionB', 'OptionA']" into a real list
def to_list(x):
    if pd.isna(x):
        return []
    try:
        return ast.literal_eval(x)
    except (ValueError, SyntaxError):
        return []

# 3. helper to get mean score from a string-list like "[10, 6, 0]"
def list_mean(x):
    lst = to_list(x)
    if not lst:
        return None
    # sometimes it can be a single int, but literal_eval turns it into int
    if isinstance(lst, (int, float)):
        return float(lst)
    return sum(lst) / len(lst)

# create per-row numeric columns
df["agent1_mean_score"] = df["agent1_scores"].apply(list_mean)
df["agent2_mean_score"] = df["agent2_scores"].apply(list_mean)

print("Average penalties by agent personality (agent1):")
print(df.groupby("agent1_personality")["agent1_mean_score"].mean())

print("\nAverage penalties by agent personality (agent2):")
print(df.groupby("agent2_personality")["agent2_mean_score"].mean())

# cooperation rates
df["agent1_strategies_list"] = df["agent1_strategies"].apply(to_list)
df["agent2_strategies_list"] = df["agent2_strategies"].apply(to_list)

def coop_rate(strats):
    if not strats:
        return 0
    return strats.count("OptionA") / len(strats)

df["agent1_coop_rate"] = df["agent1_strategies_list"].apply(coop_rate)
df["agent2_coop_rate"] = df["agent2_strategies_list"].apply(coop_rate)

print("\nAverage cooperation rate by personality (agent1):")
print(df.groupby("agent1_personality")["agent1_coop_rate"].mean())

print("\nAverage cooperation rate by personality (agent2):")
print(df.groupby("agent2_personality")["agent2_coop_rate"].mean())
