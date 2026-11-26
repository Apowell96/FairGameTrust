## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Apowell96/FairGameTrust.git
cd FairGameTrust
```

### 2. Create a Python Environment

```bash
conda create -n fairgame-trust python=3.12
conda activate fairgame-trust
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Keys

Create a `.env` file using the provided example:

```bash
cp .env.example .env
```

Populate the required API keys:

```text
API_KEY_OPENAI=your_key_here
API_KEY_MISTRAL=your_key_here
API_KEY_ANTHROPIC=your_key_here
```

### 5. Run an Experiment

```bash
python main.py local
```

The framework will execute the configured trust experiment and store results in the results directory.

### 6. Analyse Results

```bash
python analyse_results.py
```

Generated figures and processed outputs will be stored in the analysis output directory.

```
```

## Example Trust Configuration

```json
"trust": {
        "enabled": true,
        "actions": ["LOOK", "NO_LOOK"],
        "lookCost": 0.25,
        "historyScope": "only_paid_to_look_last_1",
        "historyFields": ["strategy", "score"]
    }
```

This configuration enables trust-based monitoring with a monitoring cost of 0.25 points per monitoring action.

```
```
## Example Output
## Example Output

For each game, FAIRGAME-Trust records:

| Round | Trust Decision | Strategy  | Score |
| ----- | -------------- | --------- | ----- |
| 1     | LOOK           | Cooperate | 3     |
| 2     | LOOK           | Cooperate | 3     |
| 3     | NO_LOOK        | Cooperate | 5     |
| 4     | NO_LOOK        | Defect    | 1     |

Results are exported as CSV files for further analysis and visualisation.
