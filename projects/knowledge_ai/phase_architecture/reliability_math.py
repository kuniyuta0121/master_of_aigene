#!/usr/bin/env python3
"""
=============================================================================
 RELIABILITY MATH & PERFORMANCE MODELING
 ─ Queueing Theory, Tail Latency, Availability, Capacity Planning ─
=============================================================================

 対象: Python経験者がSenior/Staff Engineerを目指すための教科書レベル数理

 Topics:
   1. Queueing Theory Fundamentals (M/M/1, M/M/c, M/G/1, Priority)
   2. Little's Law & Applications
   3. Tail Latency Mathematics
   4. Amdahl's Law & Parallel Speedup
   5. Availability & Reliability Math
   6. Load Testing Mathematics
   7. Capacity Planning Models
   8. Network Reliability

 Run: python reliability_math.py
=============================================================================
"""

import math
import random
import statistics
import heapq
from collections import defaultdict, deque
from typing import List, Tuple, Dict, Optional, Callable
from dataclasses import dataclass, field


# ============================================================================
# 1. QUEUEING THEORY FUNDAMENTALS (~350 lines)
# ============================================================================
"""
┌─────────────────────────────────────────────────────────────────────┐
│                    QUEUEING THEORY OVERVIEW                        │
│                                                                     │
│  Kendall Notation:  A / S / c / K / N / D                          │
│                                                                     │
│    A = Arrival process    (M=Markov/Poisson, D=Deterministic,      │
│                            G=General)                               │
│    S = Service time dist  (M=Exponential, D=Deterministic,         │
│                            G=General)                               │
│    c = Number of servers                                            │
│    K = System capacity    (default: ∞)                              │
│    N = Population size    (default: ∞)                              │
│    D = Queue discipline   (default: FIFO)                           │
│                                                                     │
│  Most common models:                                                │
│    M/M/1   - Single server, Poisson arrivals, Exp service          │
│    M/M/c   - c servers, Poisson arrivals, Exp service              │
│    M/G/1   - Single server, General service distribution           │
│    M/D/1   - Single server, Deterministic (constant) service       │
│                                                                     │
│  Key insight: Queueing explains why systems degrade non-linearly   │
│  as utilization increases. This is THE reason 80%+ CPU is danger.  │
└─────────────────────────────────────────────────────────────────────┘
"""


class MM1Queue:
    """
    M/M/1 Queue: Single server, Poisson arrivals, Exponential service.

    ─── The most fundamental queueing model ───

    Parameters:
      λ (lambda_rate) = arrival rate (requests/second)
      μ (mu_rate)     = service rate (requests/second)
      ρ = λ/μ         = utilization (must be < 1 for stability)

    Key formulas:
      L  = ρ/(1-ρ)           # avg number in system
      Lq = ρ²/(1-ρ)          # avg number in queue (waiting)
      W  = 1/(μ-λ)           # avg time in system
      Wq = ρ/(μ(1-ρ))        # avg wait time in queue
      Ls = ρ                  # avg number in service

    Derivation intuition (L = ρ/(1-ρ)):
      - P(n customers in system) = (1-ρ)ρⁿ  (geometric distribution)
      - E[N] = Σ n·P(n) = Σ n(1-ρ)ρⁿ = ρ/(1-ρ)
      - This is why small ρ changes near 1.0 cause huge queue growth
    """

    def __init__(self, arrival_rate: float, service_rate: float):
        self.lambda_rate = arrival_rate  # λ
        self.mu_rate = service_rate      # μ
        self.rho = arrival_rate / service_rate  # ρ = utilization

        if self.rho >= 1.0:
            raise ValueError(
                f"System unstable: ρ={self.rho:.3f} >= 1.0. "
                f"Arrival rate ({arrival_rate}) must be < service rate ({service_rate})"
            )

    def utilization(self) -> float:
        """ρ = λ/μ"""
        return self.rho

    def avg_number_in_system(self) -> float:
        """L = ρ/(1-ρ) - avg customers in system (queue + service)"""
        return self.rho / (1 - self.rho)

    def avg_number_in_queue(self) -> float:
        """Lq = ρ²/(1-ρ) - avg customers waiting in queue"""
        return self.rho ** 2 / (1 - self.rho)

    def avg_time_in_system(self) -> float:
        """W = 1/(μ-λ) - avg total time (wait + service)"""
        return 1.0 / (self.mu_rate - self.lambda_rate)

    def avg_wait_time(self) -> float:
        """Wq = ρ/(μ(1-ρ)) - avg time waiting in queue"""
        return self.rho / (self.mu_rate * (1 - self.rho))

    def prob_n_in_system(self, n: int) -> float:
        """P(N=n) = (1-ρ)ρⁿ - probability of exactly n in system"""
        return (1 - self.rho) * (self.rho ** n)

    def prob_wait_exceeds(self, t: float) -> float:
        """P(W > t) = e^(-μ(1-ρ)t) - prob total time exceeds t"""
        return math.exp(-self.mu_rate * (1 - self.rho) * t)

    def report(self) -> str:
        lines = [
            f"=== M/M/1 Queue Analysis ===",
            f"  Arrival rate (λ):       {self.lambda_rate:.2f} req/s",
            f"  Service rate (μ):       {self.mu_rate:.2f} req/s",
            f"  Utilization (ρ):        {self.rho:.4f} ({self.rho*100:.1f}%)",
            f"  Avg in system (L):      {self.avg_number_in_system():.2f}",
            f"  Avg in queue (Lq):      {self.avg_number_in_queue():.2f}",
            f"  Avg time in system (W): {self.avg_time_in_system()*1000:.2f} ms",
            f"  Avg wait time (Wq):     {self.avg_wait_time()*1000:.2f} ms",
        ]
        return "\n".join(lines)


def simulate_mm1_queue(arrival_rate: float, service_rate: float,
                       num_customers: int = 10000, seed: int = 42) -> dict:
    """
    Discrete-event simulation of M/M/1 queue.
    Verifies analytical formulas with Monte Carlo.

    Simulation approach:
      1. Generate inter-arrival times ~ Exp(λ)
      2. Generate service times ~ Exp(μ)
      3. Track arrival, start-service, departure times
      4. Compute empirical statistics
    """
    rng = random.Random(seed)

    # Generate events
    arrival_times = []
    service_times = []
    t = 0.0
    for _ in range(num_customers):
        t += rng.expovariate(arrival_rate)
        arrival_times.append(t)
        service_times.append(rng.expovariate(service_rate))

    # Process queue
    start_times = []
    departure_times = []
    server_free_at = 0.0

    for i in range(num_customers):
        start = max(arrival_times[i], server_free_at)
        start_times.append(start)
        depart = start + service_times[i]
        departure_times.append(depart)
        server_free_at = depart

    # Compute statistics
    wait_times = [start_times[i] - arrival_times[i] for i in range(num_customers)]
    system_times = [departure_times[i] - arrival_times[i] for i in range(num_customers)]

    return {
        "avg_wait_time": statistics.mean(wait_times),
        "avg_system_time": statistics.mean(system_times),
        "avg_queue_length": sum(wait_times) * arrival_rate / num_customers,
        "p95_system_time": sorted(system_times)[int(0.95 * num_customers)],
        "p99_system_time": sorted(system_times)[int(0.99 * num_customers)],
        "max_wait_time": max(wait_times),
    }


def demo_mm1():
    """Demonstrate M/M/1 and verify simulation against formulas."""
    print("\n" + "=" * 70)
    print(" 1. M/M/1 QUEUE - Analytical vs Simulation")
    print("=" * 70)

    q = MM1Queue(arrival_rate=80, service_rate=100)
    print(q.report())

    sim = simulate_mm1_queue(80, 100, num_customers=50000)
    print(f"\n  --- Simulation verification (50k customers) ---")
    print(f"  Simulated avg wait:   {sim['avg_wait_time']*1000:.2f} ms "
          f"(formula: {q.avg_wait_time()*1000:.2f} ms)")
    print(f"  Simulated avg system: {sim['avg_system_time']*1000:.2f} ms "
          f"(formula: {q.avg_time_in_system()*1000:.2f} ms)")
    print(f"  P95 system time:      {sim['p95_system_time']*1000:.2f} ms")
    print(f"  P99 system time:      {sim['p99_system_time']*1000:.2f} ms")


def utilization_vs_latency_curve():
    """
    The "hockey stick" curve - THE most important graph in capacity planning.

    ┌──────────────────────────────────────────────┐
    │  Latency                                     │
    │  (ms)    │                              ╱    │
    │  500     │                            ╱      │
    │          │                          ╱        │
    │  400     │                        ╱          │
    │          │                      ╱            │
    │  300     │                    ╱               │
    │          │                  ╱                 │
    │  200     │                ╱                   │
    │          │             ╱                      │
    │  100     │          ╱                         │
    │          │     ─────                          │
    │   50     │─────                               │
    │          └──────────────────────────── ρ      │
    │          0%  20%  40%  60%  80%  90%  95%     │
    │                                               │
    │  KEY INSIGHT: Latency explodes after ~80%     │
    │  utilization. This is pure mathematics,       │
    │  not an engineering failure.                  │
    └──────────────────────────────────────────────┘
    """
    print("\n  --- Utilization vs Latency (M/M/1, μ=100 req/s) ---")
    print(f"  {'ρ':>6} {'Lq':>8} {'Wq(ms)':>10} {'W(ms)':>10}  Chart")
    print(f"  {'─'*6} {'─'*8} {'─'*10} {'─'*10}  {'─'*30}")

    mu = 100  # service rate
    for rho_pct in [10, 20, 30, 40, 50, 60, 70, 75, 80, 85, 90, 95, 98]:
        rho = rho_pct / 100.0
        lam = rho * mu
        q = MM1Queue(lam, mu)
        wq_ms = q.avg_wait_time() * 1000
        w_ms = q.avg_time_in_system() * 1000
        lq = q.avg_number_in_queue()
        bar = "█" * min(int(wq_ms / 10), 30)
        print(f"  {rho_pct:5d}% {lq:8.2f} {wq_ms:10.2f} {w_ms:10.2f}  {bar}")

    print("\n  ⚠ At ρ=90%, wait time is 9x the service time!")
    print("  ⚠ At ρ=95%, wait time is 19x the service time!")
    print("  → Target utilization: 60-70% for latency-sensitive services")


