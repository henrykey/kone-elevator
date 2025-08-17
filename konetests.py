#!/usr/bin/env python
"""
konetests.py

Parse `kone_info.md` (items 1-5) and call existing `KoneValidationSuite` tests using provided parameters.
Script rules: call existing modules without modifying them; catch and continue on network/auth failures.

Usage:
    python konetests.py

Output:
    konetests_results.json

"""

import argparse
import asyncio
import json
import logging
import re
from pathlib import Path

from testall_v2 import KoneValidationSuite

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

KONE_INFO = Path(__file__).parent / 'kone_info.md'
OUTPUT_DIR = Path(__file__).parent / 'reports'
OUTPUT_FILE = OUTPUT_DIR / 'konetests_results.json'

# Default mapping fallback if kone_info.md doesn't contain (Test ...) annotations
DEFAULT_ITEM_TO_TESTS = {
    1: [7, 6],
    2: [12, 14],
    3: [11],
    4: [24, 23],
    5: [21, 22]
}

# Minimal mapping of test numbers to English canonical names.
# This ensures the JSON output uses English names even if test docstrings are in another language.
TEST_NAME_OVERRIDES = {
    1: "Test 1: Initialization test",
    6: "Test 6: Unknown action handling",
    7: "Test 7: Disabled action test - action=4 (per official test guide)",
    11: "Test 11: Transfer call test - multi-segment journey",
    12: "Test 12: Through lift call - same floor opposite sides (per official guide)",
    14: "Test 14: Specific elevator assignment",
    21: "Test 21: Wrong Building ID - per official guide",
    23: "Test 23: Access control - card required",
    24: "Test 24: Invalid request format",
}


def parse_kone_info(path: Path) -> dict:
    """Parse kone_info.md and extract parameters for items 1-5: building id, group/terminal/area,
    and any Test numbers listed in parentheses.
    Returns: {index: {'building_id': str, 'group': str|None, 'tests': [int,...], ...}}
    """
    text = path.read_text(encoding='utf-8')
    lines = text.splitlines()

    items = {}

    # Find lines starting with '1.'..'5.' and capture the following block
    for i in range(1, 6):
        header_re = re.compile(rf'^\s*{i}\.' )
        start_idx = None
        for idx, line in enumerate(lines):
            if header_re.match(line):
                start_idx = idx
                break
        if start_idx is None:
            items[i] = {'building_id': None, 'group': None, 'tests': DEFAULT_ITEM_TO_TESTS.get(i, [])}
            continue

    # Read the next 12 lines as the block (kone_info.md is short); extract Building ID / Media / Group / Area
        block = '\n'.join(lines[start_idx:start_idx + 12])

        # Building ID
        m_build = re.search(r'Building ID:\s*([A-Za-z0-9:_\-]+)', block)
        building_id = m_build.group(1) if m_build else None

    # Group id or Terminal
        m_group = re.search(r'Group\s*1:|Group 1:|Group 1\s*\n|Group 1\s*\n', block)
    # More reliable search for Terminal ID
        m_terminal = re.search(r'Terminal ID\s*=\s*([0-9]+)', block)
        terminal = m_terminal.group(1) if m_terminal else None

    # Media / Media ID
        m_media = re.search(r'Media ID\s*=\s*([A-Za-z0-9]+)', block)
        media_id = m_media.group(1) if m_media else None

    # Area IDs (comma-separated or ranges)
        m_areas = re.findall(r'Area IDs?\s*=\s*([0-9,\s\-–]+)', block)
        area_ids = m_areas[0].strip() if m_areas else None

        # Attempt to find explicit 'Tests:' lines or any 'Test N' mentions inside the item block.
        tests = []

        # 1) Look for a line like 'Tests: Test 7, Test 6' or 'Tests: 7,6'
        m_tests_line = re.search(r'Tests?\s*[:：]\s*(.*)', block, re.IGNORECASE)
        if m_tests_line:
            raw = m_tests_line.group(1)
            # extract all numbers from the remainder of the line
            nums = re.findall(r'(\d+)', raw)
            tests = [int(x) for x in nums]
        else:
            # 2) Fallback: find any 'Test 7' occurrences in the block (covers 'Test 14' etc.)
            nums = re.findall(r'Test\s*([0-9]+)', block, re.IGNORECASE)
            tests = [int(x) for x in nums]

        if not tests:
            # final fallback: default mapping
            tests = DEFAULT_ITEM_TO_TESTS.get(i, [])

        items[i] = {
            'building_id': building_id,
            'terminal': terminal,
            'media_id': media_id,
            'area_ids': area_ids,
            'group': None,
            'tests': tests
        }

    return items


