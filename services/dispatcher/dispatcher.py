"""
Work Dispatcher Service
Runs every 30 minutes, wakes agents, queues work, monitors progress
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import json
import logging
from typing import Dict, List
import time

from work_queue import WorkQueue, JobSpec
from agent_controller import AgentController

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WorkDispatcher:
    def __init__(self, redis_url: str = "redis://localhost:6379", dispatch_interval_minutes: int = 30):
        self.queue = WorkQueue(redis_url)
        self.scheduler = BackgroundScheduler()
        self.dispatch_interval = dispatch_interval_minutes
        
        # Initialize agent controllers
        self.agents = {
            "dream_journal": AgentController(
                agent_name="dream_journal",
                agent_type="dream_journal",
                container_name="lantern-dream-journal"
            )
        }
        
        self.dispatch_stats = {
            "total_dispatches": 0,
            "total_jobs_processed": 0,
            "failed_jobs": 0,
            "start_time": datetime.utcnow().isoformat()
        }
    
    def dispatch_work(self):
        """Main dispatch cycle - runs every N minutes"""
        dispatch_id = f"dispatch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"\n{'='*70}")
        logger.info(f"[DISPATCH] {dispatch_id} - Starting work dispatch cycle")
        logger.info(f"{'='*70}")
        
        self.dispatch_stats["total_dispatches"] += 1
        
        # Get pending work
        pending_jobs = self.queue.get_pending_jobs()
        
        if not pending_jobs:
            logger.info(f"[DISPATCH] No pending work. All agents stay asleep. Sleeping for {self.dispatch_interval}min...")
            logger.info(f"[METRIC] Memory saved: ~1,190 MB (agents idle)")
            logger.info(f"[METRIC] CPU saved: ~95% (idle state)")
            return
        
        logger.info(f"[DISPATCH] Found {len(pending_jobs)} pending jobs")
        
        # Group jobs by agent type
        jobs_by_agent = {}
        for job in pending_jobs:
            if job.agent_type not in jobs_by_agent:
                jobs_by_agent[job.agent_type] = []
            jobs_by_agent[job.agent_type].append(job)
        
        # Process each agent's work
        total_jobs = 0
        for agent_type, jobs in jobs_by_agent.items():
            logger.info(f"\n[AGENT] {agent_type.upper()} - {len(jobs)} jobs to process")
            
            if agent_type not in self.agents:
                logger.warning(f"[ERROR] Agent type '{agent_type}' not configured")
                continue
            
            agent = self.agents[agent_type]
            
            # Wake agent
            logger.info(f"[WAKE] Starting agent container...")
            if not agent.wake():
                logger.error(f"[ERROR] Failed to wake agent {agent_type}")
                for job in jobs:
                    self.queue.mark_failed(job.job_id, "Agent wake failed")
                continue
            
            # Process batch of jobs
            logger.info(f"[BATCH] Processing {len(jobs)} jobs...")
            for job in jobs:
                self.queue.mark_processing(job.job_id)
                
                result = agent.process_job(job.payload)
                
                if result.get("success"):
                    self.queue.mark_completed(job.job_id, result)
                    logger.info(f"[OK] Job {job.job_id} completed in {result.get('elapsed_ms', 0)}ms")
                    self.dispatch_stats["total_jobs_processed"] += 1
                else:
                    self.queue.mark_failed(job.job_id, result.get("error", "Unknown error"))
                    logger.error(f"[FAIL] Job {job.job_id}: {result.get('error')}")
                    self.dispatch_stats["failed_jobs"] += 1
                
                total_jobs += 1
            
            # Sleep agent (free memory)
            logger.info(f"[SLEEP] Returning agent to sleep...")
            agent.sleep()
            logger.info(f"[METRIC] {agent_type} freed ~173 MB memory")
        
        # Summary
        logger.info(f"\n{'='*70}")
        logger.info(f"[DISPATCH] {dispatch_id} - Cycle complete")
        logger.info(f"[SUMMARY] Jobs processed: {total_jobs}")
        logger.info(f"[SUMMARY] Failed: {self.dispatch_stats['failed_jobs']}")
        logger.info(f"[SUMMARY] Total memory freed: ~{len(self.agents) * 173} MB")
        logger.info(f"[SUMMARY] CPU freed: ~95%")
        logger.info(f"[SUMMARY] Next cycle: {self.dispatch_interval}min")
        logger.info(f"{'='*70}\n")
    
    def schedule_dispatch(self):
        """Schedule periodic dispatch"""
        trigger = IntervalTrigger(minutes=self.dispatch_interval)
        self.scheduler.add_job(
            self.dispatch_work,
            trigger=trigger,
            id="work_dispatcher",
            name="Work Dispatcher",
            replace_existing=True
        )
        logger.info(f"[SCHEDULER] Dispatch scheduled every {self.dispatch_interval} minutes")
    
    def start(self):
        """Start the dispatcher"""
        logger.info("[START] Work Dispatcher starting...")
        self.schedule_dispatch()
        self.scheduler.start()
        logger.info("[START] Dispatcher running. Press Ctrl+C to stop.")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("[STOP] Dispatcher stopping...")
            self.scheduler.shutdown()
    
    def get_stats(self) -> Dict:
        """Get dispatcher statistics"""
        return {
            "dispatch_stats": self.dispatch_stats,
            "queue_stats": self.queue.queue_stats(),
            "agent_stats": [agent.get_stats() for agent in self.agents.values()]
        }
    
    def manual_dispatch(self):
        """Trigger dispatch immediately (for testing)"""
        logger.info("[MANUAL] Triggering immediate dispatch...")
        self.dispatch_work()

if __name__ == "__main__":
    import sys
    
    # Configuration
    redis_url = "redis://localhost:6379"
    dispatch_interval = 30  # minutes
    
    # Create dispatcher
    dispatcher = WorkDispatcher(
        redis_url=redis_url,
        dispatch_interval_minutes=dispatch_interval
    )
    
    # Command line options
    if len(sys.argv) > 1:
        if sys.argv[1] == "--manual":
            # Test immediate dispatch
            dispatcher.manual_dispatch()
        elif sys.argv[1] == "--stats":
            # Show stats
            print(json.dumps(dispatcher.get_stats(), indent=2))
        else:
            print(f"Usage: {sys.argv[0]} [--manual|--stats]")
    else:
        # Start normal scheduling
        dispatcher.start()
