"""
Agent Controller - Manages agent state (sleeping, waking, processing)
"""

import subprocess
import time
import json
from enum import Enum
from typing import Dict, Any
from datetime import datetime
from pathlib import Path

class AgentState(Enum):
    SLEEPING = "sleeping"
    WAKING = "waking"
    AWAKE = "awake"
    PROCESSING = "processing"
    IDLE_CHECK = "idle_check"

class AgentController:
    def __init__(self, agent_name: str, agent_type: str, container_name: str = None):
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.container_name = container_name or agent_name
        self.state = AgentState.SLEEPING
        self.idle_timer = None
        self.state_log = []
        self.metrics = {
            "wake_count": 0,
            "sleep_count": 0,
            "jobs_processed": 0,
            "total_processing_time": 0,
        }
    
    def log_state(self, new_state: AgentState, details: str = ""):
        """Log state transition"""
        transition = {
            "timestamp": datetime.utcnow().isoformat(),
            "from_state": self.state.value,
            "to_state": new_state.value,
            "details": details
        }
        self.state_log.append(transition)
        self.state = new_state
        print(f"[{self.agent_name}] {self.state.value.upper()} - {details}")
    
    def wake(self):
        """Wake agent from sleep"""
        print(f"\n[WAKE] {self.agent_name}...")
        self.log_state(AgentState.WAKING, "Initializing container")
        
        try:
            # Docker: start container
            result = subprocess.run(
                ["docker", "start", self.container_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise Exception(f"Failed to start container: {result.stderr}")
            
            # Wait for container to be ready
            time.sleep(2)
            
            # Health check
            health_result = subprocess.run(
                ["docker", "exec", self.container_name, "curl", "-s", "http://localhost:5000/health"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if health_result.returncode != 0:
                raise Exception(f"Health check failed: {health_result.stderr}")
            
            self.log_state(AgentState.AWAKE, "Ready to process jobs")
            self.idle_timer = time.time()
            self.metrics["wake_count"] += 1
            
            print(f"[OK] {self.agent_name} awake and ready")
            return True
            
        except Exception as e:
            self.log_state(AgentState.SLEEPING, f"Wake failed: {str(e)}")
            return False
    
    def sleep(self):
        """Return agent to sleep"""
        print(f"\n[SLEEP] {self.agent_name}...")
        self.log_state(AgentState.SLEEPING, "Stopping container")
        
        try:
            subprocess.run(
                ["docker", "stop", self.container_name],
                capture_output=True,
                timeout=10
            )
            self.metrics["sleep_count"] += 1
            print(f"[OK] {self.agent_name} asleep (0 memory)")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to stop container: {str(e)}")
            return False
    
    def process_job(self, job_payload: Dict[str, Any]) -> Dict:
        """Process a job"""
        if self.state != AgentState.AWAKE:
            return {"error": f"Agent not awake (state: {self.state.value})"}
        
        self.log_state(AgentState.PROCESSING, f"Processing job")
        
        start_time = time.time()
        
        try:
            # Post job to agent
            import requests
            response = requests.post(
                f"http://localhost:5000/dreams/log",
                json=job_payload,
                timeout=30
            )
            
            if response.status_code not in [200, 201]:
                raise Exception(f"Agent returned {response.status_code}")
            
            result = response.json()
            elapsed = time.time() - start_time
            
            self.metrics["jobs_processed"] += 1
            self.metrics["total_processing_time"] += elapsed
            
            self.log_state(AgentState.AWAKE, f"Job completed in {elapsed:.2f}s")
            self.idle_timer = time.time()
            
            return {"success": True, "result": result, "elapsed_ms": int(elapsed * 1000)}
            
        except Exception as e:
            self.log_state(AgentState.AWAKE, f"Job failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def check_idle(self, timeout_seconds: int = 120):
        """Auto-sleep if idle too long"""
        if self.state == AgentState.AWAKE and self.idle_timer:
            elapsed = time.time() - self.idle_timer
            if elapsed > timeout_seconds:
                print(f"\n[IDLE] {self.agent_name} idle for {elapsed:.0f}s, sleeping...")
                self.sleep()
    
    def get_stats(self) -> Dict:
        """Get agent statistics"""
        return {
            "agent_name": self.agent_name,
            "agent_type": self.agent_type,
            "state": self.state.value,
            "metrics": self.metrics,
            "avg_processing_time_ms": (
                self.metrics["total_processing_time"] / self.metrics["jobs_processed"] * 1000
                if self.metrics["jobs_processed"] > 0 else 0
            )
        }

if __name__ == "__main__":
    # Test
    controller = AgentController(
        agent_name="dream_journal",
        agent_type="dream_journal",
        container_name="lantern-dream-journal"
    )
    
    print("Testing Agent Controller...")
    print(f"Initial state: {controller.state.value}")
    
    # Wake
    if controller.wake():
        print(f"State after wake: {controller.state.value}")
        
        # Process a job
        job = {
            "content": "POC test dream",
            "lucidity": 0.8,
            "emotions": ["test"],
            "tags": ["poc"]
        }
        result = controller.process_job(job)
        print(f"Job result: {json.dumps(result, indent=2)}")
        
        # Sleep
        controller.sleep()
        print(f"State after sleep: {controller.state.value}")
    
    print(f"\nFinal stats:\n{json.dumps(controller.get_stats(), indent=2)}")
