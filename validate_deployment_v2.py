#!/usr/bin/env python3
"""
Automated Validation Suite for Lantern Deployment v2
Tests actual available endpoints
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

class LanternValidator:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.results = []
        self.start_time = datetime.now()

    def log_result(self, test_name: str, status: str, details: str, response_data: Any = None):
        """Log validation result"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response": response_data if isinstance(response_data, (dict, list, str, int, float, bool, type(None))) else str(response_data)
        }
        self.results.append(result)
        print(f"[{status}] {test_name}: {details}")

    def test_root_page(self):
        """Test the root Lantern interface"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200 and "Lantern Browser" in response.text:
                self.log_result("Root Interface", "PASS", "Lantern Browser loads successfully")
            else:
                self.log_result("Root Interface", "FAIL", f"Status {response.status_code}, unexpected content")
        except Exception as e:
            self.log_result("Root Interface", "ERROR", str(e))

    def test_chat_api_get(self):
        """Test GET /api/chat endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/chat", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "Chat API (GET)",
                    "PASS",
                    f"Retrieved {len(data)} messages from chat history",
                    {"message_count": len(data), "type": type(data).__name__}
                )
            else:
                self.log_result("Chat API (GET)", "FAIL", f"Status {response.status_code}")
        except Exception as e:
            self.log_result("Chat API (GET)", "ERROR", str(e))

    def test_chat_api_post(self):
        """Test POST /api/chat endpoint"""
        try:
            payload = {
                "content": "Automated validation test message"
            }
            response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=5)
            if response.status_code == 200:
                self.log_result(
                    "Chat API (POST)",
                    "PASS",
                    "Message posted to chat successfully",
                    response.json() if response.text else {}
                )
            elif response.status_code == 201:
                self.log_result(
                    "Chat API (POST)",
                    "PASS",
                    "Message created (status 201)",
                    response.json() if response.text else {}
                )
            else:
                self.log_result("Chat API (POST)", "FAIL", f"Status {response.status_code}")
        except Exception as e:
            self.log_result("Chat API (POST)", "ERROR", str(e))

    def test_audio_api(self):
        """Test GET /api/audio endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/audio", timeout=5)
            if response.status_code == 200:
                data = response.json()
                audio_count = len(data) if isinstance(data, list) else 0
                self.log_result(
                    "Audio API",
                    "PASS",
                    f"Retrieved {audio_count} audio files",
                    {"file_count": audio_count}
                )
            else:
                self.log_result("Audio API", "FAIL", f"Status {response.status_code}")
        except Exception as e:
            self.log_result("Audio API", "ERROR", str(e))

    def test_response_times(self):
        """Test response latency for critical endpoints"""
        endpoints = [
            ("/", "Root"),
            ("/api/chat", "Chat API"),
            ("/api/audio", "Audio API")
        ]

        for path, name in endpoints:
            try:
                start = datetime.now()
                response = requests.get(f"{self.base_url}{path}", timeout=5)
                elapsed_ms = (datetime.now() - start).total_seconds() * 1000

                if response.status_code in [200, 201]:
                    status = "PASS" if elapsed_ms < 500 else "WARN"
                    self.log_result(
                        f"Response Time: {name}",
                        status,
                        f"{elapsed_ms:.1f}ms",
                        {"latency_ms": elapsed_ms}
                    )
                else:
                    self.log_result(f"Response Time: {name}", "FAIL", f"Status {response.status_code}")
            except Exception as e:
                self.log_result(f"Response Time: {name}", "ERROR", str(e))

    def test_availability(self):
        """Test service availability (5 sequential requests)"""
        successful = 0
        total = 5

        for i in range(total):
            try:
                response = requests.get(f"{self.base_url}/api/chat", timeout=2)
                if response.status_code == 200:
                    successful += 1
            except:
                pass

        availability = (successful / total) * 100
        status = "PASS" if availability == 100 else "WARN"
        self.log_result(
            "Availability (5 requests)",
            status,
            f"{successful}/{total} requests successful ({availability:.0f}%)",
            {"successful": successful, "total": total, "availability_percent": availability}
        )

    def generate_report(self) -> Dict:
        """Generate comprehensive validation report"""
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        failed = sum(1 for r in self.results if r['status'] == 'FAIL')
        errors = sum(1 for r in self.results if r['status'] == 'ERROR')
        warnings = sum(1 for r in self.results if r['status'] == 'WARN')

        report = {
            "deployment_validation_report_v2": {
                "timestamp": self.start_time.isoformat(),
                "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
                "summary": {
                    "total_tests": len(self.results),
                    "passed": passed,
                    "failed": failed,
                    "errors": errors,
                    "warnings": warnings,
                    "success_rate": f"{(passed / len(self.results) * 100) if self.results else 0:.1f}%"
                },
                "services_validated": [
                    "Lantern Flask App (port 5000)",
                    "Browser Interface",
                    "Chat API",
                    "Audio Library API"
                ],
                "endpoints_tested": [
                    "GET /",
                    "GET /api/chat",
                    "POST /api/chat",
                    "GET /api/audio"
                ],
                "detailed_results": self.results,
                "conclusion": self._generate_conclusion()
            }
        }
        return report

    def _generate_conclusion(self) -> str:
        """Generate conclusion based on results"""
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        total = len(self.results)

        if passed == total:
            return "DEPLOYMENT VALIDATED: All tests passed. Lantern is fully operational."
        elif passed >= total * 0.9:
            return "DEPLOYMENT VALIDATED WITH WARNINGS: Core functionality operational, minor issues noted."
        elif passed >= total * 0.7:
            return "DEPLOYMENT PARTIAL: Core chat API working, some ancillary features need attention."
        else:
            return "DEPLOYMENT NEEDS ATTENTION: Critical functionality failing."

    def run_all_tests(self):
        """Execute all validation tests"""
        print("\n" + "="*70)
        print("LANTERN DEPLOYMENT VALIDATION v2")
        print("="*70 + "\n")

        self.test_root_page()
        self.test_chat_api_get()
        self.test_chat_api_post()
        self.test_audio_api()
        self.test_response_times()
        self.test_availability()

        report = self.generate_report()

        print("\n" + "="*70)
        print("VALIDATION REPORT")
        print("="*70)
        print(json.dumps(report, indent=2))

        return report

if __name__ == "__main__":
    validator = LanternValidator()
    report = validator.run_all_tests()

    # Save report to file for RAG ingestion
    report_path = "/tmp/lantern_validation_report_v2.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n[OK] Report saved to: {report_path}")

    # Exit with appropriate code
    passed = sum(1 for r in report['deployment_validation_report_v2']['detailed_results'] if r['status'] == 'PASS')
    total = len(report['deployment_validation_report_v2']['detailed_results'])
    sys.exit(0 if passed == total else 1)
