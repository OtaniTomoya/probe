# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based taxi data processing project that analyzes sensor data from taxi vehicles. The system processes approximately **49,085 JSON files** (>30GB) from taxi telemetry data to create machine learning datasets for passenger boarding/alighting detection.

**Core Data**: 
- Vehicle telemetry data (GPS, speed, heading, altitude)
- Accelerometer data (X, Y, Z axes) 
- Gyroscope data (radial acceleration)
- Vehicle state information (blinkers, brakes)
- Status management and change flags for passenger boarding/alighting detection

**Current Status**: The project includes processed datasets and is ready for analysis or model development.

## Key Components

### Core Processing Classes
1. **TaxiDatasetCreator** (`taxi_data_processor.py:9-266`)
   - Original implementation with statistical feature aggregation
   - Extracts statistical features from sensor array data (mean, max, min, std, median)
   - Creates single row per timestamp with 30+ aggregated features

2. **TaxiDatasetCreatorV2** (`taxi_data_processor_v2.py:9+`)
   - Enhanced version with separation of base data and acceleration data
   - Outputs two datasets: base data (1 row/timestamp) and acceleration data (100 rows/timestamp for 100Hz sampling)
   - Implements stop-based filtering and improved temporal analysis
   - Better handling of high-frequency sensor data

### Data Architecture
- **JSON Files**: Located in `json/` directory with naming pattern `TRP_{IMEI}_{timestamp}.json`
- **Each JSON contains**:
  - Device metadata (IMEI, timestamps)
  - GPS location data
  - Time-series sensor arrays (typically 100 samples per record)
  - Vehicle information arrays
- **Labels**: Derived from status management codes and change flags
  - 0: No change
  - 1: Passenger boarding (get_on_map patterns)
  - 2: Passenger alighting (get_off_map patterns)

### Status Change Detection
The system uses specific 4-digit status codes to detect passenger events:
- **Boarding patterns**: `get_on_map` - transitions like '0003', '0012', etc.
- **Alighting patterns**: `get_off_map` - transitions like '0300', '1200', etc.

## Development Commands

### Environment Setup
```bash
# Method 1: Automatic setup and execution (PREFERRED)
python setup_and_run.py

# Method 2: Using uv (modern Python package manager)
uv run python taxi_data_processor.py

# Method 3: Manual setup
pip install pandas numpy tqdm loads

# For development and analysis
pip install jupyter matplotlib seaborn scikit-learn
```

### Running the Main Script
```bash
# Option 1: Original processor (statistical aggregation)
python src/taxi_data_processor.py

# Option 2: V2 processor (separate base/acceleration data)
python src/taxi_data_processor_v2.py

# Always run validation tests first (RECOMMENDED)
python tests/test_processing.py

# For v2 processor testing
python tests/test_v2_processing.py

# Automated setup and execution
python scripts/setup_and_run.py

# The main scripts expect:
# - TRP*.json files in ./json/ directory (49,085 files, ~600KB each)
# - change_flag_filled0.csv file in ./data/ directory (REQUIRED for labeling)
# - Creates output files in ./outputs/ directory
```

### Quick Development Workflow
```bash
# 1. Test environment and sample files
python tests/test_processing.py

# 2. Run full processing (takes significant time)
python scripts/setup_and_run.py  # OR python src/taxi_data_processor.py

# 3. Check results in outputs directory
# - outputs/taxi_dataset_full.csv (complete dataset)
# - outputs/taxi_dataset_train.csv (80% for training)  
# - outputs/taxi_dataset_test.csv (20% for testing)
```

### File Structure
```
probe/
├── src/                           # Source code
│   ├── taxi_data_processor.py     # Original processor (statistical aggregation)
│   └── taxi_data_processor_v2.py  # Enhanced processor (base/acceleration separation)
├── tests/                         # Test scripts
│   ├── test_processing.py         # Tests for original processor
│   └── test_v2_processing.py      # Tests for v2 processor
├── scripts/                       # Utility scripts
│   └── setup_and_run.py          # Automated setup and execution
├── data/                          # Input data
│   └── change_flag_filled0.csv   # REQUIRED: ground truth labels for passenger events
├── outputs/                       # Generated datasets and results
│   └── taxi_dataset_*.csv        # Generated datasets (when created)
├── docs/                          # Documentation
│   └── README.md                 # Project documentation
├── json/                          # Raw JSON data (49,085 TRP files, ~30GB total)
│   ├── TRP_352176111064442_20240713130101.json (~600KB each)
│   ├── TRP_352176111064442_20240713130201.json
│   └── ... (49,083 more files)  
├── pyproject.toml                 # Project dependencies (uv-managed)
├── uv.lock                        # Dependency lockfile
└── CLAUDE.md                      # This file
```

