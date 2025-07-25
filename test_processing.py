#!/usr/bin/env python3
"""
TRP処理のテストスクリプト
最初の数ファイルで動作確認
"""

import os
import sys
from glob import glob

def test_file_detection():
    """ファイル検出テスト"""
    print("=== File Detection Test ===")
    
    # jsonディレクトリの確認
    if not os.path.exists("./json"):
        print("✗ ./json directory not found")
        return False
    
    # TRPファイルの確認
    trp_files = glob("./json/TRP*.json")
    print(f"Found {len(trp_files)} TRP files")
    
    if len(trp_files) == 0:
        print("✗ No TRP files found")
        return False
    
    # change_flag_filled0.csvの確認（必須）
    if not os.path.exists("./change_flag_filled0.csv"):
        print("✗ Required file not found: ./change_flag_filled0.csv")
        print("  This file is essential for labeling passenger events.")
        return False
    
    print("✓ change_flag_filled0.csv found")
    
    # 最初の5ファイルを表示
    print("First 5 files:")
    for i, f in enumerate(trp_files[:5]):
        size_mb = os.path.getsize(f) / (1024*1024)
        print(f"  {os.path.basename(f)} ({size_mb:.1f} MB)")
    
    return True

def test_json_parsing():
    """JSON解析テスト"""
    print("\n=== JSON Parsing Test ===")
    
    try:
        import json
        
        # 最初のファイルを読み込み
        trp_files = glob("./json/TRP*.json")
        if not trp_files:
            print("✗ No files to test")
            return False
        
        test_file = trp_files[0]
        print(f"Testing file: {os.path.basename(test_file)}")
        
        with open(test_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("✓ JSON parsing successful")
        print(f"Keys: {list(data.keys())}")
        
        # IMEIとデータ数を確認
        imei = data.get('imei', 'N/A')
        data_count = len(data.get('data', []))
        print(f"IMEI: {imei}")
        print(f"Data records: {data_count}")
        
        return True
        
    except Exception as e:
        print(f"✗ JSON parsing failed: {str(e)}")
        return False

def test_basic_processing():
    """基本処理テスト（少数ファイル）"""
    print("\n=== Basic Processing Test ===")
    
    try:
        # 必要なモジュールの確認
        import pandas as pd
        import numpy as np
        from tqdm import tqdm
        print("✓ All required modules available")
        
        # TaxiDatasetCreatorクラスのインポート
        sys.path.append('.')
        from json import TaxiDatasetCreator
        
        # 最初の3ファイルで処理テスト
        creator = TaxiDatasetCreator("./json")
        
        # テスト用に少数のファイルを処理
        print("Running processing test with first 3 files...")
        
        # Note: This is a simplified test - full processing might be too intensive
        trp_files = glob("./json/TRP*.json")
        sample_files = trp_files[:3]
        
        for file_path in sample_files:
            df = creator.process_json_file(file_path)
            print(f"  {os.path.basename(file_path)}: {len(df)} records")
        
        print("✓ Basic processing test completed")
        return True
        
    except ImportError as e:
        print(f"✗ Missing dependency: {str(e)}")
        print("Run: pip install pandas numpy tqdm")
        return False
    except Exception as e:
        print(f"✗ Processing test failed: {str(e)}")
        return False

def main():
    print("TRP File Processing Test\n")
    
    tests = [
        ("File Detection", test_file_detection),
        ("JSON Parsing", test_json_parsing), 
        ("Basic Processing", test_basic_processing)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} crashed: {str(e)}")
            results.append((test_name, False))
    
    print("\n=== Test Summary ===")
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! Ready to run full processing.")
        print("Run: python json.py")
    else:
        print("\n❌ Some tests failed. Please fix issues before running full processing.")

if __name__ == "__main__":
    main()