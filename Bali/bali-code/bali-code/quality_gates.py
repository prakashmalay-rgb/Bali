#!/usr/bin/env python3
"""
Quality Gates for M1/M2 Implementation
Prevents regression and ensures code quality
"""

import subprocess
import sys
import os
import asyncio
from pathlib import Path

class QualityGateChecker:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_dir = self.project_root / "easybali-backend"
        self.frontend_dir = self.project_root / "bali-frontend"
        
    def run_command(self, cmd, cwd=None):
        """Run command and return success status"""
        try:
            result = subprocess.run(
                cmd, shell=True, cwd=cwd or self.project_root,
                capture_output=True, text=True, timeout=300
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def check_python_syntax(self):
        """Check Python syntax in backend"""
        print("🔍 Checking Python syntax...")
        success, stdout, stderr = self.run_command(
            f"python -m py_compile {self.backend_dir}/app/**/*.py"
        )
        if not success:
            print(f"❌ Python syntax errors: {stderr}")
            return False
        print("✅ Python syntax OK")
        return True
    
    def check_imports(self):
        """Check that all imports work correctly"""
        print("🔍 Checking imports...")
        
        # Test critical imports
        test_imports = [
            "from app.services.promo_service import validate_promo_code, increment_promo_usage",
            "from app.services.payment_service import create_xendit_payment_with_distribution",
            "from app.routes.xendit_webhook import handle_xendit_webhook",
            "from app.routes.promo_admin import router as promo_router"
        ]
        
        for import_stmt in test_imports:
            try:
                success, stdout, stderr = self.run_command(
                    f'python -c "{import_stmt}"',
                    cwd=self.backend_dir
                )
                if not success:
                    print(f"❌ Import failed: {import_stmt}")
                    print(f"   Error: {stderr}")
                    return False
            except Exception as e:
                print(f"❌ Import exception: {import_stmt} - {e}")
                return False
        
        print("✅ All imports OK")
        return True
    
    def run_unit_tests(self):
        """Run unit tests"""
        print("🔍 Running unit tests...")
        
        # Run promo integration tests
        success, stdout, stderr = self.run_command(
            "python test_promo_integration.py -v",
            cwd=self.backend_dir
        )
        
        if not success:
            print(f"❌ Unit tests failed: {stderr}")
            return False
        
        print("✅ Unit tests passed")
        return True
    
    def check_docker_files(self):
        """Check Docker configuration"""
        print("🔍 Checking Docker configuration...")
        
        # Check if Dockerfiles exist
        backend_dockerfile = self.backend_dir / "Dockerfile"
        frontend_dockerfile = self.frontend_dir / "Dockerfile"
        
        if not backend_dockerfile.exists():
            print("❌ Backend Dockerfile missing")
            return False
        
        if not frontend_dockerfile.exists():
            print("❌ Frontend Dockerfile missing")
            return False
        
        # Check docker-compose files
        compose_prod = self.project_root / "docker-compose.yml"
        compose_staging = self.project_root / "docker-compose.staging.yml"
        
        if not compose_prod.exists():
            print("❌ Production docker-compose.yml missing")
            return False
        
        if not compose_staging.exists():
            print("❌ Staging docker-compose.staging.yml missing")
            return False
        
        print("✅ Docker configuration OK")
        return True
    
    def check_environment_files(self):
        """Check environment configuration"""
        print("🔍 Checking environment files...")
        
        env_files = [
            self.backend_dir / ".env",
            self.backend_dir / ".env.staging",
            self.frontend_dir / ".env",
            self.frontend_dir / ".env.staging"
        ]
        
        for env_file in env_files:
            if not env_file.exists():
                print(f"❌ Environment file missing: {env_file}")
                return False
        
        print("✅ Environment files OK")
        return True
    
    def check_database_models(self):
        """Check database model compatibility"""
        print("🔍 Checking database models...")
        
        try:
            success, stdout, stderr = self.run_command(
                'python -c "from app.models.order_summary import Order; print(\'Order model OK\')"',
                cwd=self.backend_dir
            )
            
            if not success:
                print(f"❌ Database model error: {stderr}")
                return False
            
            print("✅ Database models OK")
            return True
            
        except Exception as e:
            print(f"❌ Database model exception: {e}")
            return False
    
    def check_api_endpoints(self):
        """Check API endpoint structure"""
        print("🔍 Checking API endpoints...")
        
        required_endpoints = [
            "app/routes/promo_admin.py",
            "app/routes/health.py",
            "app/routes/xendit_webhook.py"
        ]
        
        for endpoint in required_endpoints:
            endpoint_path = self.backend_dir / endpoint
            if not endpoint_path.exists():
                print(f"❌ Required endpoint missing: {endpoint}")
                return False
        
        print("✅ API endpoints OK")
        return True
    
    def run_quality_gates(self):
        """Run all quality gates"""
        print("🚀 Running M1/M2 Quality Gates...")
        print("=" * 50)
        
        gates = [
            ("Python Syntax", self.check_python_syntax),
            ("Import Checks", self.check_imports),
            ("Unit Tests", self.run_unit_tests),
            ("Docker Configuration", self.check_docker_files),
            ("Environment Files", self.check_environment_files),
            ("Database Models", self.check_database_models),
            ("API Endpoints", self.check_api_endpoints)
        ]
        
        passed = 0
        total = len(gates)
        
        for gate_name, gate_func in gates:
            print(f"\n📋 {gate_name}")
            print("-" * 30)
            
            if gate_func():
                passed += 1
            else:
                print(f"❌ {gate_name} FAILED")
                return False
        
        print("\n" + "=" * 50)
        print(f"🎉 Quality Gates: {passed}/{total} passed")
        
        if passed == total:
            print("✅ All quality gates passed - Ready for deployment!")
            return True
        else:
            print("❌ Some quality gates failed - Fix issues before deployment")
            return False

def main():
    """Main entry point"""
    checker = QualityGateChecker()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--fix":
        print("🔧 Auto-fix mode not implemented yet")
        return
    
    success = checker.run_quality_gates()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