class MMcQueue:
    """
    M/M/c Queue: c parallel servers, Poisson arrivals, Exponential service.

    ─── Models: load balancer → N backend servers ───

    Key formulas:
      ρ = λ/(cμ)  (per-server utilization, must be < 1)

      Erlang C formula - P(waiting):
        C(c,a) = [a^c/c! · 1/(1-ρ)] / [Σ(k=0..c-1) a^k/k! + a^c/c! · 1/(1-ρ)]
        where a = λ/μ (offered load in Erlangs)

      Wq = C(c,a) / (cμ - λ)
      Lq = λ · Wq
    """

    def __init__(self, arrival_rate: float, service_rate: float, num_servers: int):
        self.lambda_rate = arrival_rate
        self.mu_rate = service_rate
        self.c = num_servers
        self.a = arrival_rate / service_rate  # offered load (Erlangs)
        self.rho = arrival_rate / (num_servers * service_rate)

        if self.rho >= 1.0:
            raise ValueError(
                f"System unstable: ρ={self.rho:.3f} >= 1. "
                f"Need more servers or faster service."
            )

    def erlang_c(self) -> float:
        """
        Erlang C formula: probability that an arriving customer must wait.

        C(c, a) = P0 · a^c / (c! · (1-ρ))
        where P0 = 1 / [Σ(k=0..c-1) a^k/k! + a^c/(c!(1-ρ))]
        """
        a, c, rho = self.a, self.c, self.rho

        # Compute summation terms (use log to avoid overflow)
        sum_terms = sum(a ** k / math.factorial(k) for k in range(c))
        last_term = (a ** c) / (math.factorial(c) * (1 - rho))

        p0 = 1.0 / (sum_terms + last_term)
        return p0 * last_term

    def avg_wait_time(self) -> float:
        """Wq = C(c,a) / (cμ - λ)"""
        return self.erlang_c() / (self.c * self.mu_rate - self.lambda_rate)

    def avg_time_in_system(self) -> float:
        """W = Wq + 1/μ"""
        return self.avg_wait_time() + 1.0 / self.mu_rate

    def avg_queue_length(self) -> float:
        """Lq = λ · Wq"""
        return self.lambda_rate * self.avg_wait_time()

    def prob_immediate_service(self) -> float:
        """1 - Erlang C = probability of no waiting"""
        return 1.0 - self.erlang_c()

    @staticmethod
    def optimal_servers(arrival_rate: float, service_rate: float,
                        target_wait: float, max_servers: int = 100) -> int:
        """Find minimum servers to achieve target average wait time."""
        a = arrival_rate / service_rate
        min_servers = max(int(math.ceil(a)), 1)  # need at least ⌈a⌉ servers

        for c in range(min_servers, max_servers + 1):
            try:
                q = MMcQueue(arrival_rate, service_rate, c)
                if q.avg_wait_time() <= target_wait:
                    return c
            except ValueError:
                continue
        return max_servers


def demo_mmc():
    """Demonstrate M/M/c queue and optimal server calculation."""
    print("\n" + "=" * 70)
    print(" M/M/c QUEUE - Multi-Server Analysis")
    print("=" * 70)

    # Scenario: 800 req/s, each takes 10ms (μ=100/s per server)
    lam, mu = 800, 100
    print(f"\n  Scenario: λ={lam} req/s, μ={mu} req/s per server")
    print(f"  Minimum servers for stability: {int(math.ceil(lam/mu))}")

    print(f"\n  {'Servers':>8} {'ρ':>8} {'P(wait)':>10} {'Wq(ms)':>10} {'Lq':>8}")
    print(f"  {'─'*8} {'─'*8} {'─'*10} {'─'*10} {'─'*8}")

    for c in [9, 10, 11, 12, 14, 16, 20]:
        try:
            q = MMcQueue(lam, mu, c)
            print(f"  {c:8d} {q.rho:8.3f} {q.erlang_c():10.4f} "
                  f"{q.avg_wait_time()*1000:10.2f} {q.avg_queue_length():8.2f}")
        except ValueError as e:
            print(f"  {c:8d} UNSTABLE")

    # Optimal server count for target latency
    target_ms = 5  # 5ms wait target
    optimal = MMcQueue.optimal_servers(lam, mu, target_ms / 1000)
    print(f"\n  Optimal servers for Wq ≤ {target_ms}ms: {optimal}")


class MG1Queue:
    """
    M/G/1 Queue: Poisson arrivals, General service distribution.

    Uses the Pollaczek-Khinchine (P-K) formula:
      Lq = (ρ² + λ²·Var[S]) / (2(1-ρ))
      Wq = Lq / λ

    where:
      ρ = λ · E[S]
      E[S] = mean service time
      Var[S] = variance of service time
      C² = Var[S] / E[S]² = squared coefficient of variation

    Key insight: Higher variance → longer queues!
      - M/M/1: C²=1 → Lq = ρ²/(1-ρ)
      - M/D/1: C²=0 → Lq = ρ²/(2(1-ρ))   (half the queue of M/M/1!)
      - High C²   → Lq >> ρ²/(1-ρ)
    """

    def __init__(self, arrival_rate: float, mean_service: float, var_service: float):
        self.lambda_rate = arrival_rate
        self.mean_service = mean_service
        self.var_service = var_service
        self.rho = arrival_rate * mean_service
        self.cv_squared = var_service / (mean_service ** 2)  # C²

        if self.rho >= 1.0:
            raise ValueError(f"Unstable: ρ={self.rho:.3f}")

    def avg_queue_length(self) -> float:
        """Pollaczek-Khinchine: Lq = (ρ² + λ²·Var[S]) / (2(1-ρ))"""
        rho, lam, var_s = self.rho, self.lambda_rate, self.var_service
        return (rho ** 2 + lam ** 2 * var_s) / (2 * (1 - rho))

    def avg_wait_time(self) -> float:
        """Wq = Lq / λ"""
        return self.avg_queue_length() / self.lambda_rate

    def avg_time_in_system(self) -> float:
        return self.avg_wait_time() + self.mean_service


def demo_mg1_variance_impact():
    """Show how service time variance affects queue length."""
    print("\n" + "=" * 70)
    print(" M/G/1 QUEUE - Impact of Service Time Variance")
    print("=" * 70)

    lam = 80  # arrival rate
    mean_s = 0.01  # 10ms mean service

    print(f"\n  λ={lam} req/s, E[S]={mean_s*1000}ms, ρ={lam*mean_s:.2f}")
    print(f"\n  {'Distribution':>20} {'C²':>6} {'Lq':>8} {'Wq(ms)':>10}")
    print(f"  {'─'*20} {'─'*6} {'─'*8} {'─'*10}")

    scenarios = [
        ("Deterministic(M/D/1)", 0.0),
        ("Low variance", 0.25),
        ("Exponential (M/M/1)", 1.0),
        ("High variance", 4.0),
        ("Very high variance", 10.0),
    ]

    for name, cv2 in scenarios:
        var_s = cv2 * mean_s ** 2
        q = MG1Queue(lam, mean_s, var_s)
        print(f"  {name:>20} {cv2:6.2f} {q.avg_queue_length():8.3f} "
              f"{q.avg_wait_time()*1000:10.3f}")

    print("\n  → Reducing variance (e.g., caching, consistent processing)")
    print("    is as effective as adding capacity!")


class PriorityQueue:
    """
    Priority Queue (Non-preemptive, 2 classes).

    ─── Models: Priority lanes in API gateways ───

    Class 1 (high priority): arrival rate λ1, service rate μ1
    Class 2 (low priority):  arrival rate λ2, service rate μ2

    Non-preemptive: current service completes before switching.

    Wait times (M/M/1 with priorities):
      W0 = base wait = Σ(ρi/(μi)) / (1-ρ_total) ... simplified
      W1 = W0 / (1 - ρ1)
      W2 = W0 / ((1-ρ1)(1-ρ1-ρ2))
    """

    def __init__(self, classes: List[Tuple[float, float]]):
        """classes: list of (arrival_rate, service_rate) per priority class."""
        self.classes = classes
        self.rhos = [lam / mu for lam, mu in classes]
        self.rho_total = sum(self.rhos)

        if self.rho_total >= 1.0:
            raise ValueError(f"Unstable: total ρ={self.rho_total:.3f}")

    def avg_wait_times(self) -> List[float]:
        """Compute average wait time for each priority class."""
        # Base work intensity
        w0_num = sum(rho / mu for (lam, mu), rho in zip(self.classes, self.rhos))

        wait_times = []
        sigma_prev = 0.0
        for i, rho in enumerate(self.rhos):
            sigma_curr = sigma_prev + rho
            denom = (1 - sigma_prev) * (1 - sigma_curr)
            if denom <= 0:
                wait_times.append(float('inf'))
            else:
                wait_times.append(w0_num / denom)
            sigma_prev = sigma_curr

        return wait_times


def simulate_priority_queue(classes: List[Tuple[float, float]],
                            num_customers: int = 20000,
                            seed: int = 42) -> List[float]:
    """Simulate non-preemptive priority queue to verify formulas."""
    rng = random.Random(seed)

    # Generate all arrivals with class labels
    events = []  # (arrival_time, service_time, priority)
    for pri, (lam, mu) in enumerate(classes):
        t = 0.0
        n = int(num_customers * lam / sum(l for l, _ in classes))
        for _ in range(n):
            t += rng.expovariate(lam)
            s = rng.expovariate(mu)
            events.append((t, s, pri))

    events.sort(key=lambda x: x[0])

    # Process with priority (non-preemptive)
    server_free = 0.0
    wait_by_class = defaultdict(list)
    pending = []  # heap: (priority, arrival_order, arrival_time, service_time)

    idx = 0
    order = 0
    sim_time = 0.0

    while idx < len(events) or pending:
        # Add arrivals up to current time
        while idx < len(events) and events[idx][0] <= sim_time:
            arr, svc, pri = events[idx]
            heapq.heappush(pending, (pri, order, arr, svc))
            order += 1
            idx += 1

        if pending:
            pri, _, arr, svc = heapq.heappop(pending)
            start = max(arr, server_free)
            wait_by_class[pri].append(start - arr)
            server_free = start + svc
            sim_time = server_free
        elif idx < len(events):
            sim_time = events[idx][0]
        else:
            break

    return [statistics.mean(wait_by_class.get(i, [0]))
            for i in range(len(classes))]


def demo_priority_queue():
    """Demonstrate priority queueing."""
    print("\n" + "=" * 70)
    print(" PRIORITY QUEUE - Non-preemptive, 2 Classes")
    print("=" * 70)

    classes = [(30, 100), (50, 100)]  # (λ, μ) for high-pri, low-pri
    pq = PriorityQueue(classes)
    analytical = pq.avg_wait_times()
    simulated = simulate_priority_queue(classes)

    print(f"\n  High-priority: λ1={classes[0][0]}, μ={classes[0][1]}")
    print(f"  Low-priority:  λ2={classes[1][0]}, μ={classes[1][1]}")
    print(f"  Total ρ = {pq.rho_total:.3f}")

    for i, name in enumerate(["High-priority", "Low-priority"]):
        print(f"\n  {name}:")
        print(f"    Analytical Wq: {analytical[i]*1000:.2f} ms")
        print(f"    Simulated Wq:  {simulated[i]*1000:.2f} ms")


# ============================================================================
# 2. LITTLE'S LAW & APPLICATIONS (~200 lines)
# ============================================================================
"""
┌─────────────────────────────────────────────────────────────────────┐
│                      LITTLE'S LAW                                   │
│                                                                     │
│                    L = λ · W                                        │
│                                                                     │
│  L = avg number of items in system                                  │
│  λ = arrival rate (throughput)                                      │
│  W = avg time each item spends in system                            │
│                                                                     │
│  This law is UNIVERSAL:                                             │
│  - Any stable system, any distribution, any discipline              │
│  - Applies to queues, databases, networks, thread pools             │
│  - No assumptions about arrival/service distributions!              │
│                                                                     │
│  Proof intuition:                                                   │
│    Over time T, total arrivals ≈ λT                                │
│    Area under "number in system" curve ≈ L·T                        │
│    Each arrival contributes W to that area                          │
│    So L·T = λT·W → L = λW                                         │
└─────────────────────────────────────────────────────────────────────┘
"""


