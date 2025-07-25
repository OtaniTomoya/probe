#!/usr/bin/env python3
"""
セットアップと実行スクリプト
TRPファイル処理用の環境セットアップと実行
"""

import subprocess
import sys
import os

def install_dependencies():
    """必要な依存関係をインストール"""
    print("Installing required dependencies...")
    dependencies = [
        "pandas",
        "numpy", 
        "tqdm"
    ]
    
    for dep in dependencies:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"✓ {dep} installed successfully")
        except subprocess.CalledProcessError:
            print(f"✗ Failed to install {dep}")
            return False
    return True

def check_environment():
    """環境をチェック"""
    print("Checking environment...")
    
    # jsonディレクトリの存在確認
    if not os.path.exists("./json"):
        print("✗ ./json directory not found")
        return False
    
    # TRPファイルの存在確認
    import glob
    trp_files = glob.glob("./json/TRP*.json")
    if not trp_files:
        print("✗ No TRP*.json files found in ./json directory")
        return False
    
    print(f"✓ Found {len(trp_files)} TRP files")
    
    # change_flag_filled0.csvの存在確認（必須）
    if not os.path.exists("./data/change_flag_filled0.csv"):
        print("✗ Required file not found: ./data/change_flag_filled0.csv")
        print("  This file is essential for labeling passenger events.")
        return False
    
    print("✓ data/change_flag_filled0.csv found")
    
    # 最初の数ファイルの名前を表示
    print("Sample files:")
    for i, f in enumerate(trp_files[:5]):
        print(f"  {os.path.basename(f)}")
    if len(trp_files) > 5:
        print(f"  ... and {len(trp_files) - 5} more files")
    
    return True

def run_processing():
    """TRPファイル処理を実行"""
    print("\nStarting TRP file processing...")
    try:
        import sys
        sys.path.append('src')
        exec(open('src/taxi_data_processor.py').read())
        return True
    except Exception as e:
        print(f"✗ Processing failed: {str(e)}")
        return False

def main():
    print("=== TRP File Processing Setup and Execution ===")
    print()
    
    # 環境チェック
    if not check_environment():
        print("\nEnvironment check failed. Please fix the issues above.")
        return
    
    # 依存関係インストール
    if not install_dependencies():
        print("\nDependency installation failed.")
        return
    
    # 処理実行
    if run_processing():
        print("\n✓ Processing completed successfully!")
        print("\nOutput files created:")
        output_files = [
            "./outputs/taxi_dataset_full.csv",
            "./outputs/taxi_dataset_train.csv", 
            "./outputs/taxi_dataset_test.csv"
        ]
        for f in output_files:
            if os.path.exists(f):
                size = os.path.getsize(f) / (1024*1024)  # MB
                print(f"  {f} ({size:.1f} MB)")
    else:
        print("\n✗ Processing failed.")

if __name__ == "__main__":
    main()