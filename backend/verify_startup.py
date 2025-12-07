#!/usr/bin/env python3
"""
Agent47 Backend Startup Verification Script
Verifies all components are properly connected and configured
"""

import asyncio
import sys
import os
from pathlib import Path
import importlib.util
import subprocess
import json
from typing import Dict, List, Any

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

class StartupVerifier:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.success_count = 0
        self.total_checks = 0
        
    def log_issue(self, component: str, issue: str):
        """Log a critical issue"""
        self.issues.append(f"❌ {component}: {issue}")
        self.total_checks += 1
        
    def log_warning(self, component: str, warning: str):
        """Log a warning"""
        self.warnings.append(f"⚠️ {component}: {warning}")
        self.total_checks += 1
        
    def log_success(self, component: str, message: str):
        """Log a success"""
        print(f"✅ {component}: {message}")
        self.success_count += 1
        self.total_checks += 1
        
    def check_imports(self, module_path: str, imports: List[str]) -> bool:
        """Check if imports work correctly"""
        try:
            spec = importlib.util.find_spec(module_path)
            if spec is None:
                return False
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            for import_name in imports:
                if not hasattr(module, import_name):
                    return False
            return True
        except Exception:
            return False
            
    def check_file_exists(self, file_path: str) -> bool:
        """Check if file exists"""
        return Path(file_path).exists()
        
    def check_port_configuration(self) -> bool:
        """Check port configuration consistency"""
        try:
            from core.config import settings
            
            # Expected port mapping
            expected_ports = {
                'aria_port': 8001,
                'clara_port': 8002,
                'eric_port': 8003,
                'jackie_port': 8004,
                'joe_port': 8005,
                'purity_port': 8006,
                'shakes_port': 8007
            }
            
            all_correct = True
            for port_name, expected_port in expected_ports.items():
                actual_port = getattr(settings.agents, port_name, None)
                if actual_port != expected_port:
                    self.log_issue("Port Configuration", 
                                 f"{port_name} should be {expected_port}, got {actual_port}")
                    all_correct = False
                    
            if all_correct:
                self.log_success("Port Configuration", "All agent ports correctly configured")
                
            return all_correct
            
        except Exception as e:
            self.log_issue("Port Configuration", f"Failed to check ports: {e}")
            return False
            
    def check_core_modules(self) -> bool:
        """Check core module imports"""
        core_modules = [
            ('core.config', ['settings']),
            ('core.database', ['init_database', 'get_database']),
            ('core.cache', ['init_redis', 'get_redis']),
            ('core.event_bus', ['init_kafka', 'get_kafka']),
            ('core.storage', ['init_chroma', 'get_chroma']),
            ('core.ai', ['get_ai_service_manager']),
        ]
        
        all_success = True
        for module_name, imports in core_modules:
            if self.check_imports(module_name, imports):
                self.log_success("Core Modules", f"{module_name} imports correctly")
            else:
                self.log_issue("Core Modules", f"{module_name} import failed")
                all_success = False
                
        return all_success
        
    def check_agent_files(self) -> bool:
        """Check agent file structure and imports"""
        agents = ['aria', 'clara', 'eric', 'jackie', 'joe', 'purity', 'shakes']
        all_success = True
        
        for agent in agents:
            # Check main files exist
            main_file = f"agents/{agent}/app/main.py"
            run_file = f"agents/{agent}/run_{agent}.py"
            
            if not self.check_file_exists(main_file):
                self.log_issue("Agent Files", f"{agent} main.py missing")
                all_success = False
            else:
                self.log_success("Agent Files", f"{agent} main.py exists")
                
            if not self.check_file_exists(run_file):
                self.log_issue("Agent Files", f"{agent} run_{agent}.py missing")
                all_success = False
            else:
                self.log_success("Agent Files", f"{agent} run_{agent}.py exists")
                
        return all_success
        
    def check_agent_imports(self) -> bool:
        """Check agent import paths"""
        agents = ['aria', 'clara', 'eric', 'jackie', 'joe', 'purity', 'shakes']
        all_success = True
        
        for agent in agents:
            try:
                # Try to import agent main
                module_name = f"agents.{agent}.app.main"
                if self.check_imports(module_name, ['app']):
                    self.log_success("Agent Imports", f"{agent} main imports correctly")
                else:
                    self.log_issue("Agent Imports", f"{agent} main import failed")
                    all_success = False
                    
            except Exception as e:
                self.log_issue("Agent Imports", f"{agent} import error: {e}")
                all_success = False
                
        return all_success
        
    def check_docker_compose(self) -> bool:
        """Check Docker Compose configuration"""
        compose_file = "docker-compose.yml"
        if not self.check_file_exists(compose_file):
            self.log_issue("Docker Compose", "docker-compose.yml not found")
            return False
            
        try:
            with open(compose_file, 'r') as f:
                content = f.read()
                
            # Check for required services
            required_services = ['postgres', 'redis', 'kafka', 'chromadb', 'backend']
            agent_services = ['aria-agent', 'clara-agent', 'eric-agent', 'jackie-agent', 
                            'joe-agent', 'purity-agent', 'shakes-agent']
            
            all_services = required_services + agent_services
            
            for service in all_services:
                if service in content:
                    self.log_success("Docker Compose", f"{service} service configured")
                else:
                    self.log_issue("Docker Compose", f"{service} service missing")
                    return False
                    
            return True
            
        except Exception as e:
            self.log_issue("Docker Compose", f"Failed to read docker-compose.yml: {e}")
            return False
            
    def check_environment_config(self) -> bool:
        """Check environment configuration"""
        env_example = "env.example"
        if not self.check_file_exists(env_example):
            self.log_issue("Environment Config", "env.example not found")
            return False
            
        try:
            with open(env_example, 'r') as f:
                content = f.read()
                
            # Check for required configurations
            required_configs = [
                # 'CHUTES_API_KEY',  # Removed
                'DB_POSTGRES_HOST',
                'REDIS_HOST',
                'KAFKA_BOOTSTRAP_SERVERS',
                'CHROMA_HOST'
            ]
            
            for config in required_configs:
                if config in content:
                    self.log_success("Environment Config", f"{config} configured")
                else:
                    self.log_warning("Environment Config", f"{config} not found in env.example")
                    
            return True
            
        except Exception as e:
            self.log_issue("Environment Config", f"Failed to read env.example: {e}")
            return False
            
    def check_startup_scripts(self) -> bool:
        """Check startup scripts"""
        scripts = [
            'scripts/start.sh',
            'backend/start_server.py',
            'backend/main.py'
        ]
        
        all_success = True
        for script in scripts:
            if self.check_file_exists(script):
                self.log_success("Startup Scripts", f"{script} exists")
            else:
                self.log_issue("Startup Scripts", f"{script} missing")
                all_success = False
                
        return all_success
        
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all verification checks"""
        print("🔍 Starting Agent47 Backend Startup Verification...")
        print("=" * 60)
        
        checks = [
            ("Port Configuration", self.check_port_configuration),
            ("Core Modules", self.check_core_modules),
            ("Agent Files", self.check_agent_files),
            ("Agent Imports", self.check_agent_imports),
            ("Docker Compose", self.check_docker_compose),
            ("Environment Config", self.check_environment_config),
            ("Startup Scripts", self.check_startup_scripts),
        ]
        
        results = {}
        for check_name, check_func in checks:
            print(f"\n📋 Checking {check_name}...")
            try:
                results[check_name] = check_func()
            except Exception as e:
                self.log_issue(check_name, f"Check failed with exception: {e}")
                results[check_name] = False
                
        return results
        
    def print_summary(self, results: Dict[str, Any]):
        """Print verification summary"""
        print("\n" + "=" * 60)
        print("📊 VERIFICATION SUMMARY")
        print("=" * 60)
        
        # Print issues
        if self.issues:
            print(f"\n❌ CRITICAL ISSUES ({len(self.issues)}):")
            for issue in self.issues:
                print(f"   {issue}")
                
        # Print warnings
        if self.warnings:
            print(f"\n⚠️ WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   {warning}")
                
        # Print results
        print(f"\n📈 RESULTS:")
        print(f"   ✅ Successful checks: {self.success_count}/{self.total_checks}")
        print(f"   ❌ Critical issues: {len(self.issues)}")
        print(f"   ⚠️ Warnings: {len(self.warnings)}")
        
        # Overall status
        if self.issues:
            print(f"\n🚨 STATUS: FAILED - {len(self.issues)} critical issues must be fixed")
            return False
        elif self.warnings:
            print(f"\n⚠️ STATUS: WARNING - {len(self.warnings)} warnings (system may work)")
            return True
        else:
            print(f"\n🎉 STATUS: SUCCESS - All checks passed!")
            return True

def main():
    """Main verification function"""
    verifier = StartupVerifier()
    
    try:
        results = verifier.run_all_checks()
        success = verifier.print_summary(results)
        
        if success:
            print("\n🚀 System is ready to start!")
            print("\nNext steps:")
            print("1. Copy env.example to .env and configure your API keys")
            print("2. Run: ./scripts/start.sh")
            print("3. Or manually: docker-compose up -d")
        else:
            print("\n🛑 System has critical issues that must be fixed before starting")
            print("Please address the issues above and run verification again")
            
        return 0 if success else 1
        
    except Exception as e:
        print(f"\n❌ Verification failed with exception: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
