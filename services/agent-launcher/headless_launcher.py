"""
Headless Agent Launcher
Runs inside container - spawns agent instances without popups
"""

import subprocess
import sys
import json
from pathlib import Path
from typing import List, Dict, Any
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

class HeadlessAgentLauncher:
    """Launches agents inside container without UI/popups"""
    
    def __init__(self, config_path: str = "/app/config/agents.json"):
        self.config_path = Path(config_path)
        self.agents: List[Dict[str, Any]] = []
        self.processes: Dict[str, subprocess.Popen] = {}
    
    def load_agent_config(self) -> bool:
        """Load agent configuration"""
        if not self.config_path.exists():
            logger.error(f"Config not found: {self.config_path}")
            return False
        
        try:
            with open(self.config_path, 'r') as f:
                self.agents = json.load(f)
            logger.info(f"Loaded {len(self.agents)} agents from config")
            return True
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return False
    
    def spawn_agent_process(self, agent: Dict[str, Any]) -> bool:
        """Spawn agent as subprocess (no popup)"""
        agent_id = agent.get("id")
        agent_name = agent.get("name")
        agent_cmd = agent.get("command")
        agent_port = agent.get("port", 5000)
        
        if not agent_cmd:
            logger.warning(f"Agent {agent_name} has no command")
            return False
        
        try:
            # Replace placeholders
            cmd = agent_cmd.format(
                name=agent_name,
                port=agent_port,
                id=agent_id
            )
            
            logger.info(f"Spawning agent: {agent_name} (port {agent_port})")
            
            # Spawn process WITHOUT popup (creationflags)
            # For Windows: CREATE_NO_WINDOW = 0x08000000
            # For Unix: just use Popen normally
            
            creationflags = 0
            if sys.platform == "win32":
                creationflags = 0x08000000
            
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creationflags,
                preexec_fn=None if sys.platform == "win32" else lambda: None
            )
            
            self.processes[agent_id] = process
            logger.info(f"✓ Agent {agent_name} spawned (PID: {process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to spawn agent {agent_name}: {e}")
            return False
    
    def launch_all_agents(self) -> int:
        """Launch all configured agents"""
        if not self.load_agent_config():
            return 0
        
        logger.info(f"Launching {len(self.agents)} agents...")
        
        launched = 0
        for agent in self.agents:
            if self.spawn_agent_process(agent):
                launched += 1
                time.sleep(0.5)  # Small delay between spawns
        
        logger.info(f"Launched {launched}/{len(self.agents)} agents")
        return launched
    
    def monitor_agents(self):
        """Monitor agent processes and restart if crashed"""
        logger.info("Starting agent monitor...")
        
        while True:
            time.sleep(5)  # Check every 5 seconds
            
            for agent_id, process in list(self.processes.items()):
                if process.poll() is not None:  # Process exited
                    agent_name = next(
                        (a.get("name") for a in self.agents if a.get("id") == agent_id),
                        "Unknown"
                    )
                    logger.warning(f"Agent {agent_name} crashed (PID: {process.pid})")
                    
                    # Restart agent
                    agent_config = next(
                        (a for a in self.agents if a.get("id") == agent_id),
                        None
                    )
                    if agent_config:
                        logger.info(f"Restarting agent {agent_name}...")
                        if self.spawn_agent_process(agent_config):
                            logger.info(f"✓ Restarted {agent_name}")
    
    def shutdown_all(self):
        """Gracefully shutdown all agents"""
        logger.info("Shutting down agents...")
        
        for agent_id, process in self.processes.items():
            try:
                process.terminate()
                process.wait(timeout=5)
                logger.info(f"Terminated agent (PID: {process.pid})")
            except subprocess.TimeoutExpired:
                process.kill()
                logger.info(f"Killed agent (PID: {process.pid})")
    
    def run(self):
        """Main entry point - launch and monitor"""
        try:
            launched = self.launch_all_agents()
            
            if launched == 0:
                logger.error("No agents launched, exiting")
                return 1
            
            logger.info("All agents running, starting monitor...")
            self.monitor_agents()
            
        except KeyboardInterrupt:
            logger.info("Received interrupt, shutting down...")
            self.shutdown_all()
            return 0
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            self.shutdown_all()
            return 1

if __name__ == "__main__":
    launcher = HeadlessAgentLauncher()
    sys.exit(launcher.run())
