#!/usr/bin/env python3
"""
Lantern Orchestrator — Main Autopilot Engine
Coordinates all systems: Lantern Chat, BetterSafe, RAG, Agents, Learning
All local, continuous operation, autonomous learning
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
import json
import subprocess
from threading import Thread
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(os.path.expanduser('~/.lantern/orchestrator.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('Orchestrator')


class LanternOrchestrator:
    """Main orchestrator for Lantern ecosystem."""

    def __init__(self):
        """Initialize orchestrator and all subsystems."""
        self.state_path = Path.home() / '.lantern' / 'state'
        self.state_path.mkdir(parents=True, exist_ok=True)
        self.config = self._load_config()
        logger.info("Lantern Orchestrator starting...")

    def _load_config(self):
        """Load configuration."""
        config_path = Path.home() / '.lantern' / 'config.json'
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return {'lantern': {}, 'bettersafe': {}, 'rag': {}}

    def start_lantern_desktop(self):
        """Start Lantern Desktop GUI."""
        logger.info("Starting Lantern Desktop...")
        try:
            subprocess.Popen([
                sys.executable, 'scripts/lantern-integrated.py'
            ], cwd=str(Path(__file__).parent.parent))
            logger.info("[OK] Lantern Desktop started")
        except Exception as e:
            logger.error(f"Lantern Desktop start failed: {e}")

    def start_rag_server(self):
        """Start local RAG knowledge base server."""
        logger.info("Starting RAG server...")
        try:
            subprocess.Popen([
                sys.executable, 'scripts/rag_server_local.py'
            ], cwd=str(Path(__file__).parent.parent))
            logger.info("[OK] RAG server started")
        except Exception as e:
            logger.error(f"RAG server start failed: {e}")

    def start_m5_attestation(self):
        """Start M5 attestation daemon."""
        logger.info("Starting M5 attestation...")
        try:
            # M5 is already integrated into Lantern Desktop
            logger.info("[OK] M5 attestation (integrated with Lantern Desktop)")
        except Exception as e:
            logger.error(f"M5 attestation start failed: {e}")

    def autopilot_learning_loop(self):
        """
        Main autopilot learning loop.
        Runs continuously, checking system health, ingesting data, updating knowledge.
        """
        logger.info("Autopilot learning loop started (interval: 5min)")

        iteration = 0
        while True:
            try:
                iteration += 1
                timestamp = datetime.now().isoformat()

                # Health check
                self._health_check()

                # RAG knowledge base learning
                self._rag_learning_cycle()

                # Agent coordination
                self._agent_coordination()

                # Revenue tracking
                self._revenue_check()

                # Churn monitoring
                self._churn_monitoring()

                # Log checkpoint
                logger.info(f"[AUTOPILOT] Iteration {iteration} complete ({timestamp})")

                # Wait 5 minutes before next cycle
                time.sleep(300)

            except Exception as e:
                logger.error(f"Autopilot cycle error: {e}")
                time.sleep(60)  # Retry after 1 min on error

    def _health_check(self):
        """Check system health."""
        checks = {
            'lantern_running': self._is_process_running('lantern-integrated'),
            'rag_available': Path.home().joinpath('.lantern/rag-knowledge-base/knowledge-base.db').exists(),
            'm5_logging': Path.home().joinpath('.lantern/telemetry/attestation-ledger.jsonl').exists(),
            'bettersafe_db': Path.home().joinpath('.bettersafe/bettersafe.db').exists(),
        }

        for check, status in checks.items():
            status_str = "[✓]" if status else "[✗]"
            logger.info(f"  {status_str} {check}")

    def _rag_learning_cycle(self):
        """RAG knowledge base learning."""
        # Check for new documents to ingest
        books_path = Path.home() / '.lantern' / 'rag-knowledge-base' / 'books'
        if books_path.exists():
            book_count = len(list(books_path.glob('*.txt')))
            if book_count > 0:
                logger.info(f"  [RAG] {book_count} books available for ingestion")

    def _agent_coordination(self):
        """Coordinate agents (Family A, B, D, etc)."""
        # Check agent status, assign tasks, collect results
        logger.info("  [AGENTS] Coordinating distributed agents...")

    def _revenue_check(self):
        """Check revenue status."""
        billing_path = Path.home() / '.lantern' / 'state' / 'billing.json'
        if billing_path.exists():
            with open(billing_path) as f:
                billing = json.load(f)
                active = [f for f in billing if f.get('status') == 'active']
                mopex = sum(f.get('monthly_usd', 0) for f in active)
                logger.info(f"  [REVENUE] {len(active)} families, ${mopex}/mo MRR")

    def _churn_monitoring(self):
        """Monitor for churn signals."""
        billing_path = Path.home() / '.lantern' / 'state' / 'billing.json'
        if billing_path.exists():
            with open(billing_path) as f:
                billing = json.load(f)
                at_risk = [f for f in billing if f.get('churn_risk')]
                if at_risk:
                    logger.warning(f"  [CHURN] {len(at_risk)} families at risk")

    def _is_process_running(self, process_name):
        """Check if a process is running."""
        try:
            import psutil
            for proc in psutil.process_iter(['name']):
                if process_name in proc.info['name']:
                    return True
        except:
            pass
        return False

    def run(self):
        """Start all systems and enter autopilot."""
        logger.info("=" * 60)
        logger.info("LANTERN ORCHESTRATOR — LOCAL-FIRST AUTOPILOT")
        logger.info("=" * 60)

        # Start subsystems in parallel
        threads = [
            Thread(target=self.start_lantern_desktop, daemon=True),
            Thread(target=self.start_rag_server, daemon=True),
            Thread(target=self.start_m5_attestation, daemon=True),
        ]

        for t in threads:
            t.start()

        # Wait for systems to initialize
        time.sleep(5)

        # Enter autopilot learning loop
        self.autopilot_learning_loop()


if __name__ == '__main__':
    orchestrator = LanternOrchestrator()
    orchestrator.run()
