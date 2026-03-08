"""Comprehensive QA Testing Framework for Role-Based Testing"""
import json
import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import UUID

# Get project root
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent

# Add paths
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "packages" / "common" / "src"))

# Set PYTHONPATH
os.environ['PYTHONPATH'] = f"{PROJECT_ROOT / 'apps' / 'api' / 'src'}:{PROJECT_ROOT / 'packages' / 'common' / 'src'}"

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    # Fallback: create simple mock token
    def jwt_encode(payload, key, algorithm):
        return f"mock-token-{payload.get('email', 'user')}"

import httpx
from uepi_api.storage_file import BASE_PATH

# API Base URL
API_BASE_URL = "http://localhost:8000/api/v1"

# QA Test Users
QA_USERS = {
    "ROLE_PAYER_CMO": {
        "email": "qa.payer.cmo@test.com",
        "user_id": "10000000-0000-0000-0000-000000000001",
        "roles": ["EXEC_VIEWER", "STRATEGY"],
    },
    "ROLE_PROVIDER_CFO": {
        "email": "qa.provider.cfo@test.com",
        "user_id": "10000000-0000-0000-0000-000000000002",
        "roles": ["EXEC_VIEWER"],
    },
    "ROLE_PAYER_UM_LEAD": {
        "email": "qa.payer.um.lead@test.com",
        "user_id": "10000000-0000-0000-0000-000000000003",
        "roles": ["UM_LEADER"],
    },
    "ROLE_PAYER_ACTUARY": {
        "email": "qa.payer.actuary@test.com",
        "user_id": "10000000-0000-0000-0000-000000000004",
        "roles": ["ACTUARIAL"],
    },
    "ROLE_PAYER_NETWORK_STRATEGY": {
        "email": "qa.payer.network.strategy@test.com",
        "user_id": "10000000-0000-0000-0000-000000000005",
        "roles": ["STRATEGY"],
    },
    "ROLE_PAYER_ANALYTICS": {
        "email": "qa.payer.analytics@test.com",
        "user_id": "10000000-0000-0000-0000-000000000006",
        "roles": ["ACTUARIAL", "STRATEGY"],
    },
    "ROLE_READ_ONLY_EXEC": {
        "email": "qa.readonly.exec@test.com",
        "user_id": "10000000-0000-0000-0000-000000000007",
        "roles": ["EXEC_VIEWER"],
    },
}

# Test Results Storage
TEST_RESULTS_DIR = BASE_PATH / "qa_test_results"
TEST_RESULTS_DIR.mkdir(parents=True, exist_ok=True)


class QATestResult:
    """Test result container"""
    def __init__(self, test_name: str, role: str):
        self.test_name = test_name
        self.role = role
        self.passed = False
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.console_errors: List[str] = []
        self.response_data: Optional[Dict] = None
        self.status_code: Optional[int] = None
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_name": self.test_name,
            "role": self.role,
            "passed": self.passed,
            "errors": self.errors,
            "warnings": self.warnings,
            "console_errors": self.console_errors,
            "status_code": self.status_code,
            "timestamp": self.timestamp,
        }


