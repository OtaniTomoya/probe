import pandas as pd
import numpy as np

# データセットの読み込み
base_df = pd.read_csv('/Users/tomoya/Research/probe/outputs/taxi_dataset_v2_base.csv')
accel_df = pd.read_csv('/Users/tomoya/Research/probe/outputs/taxi_dataset_v2_accel.csv')

print("=== taxi_dataset_v2_base.csv の統計情報 ===")
print(f"データ形状: {base_df.shape}")
print(f"カラム数: {base_df.shape[1]}")
print(f"行数: {base_df.shape[0]:,}")
print("\nカラム名:")
print(base_df.columns.tolist())
print("\n基本統計情報:")
print(base_df.describe())

print("\n=== taxi_dataset_v2_accel.csv の統計情報 ===")
print(f"データ形状: {accel_df.shape}")
print(f"カラム数: {accel_df.shape[1]}")
print(f"行数: {accel_df.shape[0]:,}")
print("\nカラム名:")
print(accel_df.columns.tolist())
print("\n基本統計情報:")
print(accel_df.describe())

print("\n=== ラベルの分布と割合 ===")
print("\n--- Base データセットのラベル分布 ---")
if 'label' in base_df.columns:
    label_counts_base = base_df['label'].value_counts().sort_index()
    label_ratio_base = base_df['label'].value_counts(normalize=True).sort_index() * 100
    
    print("ラベル値の分布:")
    for label, count in label_counts_base.items():
        ratio = label_ratio_base[label]
        print(f"  ラベル {label}: {count:,}件 ({ratio:.2f}%)")
        
    print(f"\n合計: {base_df.shape[0]:,}件")
else:
    print("ラベル列が見つかりません")

print("\n--- Acceleration データセットのラベル分布 ---")
if 'label' in accel_df.columns:
    label_counts_accel = accel_df['label'].value_counts().sort_index()
    label_ratio_accel = accel_df['label'].value_counts(normalize=True).sort_index() * 100
    
    print("ラベル値の分布:")
    for label, count in label_counts_accel.items():
        ratio = label_ratio_accel[label]
        print(f"  ラベル {label}: {count:,}件 ({ratio:.2f}%)")
        
    print(f"\n合計: {accel_df.shape[0]:,}件")
else:
    print("ラベル列が見つかりません")

print("\n=== データ型情報 ===")
print("\n--- Base データセット ---")
print(base_df.dtypes)

print("\n--- Acceleration データセット ---")
print(accel_df.dtypes)

print("\n=== 欠損値情報 ===")
print("\n--- Base データセット ---")
missing_base = base_df.isnull().sum()
print(f"欠損値のあるカラム: {missing_base[missing_base > 0]}")
if missing_base.sum() == 0:
    print("欠損値なし")

print("\n--- Acceleration データセット ---")
missing_accel = accel_df.isnull().sum()
print(f"欠損値のあるカラム: {missing_accel[missing_accel > 0]}")
if missing_accel.sum() == 0:
    print("欠損値なし")