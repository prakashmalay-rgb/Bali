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
        print("[CHECK] Checking Checking Python syntax...")
        import glob
        import py_compile
        
        backend_app_path = str(self.backend_dir / "app")
        python_files = glob.glob(f"{backend_app_path}/**/*.py", recursive=True)
        
        if not python_files:
            print("[WARNING] No Python files found to check")
            return True
            
        errors = []
        for py_file in python_files:
            try:
                py_compile.compile(py_file, doraise=True)
            except py_compile.PyCompileError as e:
                errors.append(str(e))
                print(f"[FAIL] Syntax error in {py_file}: {e}")
            except Exception as e:
                errors.append(f"Error checking {py_file}: {e}")
                
        if errors:
            print(f"[FAIL] Python syntax errors found: {len(errors)}")
            return False
            
        print(f"[PASS] Python syntax OK ({len(python_files)} files checked)")
        return True

    def check_linting(self):
        """Run static analysis (Sonar-like)"""
        print("[CHECK] Running static analysis (Linting)...")
        # Flake8 check for critical issues (E9, F)
        f_success, f_out, f_err = self.run_command(
            "flake8 app --count --select=E9,F63,F7,F82 --show-source --statistics",
            cwd=self.backend_dir
        )
        
        # Pylint check
        p_success, p_out, p_err = self.run_command(
            "pylint app --fail-under=5.0",
            cwd=self.backend_dir
        )
        
        if not f_success:
            print(f"[FAIL] Critical linting issues found by Flake8")
            return False
            
        print("[PASS] Static analysis OK (Sonar-like check passed)")
        return True
    
    def check_imports(self):
        """Check that all imports work correctly"""
        print("[CHECK] Checking imports...")
        
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
                    print(f"[FAIL] Import failed: {import_stmt}")
                    print(f"   Error: {stderr}")
                    return False
            except Exception as e:
                print(f"[FAIL] Import exception: {import_stmt} - {e}")
                return False
        
        print("[PASS] All imports OK")
        return True
    
    def run_unit_tests(self):
        """Run unit tests"""
        print("[CHECK] Running unit tests...")
        
        success, stdout, stderr = self.run_command(
            "python test_promo_integration.py -v",
            cwd=self.backend_dir
        )
        
        if not success:
            print(f"[FAIL] Unit tests failed: {stderr}")
            return False
        
        print("[PASS] Unit tests passed")
        return True
    
    def check_docker_files(self):
        """Check Docker configuration"""
        print("[CHECK] Checking Docker configuration...")
        
        backend_dockerfile = self.backend_dir / "Dockerfile"
        frontend_dockerfile = self.frontend_dir / "Dockerfile"
        
        if not backend_dockerfile.exists():
            print("[FAIL] Backend Dockerfile missing")
            return False
        
        if not frontend_dockerfile.exists():
            print("[FAIL] Frontend Dockerfile missing")
            return False
        
        print("[PASS] Docker configuration OK")
        return True
    
    def check_environment_files(self):
        """Check environment configuration"""
        print("[CHECK] Checking environment files...")
        
        env_files = [
            self.backend_dir / ".env",
            self.backend_dir / ".env.staging",
            self.frontend_dir / ".env",
            self.frontend_dir / ".env.staging"
        ]
        
        for env_file in env_files:
            if not env_file.exists():
                print(f"[FAIL] Environment file missing: {env_file}")
                return False
        
        print("[PASS] Environment files OK")
        return True
    
    def check_database_models(self):
        """Check database model compatibility"""
        print("[CHECK] Checking database models...")
        
        try:
            success, stdout, stderr = self.run_command(
                'python -c "from app.models.order_summary import Order; print(\'Order model OK\')"',
                cwd=self.backend_dir
            )
            
            if not success:
                print(f"[FAIL] Database model error: {stderr}")
                return False
            
            print("[PASS] Database models OK")
            return True
            
        except Exception as e:
            print(f"[FAIL] Database model exception: {e}")
            return False
    
    def check_api_endpoints(self):
        """Check API endpoint structure"""
        print("[CHECK] Checking API endpoints...")
        
        required_endpoints = [
            "app/routes/promo_admin.py",
            "app/routes/health.py",
            "app/routes/xendit_webhook.py"
        ]
        
        for endpoint in required_endpoints:
            endpoint_path = self.backend_dir / endpoint
            if not endpoint_path.exists():
                print(f"[FAIL] Required endpoint missing: {endpoint}")
                return False
        
        print("[PASS] API endpoints OK")
        return True
    
    def run_quality_gates(self):
        """Run all quality gates"""
        print("--- Running M1/M2 Quality Gates ---")
        print("=" * 50)
        
        gates = [
            ("Python Syntax", self.check_python_syntax),
            ("Sonar-like Linting", self.check_linting),
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
            print(f"\n[STEP] {gate_name}")
            print("-" * 30)
            
            if gate_func():
                passed += 1
            else:
                print(f"[FAIL] {gate_name} FAILED")
                return False
        
        print("\n" + "=" * 50)
        print(f"RESULTS: {passed}/{total} passed")
        
        if passed == total:
            print("[SUCCESS] All quality gates passed - Ready for deployment!")
            return True
        else:
            print("[ERROR] Some quality gates failed")
            return False

def main():
    """Main entry point"""
    checker = QualityGateChecker()
    success = checker.run_quality_gates()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
