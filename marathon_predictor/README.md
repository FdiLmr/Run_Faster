# Marathon Time Predictor

A neural network-based marathon time prediction system that uses race performance data and training volume to predict marathon finishing times.

## Features

- **Two Neural Network Models**:
  - **Model 1**: Single race prediction using one race result + training mileage
  - **Model 2**: Dual race prediction using two race results + training mileage
- **Robust Input Validation**: Comprehensive validation of race distances, times, and training data
- **Clean API**: Easy-to-use `MarathonPredictor` class with unified interface
- **Command Line Interface**: Interactive CLI for making predictions
- **Comprehensive Testing**: 110+ tests covering all functionality
- **Type Hints**: Full type annotation for better code clarity

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd marathon-predictor
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Python API

```python
from marathon_predictor import MarathonPredictor

# Initialize predictor
predictor = MarathonPredictor()

# Load trained models (you'll need to train and save models first)
predictor.load_all_models()

# Single race prediction
marathon_time = predictor.predict_single_race(
    distance=10000,      # 10K race in meters
    time_minutes=40.0,   # Race time in minutes
    mileage=60.0         # Weekly training miles
)

# Dual race prediction
marathon_time = predictor.predict_dual_race(
    distance1=5000,      # 5K race in meters
    time1_minutes=20.0,  # 5K time in minutes
    distance2=10000,     # 10K race in meters
    time2_minutes=40.0,  # 10K time in minutes
    mileage=60.0         # Weekly training miles
)

# Get predictions from both models
results = predictor.predict_both(
    distance1=5000, time1_minutes=20.0,
    distance2=10000, time2_minutes=40.0,
    mileage=60.0
)
print(f"Model 1 prediction: {results['model1']:.1f} minutes")
print(f"Model 2 prediction: {results['model2']:.1f} minutes")
```

### Command Line Interface

```bash
python -m marathon_predictor.cli
```

The CLI will interactively prompt you for:
- Two race distances and times
- Weekly training mileage
- Then provide predictions from both models

### Direct Function Usage

```python
from marathon_predictor.inference import predict_marathon_time_model1, predict_marathon_time_model2
from marathon_predictor.models import Neuromodel1, Neuromodel2
from utils.marathon_predictor_utils import load_model_and_scaler

# Load model and scaler
model, scaler = load_model_and_scaler(
    Neuromodel1, 
    "path/to/model.pth", 
    "path/to/scaler.pkl"
)

# Make prediction
prediction = predict_marathon_time_model1(
    model, scaler, 
    distance=10000, 
    time_minutes=40.0, 
    mileage=60.0
)
```

## Model Architecture

### Neuromodel1 (Single Race)
- **Input**: 3 features (distance, time, mileage)
- **Architecture**: 3 → 7 → 12 → 1
- **Activation**: ReLU
- **Output**: Marathon time in minutes

### Neuromodel2 (Dual Race)
- **Input**: 5 features (distance1, time1, distance2, time2, mileage)
- **Architecture**: 5 → 5 → 12 → 1
- **Activation**: ReLU
- **Output**: Marathon time in minutes

## Input Validation

The system validates all inputs:
- **Race distances**: Must be positive, ≤ 50km
- **Race times**: Must be positive, ≤ 10 hours
- **Training mileage**: Must be non-negative, ≤ 200 miles/week

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test categories
pytest tests/test_models.py -v
pytest tests/test_inference.py -v
pytest tests/test_predictor.py -v
```

Test coverage includes:
- Model architecture and forward passes
- Input validation functions
- Prediction functions with various scenarios
- Error handling and edge cases
- File I/O operations
- Time formatting utilities

## Project Structure

```
marathon_predictor/
├── marathon_predictor/
│   ├── __init__.py          # Package exports
│   ├── models.py            # Neural network models
│   ├── inference.py         # Prediction functions
│   ├── predictor.py         # Main MarathonPredictor class
│   └── cli.py              # Command line interface
├── utils/
│   ├── time_utils.py        # Time formatting utilities
│   └── marathon_predictor_utils.py  # Model I/O utilities
├── tests/
│   ├── test_models.py       # Model tests
│   ├── test_inference.py    # Inference tests
│   ├── test_predictor.py    # Predictor class tests
│   ├── test_utils.py        # Utility tests
│   └── test_time_utils.py   # Time utility tests
├── requirements.txt         # Dependencies
├── pytest.ini             # Test configuration
└── README.md              # This file
```

## Dependencies

- **PyTorch**: Neural network framework
- **scikit-learn**: Data preprocessing (StandardScaler)
- **NumPy**: Numerical computations
- **joblib**: Model serialization
- **pytest**: Testing framework

## Development

### Adding New Models

1. Create model class inheriting from `torch.nn.Module`
2. Add validation for expected input size
3. Implement forward pass with proper error handling
4. Add corresponding inference function
5. Update `MarathonPredictor` class if needed
6. Write comprehensive tests

### Training Models

Models expect preprocessed input:
- Distances in meters
- Times in seconds (for model input)
- Mileage in miles per week
- StandardScaler normalization

Example training data format:
```python
# Model 1: [distance_m, time_s, mileage_mpw]
# Model 2: [distance1_m, time1_s, distance2_m, time2_s, mileage_mpw]
```

## Error Handling

The system provides detailed error messages for:
- Invalid input values (negative times, unrealistic distances)
- Missing or corrupted model files
- Model prediction failures
- File I/O errors

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

[Add your license information here]

## Changelog

### v1.0.0
- Complete refactoring of marathon predictor
- Added comprehensive input validation
- Implemented unified `MarathonPredictor` class
- Added 110+ tests with full coverage
- Improved error handling and documentation
- Added type hints throughout codebase
