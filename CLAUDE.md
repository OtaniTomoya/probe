# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based taxi data processing project that analyzes sensor data from taxi vehicles. The main script processes large JSON datasets containing:
- Vehicle telemetry data (GPS, speed, heading, altitude)
- Accelerometer data (X, Y, Z axes)
- Gyroscope data (radial acceleration)
- Vehicle state information (blinkers, brakes)
- Status management and change flags for passenger boarding/alighting detection

## Key Components

### Core Processing Class: TaxiDatasetCreator
- **Location**: `taxi_data_processor.py:9-266`
- **Purpose**: Processes thousands of timestamped JSON files and creates machine learning datasets
- **Key Features**:
  - Extracts statistical features from sensor array data (mean, max, min, std, median)
  - Merges with change flag CSV data for labeling
  - Splits data into training/test sets while preserving time series structure
  - Handles status change detection for passenger events

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
# Method 1: Automatic setup and execution
python setup_and_run.py

# Method 2: Manual setup
pip install pandas numpy tqdm

# For development, also install
pip install jupyter matplotlib seaborn scikit-learn
```

### Running the Main Script
```bash
# Process all TRP files and create datasets
python taxi_data_processor.py

# The script expects:
# - TRP*.json files in ./json/ directory (thousands of files)
# - change_flag_filled0.csv file in current directory (REQUIRED for labeling)
# - Creates output files: taxi_dataset_train.csv, taxi_dataset_test.csv, taxi_dataset_full.csv
```

### File Structure
```
probe/
├── json/                    # Directory with thousands of TRP files
│   ├── TRP_352176111064442_20240713130101.json
│   ├── TRP_352176111064442_20240713130201.json
│   └── ... (thousands more)
├── taxi_data_processor.py   # Main processing script
├── setup_and_run.py        # Automated setup and execution
├── change_flag_filled0.csv  # REQUIRED: ground truth labels for passenger events
└── CLAUDE.md               # This file
```

### Data Processing Pipeline
1. **JSON Processing**: Each file processed with `process_json_file()` - extracts features from sensor arrays
2. **Feature Engineering**: Statistical aggregation of time-series data per timestamp
3. **Label Generation**: Merges with change flag data and applies status transition rules
4. **Dataset Split**: Time-aware train/test split (80/20) per vehicle to avoid data leakage

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

Currently no formal test suite exists. For development:
1. Run on small subset of JSON files first
2. Verify output CSV structure and label distributions
3. Check for memory usage with large datasets
4. Validate timestamp alignment between JSON and CSV data

## Performance Notes

- Processing time scales with number of JSON files (thousands expected)
- Memory usage depends on dataset size - monitor for large vehicle fleets
- Consider parallel processing for production use cases
- Feature extraction is computationally intensive due to statistical calculations