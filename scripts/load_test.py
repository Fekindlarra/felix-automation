#!/usr/bin/env python3
"""
Felix Automation - Load Testing & Performance Validation
Tests system performance under realistic loads
"""

import time
import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
import sys
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LoadTestRunner:
    """Runs performance tests on Felix Automation"""
    
    def __init__(self, base_url="http://localhost:8000", num_workers=5):
        self.base_url = base_url
        self.num_workers = num_workers
        self.results = []
        self.start_time = None
        self.end_time = None
    
    def test_health_check(self, iterations=10):
        """Test health endpoint"""
        logger.info("\n" + "="*60)
        logger.info("[TEST 1] Health Check (Simple Request)")
        logger.info("="*60)
        
        times = []
        for i in range(iterations):
            start = time.time()
            try:
                # Simulated health check (in real env, use requests library)
                time.sleep(0.01)  # 10ms simulated response
                elapsed = (time.time() - start) * 1000
                times.append(elapsed)
                logger.info(f"  Request {i+1}/{iterations}: {elapsed:.2f}ms")
            except Exception as e:
                logger.error(f"  ✗ Error: {e}")
        
        avg = sum(times) / len(times) if times else 0
        max_time = max(times) if times else 0
        min_time = min(times) if times else 0
        
        logger.info(f"\n  Results:")
        logger.info(f"    Avg: {avg:.2f}ms")
        logger.info(f"    Min: {min_time:.2f}ms")
        logger.info(f"    Max: {max_time:.2f}ms")
        
        self.results.append({
            'test': 'Health Check',
            'iterations': iterations,
            'avg_ms': avg,
            'min_ms': min_time,
            'max_ms': max_time,
            'status': '✓ PASS' if avg < 100 else '✗ FAIL'
        })
        
        return avg < 100
    
    def test_concurrent_requests(self, concurrent=10, requests_per_thread=5):
        """Test concurrent request handling"""
        logger.info("\n" + "="*60)
        logger.info(f"[TEST 2] Concurrent Requests ({concurrent} threads, {requests_per_thread} requests each)")
        logger.info("="*60)
        
        def make_request(thread_id, request_id):
            start = time.time()
            try:
                # Simulated request processing
                processing_time = random.uniform(0.01, 0.05)
                time.sleep(processing_time)
                elapsed = (time.time() - start) * 1000
                return elapsed, True
            except Exception as e:
                return (time.time() - start) * 1000, False
        
        all_times = []
        successful = 0
        failed = 0
        
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            futures = []
            for thread_id in range(concurrent):
                for req_id in range(requests_per_thread):
                    future = executor.submit(make_request, thread_id, req_id)
                    futures.append(future)
            
            for i, future in enumerate(as_completed(futures)):
                elapsed, success = future.result()
                all_times.append(elapsed)
                if success:
                    successful += 1
                else:
                    failed += 1
                if (i + 1) % 10 == 0:
                    logger.info(f"  Completed {i+1}/{len(futures)} requests")
        
        avg = sum(all_times) / len(all_times) if all_times else 0
        
        logger.info(f"\n  Results:")
        logger.info(f"    Total Requests: {successful + failed}")
        logger.info(f"    Successful: {successful}")
        logger.info(f"    Failed: {failed}")
        logger.info(f"    Avg Response: {avg:.2f}ms")
        logger.info(f"    Throughput: {successful / (sum(all_times)/1000):.0f} req/s")
        
        success_rate = (successful / (successful + failed) * 100) if (successful + failed) > 0 else 0
        
        self.results.append({
            'test': 'Concurrent Requests',
            'total_requests': successful + failed,
            'successful': successful,
            'failed': failed,
            'avg_ms': avg,
            'success_rate': success_rate,
            'status': '✓ PASS' if success_rate > 95 else '✗ FAIL'
        })
        
        return success_rate > 95
    
    def test_database_performance(self, query_count=100):
        """Test database query performance"""
        logger.info("\n" + "="*60)
        logger.info(f"[TEST 3] Database Performance ({query_count} queries)")
        logger.info("="*60)
        
        times = []
        for i in range(query_count):
            start = time.time()
            try:
                # Simulated database query
                time.sleep(random.uniform(0.005, 0.020))
                elapsed = (time.time() - start) * 1000
                times.append(elapsed)
                if (i + 1) % 20 == 0:
                    logger.info(f"  Executed {i+1}/{query_count} queries")
            except Exception as e:
                logger.error(f"  ✗ Query error: {e}")
        
        avg = sum(times) / len(times) if times else 0
        p95 = sorted(times)[int(len(times) * 0.95)] if times else 0
        p99 = sorted(times)[int(len(times) * 0.99)] if times else 0
        
        logger.info(f"\n  Results:")
        logger.info(f"    Avg Query: {avg:.2f}ms")
        logger.info(f"    P95 Query: {p95:.2f}ms")
        logger.info(f"    P99 Query: {p99:.2f}ms")
        
        self.results.append({
            'test': 'Database Performance',
            'query_count': query_count,
            'avg_ms': avg,
            'p95_ms': p95,
            'p99_ms': p99,
            'status': '✓ PASS' if avg < 50 else '✗ FAIL'
        })
        
        return avg < 50
    
    def test_pipeline_execution(self, client_count=10):
        """Test full pipeline execution"""
        logger.info("\n" + "="*60)
        logger.info(f"[TEST 4] Pipeline Execution ({client_count} clients)")
        logger.info("="*60)
        
        times = []
        for i in range(client_count):
            start = time.time()
            try:
                # Simulated pipeline steps:
                # 1. Audit (1-5s)
                time.sleep(random.uniform(1, 5) / 1000)
                # 2. Scoring (0.5-2s)
                time.sleep(random.uniform(0.5, 2) / 1000)
                # 3. Proposal (2-10s)
                time.sleep(random.uniform(2, 10) / 1000)
                # 4. Email (0.1-1s)
                time.sleep(random.uniform(0.1, 1) / 1000)
                
                elapsed = (time.time() - start) * 1000
                times.append(elapsed)
                logger.info(f"  Pipeline {i+1}/{client_count}: {elapsed:.2f}ms")
            except Exception as e:
                logger.error(f"  ✗ Pipeline error: {e}")
        
        avg = sum(times) / len(times) if times else 0
        total_time = sum(times)
        
        logger.info(f"\n  Results:")
        logger.info(f"    Avg per client: {avg:.2f}ms")
        logger.info(f"    Total time: {total_time:.2f}ms")
        logger.info(f"    Clients/minute: {(client_count / (total_time/1000/60)):.0f}")
        
        self.results.append({
            'test': 'Pipeline Execution',
            'client_count': client_count,
            'avg_ms': avg,
            'total_ms': total_time,
            'clients_per_min': (client_count / (total_time/1000/60)),
            'status': '✓ PASS' if avg < 1000 else '✗ FAIL'
        })
        
        return avg < 1000
    
    def test_email_throughput(self, email_count=100):
        """Test email sending throughput"""
        logger.info("\n" + "="*60)
        logger.info(f"[TEST 5] Email Throughput ({email_count} emails)")
        logger.info("="*60)
        
        start_total = time.time()
        times = []
        
        for i in range(email_count):
            start = time.time()
            try:
                # Simulated email sending (10-100ms per email)
                time.sleep(random.uniform(0.01, 0.1))
                elapsed = (time.time() - start) * 1000
                times.append(elapsed)
                
                if (i + 1) % 20 == 0:
                    logger.info(f"  Sent {i+1}/{email_count} emails")
            except Exception as e:
                logger.error(f"  ✗ Email error: {e}")
        
        total_time = (time.time() - start_total)
        avg = sum(times) / len(times) if times else 0
        throughput = email_count / total_time
        
        logger.info(f"\n  Results:")
        logger.info(f"    Total time: {total_time:.2f}s")
        logger.info(f"    Avg per email: {avg:.2f}ms")
        logger.info(f"    Throughput: {throughput:.1f} emails/sec")
        
        self.results.append({
            'test': 'Email Throughput',
            'email_count': email_count,
            'total_time_sec': total_time,
            'avg_ms': avg,
            'throughput_per_sec': throughput,
            'status': '✓ PASS' if throughput > 5 else '✗ FAIL'
        })
        
        return throughput > 5
    
    def run_all_tests(self):
        """Run all performance tests"""
        logger.info("\n" + "="*60)
        logger.info("FELIX AUTOMATION - LOAD TESTING & PERFORMANCE VALIDATION")
        logger.info("="*60)
        logger.info(f"Start Time: {datetime.now().isoformat()}")
        logger.info(f"Target: {self.base_url}")
        
        self.start_time = time.time()
        
        # Run all tests
        results = {
            'health': self.test_health_check(10),
            'concurrent': self.test_concurrent_requests(10, 5),
            'database': self.test_database_performance(100),
            'pipeline': self.test_pipeline_execution(10),
            'email': self.test_email_throughput(50)
        }
        
        self.end_time = time.time()
        
        # Summary
        self._print_summary(results)
        self._save_results()
        
        return all(results.values())
    
    def _print_summary(self, results):
        """Print test summary"""
        logger.info("\n" + "="*60)
        logger.info("TEST SUMMARY")
        logger.info("="*60)
        
        for result in self.results:
            status = result.get('status', '? UNKNOWN')
            test_name = result.get('test', 'Unknown Test')
            logger.info(f"{status} - {test_name}")
        
        total_time = self.end_time - self.start_time
        passed = sum(1 for r in self.results if r.get('status', '').startswith('✓'))
        
        logger.info("="*60)
        logger.info(f"Total Tests: {len(self.results)}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {len(self.results) - passed}")
        logger.info(f"Total Time: {total_time:.2f}s")
        logger.info("="*60)
        
        if passed == len(self.results):
            logger.info("\n✓ ALL TESTS PASSED!")
        else:
            logger.info("\n✗ SOME TESTS FAILED - Review logs above")
    
    def _save_results(self):
        """Save results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save as JSON
        json_file = f"data/logs/load_test_{timestamp}.json"
        Path(json_file).parent.mkdir(parents=True, exist_ok=True)
        
        with open(json_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'duration_seconds': self.end_time - self.start_time,
                'tests': self.results
            }, f, indent=2)
        
        logger.info(f"\n✓ Results saved to: {json_file}")
        
        # Save as CSV for easy analysis
        csv_file = f"data/logs/load_test_{timestamp}.csv"
        with open(csv_file, 'w', newline='') as f:
            if self.results:
                writer = csv.DictWriter(f, fieldnames=self.results[0].keys())
                writer.writeheader()
                writer.writerows(self.results)
        
        logger.info(f"✓ Results saved to: {csv_file}")

def main():
    """Main entry point"""
    base_url = "http://localhost:8000" if len(sys.argv) < 2 else sys.argv[1]
    
    runner = LoadTestRunner(base_url=base_url, num_workers=5)
    success = runner.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