async def run_for_item(suite: KoneValidationSuite, item_index: int, item: dict, include_auto: bool = False) -> list:
    """为单个 kone_info 条目运行其关联的 test 列表，返回该条目的结果列表
    include_auto: 是否运行 AUTO 模式（默认 False）。当为 False 时，AUTO 模式完全跳过。"""
    results = []
    # We'll run each test twice: (A) automatic configuration chosen by suite, (B) kone_info parameters
    for test_num in item.get('tests', []):
        # find method in suite matching test number prefix
        prefix = f"test_{int(test_num):02d}_"
        method_name = None
        for name in dir(suite):
            if name.startswith(prefix):
                method_name = name
                break
        if not method_name:
            logger.warning(f"No test method found for Test {test_num} (prefix {prefix})")
            continue

        method = getattr(suite, method_name)
        test_doc = (method.__doc__ or method_name).strip()
        logger.info(f"Running Test {test_num}: {method_name} -> {test_doc}")

        # --- Run A: automatic configuration (optional) ---
        if include_auto:
            try:
                # AUTO mode: use the building selected during suite.setup() (do not force-switch to defaults)
                logger.info(f"AUTO mode will use current building: {suite.building_id}")

                # Run AUTO: only print minimal PASS/FAIL
                res_auto = await suite.run_test(method, int(test_num), test_doc, "")
                status_auto = getattr(res_auto, 'result', None) or (res_auto.to_dict().get('result') if hasattr(res_auto, 'to_dict') else None)
                if status_auto and str(status_auto).lower().startswith('pass'):
                    print(f"AUTO Test {test_num}: PASS")
                else:
                    print(f"AUTO Test {test_num}: FAIL")
                auto_dict = res_auto.to_dict()
                auto_dict['mode'] = 'auto_config'
                auto_dict['item_index'] = item_index
                # Override name with canonical English name when available
                try:
                    tn = int(test_num)
                    if tn in TEST_NAME_OVERRIDES:
                        auto_dict['name'] = TEST_NAME_OVERRIDES[tn]
                except Exception:
                    pass
                # Convert numeric test_id into 'test': 'Test N' key/value when present
                try:
                    if 'test_id' in auto_dict:
                        tid = auto_dict.pop('test_id')
                        auto_dict['test'] = f"Test {tid}"
                except Exception:
                    pass
                # By default we don't append AUTO results unless caller opts in to collect them.
                results.append(auto_dict)
            except Exception as e:
                logger.exception(f"Exception while running AUTO Test {test_num}: {e}")
                print(f"❌ AUTO Test {test_num}: ERROR during execution: {e}")

        # --- Run B: kone_info parameters ---
        # apply kone_info building/group if provided
        b = item.get('building_id')
        original_building = suite.building_id
        original_group = suite.group_id
        if b:
            if not str(b).startswith('building:'):
                suite.building_id = f'building:{b}'
            else:
                suite.building_id = b
            logger.info(f"KONE_INFO override for item {item_index}: using building {suite.building_id}")
        else:
            logger.info(f"KONE_INFO override for item {item_index}: no building specified, using current {suite.building_id}")

        if item.get('group'):
            suite.group_id = str(item['group'])

        try:
            # Run KONE_INFO: print PASS/FAIL + building id + failure reason if any
            res_kone = await suite.run_test(method, int(test_num), test_doc, "")
            status_kone = getattr(res_kone, 'result', None) or (res_kone.to_dict().get('result') if hasattr(res_kone, 'to_dict') else None)
            reason_kone = getattr(res_kone, 'reason', None) or (res_kone.to_dict().get('reason') if hasattr(res_kone, 'to_dict') else '')
            if status_kone and str(status_kone).lower().startswith('pass'):
                print(f"KONE_INFO Test {test_num}: PASS — building {suite.building_id}")
            else:
                # include reason when failing
                print(f"KONE_INFO Test {test_num}: FAIL — building {suite.building_id} — {reason_kone}")
            kone_dict = res_kone.to_dict()
            kone_dict['mode'] = 'kone_info'
            kone_dict['item_index'] = item_index
            # Override name with canonical English name when available
            try:
                tn = int(test_num)
                if tn in TEST_NAME_OVERRIDES:
                    kone_dict['name'] = TEST_NAME_OVERRIDES[tn]
            except Exception:
                pass
            # Convert numeric test_id into 'test': 'Test N' key/value when present
            try:
                if 'test_id' in kone_dict:
                    tid = kone_dict.pop('test_id')
                    kone_dict['test'] = f"Test {tid}"
            except Exception:
                pass
            results.append(kone_dict)
        except Exception as e:
            logger.exception(f"Exception while running KONE_INFO Test {test_num}: {e}")
            print(f"❌ KONE_INFO Test {test_num}: ERROR during execution: {e}")
        finally:
            # restore original building/group to avoid side-effects between items
            suite.building_id = original_building
            suite.group_id = original_group

    return results