### Data Processing Pipeline

#### Original Processor (`taxi_data_processor.py`)
1. **JSON Processing**: Each file processed with `process_json_file()` - extracts statistical features from sensor arrays
2. **Feature Engineering**: Statistical aggregation (mean, max, min, std, median) of time-series data per timestamp
3. **Label Generation**: Merges with change flag data and applies status transition rules
4. **Dataset Split**: Time-aware train/test split (80/20) per vehicle to avoid data leakage

#### V2 Processor (`taxi_data_processor_v2.py`)
1. **Dual Data Extraction**: Separates base data (GPS, speed, blinkers) from acceleration data
2. **High-Frequency Preservation**: Maintains 100Hz sampling for acceleration/gyroscope data
3. **Stop Detection**: Identifies vehicle stop segments based on speed thresholds
4. **Enhanced Labeling**: Applies passenger event detection only during stop periods

## Code Architecture Notes

### Memory Considerations
- JSON files can be very large (>600KB each with extensive sensor arrays)
- Uses pandas for efficient data manipulation and concatenation
- Processes files sequentially with progress tracking via tqdm

### Error Handling
- Graceful handling of malformed JSON files
- Default values for missing sensor data
- Try-catch blocks around array parsing operations

### Data Flow
1. `load_change_flag_data()` - Loads ground truth labels
2. `process_json_file()` - Per-file feature extraction
3. `extract_array_features()` - Statistical feature engineering
4. `create_dataset()` - Combines all data and applies labeling logic
5. `save_dataset()` - Outputs train/test/full datasets

## Important Implementation Details

### Timestamp Handling
- JSON contains both `recordDateTime` (YYYYMMDDHHMMSS) and `timeStamp` (epoch milliseconds)
- Merging uses millisecond timestamps for precision matching
- Time-series ordering preserved in final datasets

### Feature Engineering
- Sensor arrays converted to statistical summaries (5 features × 6 sensors = 30 features per record)
- Vehicle information arrays processed with majority voting (blinkers)
- Speed and GPS data included as direct features

### Data Quality
- Handles missing/invalid sensor readings with np.nan
- Validates JSON structure before processing
- Reports processing statistics and label distributions

## Testing and Validation

### Available Test Scripts
```bash
# Run comprehensive validation tests (ALWAYS use this before full processing)
python tests/test_processing.py        # For original processor
python tests/test_v2_processing.py     # For v2 processor
```

The test scripts validate:
1. **File Detection**: Verifies JSON files and required CSV exist
2. **JSON Parsing**: Tests parsing of sample files
3. **Basic Processing**: Runs processing on first 3 files
4. **Data Structure**: Validates output format and feature extraction

### Development Testing Strategy
1. Always run appropriate test script first (`tests/test_processing.py` or `tests/test_v2_processing.py`)
2. Use uv for dependency management: `uv run python <script>.py`
3. Monitor memory usage when processing large batches
4. Validate timestamp alignment between JSON and CSV data
5. For analysis work, prefer using existing datasets in `outputs/` rather than reprocessing

### Code Quality Tools
- **Dependencies**: Managed via uv and pyproject.toml
- **No explicit linting**: Project uses standard Python conventions
- **Error Handling**: Comprehensive try-catch blocks in processing functions

## Performance Notes

- **Dataset Size**: 49,085 JSON files (~30GB total, ~600KB each)
- **Processing Time**: Full processing takes several hours due to file volume
- **Memory Usage**: Sequential processing to avoid memory issues with large datasets
- **Feature Extraction**: Computationally intensive statistical calculations on sensor arrays
- **Recommendation**: Use existing processed datasets (`taxi_dataset_*.csv`) for analysis rather than reprocessing

## Dataset Information

### Original Processor Output
- **taxi_dataset_full.csv**: Complete dataset with statistical features
- **taxi_dataset_train.csv**: Training split (80% of data, time-aware split)
- **taxi_dataset_test.csv**: Test split (20% of data, time-aware split)

Each record contains:
- Vehicle metadata (car_id, timestamp, speed, GPS coordinates)
- 30+ statistical features from sensor arrays (mean, max, min, std, median for each sensor)
- Vehicle state features (blinkers)
- Target labels (0=no change, 1=boarding, 2=alighting)

### V2 Processor Output
Generates two separate datasets:
1. **Base Data**: One row per timestamp with GPS, speed, and vehicle state
2. **Acceleration Data**: 100 rows per timestamp preserving high-frequency sensor data

This separation allows for both traditional ML approaches (using base data) and deep learning/time-series approaches (using acceleration data).