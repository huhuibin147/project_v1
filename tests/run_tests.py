#!/usr/bin/env python3
"""自动化测试入口 - 一键运行所有测试"""
import sys
import time
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "backend"))
sys.path.insert(0, str(ROOT_DIR / "tests"))

TEST_MODULES = {
    "config": "test_config_data",
    "backend": "test_backend_logic",
    "map": "test_map_system",
    "api": "test_api_integration",
}

LABELS = {
    "config": "配置数据测试",
    "backend": "后端逻辑测试",
    "map": "地图系统测试",
    "api": "API 集成测试",
}


def run_tests(modules=None, verbose=True):
    loader = unittest.TestLoader()
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)

    if modules:
        target_modules = {}
        for m in modules:
            if m in TEST_MODULES:
                target_modules[m] = TEST_MODULES[m]
            else:
                print(f"未知测试模块: {m}")
                print(f"可用模块: {', '.join(TEST_MODULES.keys())}")
                return 1
    else:
        target_modules = TEST_MODULES

    total_pass = 0
    total_fail = 0
    total_error = 0
    total_skip = 0
    results_by_module = {}

    print("=" * 60)
    print("自动化测试报告")
    print("=" * 60)
    print()

    start_time = time.time()

    for module_key, module_name in target_modules.items():
        label = LABELS.get(module_key, module_key)
        print(f"[{label}]")
        print("-" * 40)

        try:
            suite = loader.loadTestsFromName(module_name)
            result = runner.run(suite)
        except Exception as e:
            print(f"  加载测试模块失败: {e}")
            print()
            results_by_module[module_key] = {"pass": 0, "fail": 0, "error": 1, "skip": 0}
            total_error += 1
            continue

        passed = result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)
        failed = len(result.failures)
        errored = len(result.errors)
        skipped = len(result.skipped)

        results_by_module[module_key] = {
            "pass": passed,
            "fail": failed,
            "error": errored,
            "skip": skipped,
        }

        total_pass += passed
        total_fail += failed
        total_error += errored
        total_skip += skipped

        status = "✓" if failed == 0 and errored == 0 else "✗"
        print(f"  {passed}/{result.testsRun} 通过 {status}")
        if failed > 0:
            print(f"  失败: {failed}")
        if errored > 0:
            print(f"  错误: {errored}")
        if skipped > 0:
            print(f"  跳过: {skipped}")
        print()

    elapsed = time.time() - start_time
    total_tests = total_pass + total_fail + total_error + total_skip
    pct = (total_pass / total_tests * 100) if total_tests > 0 else 0

    print("=" * 60)
    print(f"总计: {total_pass}/{total_tests} 通过 ({pct:.1f}%)")
    if total_fail > 0:
        print(f"失败: {total_fail}")
    if total_error > 0:
        print(f"错误: {total_error}")
    if total_skip > 0:
        print(f"跳过: {total_skip}")
    print(f"耗时: {elapsed:.2f}s")
    print("=" * 60)

    return 1 if total_fail > 0 or total_error > 0 else 0


def main():
    if len(sys.argv) < 2:
        return run_tests()

    args = sys.argv[1:]
    if args[0] in ("--help", "-h"):
        print("用法: python run_tests.py [模块名...]")
        print()
        print("可用模块:")
        for key, label in LABELS.items():
            print(f"  {key:10s} - {label}")
        print()
        print("示例:")
        print("  python run_tests.py              # 运行所有测试")
        print("  python run_tests.py config map    # 只运行配置和地图测试")
        return 0

    return run_tests(args)


if __name__ == "__main__":
    sys.exit(main())
