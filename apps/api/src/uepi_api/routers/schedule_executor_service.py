"""
Background Schedule Executor Service
Runs scheduled jobs periodically
"""
import time
import threading
from typing import Optional

# Global executor thread
_executor_thread: Optional[threading.Thread] = None
_running = False


def start_schedule_executor(interval_seconds: int = 60):
    """
    Start the schedule executor in a background thread
    
    Args:
        interval_seconds: How often to check for due schedules (default: 60 seconds)
    """
    global _executor_thread, _running
    
    if _running:
        print("Schedule executor is already running")
        return
    
    _running = True
    
    def executor_loop():
        from uepi_api.routers.schedule_executor import run_schedule_executor
        
        print(f"Schedule executor started (checking every {interval_seconds} seconds)")
        
        while _running:
            try:
                results = run_schedule_executor()
                if results:
                    print(f"Executed {len(results)} scheduled jobs")
                    for result in results:
                        if result.get("success"):
                            print(f"  ✓ Schedule {result.get('schedule_id')} executed successfully")
                        else:
                            print(f"  ✗ Schedule {result.get('schedule_id')} failed: {result.get('error')}")
            except Exception as e:
                print(f"Error in schedule executor loop: {e}")
                import traceback
                traceback.print_exc()
            
            # Sleep until next check
            for _ in range(interval_seconds):
                if not _running:
                    break
                time.sleep(1)
        
        print("Schedule executor stopped")
    
    _executor_thread = threading.Thread(target=executor_loop, daemon=True)
    _executor_thread.start()
    print("Schedule executor thread started")


def stop_schedule_executor():
    """Stop the schedule executor"""
    global _running
    _running = False
    print("Schedule executor stop requested")


def is_running() -> bool:
    """Check if schedule executor is running"""
    return _running
