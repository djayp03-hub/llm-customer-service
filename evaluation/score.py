"""Score recorded predictions; this tool does not generate model predictions."""
import argparse
import json
from pathlib import Path


def score(rows):
    seen = set()
    top1 = top3 = slots = 0
    slot_count = 0
    task_results = []
    failures = []
    for row in rows:
        case_id = row['id']
        if not isinstance(case_id, str) or not case_id or case_id in seen:
            raise ValueError('Case IDs must be nonempty and unique')
        seen.add(case_id)
        expected = row['expected_flow']
        candidates = row['candidates']
        if not isinstance(expected, str) or not isinstance(candidates, list) or any(
            not isinstance(c, str) for c in candidates
        ):
            raise ValueError('Expected flow and candidate flows must be strings')
        hit1 = bool(candidates) and candidates[0] == expected
        hit3 = expected in candidates[:3]
        top1 += hit1
        top3 += hit3
        if not hit1:
            failures.append(case_id)
        if 'expected_slots' in row:
            slot_count += 1
            slots += row['expected_slots'] == row.get('predicted_slots')
        if 'task_success' in row:
            if type(row['task_success']) is not bool:
                raise ValueError('task_success must be a boolean judged from task outcome')
            task_results.append(row['task_success'])
    count = len(seen)
    return {
        'cases': count,
        'top1': top1 / count if count else None,
        'top3': top3 / count if count else None,
        'slot_cases': slot_count,
        'slot_exact_match': slots / slot_count if slot_count else None,
        'task_cases': len(task_results),
        'task_success_rate': sum(task_results) / len(task_results) if task_results else None,
        'top1_failure_ids': failures,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('predictions', type=Path)
    args = parser.parse_args()
    with args.predictions.open(encoding='utf-8') as stream:
        rows = [json.loads(line) for line in stream if line.strip()]
    print(json.dumps(score(rows), ensure_ascii=False, indent=2))
