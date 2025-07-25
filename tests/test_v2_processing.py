#!/usr/bin/env python3
"""
新しいデータ処理システムのテストスクリプト
"""

import sys
sys.path.append('./src')
from taxi_data_processor_v2 import TaxiDatasetCreatorV2
import pandas as pd
import numpy as np
from glob import glob
import os

def test_small_sample():
    """小さなサンプルで完全な処理をテスト"""
    print("=== Testing with small sample (100 files) ===")
    
    # 100ファイルで処理
    creator = TaxiDatasetCreatorV2('./json', './data/change_flag_filled0.csv', stop_speed_threshold=10.0)
    
    # データセットを作成して保存
    try:
        base_df, accel_df = creator.save_dataset('./outputs/test_v2_sample', max_files=100)
        
        print(f"\nSuccessfully created datasets:")
        print(f"Base data shape: {base_df.shape}")
        print(f"Acceleration data shape: {accel_df.shape}")
        
        # 基本データの統計
        print("\n=== Base Data Statistics ===")
        print(f"Unique vehicles: {base_df['car_id'].nunique()}")
        print(f"Date range: {base_df['timestamp'].min()} to {base_df['timestamp'].max()}")
        print(f"\nSpeed statistics:")
        print(f"  Min: {base_df['speed'].min():.1f} km/h")
        print(f"  Max: {base_df['speed'].max():.1f} km/h")
        print(f"  Mean: {base_df['speed'].mean():.1f} km/h")
        
        # 停車統計
        print(f"\nStop statistics:")
        stopped_records = base_df[base_df['is_stopped'] == 1]
        print(f"  Total stopped records: {len(stopped_records)}")
        print(f"  Stop percentage: {len(stopped_records) / len(base_df) * 100:.1f}%")
        
        # ラベル分布
        print(f"\nLabel distribution:")
        for label, count in base_df['label'].value_counts().sort_index().items():
            label_name = ['Normal', 'Boarding', 'Alighting'][int(label)]
            print(f"  {label} ({label_name}): {count} records ({count/len(base_df)*100:.1f}%)")
        
        # ラベル付き停車区間の詳細
        labeled_stops = base_df[(base_df['is_stopped'] == 1) & (base_df['label'] > 0)]
        if len(labeled_stops) > 0:
            print(f"\n=== Labeled Stop Segments ===")
            print(f"Total labeled stop records: {len(labeled_stops)}")
            
            # 各ラベルタイプごとの停車区間数を数える
            for label in [1, 2]:
                label_name = ['', 'Boarding', 'Alighting'][label]
                label_stops = labeled_stops[labeled_stops['label'] == label]
                if len(label_stops) > 0:
                    # ユニークな停車区間を数える
                    unique_segments = label_stops.groupby(['car_id', 'stop_segment']).size()
                    print(f"\n{label_name} stops:")
                    print(f"  Records: {len(label_stops)}")
                    print(f"  Unique segments: {len(unique_segments)}")
                    
                    # 最初の3つの例を表示
                    examples = label_stops.groupby(['car_id', 'stop_segment']).agg({
                        'timestamp': ['min', 'max', 'count'],
                        'speed': 'mean'
                    }).head(3)
                    print(f"  Examples:")
                    for idx, row in examples.iterrows():
                        duration = (row[('timestamp', 'max')] - row[('timestamp', 'min')]).total_seconds()
                        print(f"    Car {idx[0]}, Segment {idx[1]}: {row[('timestamp', 'count')]} records, {duration:.1f}s")
        
        # 加速度データのサンプル
        if not accel_df.empty:
            print(f"\n=== Acceleration Data Sample ===")
            print(f"Total acceleration records: {len(accel_df)}")
            print(f"Records per timestamp (average): {len(accel_df) / len(base_df):.1f}")
            print("\nFirst 5 acceleration records:")
            print(accel_df.head())
        
        return base_df, accel_df
        
    except Exception as e:
        print(f"Error during processing: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None

def check_data_linkage():
    """基本データと加速度データのリンケージを確認"""
    print("\n=== Checking Data Linkage ===")
    
    # 生成されたファイルを読み込み
    if os.path.exists('./test_v2_sample_base.csv') and os.path.exists('./test_v2_sample_accel.csv'):
        base_df = pd.read_csv('./test_v2_sample_base.csv', nrows=1000)
        accel_df = pd.read_csv('./test_v2_sample_accel.csv', nrows=10000)
        
        # タイムスタンプを変換
        base_df['timestamp'] = pd.to_datetime(base_df['timestamp'])
        accel_df['timestamp'] = pd.to_datetime(accel_df['timestamp'])
        
        # 特定のタイムスタンプでのデータを確認
        sample_timestamp = base_df['timestamp'].iloc[0]
        base_record = base_df[base_df['timestamp'] == sample_timestamp].iloc[0]
        accel_records = accel_df[accel_df['timestamp'] == sample_timestamp]
        
        print(f"Sample timestamp: {sample_timestamp}")
        print(f"\nBase record:")
        print(f"  Speed: {base_record['speed']} km/h")
        print(f"  Location: ({base_record['latitude']:.6f}, {base_record['longitude']:.6f})")
        print(f"  Label: {base_record['label']}")
        
        print(f"\nCorresponding acceleration records: {len(accel_records)}")
        if len(accel_records) > 0:
            print("  First 5 acceleration values:")
            print(accel_records[['sample_index', 'acc_x', 'acc_y', 'acc_z']].head())

if __name__ == "__main__":
    # 小さなサンプルでテスト
    base_df, accel_df = test_small_sample()
    
    # データリンケージを確認
    if base_df is not None:
        check_data_linkage()
    
    print("\n=== Test completed ===")