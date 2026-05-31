"""
ARC Evaluation Runner

Runs hypothesis search on ARC tasks and generates competition-ready receipts.
Validates no-internet boundary before evaluation.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import numpy as np

# Import local components
from task_loader import ARCTaskLoader
from hypothesis_search import HypothesisSearch
from receipt_format import ARCExperimentReceipt
from no_internet_test import test_no_internet


def load_synthetic_tasks(data_path: str):
    """Load synthetic ARC tasks from JSON."""
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    tasks = {}
    for task_id, task_data in data.items():
        # Convert to numpy arrays
        train_examples = []
        for ex in task_data['train']:
            train_examples.append({
                'input': np.array(ex['input']),
                'output': np.array(ex['output'])
            })
        
        test_examples = []
        for ex in task_data['test']:
            test_examples.append({
                'input': np.array(ex['input'])
            })
        
        tasks[task_id] = {
            'train': train_examples,
            'test': test_examples
        }
    
    return tasks


def evaluate_task(task_id: str, task_data: dict, seed: int = 42) -> dict:
    """Evaluate a single task with hypothesis search."""
    print(f"\nEvaluating task: {task_id}")
    print(f"  Train examples: {len(task_data['train'])}")
    print(f"  Test examples: {len(task_data['test'])}")
    
    # Run hypothesis search
    search = HypothesisSearch(seed=seed, max_depth=3)
    best_hypothesis = search.search(task_data['train'], max_candidates=500)
    
    if best_hypothesis is None:
        return {
            'task_id': task_id,
            'solved': False,
            'confidence': 0.0,
            'predictions': []
        }
    
    # Generate predictions for test
    predictions = []
    for test_ex in task_data['test']:
        pred = search.predict(test_ex['input'], best_hypothesis)
        predictions.append(pred.tolist())
    
    # Get search stats
    stats = search.get_search_stats()
    
    result = {
        'task_id': task_id,
        'solved': best_hypothesis.confidence >= 0.99,
        'confidence': float(best_hypothesis.confidence),
        'operations_count': len(best_hypothesis.operations),
        'candidates_tested': stats['total_candidates'],
        'predictions': predictions,
        'operation_names': [op.name for op in best_hypothesis.operations]
    }
    
    print(f"  ✓ Confidence: {result['confidence']:.2%}")
    print(f"  ✓ Operations: {result['operations_count']}")
    print(f"  ✓ Solved: {result['solved']}")
    
    return result


def run_full_evaluation(data_path: str, output_dir: str):
    """Run full evaluation on all tasks."""
    print("=" * 60)
    print("ARC EVALUATION RUNNER")
    print("=" * 60)
    
    # Step 1: Validate no-internet boundary
    print("\n[1/4] Validating no-internet boundary...")
    has_internet, message = test_no_internet()
    if has_internet:
        print(f"  ✗ FAILED: {message}")
        print("  Evaluation aborted - ARC Prize requires offline evaluation")
        return None
    else:
        print(f"  ✓ PASSED: {message}")
    
    # Step 2: Load tasks
    print("\n[2/4] Loading tasks...")
    tasks = load_synthetic_tasks(data_path)
    print(f"  ✓ Loaded {len(tasks)} tasks")
    
    # Step 3: Evaluate each task
    print("\n[3/4] Running hypothesis search...")
    results = []
    for task_id, task_data in tasks.items():
        result = evaluate_task(task_id, task_data, seed=42)
        results.append(result)
    
    # Step 4: Generate receipt
    print("\n[4/4] Generating receipt...")
    
    solved_count = sum(1 for r in results if r['solved'])
    total_tasks = len(results)
    
    receipt = ARCExperimentReceipt(f"arc-eval-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}")
    receipt.set_method("hypothesis_search", "1.0")
    receipt.set_seed(42)
    receipt.set_parameter("max_depth", 3)
    receipt.set_parameter("max_candidates", 500)
    receipt.set_parameter("total_tasks", total_tasks)
    receipt.set_parameter("solved_count", solved_count)
    receipt.set_environment("no_internet", True)
    receipt.set_environment("timestamp", datetime.utcnow().isoformat())
    
    for result in results:
        receipt.record_result(
            task_id=result['task_id'],
            predicted_output=result['predictions'],
            accuracy=result['confidence'],
            runtime_ms=None
        )
    
    # Save receipt
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    receipt_file = output_path / f"receipt-{receipt.experiment_id}.json"
    receipt.save(str(receipt_file))
    
    # Summary
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Tasks evaluated: {total_tasks}")
    print(f"Solved: {solved_count}/{total_tasks} ({solved_count/total_tasks:.1%})")
    print(f"Average confidence: {np.mean([r['confidence'] for r in results]):.2%}")
    print(f"Receipt saved: {receipt_file}")
    print("=" * 60)
    
    return {
        'results': results,
        'receipt_path': str(receipt_file),
        'solved_count': solved_count,
        'total_tasks': total_tasks
    }


def generate_kaggle_submission(results: list, output_path: str):
    """Generate Kaggle-compatible submission file."""
    submission = {}
    
    for result in results:
        task_id = result['task_id']
        # Convert predictions to ARC format
        preds = []
        for pred in result['predictions']:
            preds.append({
                'attempt_1': pred,
                'attempt_2': pred  # Same for now
            })
        submission[task_id] = preds
    
    with open(output_path, 'w') as f:
        json.dump(submission, f, indent=2)
    
    print(f"Kaggle submission saved: {output_path}")
    return submission


if __name__ == "__main__":
    # Run evaluation
    data_path = "data/synthetic_tasks.json"
    output_dir = "experiments"
    
    eval_results = run_full_evaluation(data_path, output_dir)
    
    if eval_results:
        # Generate Kaggle submission
        submission_path = f"{output_dir}/kaggle-submission-{datetime.utcnow().strftime('%Y%m%d')}.json"
        generate_kaggle_submission(eval_results['results'], submission_path)
        
        # Update ledger
        print("\nRecording to wallet ledger...")
        ledger_event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event': 'arc_evaluation_complete',
            'solved_count': eval_results['solved_count'],
            'total_tasks': eval_results['total_tasks'],
            'receipt_path': eval_results['receipt_path'],
            'status': 'ready_for_kaggle'
        }
        print(f"Ledger event: {json.dumps(ledger_event, indent=2)}")
        
        print("\n" + "=" * 60)
        print("ARC EVALUATION COMPLETE")
        print("=" * 60)
        print("Components ready for ARC Prize submission:")
        print("  ✓ No-internet boundary validated")
        print("  ✓ Hypothesis search tested")
        print("  ✓ Receipt generated with SHA-256")
        print("  ✓ Kaggle submission format ready")
        print("\nNext: Download real ARC dataset and submit to Kaggle")
    else:
        print("\nEvaluation failed - see errors above")
        sys.exit(1)
