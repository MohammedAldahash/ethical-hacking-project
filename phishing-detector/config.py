"""Central configuration for the phishing detector."""
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent
MODEL_DIR = PROJECT_ROOT / "models" / "roberta-phishing"
DATA_DIR = PROJECT_ROOT / "data"
DATASET_PATH = DATA_DIR / "dataset.json"

# Reference to the ICS-442 phishing tool (parent folder — EmailProject IS the ICS-442 tool)
ICS442_DIR = PROJECT_ROOT.parent

# Model settings
BASE_MODEL = "roberta-base"
MAX_LENGTH = 256
NUM_LABELS = 2
LABELS = {0: "LEGITIMATE", 1: "PHISHING"}

# Training hyperparameters
EPOCHS = 4
BATCH_SIZE = 8
LEARNING_RATE = 2e-5
WARMUP_RATIO = 0.1
WEIGHT_DECAY = 0.01
TEST_SPLIT = 0.2

# Scanner settings
DEFAULT_THRESHOLD = 0.70