class LittlesLaw:
    """Apply Little's Law to various capacity planning problems."""

    @staticmethod
    def concurrent_requests(throughput_rps: float, latency_s: float) -> float:
        """
        L = λW: How many requests are in-flight simultaneously?

        Example: API at 1000 req/s with 50ms avg latency
          L = 1000 × 0.050 = 50 concurrent requests
        """
        return throughput_rps * latency_s

    @staticmethod
    def connection_pool_size(throughput_rps: float, query_time_s: float,
                             safety_factor: float = 1.5) -> int:
        """
        Size a database connection pool.

        pool_size = ⌈L × safety_factor⌉
        where L = λW = throughput × query_time

        Safety factor accounts for:
          - Variance in query times
          - Burst traffic
          - Connection overhead
        """
        l = throughput_rps * query_time_s
        return int(math.ceil(l * safety_factor))

    @staticmethod
    def thread_pool_size(throughput_rps: float, processing_time_s: float,
                         target_utilization: float = 0.7) -> int:
        """
        Size a thread pool for target utilization.

        threads = ⌈L / target_utilization⌉

        Lower utilization → more headroom for bursts.
        """
        l = throughput_rps * processing_time_s
        return int(math.ceil(l / target_utilization))

    @staticmethod
    def buffer_size_streaming(ingest_rate_mbs: float,
                              processing_time_s: float,
                              burst_factor: float = 3.0) -> float:
        """
        Buffer size for stream processing.

        buffer_MB = ingest_rate × processing_time × burst_factor
        """
        return ingest_rate_mbs * processing_time_s * burst_factor

    @staticmethod
    def required_throughput(max_concurrent: int, target_latency_s: float) -> float:
        """
        Given max concurrent capacity and latency target,
        what throughput can we sustain?

        λ = L / W
        """
        return max_concurrent / target_latency_s


def demo_littles_law():
    """Demonstrate Little's Law applications."""
    print("\n" + "=" * 70)
    print(" 2. LITTLE'S LAW - L = λW Applications")
    print("=" * 70)

    ll = LittlesLaw()

    # Example 1: API concurrent connections
    rps, latency_ms = 1000, 50
    concurrent = ll.concurrent_requests(rps, latency_ms / 1000)
    print(f"\n  Example 1: API Concurrent Connections")
    print(f"    Throughput: {rps} req/s, Latency: {latency_ms}ms")
    print(f"    → Concurrent requests: L = {rps} × {latency_ms/1000} = {concurrent:.0f}")

    # Example 2: Connection pool
    db_rps, query_ms = 500, 20
    pool = ll.connection_pool_size(db_rps, query_ms / 1000)
    print(f"\n  Example 2: DB Connection Pool Sizing")
    print(f"    Query rate: {db_rps}/s, Avg query: {query_ms}ms")
    print(f"    → Pool size (1.5x safety): {pool}")

    # Example 3: Thread pool
    threads = ll.thread_pool_size(200, 0.1, target_utilization=0.7)
    print(f"\n  Example 3: Thread Pool Sizing")
    print(f"    200 req/s, 100ms processing, 70% target util")
    print(f"    → Thread pool size: {threads}")

    # Example 4: Max throughput from constraints
    max_conns, target_lat = 100, 0.050
    max_tput = ll.required_throughput(max_conns, target_lat)
    print(f"\n  Example 4: Max Throughput from Constraints")
    print(f"    Max connections: {max_conns}, Target latency: {target_lat*1000}ms")
    print(f"    → Max throughput: {max_tput:.0f} req/s")

    # Example 5: Verify with simulation
    print(f"\n  Example 5: Simulation Verification")
    sim = simulate_mm1_queue(80, 100, num_customers=50000)
    L_sim = 80 * sim['avg_system_time']
    print(f"    λ=80, W_sim={sim['avg_system_time']*1000:.2f}ms")
    print(f"    L_sim = λ·W = 80 × {sim['avg_system_time']:.4f} = {L_sim:.2f}")
    q = MM1Queue(80, 100)
    print(f"    L_formula = ρ/(1-ρ) = {q.avg_number_in_system():.2f}")


# ============================================================================
# 3. TAIL LATENCY MATHEMATICS (~300 lines)
# ============================================================================
"""
┌─────────────────────────────────────────────────────────────────────┐
│                    TAIL LATENCY                                     │
│                                                                     │
│  "The last 1% of latency is the hardest to fix"                    │
│                                                                     │
│  Why tails matter at scale:                                         │
│  - User request fans out to 100 backend services                   │
│  - User sees latency of SLOWEST backend                            │
│  - P(all 100 < P99) = 0.99^100 = 36.6%                            │
│  - 63.4% of user requests hit a tail latency!                      │
│                                                                     │
│  Distribution:                                                      │
│    ├── P50: median (most requests)                                  │
│    ├── P90: 10th percentile from top                                │
│    ├── P99: 1 in 100 (often 5-10x P50)                             │
│    ├── P99.9: 1 in 1000 (GC pauses, disk seeks)                   │
│    └── P99.99: 1 in 10000 (network blips, retries)                 │
└─────────────────────────────────────────────────────────────────────┘
"""


class HdrHistogram:
    """
    Simplified High Dynamic Range (HDR) Histogram.

    ─── Logarithmic bucketing for efficient percentile tracking ───

    Real HdrHistogram uses sub-bucket precision within each power-of-2
    magnitude. This simplified version demonstrates the concept.

    Key properties:
      - O(1) record
      - O(log N) percentile query
      - Bounded memory regardless of sample count
      - Precision: ±0.1% of recorded value at any magnitude
    """

    def __init__(self, lowest: float = 0.001, highest: float = 60.0,
                 significant_digits: int = 3):
        self.lowest = lowest
        self.highest = highest
        # Create logarithmic buckets
        self.num_buckets = int(math.log2(highest / lowest) *
                              10 ** significant_digits) + 1
        self.num_buckets = min(self.num_buckets, 10000)  # cap
        self.log_base = math.log(highest / lowest) / self.num_buckets
        self.counts = [0] * self.num_buckets
        self.total_count = 0
        self.min_val = float('inf')
        self.max_val = 0.0

    def _bucket_index(self, value: float) -> int:
        if value <= self.lowest:
            return 0
        if value >= self.highest:
            return self.num_buckets - 1
        return min(int(math.log(value / self.lowest) / self.log_base),
                   self.num_buckets - 1)

    def _bucket_value(self, index: int) -> float:
        return self.lowest * math.exp(index * self.log_base)

    def record(self, value: float):
        idx = self._bucket_index(value)
        self.counts[idx] += 1
        self.total_count += 1
        self.min_val = min(self.min_val, value)
        self.max_val = max(self.max_val, value)

    def percentile(self, p: float) -> float:
        """Get value at percentile p (0-100)."""
        target = int(self.total_count * p / 100.0)
        cumulative = 0
        for i, count in enumerate(self.counts):
            cumulative += count
            if cumulative >= target:
                return self._bucket_value(i)
        return self.max_val

    def report(self) -> str:
        lines = [f"    Total samples: {self.total_count}"]
        for p in [50, 90, 95, 99, 99.9, 99.99]:
            val = self.percentile(p)
            lines.append(f"    P{p:<5}: {val*1000:10.3f} ms")
        lines.append(f"    Max:    {self.max_val*1000:10.3f} ms")
        return "\n".join(lines)


def tail_at_scale(p_slow: float, fan_out: int) -> float:
    """
    Probability that at least one of N parallel requests is slow.

    P(at least one slow) = 1 - (1 - p_slow)^N

    Example: P99 = 10ms means p_slow_at_10ms = 0.01
      fan_out=1:   P(slow) = 1%
      fan_out=10:  P(slow) = 9.6%
      fan_out=50:  P(slow) = 39.5%
      fan_out=100: P(slow) = 63.4%
    """
    return 1.0 - (1.0 - p_slow) ** fan_out


def effective_percentile_fanout(base_percentile: float, fan_out: int) -> float:
    """
    What effective percentile does the user experience with fan-out?

    If each backend has latency at P(base_percentile),
    the user sees the max of N independent samples.

    Effective percentile = 1 - (1 - base_percentile/100)^(1/N)
    (inverted: what single-server percentile equals the fan-out P50)

    Actually simpler: user's Pk = 1-(1-k/100)^N mapped back
    """
    p_fast = (base_percentile / 100.0) ** fan_out
    return p_fast * 100.0


def hedged_request_analysis(p_slow: float, fan_out: int,
                            hedge_after_percentile: float = 95) -> dict:
    """
    Hedged requests: send redundant request after timeout.

    Strategy: If primary doesn't respond within P95, send backup.
    Take whichever responds first.

    Cost: ~5% extra load (if hedge at P95)
    Benefit: Tail latency drops dramatically

    P(both slow) = p_slow² (for independent servers)
    """
    # Without hedging
    p_any_slow_no_hedge = tail_at_scale(p_slow, fan_out)

    # With hedging at given percentile
    hedge_threshold = 1.0 - hedge_after_percentile / 100.0
    # After hedging, p_slow per request becomes p_slow * hedge_threshold
    p_slow_hedged = p_slow * hedge_threshold
    p_any_slow_hedged = tail_at_scale(p_slow_hedged, fan_out)

    extra_load_pct = (1.0 - hedge_after_percentile / 100.0) * 100.0

    return {
        "p_slow_no_hedge": p_any_slow_no_hedge,
        "p_slow_hedged": p_any_slow_hedged,
        "improvement_factor": p_any_slow_no_hedge / max(p_any_slow_hedged, 1e-10),
        "extra_load_pct": extra_load_pct,
    }


def coordinated_omission_demo():
    """
    Coordinated Omission: The silent killer of load testing accuracy.

    ─── What is it? ───
    Most load testing tools send request N+1 only after N completes.
    If request N takes 5 seconds, during those 5 seconds NO requests
    are measured → the 5-second stall affects ONE sample instead of
    hundreds.

    ─── The math ───
    If 1 in 100 requests takes 5s (rest take 5ms):
      Naive measurement:    P99 ≈ 5ms   (WRONG!)
      Corrected measurement: P99 ≈ 5s    (CORRECT)

    Because during that 5s stall, ~1000 requests SHOULD have arrived
    and all would have experienced 0-5s of delay.
    """
    print("\n  --- Coordinated Omission Problem ---")

    # Simulate: 99% of requests take 5ms, 1% take 5000ms
    rng = random.Random(42)
    n_requests = 10000

    # "Naive" (closed-loop) measurement
    naive_latencies = []
    for _ in range(n_requests):
        if rng.random() < 0.01:
            naive_latencies.append(5.0)    # 5 seconds
        else:
            naive_latencies.append(0.005)  # 5ms

    # "Corrected" (open-loop) measurement
    # During each 5s stall, ~1000 requests would queue up
    corrected_latencies = []
    arrival_interval = 0.001  # 1000 req/s → 1ms between arrivals
    for lat in naive_latencies:
        if lat > 1.0:  # stall detected
            # All requests that would have arrived during the stall
            queued = int(lat / arrival_interval)
            for j in range(queued):
                corrected_latencies.append(lat - j * arrival_interval)
        else:
            corrected_latencies.append(lat)

    naive_sorted = sorted(naive_latencies)
    corrected_sorted = sorted(corrected_latencies)

    print(f"\n  {'Percentile':>12} {'Naive(ms)':>12} {'Corrected(ms)':>14}")
    print(f"  {'─'*12} {'─'*12} {'─'*14}")
    for p in [50, 90, 95, 99, 99.9]:
        idx_n = min(int(p / 100 * len(naive_sorted)), len(naive_sorted) - 1)
        idx_c = min(int(p / 100 * len(corrected_sorted)), len(corrected_sorted) - 1)
        print(f"  P{p:<10} {naive_sorted[idx_n]*1000:12.1f} "
              f"{corrected_sorted[idx_c]*1000:14.1f}")

    print("\n  ⚠ Naive P99 hides the 5s stalls!")
    print("  → Use open-loop load testing (e.g., wrk2, Gatling open model)")


def monte_carlo_tail_latency(fan_out: int = 50, num_trials: int = 10000,
                             seed: int = 42):
    """Monte Carlo simulation of tail latency under fan-out."""
    rng = random.Random(seed)

    user_latencies = []
    for _ in range(num_trials):
        # Each backend: lognormal latency (realistic)
        backend_latencies = [
            rng.lognormvariate(math.log(0.005), 0.8)  # median ~5ms
            for _ in range(fan_out)
        ]
        # User sees max (must wait for slowest)
        user_latencies.append(max(backend_latencies))

    user_sorted = sorted(user_latencies)
    return {
        p: user_sorted[min(int(p / 100 * len(user_sorted)), len(user_sorted) - 1)]
        for p in [50, 90, 95, 99, 99.9]
    }