class QATestAgent:
    """QA Test Agent for a specific role"""
    
    def __init__(self, role_name: str, user_config: Dict[str, Any]):
        self.role_name = role_name
        self.user_config = user_config
        self.user_id = user_config["user_id"]
        self.email = user_config["email"]
        self.roles = user_config["roles"]
        self.results: List[QATestResult] = []
        # Create a mock JWT token with user email for proper authentication
        if JWT_AVAILABLE:
            mock_token = jwt.encode(
                {
                    "email": self.email,
                    "sub": self.user_id,
                    "roles": self.roles,
                    "iss": "qa-test-issuer",
                },
                "dev-secret",
                algorithm="HS256"
            )
        else:
            # Fallback mock token
            mock_token = f"mock-token-{self.email}"
        
        self.client = httpx.AsyncClient(
            base_url=API_BASE_URL,
            timeout=30.0,
            headers={"Authorization": f"Bearer {mock_token}"}
        )
    
    async def test_endpoint(
        self,
        method: str,
        endpoint: str,
        test_name: str,
        expected_status: int = 200,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> QATestResult:
        """Test an API endpoint"""
        result = QATestResult(test_name, self.role_name)
        
        try:
            if method.upper() == "GET":
                response = await self.client.get(endpoint, params=params)
            elif method.upper() == "POST":
                response = await self.client.post(endpoint, json=data, params=params)
            elif method.upper() == "PUT":
                response = await self.client.put(endpoint, json=data, params=params)
            elif method.upper() == "DELETE":
                response = await self.client.delete(endpoint, params=params)
            else:
                result.errors.append(f"Unsupported HTTP method: {method}")
                return result
            
            result.status_code = response.status_code
            
            try:
                result.response_data = response.json()
            except Exception:
                result.response_data = {"raw": response.text[:500]}
            
            if response.status_code == expected_status:
                result.passed = True
            else:
                result.errors.append(
                    f"Expected status {expected_status}, got {response.status_code}. "
                    f"Response: {response.text[:200]}"
                )
                
                # Check for permission errors
                if response.status_code == 403:
                    result.errors.append("Permission denied - role may not have access to this resource")
                elif response.status_code == 404:
                    result.errors.append("Resource not found")
                elif response.status_code == 500:
                    result.errors.append("Internal server error - check server logs")
        
        except httpx.TimeoutException:
            result.errors.append("Request timeout - API server may be slow or unresponsive")
        except httpx.ConnectError:
            result.errors.append("Connection error - API server may not be running")
        except Exception as e:
            result.errors.append(f"Unexpected error: {str(e)}")
        
        self.results.append(result)
        return result
    
    async def test_dashboard_access(self) -> QATestResult:
        """Test dashboard access"""
        return await self.test_endpoint(
            "GET",
            "/dashboard/summary",
            "Dashboard Access",
            expected_status=200
        )
    
    async def test_policy_list(self) -> QATestResult:
        """Test policy listing"""
        return await self.test_endpoint(
            "GET",
            "/policies",
            "List Policies",
            expected_status=200,
            params={"limit": 10}
        )
    
    async def test_policy_create(self) -> QATestResult:
        """Test policy creation (if role has permission)"""
        test_policy = {
            "name": f"QA Test Policy - {self.role_name}",
            "description": "Test policy created by QA agent",
            "policy_type": "PRIOR_AUTH",  # Use underscore format for enum
            "status": "DRAFT",
        }
        
        expected_status = 201 if "UM_LEADER" in self.roles or "POLICY_ADMIN" in self.roles else 403
        return await self.test_endpoint(
            "POST",
            "/policies",
            "Create Policy",
            expected_status=expected_status,
            data=test_policy
        )
    
    async def test_analyses_access(self) -> QATestResult:
        """Test analyses access"""
        return await self.test_endpoint(
            "GET",
            "/analyses",
            "List Analyses",
            expected_status=200,
            params={"limit": 10}
        )
    
    async def test_decisions_access(self) -> QATestResult:
        """Test decisions access"""
        return await self.test_endpoint(
            "GET",
            "/decisions",
            "List Decisions",
            expected_status=200,
            params={"limit": 10}
        )
    
    async def test_conversational_ai_access(self) -> QATestResult:
        """Test conversational AI access"""
        return await self.test_endpoint(
            "GET",
            "/conversational-ai/conversations",
            "Conversational AI Access",
            expected_status=200
        )
    
    async def test_conversational_ai_create(self) -> QATestResult:
        """Test creating a conversation"""
        conversation_data = {
            "mode": "DRAFT",
            "domain": "POLICY",
            "title": f"QA Test Conversation - {self.role_name}"
        }
        return await self.test_endpoint(
            "POST",
            "/conversational-ai/conversations",
            "Create Conversation",
            expected_status=201,
            data=conversation_data
        )
    
    async def test_user_info(self) -> QATestResult:
        """Test getting current user info"""
        return await self.test_endpoint(
            "GET",
            "/auth/me",
            "Get User Info",
            expected_status=200
        )
    
    async def test_permissions(self) -> QATestResult:
        """Test permission checking"""
        return await self.test_endpoint(
            "GET",
            "/access/check-permission",
            "Check Permissions",
            expected_status=200,
            params={"resource": "policies", "action": "read"}
        )
    
    async def run_all_tests(self) -> List[QATestResult]:
        """Run all tests for this role"""
        print(f"\n{'='*70}")
        print(f"Testing Role: {self.role_name}")
        print(f"User: {self.email}")
        print(f"Roles: {', '.join(self.roles)}")
        print(f"{'='*70}\n")
        
        # Run all tests
        await self.test_user_info()
        await self.test_dashboard_access()
        await self.test_policy_list()
        await self.test_policy_create()
        await self.test_analyses_access()
        await self.test_decisions_access()
        await self.test_conversational_ai_access()
        await self.test_conversational_ai_create()
        await self.test_permissions()
        
        return self.results
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


async def run_qa_tests():
    """Run QA tests for all roles"""
    print("=" * 70)
    print("QA Testing Framework - Role-Based Testing")
    print("=" * 70)
    print()
    print("Testing all roles from user perspective...")
    print()
    
    all_results: Dict[str, List[QATestResult]] = {}
    agents: List[QATestAgent] = []
    
    # Create agents for each role
    for role_name, user_config in QA_USERS.items():
        agent = QATestAgent(role_name, user_config)
        agents.append(agent)
    
    # Run tests for each agent
    for agent in agents:
        try:
            results = await agent.run_all_tests()
            all_results[agent.role_name] = results
            
            # Print summary
            passed = sum(1 for r in results if r.passed)
            total = len(results)
            print(f"\n{agent.role_name}: {passed}/{total} tests passed\n")
        except Exception as e:
            print(f"❌ Error testing {agent.role_name}: {e}\n")
        finally:
            await agent.close()
    
    # Generate report
    generate_report(all_results)
    
    return all_results


def generate_report(all_results: Dict[str, List[QATestResult]]):
    """Generate comprehensive QA report"""
    report_file = TEST_RESULTS_DIR / f"qa_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Calculate statistics
    total_tests = sum(len(results) for results in all_results.values())
    total_passed = sum(sum(1 for r in results if r.passed) for results in all_results.values())
    total_failed = total_tests - total_passed
    
    # Collect all errors
    all_errors: List[Dict[str, Any]] = []
    all_warnings: List[Dict[str, Any]] = []
    
    for role_name, results in all_results.items():
        for result in results:
            if not result.passed:
                all_errors.append({
                    "role": role_name,
                    "test": result.test_name,
                    "errors": result.errors,
                    "status_code": result.status_code,
                })
            if result.warnings:
                all_warnings.append({
                    "role": role_name,
                    "test": result.test_name,
                    "warnings": result.warnings,
                })
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_tests": total_tests,
            "passed": total_passed,
            "failed": total_failed,
            "pass_rate": f"{(total_passed/total_tests*100):.1f}%" if total_tests > 0 else "0%",
        },
        "by_role": {
            role_name: {
                "total": len(results),
                "passed": sum(1 for r in results if r.passed),
                "failed": sum(1 for r in results if not r.passed),
            }
            for role_name, results in all_results.items()
        },
        "errors": all_errors,
        "warnings": all_warnings,
        "detailed_results": {
            role_name: [r.to_dict() for r in results]
            for role_name, results in all_results.items()
        },
    }
    
    # Save report
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 70)
    print("QA TEST REPORT SUMMARY")
    print("=" * 70)
    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Pass Rate: {report['summary']['pass_rate']}")
    print(f"\nReport saved to: {report_file}")
    print("\n" + "=" * 70)
    
    # Print errors by role
    if all_errors:
        print("\n❌ ERRORS BY ROLE:")
        print("-" * 70)
        for role_name, results in all_results.items():
            role_errors = [r for r in results if not r.passed]
            if role_errors:
                print(f"\n{role_name}:")
                for result in role_errors:
                    print(f"  • {result.test_name}: {', '.join(result.errors)}")
    
    return report


if __name__ == "__main__":
    asyncio.run(run_qa_tests())

