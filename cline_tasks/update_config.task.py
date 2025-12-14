#!/usr/bin/env python3
"""
Cline CLI task: update_config
This task demonstrates automated configuration updates based on incidents.
Can be invoked by Kestra or manually via: cline task update_config.task.py
"""
import os
import sys
import json
import copy
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration file."""
    # Return default config for demo
    return {
        "monitoring": {
            "check_interval": 60,
            "alert_threshold": 5,
            "enabled_detectors": ["error_rate", "latency", "availability"]
        },
        "repair": {
            "auto_fix_enabled": False,
            "max_attempts": 3,
            "require_review": True
        },
        "notifications": {
            "slack_webhook": "",
            "email_recipients": []
        }
    }


def analyze_config_issue(incident_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze what config changes are needed based on the incident.
    In production, this would use ML/heuristics to determine optimal settings.
    """
    return {
        "incident_id": incident_id,
        "issue_type": "threshold_tuning",
        "recommendations": [
            {
                "path": "monitoring.check_interval",
                "current_value": config.get("monitoring", {}).get("check_interval", 60),
                "suggested_value": 30,
                "reason": "Reduce check interval to detect issues faster"
            },
            {
                "path": "repair.auto_fix_enabled",
                "current_value": config.get("repair", {}).get("auto_fix_enabled", False),
                "suggested_value": True,
                "reason": "Enable auto-fix for faster incident resolution"
            },
            {
                "path": "monitoring.alert_threshold",
                "current_value": config.get("monitoring", {}).get("alert_threshold", 5),
                "suggested_value": 3,
                "reason": "Lower threshold to catch issues earlier"
            }
        ]
    }


def apply_config_updates(config: Dict[str, Any], recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Apply configuration updates based on recommendations."""
    updated_config = copy.deepcopy(config)
    changes = []
    
    for rec in recommendations:
        path_parts = rec["path"].split(".")
        
        # Navigate to the nested key
        current = updated_config
        for part in path_parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Update the value
        old_value = current.get(path_parts[-1])
        current[path_parts[-1]] = rec["suggested_value"]
        
        changes.append({
            "path": rec["path"],
            "old_value": old_value,
            "new_value": rec["suggested_value"],
            "reason": rec["reason"]
        })
    
    return {
        "config": updated_config,
        "changes": changes
    }


def create_config_diff(changes: List[Dict[str, Any]]) -> str:
    """Create a human-readable diff of configuration changes."""
    diff_lines = ["Configuration Changes:", "=" * 50]
    
    for change in changes:
        diff_lines.append(f"\n{change['path']}:")
        diff_lines.append(f"  - Old: {change['old_value']}")
        diff_lines.append(f"  + New: {change['new_value']}")
        diff_lines.append(f"  Reason: {change['reason']}")
    
    return "\n".join(diff_lines)


def run(context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Main entry point for programmatic invocation.
    Can be called by Kestra or other orchestration tools.
    """
    incident_id = (context or {}).get("incident_id", "placeholder-incident")
    config_path = (context or {}).get("config_path", "config.yaml")
    
    # Load current config
    current_config = load_config(config_path)
    
    # Analyze what needs to change
    analysis = analyze_config_issue(incident_id, current_config)
    
    # Apply updates
    update_result = apply_config_updates(current_config, analysis["recommendations"])
    
    # Generate diff
    diff = create_config_diff(update_result["changes"])
    
    return {
        "status": "completed",
        "message": "Config update analysis completed",
        "incident_id": incident_id,
        "config_path": config_path,
        "analysis": analysis,
        "changes": update_result["changes"],
        "diff": diff,
        "dry_run": True,
        "timestamp": datetime.utcnow().isoformat()
    }


def main():
    """Main entry point for CLI invocation."""
    if len(sys.argv) < 2:
        print("Usage: python update_config.task.py <incident_id> [config_path]")
        sys.exit(1)
    
    incident_id = sys.argv[1]
    config_path = sys.argv[2] if len(sys.argv) > 2 else "config.yaml"
    
    print(f"[update_config] Starting config update for incident: {incident_id}")
    
    result = run({"incident_id": incident_id, "config_path": config_path})
    
    print(f"\n[update_config] Found {len(result['changes'])} recommendations")
    print("\n" + result['diff'])
    print(f"\n[update_config] Config would be saved to {config_path} (dry run)")
    print("\n[update_config] Task completed successfully!")
    print(json.dumps(result, indent=2))
    
    return result


if __name__ == "__main__":
    main()