def demo_tail_latency():
    """Demonstrate tail latency mathematics."""
    print("\n" + "=" * 70)
    print(" 3. TAIL LATENCY MATHEMATICS")
    print("=" * 70)

    # Fan-out effect
    print("\n  --- Tail-at-Scale: Fan-out Effect ---")
    print(f"  {'Fan-out N':>10} {'P(≥1 slow)':>12}  Impact")
    print(f"  {'─'*10} {'─'*12}  {'─'*30}")
    for n in [1, 5, 10, 20, 50, 100, 200]:
        p = tail_at_scale(0.01, n)
        bar = "█" * int(p * 30)
        print(f"  {n:10d} {p:12.1%}  {bar}")

    # Hedged requests
    print("\n  --- Hedged Requests Analysis ---")
    for fan_out in [10, 50, 100]:
        result = hedged_request_analysis(0.01, fan_out, 95)
        print(f"\n  Fan-out={fan_out}:")
        print(f"    Without hedging: {result['p_slow_no_hedge']:.1%} requests slow")
        print(f"    With hedging:    {result['p_slow_hedged']:.1%} requests slow")
        print(f"    Improvement:     {result['improvement_factor']:.1f}x better")
        print(f"    Extra load:      {result['extra_load_pct']:.0f}%")

    # Monte Carlo simulation
    print("\n  --- Monte Carlo: User Latency with 50-way Fan-out ---")
    print("  (Backend latency: lognormal, median ~5ms)")
    mc = monte_carlo_tail_latency(fan_out=50)
    for p, val in mc.items():
        print(f"    P{p:<5}: {val*1000:8.1f} ms")

    # HDR Histogram demo
    print("\n  --- HDR Histogram Demo ---")
    hist = HdrHistogram(0.001, 10.0)
    rng = random.Random(42)
    for _ in range(100000):
        lat = rng.lognormvariate(math.log(0.005), 0.5)
        hist.record(lat)
    print(hist.report())

    # Coordinated omission
    coordinated_omission_demo()


# ============================================================================
# 4. AMDAHL'S LAW & PARALLEL SPEEDUP (~200 lines)
# ============================================================================
"""
┌─────────────────────────────────────────────────────────────────────┐
│                  SCALING LAWS                                       │
│                                                                     │
│  Amdahl's Law (fixed problem size):                                │
│    S(N) = 1 / ((1-P) + P/N)                                       │
│    P = parallelizable fraction                                      │
│    N = number of processors                                         │
│    Max speedup = 1/(1-P) as N→∞                                    │
│                                                                     │
│  Gustafson's Law (scaled problem size):                            │
│    S(N) = N - α(N-1)                                               │
│    α = serial fraction                                              │
│    "More processors → solve bigger problems"                        │
│                                                                     │
│  Universal Scalability Law (USL):                                   │
│    S(N) = N / (1 + σ(N-1) + κN(N-1))                              │
│    σ = contention (serialization)                                   │
│    κ = coherency (communication overhead)                           │
│    Models: contention AND retrograde (negative scaling)             │
└─────────────────────────────────────────────────────────────────────┘
"""


class ScalingLaws:
    """Implementation of major scaling laws."""

    @staticmethod
    def amdahl(parallel_fraction: float, num_processors: int) -> float:
        """
        Amdahl's Law: S(N) = 1 / ((1-P) + P/N)

        Key insight: Even with infinite processors, speedup is bounded by
        the serial portion. If 5% is serial, max speedup = 20x.
        """
        p = parallel_fraction
        n = num_processors
        return 1.0 / ((1.0 - p) + p / n)

    @staticmethod
    def amdahl_max_speedup(parallel_fraction: float) -> float:
        """Maximum theoretical speedup = 1/(1-P)"""
        return 1.0 / (1.0 - parallel_fraction)

    @staticmethod
    def gustafson(serial_fraction: float, num_processors: int) -> float:
        """
        Gustafson's Law: S(N) = N - α(N-1)

        Assumes problem size scales with N.
        More optimistic than Amdahl for data-parallel workloads.
        """
        return num_processors - serial_fraction * (num_processors - 1)

    @staticmethod
    def usl(num_processors: int, sigma: float, kappa: float) -> float:
        """
        Universal Scalability Law:
        S(N) = N / (1 + σ(N-1) + κN(N-1))

        σ (sigma) = contention/serialization coefficient
        κ (kappa) = coherency/crosstalk coefficient

        When κ=0: reduces to Amdahl's Law
        When κ>0: throughput DECREASES after optimal N
                  (retrograde behavior, common in distributed systems)
        """
        n = num_processors
        return n / (1.0 + sigma * (n - 1) + kappa * n * (n - 1))

    @staticmethod
    def usl_optimal_n(sigma: float, kappa: float) -> float:
        """
        Optimal N for USL (peak throughput before retrograde).
        N_opt = sqrt((1-σ) / κ)
        """
        if kappa <= 0:
            return float('inf')
        return math.sqrt((1.0 - sigma) / kappa)


