import sys
sys.path.append('./src')
from taxi_data_processor_v2 import TaxiDatasetCreatorV2

# 修正されたプロセッサーをテスト（最初の10ファイルのみ）
creator = TaxiDatasetCreatorV2(
    json_dir="./json",
    change_flag_csv_path="./data/change_flag_filled0.csv",
    stop_speed_threshold=10.0
)

print("テスト実行中（最初の10ファイル）...")
base_df, accel_df = creator.create_dataset(max_files=10)

print(f"\nBase dataset shape: {base_df.shape}")
print(f"Acceleration dataset shape: {accel_df.shape}")

print("\nLabel distribution in base data:")
label_counts = base_df['label'].value_counts().sort_index()
print(label_counts)

print("\nLabel percentages:")
for label, count in label_counts.items():
    percentage = (count / len(base_df)) * 100
    print(f"Label {label}: {count} records ({percentage:.2f}%)")

# イベントが検出されたレコードを確認
if (base_df['label'] > 0).any():
    print("\nSample events found:")
    events = base_df[base_df['label'] > 0].head(10)
    print(events[['timestamp', 'label', 'is_stopped']].to_string())
else:
    print("\nNo events detected in test data")

# 停車統計
print(f"\nStop statistics:")
stopped_count = (base_df['is_stopped'] == 1).sum()
print(f"Total stopped records: {stopped_count}")
print(f"Stop percentage: {stopped_count / len(base_df) * 100:.2f}%")