"""
Agent Work Queue Backend
Manages pending jobs via Redis
"""

import redis
import json
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass, asdict

@dataclass
class JobSpec:
    job_id: str
    agent_type: str
    priority: int
    payload: Dict[str, Any]
    created_at: str
    status: str = "pending"  # pending, processing, completed, failed

class WorkQueue:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.queue_prefix = "queue"
        
    def enqueue_job(self, job: JobSpec) -> str:
        """Add job to queue"""
        job_dict = asdict(job)
        job_json = json.dumps(job_dict)
        
        # Add to pending queue
        self.redis_client.lpush(f"{self.queue_prefix}:pending", job_json)
        
        # Set job key for tracking
        self.redis_client.set(f"{self.queue_prefix}:job:{job.job_id}", job_json)
        
        return job.job_id
    
    def get_pending_jobs(self, agent_type: str = None, limit: int = 100) -> List[JobSpec]:
        """Pop and return pending jobs, optionally filtered by agent type"""
        jobs = []
        for _ in range(limit):
            job_json = self.redis_client.lpop(f"{self.queue_prefix}:pending")
            if job_json is None:
                break
            job_dict = json.loads(job_json)
            job = JobSpec(**job_dict)

            if agent_type is None or job.agent_type == agent_type:
                jobs.append(job)

        return jobs
    
    def get_job(self, job_id: str) -> JobSpec:
        """Get specific job"""
        job_json = self.redis_client.get(f"{self.queue_prefix}:job:{job_id}")
        if job_json:
            return JobSpec(**json.loads(job_json))
        return None
    
    def mark_processing(self, job_id: str):
        """Mark job as being processed"""
        job = self.get_job(job_id)
        job.status = "processing"
        job_json = json.dumps(asdict(job))
        self.redis_client.set(f"{self.queue_prefix}:job:{job_id}", job_json)
        self.redis_client.lpush(f"{self.queue_prefix}:processing", job_json)
    
    def mark_completed(self, job_id: str, result: Dict = None):
        """Mark job as completed"""
        job = self.get_job(job_id)
        job.status = "completed"
        job_dict = asdict(job)
        if result:
            job_dict["result"] = result
        
        job_json = json.dumps(job_dict)
        self.redis_client.set(f"{self.queue_prefix}:job:{job_id}", job_json)
        self.redis_client.lpush(f"{self.queue_prefix}:completed", job_json)
    
    def mark_failed(self, job_id: str, error: str):
        """Mark job as failed"""
        job = self.get_job(job_id)
        job.status = "failed"
        job_dict = asdict(job)
        job_dict["error"] = error
        
        job_json = json.dumps(job_dict)
        self.redis_client.set(f"{self.queue_prefix}:job:{job_id}", job_json)
        self.redis_client.lpush(f"{self.queue_prefix}:failed", job_json)
    
    def queue_stats(self) -> Dict:
        """Get queue statistics"""
        return {
            "pending": self.redis_client.llen(f"{self.queue_prefix}:pending"),
            "processing": self.redis_client.llen(f"{self.queue_prefix}:processing"),
            "completed": self.redis_client.llen(f"{self.queue_prefix}:completed"),
            "failed": self.redis_client.llen(f"{self.queue_prefix}:failed"),
        }

if __name__ == "__main__":
    # Test
    queue = WorkQueue()
    
    job = JobSpec(
        job_id="job_20260602_001",
        agent_type="dream_journal",
        priority=5,
        payload={
            "content": "Test dream",
            "lucidity": 0.7
        },
        created_at=datetime.utcnow().isoformat()
    )
    
    queue.enqueue_job(job)
    print(f"Enqueued: {job.job_id}")
    print(f"Stats: {queue.queue_stats()}")