async def main():
    logger.info("Parsing kone_info.md...")
    items = parse_kone_info(KONE_INFO)
    logger.info(f"Parsed items: {items}")

    suite = KoneValidationSuite()

    # Attempt setup (may require credentials); on failure warn and proceed — some tests may not run
    try:
        await suite.setup()
    except Exception as e:
        logger.warning(f"Setup failed or skipped: {e}")
        logger.info("Proceeding with configured building ids from kone_info.md (no network setup)")

    all_results = []

    # Only run tests associated with items 1-5 in kone_info.md
    parser = argparse.ArgumentParser(description='Run KONE-focused tests from kone_info.md')
    parser.add_argument('--include-auto', action='store_true', help='Include AUTO mode runs in execution and results')
    args = parser.parse_args()

    include_auto = bool(args.include_auto)

    for idx in range(1, 6):
        item = items.get(idx, {})
        logger.info(f"Starting item {idx} tests: {item.get('tests')}")
        item_results = await run_for_item(suite, idx, item, include_auto=include_auto)
        all_results.extend(item_results)

    # teardown if possible
    try:
        await suite.teardown()
    except Exception:
        pass

    # ensure reports directory exists
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    # If user did not request AUTO results, filter them out now (this also
    # handles leftover AUTO entries from previous runs when re-running).
    if not include_auto:
        all_results = [r for r in all_results if r.get('mode') != 'auto_config']

    # Canonicalize 'test_id' -> 'test': 'Test N' for any remaining results
    for r in all_results:
        try:
            if isinstance(r, dict) and 'test_id' in r:
                tid = int(r.pop('test_id'))
                r['test'] = f"Test {tid}"
        except Exception:
            pass

    # Wrap the list under the key 'test_results' to produce the final report object
    final_out = {'test_results': all_results}
    OUTPUT_FILE.write_text(json.dumps(final_out, indent=2, ensure_ascii=False), encoding='utf-8')
    logger.info(f"Results written to {OUTPUT_FILE} (wrapped under 'test_results')")


if __name__ == '__main__':
    asyncio.run(main())