def demo_scaling_laws():
    """Demonstrate Amdahl, Gustafson, and USL."""
    print("\n" + "=" * 70)
    print(" 4. AMDAHL'S LAW & PARALLEL SPEEDUP")
    print("=" * 70)

    sl = ScalingLaws()

    # Amdahl's Law
    print("\n  --- Amdahl's Law: Speedup by Parallel Fraction ---")
    print(f"  {'N':>5}  {'P=50%':>8} {'P=75%':>8} {'P=90%':>8} {'P=95%':>8} {'P=99%':>8}")
    print(f"  {'─'*5}  {'─'*8} {'─'*8} {'─'*8} {'─'*8} {'─'*8}")
    for n in [1, 2, 4, 8, 16, 32, 64, 128, 256, 1024]:
        vals = [sl.amdahl(p, n) for p in [0.5, 0.75, 0.9, 0.95, 0.99]]
        print(f"  {n:5d}  " + "  ".join(f"{v:7.2f}x" for v in vals))

    print("\n  Max speedup (N→∞):")
    for p in [0.5, 0.75, 0.9, 0.95, 0.99]:
        print(f"    P={p*100:.0f}%: {sl.amdahl_max_speedup(p):.1f}x")

    # USL
    print("\n  --- Universal Scalability Law ---")
    print("  σ=0.02 (2% contention), κ=0.001 (0.1% coherency)")
    sigma, kappa = 0.02, 0.001
    opt_n = sl.usl_optimal_n(sigma, kappa)
    print(f"  Optimal N = {opt_n:.0f}")

    print(f"\n  {'N':>5} {'Speedup':>10} {'Efficiency':>12}")
    print(f"  {'─'*5} {'─'*10} {'─'*12}")
    for n in [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]:
        s = sl.usl(n, sigma, kappa)
        eff = s / n * 100
        bar = "█" * int(s / 5)
        note = " ← peak" if abs(n - opt_n) < opt_n * 0.15 else ""
        note = " ← RETROGRADE" if s < sl.usl(n // 2, sigma, kappa) and n > 1 else note
        print(f"  {n:5d} {s:10.2f}x {eff:10.1f}%  {bar}{note}")

    # Real-world scenarios
    print("\n  --- Real-World Scenarios ---")
    scenarios = [
        ("DB query parallelism", 0.90, 8, "Amdahl"),
        ("MapReduce word count", 0.99, 100, "Amdahl"),
        ("Microservice fan-out", 0.95, 20, "Amdahl"),
        ("Lock-heavy code", 0.60, 16, "Amdahl"),
    ]
    for name, p, n, law in scenarios:
        s = sl.amdahl(p, n)
        max_s = sl.amdahl_max_speedup(p)
        print(f"  {name:30s}: P={p:.0%}, N={n:3d} → "
              f"S={s:.2f}x (max={max_s:.1f}x)")


# ============================================================================
# 5. AVAILABILITY & RELIABILITY MATH (~250 lines)
# ============================================================================
"""
┌─────────────────────────────────────────────────────────────────────┐
│                AVAILABILITY MATH                                    │
│                                                                     │
│  Series:   A_total = A1 × A2 × ... × An                           │
│  Parallel: A_total = 1 - (1-A1)(1-A2)...(1-An)                    │
│                                                                     │
│  Nines Table:                                                       │
│    99%     = 3.65 days/year downtime    "two nines"                │
│    99.9%   = 8.76 hours/year            "three nines"              │
│    99.95%  = 4.38 hours/year                                       │
│    99.99%  = 52.6 minutes/year          "four nines"               │
│    99.999% = 5.26 minutes/year          "five nines"               │
│                                                                     │
│  MTBF = Mean Time Between Failures                                  │
│  MTTR = Mean Time To Repair                                         │
│  A = MTBF / (MTBF + MTTR)                                         │
│                                                                     │
│  Key insight: Reducing MTTR is often easier than increasing MTBF   │
└─────────────────────────────────────────────────────────────────────┘
"""


class AvailabilityCalculator:
    """Calculate system availability for various architectures."""

    @staticmethod
    def series(*availabilities: float) -> float:
        """
        Series system: all components must work.
        A_total = A1 × A2 × ... × An

        Example: API → Auth → DB → Cache
          A = 0.999 × 0.999 × 0.999 × 0.999 = 0.996 (only 99.6%!)
        """
        result = 1.0
        for a in availabilities:
            result *= a
        return result

    @staticmethod
    def parallel(*availabilities: float) -> float:
        """
        Parallel (redundant) system: at least one must work.
        A_total = 1 - (1-A1)(1-A2)...(1-An)

        Example: 2 servers each at 99.9%
          A = 1 - (0.001)² = 0.999999 (six nines!)
        """
        p_all_fail = 1.0
        for a in availabilities:
            p_all_fail *= (1.0 - a)
        return 1.0 - p_all_fail

    @staticmethod
    def k_of_n(k: int, n: int, availability: float) -> float:
        """
        k-of-n system: at least k of n identical components must work.
        Uses binomial distribution.

        A = Σ(i=k..n) C(n,i) × A^i × (1-A)^(n-i)
        """
        total = 0.0
        for i in range(k, n + 1):
            total += (math.comb(n, i) *
                      availability ** i *
                      (1 - availability) ** (n - i))
        return total

    @staticmethod
    def from_mtbf_mttr(mtbf_hours: float, mttr_hours: float) -> float:
        """A = MTBF / (MTBF + MTTR)"""
        return mtbf_hours / (mtbf_hours + mttr_hours)

    @staticmethod
    def nines(availability: float) -> float:
        """Convert availability to 'number of nines'."""
        if availability >= 1.0:
            return float('inf')
        return -math.log10(1.0 - availability)

    @staticmethod
    def downtime_per_year(availability: float) -> dict:
        """Convert availability to downtime durations."""
        unavail_seconds = (1.0 - availability) * 365.25 * 24 * 3600
        return {
            "seconds_per_year": unavail_seconds,
            "minutes_per_year": unavail_seconds / 60,
            "hours_per_year": unavail_seconds / 3600,
            "days_per_year": unavail_seconds / 86400,
        }


def nines_table():
    """Print the standard nines table."""
    print("\n  --- Nines Table ---")
    print(f"  {'Availability':>14} {'Nines':>6} {'Downtime/Year':>20} {'Downtime/Month':>18}")
    print(f"  {'─'*14} {'─'*6} {'─'*20} {'─'*18}")

    calc = AvailabilityCalculator()
    for pct in [99, 99.5, 99.9, 99.95, 99.99, 99.999, 99.9999]:
        a = pct / 100.0
        dt = calc.downtime_per_year(a)
        n = calc.nines(a)
        monthly_min = dt["minutes_per_year"] / 12

        if dt["hours_per_year"] >= 24:
            yr_str = f"{dt['days_per_year']:.2f} days"
        elif dt["hours_per_year"] >= 1:
            yr_str = f"{dt['hours_per_year']:.2f} hours"
        elif dt["minutes_per_year"] >= 1:
            yr_str = f"{dt['minutes_per_year']:.1f} minutes"
        else:
            yr_str = f"{dt['seconds_per_year']:.1f} seconds"

        if monthly_min >= 60:
            mo_str = f"{monthly_min/60:.2f} hours"
        elif monthly_min >= 1:
            mo_str = f"{monthly_min:.1f} minutes"
        else:
            mo_str = f"{monthly_min*60:.1f} seconds"

        print(f"  {pct:>13}% {n:6.1f} {yr_str:>20} {mo_str:>18}")


class ErrorBudget:
    """
    SRE Error Budget Calculator.

    Error budget = 1 - SLO
    If SLO = 99.9%, error budget = 0.1% = 43.2 minutes/month

    Burn rate = actual_error_rate / budget_rate
    If burn_rate > 1.0, you're burning budget too fast.
    """

    def __init__(self, slo_percent: float, window_days: int = 30):
        self.slo = slo_percent / 100.0
        self.window_seconds = window_days * 24 * 3600
        self.error_budget = 1.0 - self.slo
        self.budget_seconds = self.error_budget * self.window_seconds

    def burn_rate(self, error_rate: float) -> float:
        """
        Burn rate = actual_error_rate / budget_error_rate

        error_rate: fraction of requests failing (e.g., 0.002 = 0.2%)
        budget_error_rate: error_budget / window = (1-SLO)

        burn_rate = 1 → using budget exactly on pace
        burn_rate = 2 → will exhaust budget in half the window
        burn_rate = 10 → will exhaust budget in 1/10 of window
        """
        budget_rate = self.error_budget
        return error_rate / budget_rate if budget_rate > 0 else float('inf')

    def time_to_exhaustion(self, burn_rate: float) -> float:
        """Hours until error budget is exhausted at given burn rate."""
        if burn_rate <= 0:
            return float('inf')
        window_hours = self.window_seconds / 3600
        return window_hours / burn_rate

    def remaining_budget(self, errors_so_far: int, total_requests: int) -> dict:
        """Calculate remaining error budget."""
        error_rate = errors_so_far / total_requests if total_requests > 0 else 0
        budget_errors = self.error_budget * total_requests
        remaining = budget_errors - errors_so_far
        return {
            "budget_total": budget_errors,
            "consumed": errors_so_far,
            "remaining": remaining,
            "percent_remaining": (remaining / budget_errors * 100) if budget_errors > 0 else 0,
            "current_error_rate": error_rate,
            "burn_rate": self.burn_rate(error_rate),
        }

    def multi_window_alert(self, error_rate: float) -> dict:
        """
        Multi-window burn rate alerting (Google SRE approach).

        Fast burn: 14.4x burn rate over 1 hour → page
        Slow burn: 1x burn rate over 3 days → ticket

        Alert if BOTH short and long windows show elevated burn.
        """
        br = self.burn_rate(error_rate)
        return {
            "burn_rate": br,
            "page_1h": br >= 14.4,     # Exhausts budget in ~2 hours
            "page_6h": br >= 6.0,      # Exhausts budget in ~5 hours
            "ticket_1d": br >= 3.0,    # Exhausts budget in ~10 days
            "ticket_3d": br >= 1.0,    # On pace to exhaust budget
            "time_to_exhaustion_hours": self.time_to_exhaustion(br),
        }


def cascading_failure_probability(services: int, per_service_failure: float,
                                  cascade_probability: float) -> float:
    """
    Model cascading failure probability.

    P(cascade) = 1 - (1 - p_initial × p_propagate)^(n-1)

    When one service fails, it can overload others:
      - Retry storms
      - Connection pool exhaustion
      - Timeout propagation
    """
    p_initial = 1.0 - (1.0 - per_service_failure) ** services
    p_cascade = p_initial * (1.0 - (1.0 - cascade_probability) ** (services - 1))
    return p_cascade


def markov_availability(failure_rate: float, repair_rate: float) -> dict:
    """
    Markov chain model for availability (2-state: UP ↔ DOWN).

    States:  UP ──λ──→ DOWN
             UP ←──μ── DOWN

    λ = failure rate (1/MTBF)
    μ = repair rate (1/MTTR)

    Steady-state probabilities:
      P(UP) = μ/(λ+μ) = MTBF/(MTBF+MTTR)
      P(DOWN) = λ/(λ+μ) = MTTR/(MTBF+MTTR)
    """
    p_up = repair_rate / (failure_rate + repair_rate)
    p_down = failure_rate / (failure_rate + repair_rate)
    mtbf = 1.0 / failure_rate
    mttr = 1.0 / repair_rate

    return {
        "availability": p_up,
        "unavailability": p_down,
        "mtbf_hours": mtbf,
        "mttr_hours": mttr,
        "nines": -math.log10(p_down) if p_down > 0 else float('inf'),
    }


def sla_composition(service_slas: List[Tuple[str, float, str]]) -> None:
    """
    Calculate composed SLA for multi-service architecture.

    service_slas: list of (name, availability, relationship)
      relationship: "series" or "parallel"
    """
    print("\n  --- SLA Composition for Multi-Service Architecture ---")

    calc = AvailabilityCalculator()
    current_availability = 1.0

    for name, avail, rel in service_slas:
        if rel == "series":
            new_avail = current_availability * avail
        else:  # parallel (redundancy at this layer)
            # This service has redundancy already baked in
            new_avail = current_availability * avail
        dt = calc.downtime_per_year(new_avail)
        print(f"    + {name:25s} ({avail*100:.3f}%, {rel:8s}) "
              f"→ composite: {new_avail*100:.4f}% "
              f"({dt['minutes_per_year']:.1f} min/yr)")
        current_availability = new_avail


def demo_availability():
    """Demonstrate availability and reliability math."""
    print("\n" + "=" * 70)
    print(" 5. AVAILABILITY & RELIABILITY MATH")
    print("=" * 70)

    calc = AvailabilityCalculator()
    nines_table()

    # Series vs parallel
    print("\n  --- Series vs Parallel ---")
    a_single = 0.999
    series_4 = calc.series(a_single, a_single, a_single, a_single)
    parallel_2 = calc.parallel(a_single, a_single)

    print(f"  Single component:    {a_single*100:.3f}%")
    print(f"  4 in series:         {series_4*100:.3f}%  "
          f"({calc.downtime_per_year(series_4)['hours_per_year']:.1f} hrs/yr)")
    print(f"  2 in parallel:       {parallel_2*100:.6f}%  "
          f"({calc.downtime_per_year(parallel_2)['minutes_per_year']:.3f} min/yr)")

    # k-of-n
    print(f"\n  --- k-of-n Redundancy (component A=99.9%) ---")
    for k, n in [(2, 3), (3, 5), (2, 5)]:
        a = calc.k_of_n(k, n, 0.999)
        print(f"    {k}-of-{n}: {a*100:.6f}% ({calc.nines(a):.2f} nines)")

    # MTBF/MTTR
    print(f"\n  --- MTBF/MTTR Impact ---")
    for mtbf, mttr in [(720, 1), (720, 0.5), (720, 0.25), (2160, 1)]:
        a = calc.from_mtbf_mttr(mtbf, mttr)
        print(f"    MTBF={mtbf:5.0f}h, MTTR={mttr:5.2f}h → "
              f"A={a*100:.4f}% ({calc.nines(a):.2f} nines)")
    print("    → Halving MTTR is often easier than doubling MTBF!")

    # Error budget
    print(f"\n  --- Error Budget (SLO=99.9%, 30-day window) ---")
    eb = ErrorBudget(99.9)
    print(f"    Error budget: {eb.budget_seconds:.0f}s = "
          f"{eb.budget_seconds/60:.1f} min/month")

    for rate in [0.0005, 0.001, 0.003, 0.01, 0.05]:
        alert = eb.multi_window_alert(rate)
        status = "PAGE" if alert["page_1h"] else ("TICKET" if alert["ticket_1d"] else "OK")
        print(f"    Error rate {rate:.2%}: burn_rate={alert['burn_rate']:.1f}x, "
              f"exhaust in {alert['time_to_exhaustion_hours']:.1f}h → {status}")

    # SLA composition
    sla_composition([
        ("CDN/Edge", 0.9999, "series"),
        ("Load Balancer (pair)", 0.99999, "series"),
        ("API Gateway", 0.9995, "series"),
        ("Auth Service", 0.9995, "series"),
        ("App Server", 0.9990, "series"),
        ("Database (primary)", 0.9999, "series"),
    ])

    # Markov model
    print(f"\n  --- Markov Availability Model ---")
    result = markov_availability(failure_rate=1/720, repair_rate=1/0.5)
    print(f"    MTBF={result['mtbf_hours']:.0f}h, MTTR={result['mttr_hours']:.1f}h")
    print(f"    Steady-state availability: {result['availability']*100:.4f}%")
    print(f"    Nines: {result['nines']:.2f}")


# ============================================================================
# 6. LOAD TESTING MATHEMATICS (~200 lines)
# ============================================================================
"""
┌─────────────────────────────────────────────────────────────────────┐
│                 LOAD TESTING MATH                                   │
│                                                                     │
│  Open vs Closed Workload:                                           │
│    Open:   arrivals independent of system state (real traffic)      │
│    Closed: fixed number of users, new request after response        │
│                                                                     │
│  Open workload (correct model):                                     │
│    Throughput = arrival_rate (constant)                              │
│    If system slows → queue grows → latency explodes                │
│                                                                     │
│  Closed workload (most tools default):                              │
│    Throughput = N / (think_time + response_time)                    │
│    If system slows → throughput DROPS → hides problems!            │
│                                                                     │
│  Tools: wrk2 (open), Gatling (configurable), k6 (configurable)    │
└─────────────────────────────────────────────────────────────────────┘
"""


class LoadTestAnalyzer:
    """Analyze load test results with statistical rigor."""

    @staticmethod
    def saturation_point(load_levels: List[float],
                         latencies: List[float]) -> Tuple[float, int]:
        """
        Detect saturation point (knee of the curve).

        Uses second derivative: where curvature is maximum.
        The "knee" is where latency starts growing super-linearly.
        """
        if len(load_levels) < 3:
            return load_levels[-1], len(load_levels) - 1

        # Compute second differences (discrete second derivative)
        second_diffs = []
        for i in range(1, len(latencies) - 1):
            d2 = (latencies[i + 1] - 2 * latencies[i] + latencies[i - 1])
            dx = (load_levels[i + 1] - load_levels[i - 1]) / 2
            if dx > 0:
                second_diffs.append(d2 / (dx ** 2))
            else:
                second_diffs.append(0)

        # Knee = point of maximum second derivative
        max_idx = second_diffs.index(max(second_diffs))
        knee_idx = max_idx + 1  # offset due to second derivative
        return load_levels[knee_idx], knee_idx

    @staticmethod
    def throughput_curve(max_capacity: float, utilizations: List[float]) -> List[dict]:
        """Generate throughput vs latency curve (M/M/1 model)."""
        results = []
        mu = max_capacity
        for rho in utilizations:
            if rho >= 1.0:
                continue
            lam = rho * mu
            q = MM1Queue(lam, mu)
            results.append({
                "utilization": rho,
                "throughput": lam,
                "avg_latency_ms": q.avg_time_in_system() * 1000,
                "p99_latency_ms": -math.log(0.01) / (mu * (1 - rho)) * 1000,
            })
        return results

    @staticmethod
    def is_regression_significant(baseline: List[float], candidate: List[float],
                                  confidence: float = 0.95) -> dict:
        """
        Is a latency regression statistically significant?

        Uses Mann-Whitney U test (non-parametric, no normality assumption).
        Appropriate for latency data which is typically NOT normally distributed.
        """
        n1, n2 = len(baseline), len(candidate)

        # Mann-Whitney U statistic
        u_stat = 0
        for b in baseline:
            for c in candidate:
                if b < c:
                    u_stat += 1
                elif b == c:
                    u_stat += 0.5

        # Expected U under null hypothesis
        expected_u = n1 * n2 / 2
        # Standard deviation of U
        std_u = math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)

        if std_u == 0:
            return {"significant": False, "z_score": 0, "p_value": 1.0}

        # Z-score (normal approximation for large samples)
        z = (u_stat - expected_u) / std_u

        # Two-tailed p-value (using normal approximation)
        p_value = 2 * (1 - _normal_cdf(abs(z)))

        alpha = 1.0 - confidence
        return {
            "significant": p_value < alpha,
            "z_score": z,
            "p_value": p_value,
            "baseline_median": sorted(baseline)[len(baseline) // 2],
            "candidate_median": sorted(candidate)[len(candidate) // 2],
            "diff_percent": ((statistics.mean(candidate) - statistics.mean(baseline))
                             / statistics.mean(baseline) * 100),
        }

    @staticmethod
    def bootstrap_percentile_ci(data: List[float], percentile: float,
                                confidence: float = 0.95,
                                n_bootstrap: int = 1000,
                                seed: int = 42) -> Tuple[float, float]:
        """
        Bootstrap confidence interval for a percentile.

        Resamples data with replacement to estimate the sampling
        distribution of the percentile statistic.
        """
        rng = random.Random(seed)
        n = len(data)
        bootstrap_percentiles = []

        for _ in range(n_bootstrap):
            sample = [data[rng.randint(0, n - 1)] for _ in range(n)]
            sample.sort()
            idx = int(percentile / 100 * n)
            bootstrap_percentiles.append(sample[min(idx, n - 1)])

        bootstrap_percentiles.sort()
        alpha = 1.0 - confidence
        lo_idx = int(alpha / 2 * n_bootstrap)
        hi_idx = int((1 - alpha / 2) * n_bootstrap) - 1

        return bootstrap_percentiles[lo_idx], bootstrap_percentiles[hi_idx]


def _normal_cdf(x: float) -> float:
    """Approximation of standard normal CDF."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2)))


def open_vs_closed_workload():
    """
    Demonstrate difference between open and closed workload models.
    """
    print("\n  --- Open vs Closed Workload Models ---")

    mu = 100  # service rate

    # Open workload: fixed arrival rate
    print("\n  Open workload (arrival rate constant regardless of latency):")
    print(f"  {'λ (req/s)':>10} {'ρ':>6} {'Wq (ms)':>10} {'Throughput':>12}")
    print(f"  {'─'*10} {'─'*6} {'─'*10} {'─'*12}")
    for lam in [50, 70, 80, 90, 95, 98]:
        rho = lam / mu
        q = MM1Queue(lam, mu)
        print(f"  {lam:10d} {rho:6.2f} {q.avg_wait_time()*1000:10.1f} {lam:12d}")

    # Closed workload: N users with think time
    print("\n  Closed workload (N=100 users, think_time=100ms):")
    print(f"  {'N users':>8} {'Think(ms)':>10} {'Resp(ms)':>10} {'λ effective':>12}")
    print(f"  {'─'*8} {'─'*10} {'─'*10} {'─'*12}")
    n_users = 100
    for think_ms in [100, 50, 20, 10]:
        # Iteratively solve: λ = N/(think_time + W(λ))
        lam = n_users / (think_ms / 1000 + 1 / mu)  # initial guess
        for _ in range(50):  # iterate to convergence
            if lam >= mu:
                lam = mu * 0.99
            rho = lam / mu
            w = 1 / (mu - lam)
            lam_new = n_users / (think_ms / 1000 + w)
            if abs(lam_new - lam) < 0.01:
                break
            lam = lam_new
        w_ms = 1 / (mu - lam) * 1000 if lam < mu else float('inf')
        print(f"  {n_users:8d} {think_ms:10d} {w_ms:10.1f} {lam:12.1f}")

    print("\n  ⚠ Closed workload: throughput drops as latency increases")
    print("  → This HIDES saturation! Always use open workload for testing")


def demo_load_testing():
    """Demonstrate load testing mathematics."""
    print("\n" + "=" * 70)
    print(" 6. LOAD TESTING MATHEMATICS")
    print("=" * 70)

    analyzer = LoadTestAnalyzer()

    # Throughput curve
    print("\n  --- Throughput vs Latency Curve ---")
    utils = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.98]
    results = analyzer.throughput_curve(1000, utils)
    print(f"  {'ρ':>6} {'Throughput':>12} {'Avg(ms)':>10} {'P99(ms)':>10}  Latency")
    print(f"  {'─'*6} {'─'*12} {'─'*10} {'─'*10}  {'─'*25}")
    for r in results:
        bar = "█" * min(int(r['avg_latency_ms'] / 2), 25)
        print(f"  {r['utilization']:6.0%} {r['throughput']:12.0f} "
              f"{r['avg_latency_ms']:10.2f} {r['p99_latency_ms']:10.2f}  {bar}")

    # Saturation detection
    loads = [r['throughput'] for r in results]
    lats = [r['avg_latency_ms'] for r in results]
    knee, _ = analyzer.saturation_point(loads, lats)
    print(f"\n  Saturation point (knee): ~{knee:.0f} req/s")

    # Regression detection
    print("\n  --- Statistical Regression Detection ---")
    rng = random.Random(42)
    baseline = [rng.lognormvariate(math.log(5), 0.3) for _ in range(500)]
    # 5% regression
    candidate = [rng.lognormvariate(math.log(5.25), 0.3) for _ in range(500)]

    result = analyzer.is_regression_significant(baseline, candidate)
    print(f"    Baseline median: {result['baseline_median']:.2f} ms")
    print(f"    Candidate median: {result['candidate_median']:.2f} ms")
    print(f"    Difference: {result['diff_percent']:.1f}%")
    print(f"    Z-score: {result['z_score']:.3f}")
    print(f"    P-value: {result['p_value']:.6f}")
    print(f"    Significant (95%): {result['significant']}")

    # Bootstrap CI
    print("\n  --- Bootstrap CI for P99 ---")
    lo, hi = analyzer.bootstrap_percentile_ci(baseline, 99)
    print(f"    P99 95% CI: [{lo:.2f}, {hi:.2f}] ms")

    # Open vs closed
    open_vs_closed_workload()


# ============================================================================
# 7. CAPACITY PLANNING MODELS (~200 lines)
# ============================================================================
"""
┌─────────────────────────────────────────────────────────────────────┐
│              CAPACITY PLANNING                                      │
│                                                                     │
│  Core question: How much capacity do we need?                       │
│                                                                     │
│  Demand forecasting:                                                │
│    - Linear trend: y = a + bt                                       │
│    - Exponential growth: y = a·e^(bt)                              │
│    - Seasonal decomposition                                         │
│                                                                     │
│  Headroom:                                                          │
│    Required = Peak × (1 + safety_margin) / target_utilization      │
│                                                                     │
│  Key formula:                                                       │
│    Servers = ⌈peak_rps × latency_target / target_util⌉            │
│    (This is Little's Law + utilization target)                      │
└─────────────────────────────────────────────────────────────────────┘
"""


class CapacityPlanner:
    """Models for capacity planning and demand forecasting."""

    @staticmethod
    def linear_forecast(historical: List[Tuple[float, float]],
                        future_t: float) -> Tuple[float, float, float]:
        """
        Simple linear regression forecast.
        Returns (predicted_value, slope, r_squared).
        """
        n = len(historical)
        sum_x = sum(t for t, _ in historical)
        sum_y = sum(y for _, y in historical)
        sum_xy = sum(t * y for t, y in historical)
        sum_x2 = sum(t * t for t, _ in historical)

        denom = n * sum_x2 - sum_x ** 2
        if denom == 0:
            return sum_y / n, 0, 0

        slope = (n * sum_xy - sum_x * sum_y) / denom
        intercept = (sum_y - slope * sum_x) / n

        # R-squared
        y_mean = sum_y / n
        ss_tot = sum((y - y_mean) ** 2 for _, y in historical)
        ss_res = sum((y - (intercept + slope * t)) ** 2 for t, y in historical)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0

        prediction = intercept + slope * future_t
        return prediction, slope, r_squared

    @staticmethod
    def exponential_forecast(historical: List[Tuple[float, float]],
                             future_t: float) -> Tuple[float, float]:
        """
        Exponential growth forecast: y = a·e^(bt)
        Uses log-linear regression.
        Returns (predicted_value, growth_rate).
        """
        log_data = [(t, math.log(y)) for t, y in historical if y > 0]
        n = len(log_data)

        sum_x = sum(t for t, _ in log_data)
        sum_y = sum(y for _, y in log_data)
        sum_xy = sum(t * y for t, y in log_data)
        sum_x2 = sum(t * t for t, _ in log_data)

        denom = n * sum_x2 - sum_x ** 2
        if denom == 0:
            return math.exp(sum_y / n), 0

        b = (n * sum_xy - sum_x * sum_y) / denom
        log_a = (sum_y - b * sum_x) / n

        prediction = math.exp(log_a + b * future_t)
        return prediction, b

    @staticmethod
    def headroom_calculation(peak_rps: float, service_rate_per_server: float,
                             target_utilization: float = 0.7,
                             safety_margin: float = 0.2) -> dict:
        """
        Calculate required servers with headroom.

        servers = ⌈peak × (1+safety) / (rate_per_server × target_util)⌉
        """
        effective_capacity = service_rate_per_server * target_utilization
        required = peak_rps * (1 + safety_margin) / effective_capacity
        servers = int(math.ceil(required))

        return {
            "peak_rps": peak_rps,
            "servers_needed": servers,
            "total_capacity": servers * service_rate_per_server,
            "effective_capacity": servers * effective_capacity,
            "actual_utilization": peak_rps / (servers * service_rate_per_server),
            "headroom_pct": (1 - peak_rps / (servers * service_rate_per_server)) * 100,
        }

    @staticmethod
    def autoscale_thresholds(target_util: float = 0.7,
                             scale_up_buffer: float = 0.1,
                             scale_down_buffer: float = 0.2) -> dict:
        """
        Calculate auto-scaling trigger thresholds.

        Scale up when: utilization > target + buffer
        Scale down when: utilization < target - buffer
        (asymmetric to avoid flapping)
        """
        return {
            "target_utilization": target_util,
            "scale_up_threshold": target_util + scale_up_buffer,
            "scale_down_threshold": target_util - scale_down_buffer,
            "cooldown_recommendation_s": 300,  # 5 minutes
        }

    @staticmethod
    def bin_pack_servers(workloads: List[Tuple[str, float, float]],
                         server_capacity: float) -> List[List[Tuple[str, float, float]]]:
        """
        First-Fit Decreasing bin packing for server allocation.

        workloads: list of (name, cpu_need, memory_need)
        Returns: list of servers, each containing assigned workloads

        FFD is a 11/9·OPT + 6/9 approximation.
        """
        # Sort by CPU (primary) descending
        sorted_workloads = sorted(workloads, key=lambda w: w[1], reverse=True)
        servers: List[List[Tuple[str, float, float]]] = []
        server_usage: List[float] = []

        for wl in sorted_workloads:
            name, cpu, mem = wl
            placed = False
            for i, usage in enumerate(server_usage):
                if usage + cpu <= server_capacity:
                    servers[i].append(wl)
                    server_usage[i] += cpu
                    placed = True
                    break
            if not placed:
                servers.append([wl])
                server_usage.append(cpu)

        return servers

    @staticmethod
    def spot_instance_savings(on_demand_cost: float, spot_cost: float,
                              interruption_rate_per_hour: float,
                              recovery_time_minutes: float,
                              workload_hours: int) -> dict:
        """
        Model cost savings from spot/preemptible instances.

        Expected interruptions = workload_hours × rate
        Cost of interruption = recovery_time × on_demand_cost + lost_work
        """
        expected_interruptions = workload_hours * interruption_rate_per_hour
        recovery_hours = recovery_time_minutes / 60
        recovery_cost = expected_interruptions * recovery_hours * on_demand_cost

        spot_total = workload_hours * spot_cost + recovery_cost
        on_demand_total = workload_hours * on_demand_cost
        savings = on_demand_total - spot_total

        return {
            "on_demand_total": on_demand_total,
            "spot_total": spot_total,
            "savings": savings,
            "savings_pct": savings / on_demand_total * 100 if on_demand_total > 0 else 0,
            "expected_interruptions": expected_interruptions,
            "break_even_interruption_rate": (
                (on_demand_cost - spot_cost) /
                (recovery_hours * on_demand_cost)
                if recovery_hours > 0 else float('inf')
            ),
        }


def demo_capacity_planning():
    """Demonstrate capacity planning models."""
    print("\n" + "=" * 70)
    print(" 7. CAPACITY PLANNING MODELS")
    print("=" * 70)

    cp = CapacityPlanner()

    # Demand forecasting
    print("\n  --- Demand Forecasting ---")
    # Quarterly traffic data (months, requests/s)
    historical = [(1, 1000), (2, 1100), (3, 1250), (4, 1350),
                  (5, 1500), (6, 1680), (7, 1850), (8, 2050),
                  (9, 2300), (10, 2550), (11, 2800), (12, 3100)]

    # Linear forecast
    pred_lin, slope, r2 = cp.linear_forecast(historical, 18)
    print(f"  Linear forecast (month 18): {pred_lin:.0f} req/s "
          f"(slope={slope:.0f}/month, R²={r2:.3f})")

    # Exponential forecast
    pred_exp, growth = cp.exponential_forecast(historical, 18)
    print(f"  Exponential forecast (month 18): {pred_exp:.0f} req/s "
          f"(growth={growth*100:.1f}%/month)")

    # Headroom calculation
    print("\n  --- Headroom Calculation ---")
    peak = 5000
    result = cp.headroom_calculation(peak, 200, target_utilization=0.7)
    print(f"  Peak: {peak} req/s, Server capacity: 200 req/s")
    print(f"  Servers needed:     {result['servers_needed']}")
    print(f"  Total capacity:     {result['total_capacity']} req/s")
    print(f"  Actual utilization: {result['actual_utilization']:.1%}")
    print(f"  Headroom:           {result['headroom_pct']:.1f}%")

    # Auto-scale thresholds
    print("\n  --- Auto-Scale Thresholds ---")
    thresholds = cp.autoscale_thresholds(0.7, 0.1, 0.2)
    print(f"  Scale UP when:   utilization > {thresholds['scale_up_threshold']:.0%}")
    print(f"  Scale DOWN when: utilization < {thresholds['scale_down_threshold']:.0%}")
    print(f"  Cooldown: {thresholds['cooldown_recommendation_s']}s (prevent flapping)")

    # Bin packing
    print("\n  --- Bin Packing: Server Allocation ---")
    workloads = [
        ("API-1", 0.3, 2.0), ("API-2", 0.25, 1.5), ("Worker-1", 0.4, 3.0),
        ("Worker-2", 0.35, 2.5), ("Cache", 0.15, 4.0), ("Logger", 0.1, 0.5),
        ("Monitor", 0.05, 0.3), ("Scheduler", 0.2, 1.0),
    ]
    servers = cp.bin_pack_servers(workloads, 0.8)
    for i, server in enumerate(servers):
        total_cpu = sum(cpu for _, cpu, _ in server)
        names = ", ".join(n for n, _, _ in server)
        print(f"    Server {i+1}: [{names}] CPU={total_cpu:.2f}")

    # Spot instance savings
    print("\n  --- Spot Instance Cost Analysis ---")
    spot = cp.spot_instance_savings(
        on_demand_cost=0.50,  # $/hr
        spot_cost=0.15,       # $/hr (70% discount)
        interruption_rate_per_hour=0.05,  # 5% chance/hr
        recovery_time_minutes=10,
        workload_hours=720    # 1 month
    )
    print(f"  On-demand total: ${spot['on_demand_total']:.0f}")
    print(f"  Spot total:      ${spot['spot_total']:.0f}")
    print(f"  Savings:         ${spot['savings']:.0f} ({spot['savings_pct']:.0f}%)")
    print(f"  Expected interruptions: {spot['expected_interruptions']:.0f}")
    print(f"  Break-even interruption rate: {spot['break_even_interruption_rate']:.2f}/hr")


# ============================================================================
# 8. NETWORK RELIABILITY (~150 lines)
# ============================================================================
"""
┌─────────────────────────────────────────────────────────────────────┐
│              NETWORK RELIABILITY PATTERNS                           │
│                                                                     │
│  Retry strategies:                                                  │
│    - Exponential backoff: delay = base × 2^attempt                 │
│    - With jitter: prevents thundering herd                         │
│    - With budget: max_retries = (capacity-baseline)/baseline       │
│                                                                     │
│  Circuit breaker:                                                   │
│    CLOSED → OPEN (failures exceed threshold)                       │
│    OPEN → HALF-OPEN (after timeout)                                │
│    HALF-OPEN → CLOSED (if probe succeeds)                          │
│    HALF-OPEN → OPEN (if probe fails)                               │
│                                                                     │
│  TCP RTO (Jacobson/Karn):                                          │
│    SRTT = (1-α)·SRTT + α·RTT     (α=1/8)                         │
│    RTTVAR = (1-β)·RTTVAR + β·|SRTT-RTT|  (β=1/4)                 │
│    RTO = SRTT + max(G, 4·RTTVAR)                                  │
└─────────────────────────────────────────────────────────────────────┘
"""


class ExponentialBackoff:
    """Exponential backoff with jitter variants."""

    @staticmethod
    def full_jitter(base_ms: float, attempt: int, cap_ms: float = 30000,
                    seed: int = None) -> float:
        """
        Full jitter: delay = random(0, min(cap, base × 2^attempt))

        Best for reducing contention. Most uniform spread.
        """
        rng = random.Random(seed) if seed else random
        exp_delay = min(cap_ms, base_ms * (2 ** attempt))
        return rng.uniform(0, exp_delay)

    @staticmethod
    def equal_jitter(base_ms: float, attempt: int, cap_ms: float = 30000,
                     seed: int = None) -> float:
        """
        Equal jitter: delay = exp_delay/2 + random(0, exp_delay/2)

        Guarantees minimum delay while still reducing correlation.
        """
        rng = random.Random(seed) if seed else random
        exp_delay = min(cap_ms, base_ms * (2 ** attempt))
        return exp_delay / 2 + rng.uniform(0, exp_delay / 2)

    @staticmethod
    def decorrelated_jitter(base_ms: float, previous_delay_ms: float,
                            cap_ms: float = 30000, seed: int = None) -> float:
        """
        Decorrelated jitter: delay = random(base, previous × 3)

        Each delay depends on previous, creating less bursty patterns.
        """
        rng = random.Random(seed) if seed else random
        return min(cap_ms, rng.uniform(base_ms, previous_delay_ms * 3))

    @staticmethod
    def retry_budget(capacity_rps: float, baseline_rps: float) -> float:
        """
        Maximum safe retry rate.

        retry_budget = (capacity - baseline) / baseline

        If capacity=1000 and baseline=700:
          budget = 300/700 = 0.43 → max 43% of requests can retry
        """
        if baseline_rps <= 0:
            return float('inf')
        return (capacity_rps - baseline_rps) / baseline_rps


class CircuitBreaker:
    """
    Circuit breaker state machine with failure rate tracking.

    States:
      CLOSED    → normal operation, tracking failure rate
      OPEN      → all requests fail fast (no backend calls)
      HALF_OPEN → probe: allow one request through to test
    """

    def __init__(self, failure_threshold: float = 0.5,
                 window_size: int = 100,
                 recovery_timeout_s: float = 30.0):
        self.failure_threshold = failure_threshold
        self.window_size = window_size
        self.recovery_timeout_s = recovery_timeout_s
        self.state = "CLOSED"
        self.failures = 0
        self.successes = 0
        self.total_in_window = 0
        self.last_failure_time = 0.0

    def record_success(self, current_time: float = 0):
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            self.failures = 0
            self.successes = 0
            self.total_in_window = 0
        elif self.state == "CLOSED":
            self.successes += 1
            self.total_in_window += 1
            self._check_window()

    def record_failure(self, current_time: float = 0):
        self.failures += 1
        self.total_in_window += 1
        self.last_failure_time = current_time

        if self.state == "HALF_OPEN":
            self.state = "OPEN"
        elif self.state == "CLOSED":
            self._check_window()
            if self.total_in_window >= 10:  # min samples
                failure_rate = self.failures / self.total_in_window
                if failure_rate >= self.failure_threshold:
                    self.state = "OPEN"

    def should_allow(self, current_time: float = 0) -> bool:
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if current_time - self.last_failure_time >= self.recovery_timeout_s:
                self.state = "HALF_OPEN"
                return True
            return False
        else:  # HALF_OPEN
            return True

    def _check_window(self):
        if self.total_in_window > self.window_size:
            # Sliding window approximation: halve counts
            self.failures //= 2
            self.successes //= 2
            self.total_in_window = self.failures + self.successes


class TCPRetransmission:
    """
    TCP RTO calculation (Jacobson/Karn algorithm, RFC 6298).

    SRTT    = smoothed RTT (moving average)
    RTTVAR  = RTT variance estimate
    RTO     = retransmission timeout

    Initial: RTO = 1 second
    After first measurement:
      SRTT = R (measured RTT)
      RTTVAR = R/2
      RTO = SRTT + max(G, 4·RTTVAR)

    Subsequent:
      RTTVAR = (1-β)·RTTVAR + β·|SRTT - R|     (β = 1/4)
      SRTT = (1-α)·SRTT + α·R                   (α = 1/8)
      RTO = SRTT + max(G, 4·RTTVAR)

    On timeout: RTO = RTO × 2 (exponential backoff)
    """

    def __init__(self, clock_granularity_ms: float = 1.0):
        self.srtt: Optional[float] = None
        self.rttvar: Optional[float] = None
        self.rto: float = 1000.0  # Initial 1 second
        self.g = clock_granularity_ms
        self.alpha = 1 / 8
        self.beta = 1 / 4
        self.history: List[dict] = []

    def update(self, rtt_ms: float) -> float:
        """Update estimates with new RTT measurement."""
        if self.srtt is None:
            # First measurement
            self.srtt = rtt_ms
            self.rttvar = rtt_ms / 2
        else:
            self.rttvar = (1 - self.beta) * self.rttvar + self.beta * abs(self.srtt - rtt_ms)
            self.srtt = (1 - self.alpha) * self.srtt + self.alpha * rtt_ms

        self.rto = self.srtt + max(self.g, 4 * self.rttvar)
        self.rto = max(self.rto, 200)  # minimum 200ms per RFC

        self.history.append({
            "rtt": rtt_ms, "srtt": self.srtt,
            "rttvar": self.rttvar, "rto": self.rto,
        })
        return self.rto

    def timeout_backoff(self):
        """Double RTO on timeout (exponential backoff)."""
        self.rto = min(self.rto * 2, 60000)  # cap at 60s
        return self.rto


def thundering_herd_analysis(num_clients: int, cache_ttl_s: float,
                             request_rate_per_client: float) -> dict:
    """
    Thundering herd: cache expires → all clients hit backend simultaneously.

    Mitigation strategies:
      1. Jittered TTL: TTL = base + random(0, jitter)
      2. Stale-while-revalidate: serve stale, refresh async
      3. Probabilistic early expiry: refresh at TTL - random(0, β·ln(random))
      4. Locking: only one client refreshes, others wait
    """
    simultaneous_requests = num_clients * request_rate_per_client * 0.1
    # With jitter (uniform TTL spread)
    jitter_range = cache_ttl_s * 0.1  # 10% jitter
    spread_requests = simultaneous_requests * (0.1 / jitter_range) if jitter_range > 0 else simultaneous_requests

    return {
        "without_mitigation": {
            "simultaneous_requests": int(simultaneous_requests),
            "description": "All clients expire at same time",
        },
        "with_jittered_ttl": {
            "peak_requests": int(spread_requests),
            "jitter_range_s": jitter_range,
            "description": f"Spread over {jitter_range:.1f}s window",
        },
        "probabilistic_early_refresh": {
            "description": "Refresh probability increases as TTL approaches",
            "formula": "P(refresh) = 1 - exp(-β·Δ·ln(rand))",
        },
    }


def demo_network_reliability():
    """Demonstrate network reliability patterns."""
    print("\n" + "=" * 70)
    print(" 8. NETWORK RELIABILITY")
    print("=" * 70)

    # Exponential backoff comparison
    print("\n  --- Exponential Backoff with Jitter ---")
    eb = ExponentialBackoff()
    print(f"  {'Attempt':>8} {'No Jitter':>12} {'Full':>12} {'Equal':>12} {'Decorr':>12}")
    print(f"  {'─'*8} {'─'*12} {'─'*12} {'─'*12} {'─'*12}")

    prev_delay = 100
    for attempt in range(8):
        no_jitter = min(30000, 100 * (2 ** attempt))
        full = eb.full_jitter(100, attempt, seed=42 + attempt)
        equal = eb.equal_jitter(100, attempt, seed=42 + attempt)
        decorr = eb.decorrelated_jitter(100, prev_delay, seed=42 + attempt)
        prev_delay = decorr
        print(f"  {attempt:8d} {no_jitter:10.0f}ms {full:10.0f}ms "
              f"{equal:10.0f}ms {decorr:10.0f}ms")

    # Retry budget
    print("\n  --- Retry Budget ---")
    for cap, base in [(1000, 700), (1000, 900), (1000, 500)]:
        budget = eb.retry_budget(cap, base)
        print(f"    Capacity={cap}, Baseline={base} → "
              f"Budget={budget:.2f} ({budget*100:.0f}% of requests can retry)")

    # Circuit breaker simulation
    print("\n  --- Circuit Breaker Simulation ---")
    cb = CircuitBreaker(failure_threshold=0.5, window_size=20,
                        recovery_timeout_s=5.0)
    rng = random.Random(42)

    states_log = []
    for t in range(40):
        allowed = cb.should_allow(t)
        if allowed:
            # Simulate: first 10 OK, then 60% failure, then recovery
            if t < 10:
                fail = rng.random() < 0.1
            elif t < 25:
                fail = rng.random() < 0.7
            else:
                fail = rng.random() < 0.1

            if fail:
                cb.record_failure(t)
            else:
                cb.record_success(t)
        states_log.append((t, cb.state, allowed))

    print(f"  {'Time':>6} {'State':>12} {'Allowed':>8}")
    print(f"  {'─'*6} {'─'*12} {'─'*8}")
    for t, state, allowed in states_log[::2]:  # show every other
        print(f"  {t:6d} {state:>12} {'Yes' if allowed else 'No':>8}")

    # TCP RTO
    print("\n  --- TCP RTO Calculation (Jacobson/Karn) ---")
    tcp = TCPRetransmission()
    rtts = [50, 55, 48, 52, 100, 53, 49, 51, 200, 52, 50, 51]
    print(f"  {'RTT(ms)':>8} {'SRTT':>8} {'RTTVAR':>8} {'RTO':>8}")
    print(f"  {'─'*8} {'─'*8} {'─'*8} {'─'*8}")
    for rtt in rtts:
        rto = tcp.update(rtt)
        h = tcp.history[-1]
        print(f"  {rtt:8.0f} {h['srtt']:8.1f} {h['rttvar']:8.1f} {rto:8.1f}")

    # Thundering herd
    print("\n  --- Thundering Herd Analysis ---")
    herd = thundering_herd_analysis(num_clients=10000, cache_ttl_s=300,
                                    request_rate_per_client=1.0)
    print(f"  Without mitigation: {herd['without_mitigation']['simultaneous_requests']} "
          f"simultaneous requests")
    print(f"  With jittered TTL:  {herd['with_jittered_ttl']['peak_requests']} peak "
          f"(spread over {herd['with_jittered_ttl']['jitter_range_s']:.0f}s)")


# ============================================================================
# 9. INTERVIEW PROBLEMS & PRACTICE
# ============================================================================
"""
┌─────────────────────────────────────────────────────────────────────┐
│             INTERVIEW PROBLEMS - RELIABILITY MATH                   │
│                                                                     │
│  Common question types:                                             │
│    1. "Design SLA for multi-service system"                        │
│    2. "How many servers for X req/s at Y ms P99?"                  │
│    3. "Why does latency spike at 80% CPU?"                         │
│    4. "Size the connection pool / thread pool"                     │
│    5. "What's the availability of this architecture?"              │
│    6. "Explain tail latency with fan-out"                          │
└─────────────────────────────────────────────────────────────────────┘
"""


def interview_problems():
    """Walk through common interview problems."""
    print("\n" + "=" * 70)
    print(" INTERVIEW PROBLEMS - RELIABILITY & PERFORMANCE")
    print("=" * 70)

    # Problem 1: Capacity Planning
    print("\n  ── Problem 1: Capacity Planning ──")
    print("  Q: Service handles 10,000 req/s at P50=5ms. Each server")
    print("     handles 500 req/s. Target: P99 < 50ms, 99.99% available.")
    print()
    print("  Solution:")
    ll = LittlesLaw()
    concurrent = ll.concurrent_requests(10000, 0.005)
    print(f"    Concurrent requests (Little's): L = 10000 × 0.005 = {concurrent:.0f}")

    servers_min = math.ceil(10000 / 500)
    print(f"    Minimum servers: 10000/500 = {servers_min}")

    cp = CapacityPlanner()
    result = cp.headroom_calculation(10000, 500, 0.7, 0.2)
    print(f"    With headroom (70% util, 20% safety): {result['servers_needed']} servers")

    ac = AvailabilityCalculator()
    # Need 99.99% → use redundancy
    a_single = 0.999
    servers_for_avail = result['servers_needed']
    k = servers_min  # need at least this many working
    a_system = ac.k_of_n(k, servers_for_avail, a_single)
    print(f"    {k}-of-{servers_for_avail} availability (A_server=99.9%): "
          f"{a_system*100:.4f}%")

    # Problem 2: Why 80% CPU is bad
    print("\n  ── Problem 2: Why 80% CPU Utilization is Dangerous ──")
    print("  Answer using M/M/1 model:")
    for rho in [0.5, 0.7, 0.8, 0.9, 0.95]:
        q = MM1Queue(rho * 100, 100)
        print(f"    ρ={rho:.0%}: Avg wait = {q.avg_wait_time()*1000:.1f}ms, "
              f"Queue length = {q.avg_number_in_queue():.1f}")
    print("    → Non-linear growth. At 80%→90%: wait DOUBLES.")
    print("    → At 90%→95%: wait DOUBLES again!")

    # Problem 3: Fan-out tail latency
    print("\n  ── Problem 3: Tail Latency with 100-way Fan-out ──")
    print("  Q: Backend P99=10ms. User request fans out to 100 backends.")
    print("     What latency does the user see?")
    p_slow = tail_at_scale(0.01, 100)
    print(f"    P(at least 1 slow) = 1 - 0.99^100 = {p_slow:.1%}")
    print(f"    User's effective P50 includes a tail event!")
    mc = monte_carlo_tail_latency(fan_out=100, num_trials=5000)
    for p, val in mc.items():
        print(f"    User P{p}: {val*1000:.1f}ms")
    print("    → Mitigation: hedged requests, shorter timeouts, caching")

    # Problem 4: Connection pool sizing
    print("\n  ── Problem 4: Database Connection Pool ──")
    print("  Q: API server at 2000 req/s, each query takes 5ms avg.")
    print("     How many DB connections per server (10 API servers)?")
    per_server_rps = 2000 / 10
    pool = ll.connection_pool_size(per_server_rps, 0.005, safety_factor=2.0)
    print(f"    Per-server throughput: {per_server_rps} req/s")
    print(f"    L = {per_server_rps} × 0.005 = {per_server_rps * 0.005:.0f}")
    print(f"    Pool size (2x safety): {pool}")
    print(f"    Total connections: {pool * 10} (watch DB max_connections!)")

    # Problem 5: SLA composition
    print("\n  ── Problem 5: Composite SLA ──")
    print("  Q: CDN(99.99%) → LB(99.999%) → API(99.95%) → DB(99.99%)")
    components = [0.9999, 0.99999, 0.9995, 0.9999]
    composite = ac.series(*components)
    dt = ac.downtime_per_year(composite)
    print(f"    Composite: {composite*100:.4f}%")
    print(f"    Downtime: {dt['hours_per_year']:.1f} hours/year")
    print(f"    Nines: {ac.nines(composite):.2f}")
    print("    → Weakest link (API at 99.95%) dominates!")


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 70)
    print(" RELIABILITY MATH & PERFORMANCE MODELING")
    print(" Queueing Theory → Tail Latency → Availability → Capacity")
    print("=" * 70)

    # 1. Queueing Theory
    demo_mm1()
    utilization_vs_latency_curve()
    demo_mmc()
    demo_mg1_variance_impact()
    demo_priority_queue()

    # 2. Little's Law
    demo_littles_law()

    # 3. Tail Latency
    demo_tail_latency()

    # 4. Scaling Laws
    demo_scaling_laws()

    # 5. Availability
    demo_availability()

    # 6. Load Testing
    demo_load_testing()

    # 7. Capacity Planning
    demo_capacity_planning()

    # 8. Network Reliability
    demo_network_reliability()

    # 9. Interview Problems
    interview_problems()

    print("\n" + "=" * 70)
    print(" COMPLETE - All sections executed successfully")
    print("=" * 70)
    print("\n  Key Takeaways:")
    print("  1. Queueing: Latency grows NON-LINEARLY with utilization")
    print("  2. Little's Law: L=λW is universal for capacity planning")
    print("  3. Tail latency: P99 matters more than P50 at scale")
    print("  4. Amdahl/USL: Serial fraction limits all parallelism")
    print("  5. Availability: Series degrades, parallel improves")
    print("  6. Load testing: Open workload, not closed. Watch coordinated omission.")
    print("  7. Capacity: Target 60-70% utilization, not 90%+")
    print("  8. Retries: Budget them. Backoff with jitter. Circuit break.")


if __name__ == "__main__":
    main()
