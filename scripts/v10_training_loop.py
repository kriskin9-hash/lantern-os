#!/usr/bin/env python3
"""
Σ₀ V10 Continuous Training Loop

Daemon that continuously:
1. Collects new YouTube Shorts
2. Extracts features
3. Retrains XGBoost model
4. Saves versioned checkpoints

Run with:
    python scripts/v10_training_loop.py --interval 6 (hours)
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict
import logging
import subprocess

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class ContinuousTrainingLoop:
    """Orchestrate data collection + feature extraction + model training."""

    def __init__(self, interval_hours: int = 6, dry_run: bool = False):
        self.interval_hours = interval_hours
        self.interval_seconds = interval_hours * 3600
        self.dry_run = dry_run

        # Directories
        self.data_dir = Path("data/youtube")
        self.model_dir = Path("models")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.model_dir.mkdir(parents=True, exist_ok=True)

        # Checkpoints
        self.checkpoint_dir = self.model_dir / "v10"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        self.log_file = self.checkpoint_dir / "training_log.jsonl"

    def log_event(self, event_type: str, status: str, details: Dict = None):
        """Log training event."""

        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'status': status,
            'details': details or {},
        }

        with open(self.log_file, 'a') as f:
            f.write(json.dumps(event) + '\n')

        logger.info(f"[{event_type}] {status}")

    def collect_data(self) -> bool:
        """Collect new YouTube Shorts."""

        logger.info("Starting data collection...")

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    'scripts/youtube_shorts_collector_v2.py',
                    '--limit', '5000',
                    '--use-mock',  # Use mock for now; set to False + provide API key for production
                ],
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes max
            )

            if result.returncode != 0:
                logger.error(f"Collection failed: {result.stderr}")
                self.log_event('collection', 'failed', {'error': result.stderr})
                return False

            self.log_event('collection', 'success')
            return True

        except Exception as e:
            logger.error(f"Collection error: {e}")
            self.log_event('collection', 'error', {'error': str(e)})
            return False

    def filter_gaming(self) -> bool:
        """Filter gaming subset."""

        logger.info("Filtering gaming shorts...")

        try:
            result = subprocess.run(
                [sys.executable, 'scripts/filter_gaming_shorts.py'],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                logger.error(f"Filtering failed: {result.stderr}")
                self.log_event('filtering', 'failed', {'error': result.stderr})
                return False

            self.log_event('filtering', 'success')
            return True

        except Exception as e:
            logger.error(f"Filtering error: {e}")
            self.log_event('filtering', 'error', {'error': str(e)})
            return False

    def extract_features(self) -> bool:
        """Extract Σ₀ features."""

        logger.info("Extracting features...")

        try:
            result = subprocess.run(
                [sys.executable, 'lib/v10_feature_extractor.py'],
                capture_output=True,
                text=True,
                timeout=600
            )

            if result.returncode != 0:
                logger.error(f"Feature extraction failed: {result.stderr}")
                self.log_event('feature_extraction', 'failed', {'error': result.stderr})
                return False

            self.log_event('feature_extraction', 'success')
            return True

        except Exception as e:
            logger.error(f"Feature extraction error: {e}")
            self.log_event('feature_extraction', 'error', {'error': str(e)})
            return False

    def train_model(self) -> bool:
        """Train XGBoost model."""

        logger.info("Training XGBoost model...")

        try:
            result = subprocess.run(
                [sys.executable, 'models/train_xgboost_v10.py'],
                capture_output=True,
                text=True,
                timeout=1200  # 20 minutes max
            )

            if result.returncode != 0:
                logger.error(f"Training failed: {result.stderr}")
                self.log_event('training', 'failed', {'error': result.stderr})
                return False

            # Version the model
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            versioned_model = self.checkpoint_dir / f"sigma0_v10_xgb_{timestamp}.json"

            source_model = Path('models/sigma0_v10_xgb.json')
            if source_model.exists():
                import shutil
                shutil.copy(source_model, versioned_model)
                logger.info(f"Versioned model: {versioned_model}")

            self.log_event('training', 'success', {
                'model_file': str(versioned_model)
            })
            return True

        except Exception as e:
            logger.error(f"Training error: {e}")
            self.log_event('training', 'error', {'error': str(e)})
            return False

    def run_iteration(self) -> bool:
        """Run one complete training cycle."""

        logger.info("=" * 60)
        logger.info("Starting training iteration")
        logger.info("=" * 60)

        if self.dry_run:
            logger.info("[DRY RUN] Skipping actual execution")
            self.log_event('iteration', 'dry_run')
            return True

        # Phase 1: Collect data
        if not self.collect_data():
            return False

        # Phase 1B: Filter gaming
        if not self.filter_gaming():
            return False

        # Phase 2: Extract features
        if not self.extract_features():
            return False

        # Phase 3: Train model
        if not self.train_model():
            return False

        logger.info("✅ Iteration complete")
        self.log_event('iteration', 'success')

        return True

    def run_daemon(self):
        """Run continuously."""

        logger.info(f"Starting continuous training loop (interval: {self.interval_hours}h)")

        iteration = 0
        while True:
            iteration += 1
            logger.info(f"\n[Iteration {iteration}] Starting at {datetime.utcnow()}")

            success = self.run_iteration()

            next_run = datetime.utcnow() + timedelta(hours=self.interval_hours)
            logger.info(f"Next iteration: {next_run}")
            logger.info(f"Sleeping for {self.interval_hours} hours...\n")

            try:
                time.sleep(self.interval_seconds)
            except KeyboardInterrupt:
                logger.info("\nShutdown signal received, exiting...")
                sys.exit(0)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Continuous training loop for Σ₀ V10 model"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=6,
        help="Training interval in hours (default: 6)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run: log but don't execute"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one iteration and exit"
    )

    args = parser.parse_args()

    loop = ContinuousTrainingLoop(interval_hours=args.interval, dry_run=args.dry_run)

    if args.once:
        logger.info("Running single iteration...")
        success = loop.run_iteration()
        sys.exit(0 if success else 1)
    else:
        loop.run_daemon()


if __name__ == "__main__":
    main()
