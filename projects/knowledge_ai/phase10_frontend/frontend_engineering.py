#!/usr/bin/env python3
"""
Frontend Engineering - Comprehensive Learning Module
=====================================================
Learn React, Next.js, Web Performance, CSS Architecture,
State Management, Testing, and Security through Python simulations.

Python 3.9+ | No external dependencies | Run: python frontend_engineering.py
"""

import json
import time
import hashlib
import textwrap
from dataclasses import dataclass, field
from typing import Any, Optional, Callable
from enum import Enum
from collections import defaultdict


# ============================================================================
#  Utilities
# ============================================================================

def header(title: str, level: int = 1) -> None:
    width = 72
    if level == 1:
        print("\n" + "=" * width)
        print(f"  {title}")
        print("=" * width)
    elif level == 2:
        print(f"\n--- {title} ---")
    else:
        print(f"\n  > {title}")


def explain(text: str) -> None:
    for line in textwrap.dedent(text).strip().splitlines():
        print(f"    {line}")


def code_example(label: str, code: str) -> None:
    print(f"\n  [{label}]")
    for line in textwrap.dedent(code).strip().splitlines():
        print(f"    | {line}")
    print()


# ============================================================================
#  CHAPTER 1: React Core Concepts
# ============================================================================

def chapter1_react_core():
    header("CHAPTER 1: React Core Concepts")

    # --- 1.1 Virtual DOM ---
    header("1.1 Virtual DOM & Diff Algorithm", 2)
    explain("""
        React uses a Virtual DOM (VDOM) -- a lightweight in-memory tree that
        mirrors the real DOM. When state changes, React builds a new VDOM tree,
        diffs it against the old one, and applies only the minimal set of
        mutations to the real DOM.

        Below we simulate this with Python dicts as VDOM nodes.
    """)

    @dataclass
    class VNode:
        tag: str
        props: dict = field(default_factory=dict)
        children: list = field(default_factory=list)
        key: Optional[str] = None

        def to_dict(self) -> dict:
            return {
                "tag": self.tag,
                "props": self.props,
                "children": [
                    c.to_dict() if isinstance(c, VNode) else c
                    for c in self.children
                ],
            }

    def diff_vdom(old: Optional[VNode], new: Optional[VNode],
                  path: str = "root") -> list:
        """Return a list of patches describing what changed."""
        patches = []
        if old is None and new is not None:
            patches.append({"type": "CREATE", "path": path, "node": new.tag})
        elif old is not None and new is None:
            patches.append({"type": "REMOVE", "path": path})
        elif old is not None and new is not None:
            if old.tag != new.tag:
                patches.append({
                    "type": "REPLACE", "path": path,
                    "from": old.tag, "to": new.tag,
                })
            else:
                # Diff props
                all_keys = set(old.props) | set(new.props)
                for k in all_keys:
                    ov = old.props.get(k)
                    nv = new.props.get(k)
                    if ov != nv:
                        patches.append({
                            "type": "SET_PROP", "path": path,
                            "key": k, "old": ov, "new": nv,
                        })
                # Diff children
                max_len = max(len(old.children), len(new.children))
                for i in range(max_len):
                    oc = old.children[i] if i < len(old.children) else None
                    nc = new.children[i] if i < len(new.children) else None
                    if isinstance(oc, str) or isinstance(nc, str):
                        if oc != nc:
                            patches.append({
                                "type": "TEXT", "path": f"{path}/text[{i}]",
                                "old": oc, "new": nc,
                            })
                    else:
                        patches.extend(
                            diff_vdom(oc, nc, f"{path}/{(nc or oc).tag}[{i}]")
                        )
        return patches

    old_tree = VNode("div", {"class": "app"}, [
        VNode("h1", {}, ["Hello"]),
        VNode("p", {"style": "color:blue"}, ["World"]),
    ])
    new_tree = VNode("div", {"class": "app"}, [
        VNode("h1", {}, ["Hello, React!"]),
        VNode("p", {"style": "color:red"}, ["World"]),
        VNode("button", {"onClick": "handleClick"}, ["Click me"]),
    ])

    patches = diff_vdom(old_tree, new_tree)
    print("\n  Virtual DOM Diff Results:")
    for p in patches:
        print(f"    Patch: {json.dumps(p)}")

    explain("""
        Key takeaways:
        - React only updates what actually changed (minimal DOM mutations).
        - The 'key' prop helps React match children across re-renders.
        - O(n) heuristic: React compares trees level-by-level, not globally.
    """)

    # --- 1.2 Component Lifecycle ---
    header("1.2 Component Lifecycle Simulation", 2)
    explain("""
        Class component lifecycle (legacy but important to understand):
          constructor -> render -> componentDidMount
          (update) -> shouldComponentUpdate -> render -> componentDidUpdate
          (unmount) -> componentWillUnmount

        Function component equivalent with hooks:
          useState init -> render -> useEffect(setup)
          (update) -> render -> useEffect(cleanup then setup)
          (unmount) -> useEffect(cleanup)
    """)

    class SimulatedComponent:
        def __init__(self, name: str, initial_props: dict):
            self.name = name
            self.props = initial_props
            self.state: dict = {}
            self.mounted = False
            self._log: list = []

        def _emit(self, event: str):
            self._log.append(event)
            print(f"    [{self.name}] {event}")

        def mount(self):
            self._emit("constructor(props)")
            self._emit("render()")
            self.mounted = True
            self._emit("componentDidMount() -- side effects here")

        def update(self, new_props: dict):
            if not self.mounted:
                return
            old = self.props.copy()
            self._emit(f"shouldComponentUpdate({old} -> {new_props})")
            self.props = new_props
            self._emit("render()")
            self._emit("componentDidUpdate(prevProps, prevState)")

        def unmount(self):
            self._emit("componentWillUnmount() -- cleanup here")
            self.mounted = False

    print("\n  Simulating <UserCard> lifecycle:")
    card = SimulatedComponent("UserCard", {"userId": 1})
    card.mount()
    card.update({"userId": 2})
    card.unmount()

    # --- 1.3 Hooks Mental Model ---
    header("1.3 Hooks Mental Model", 2)
    explain("""
        Hooks let function components use state and side effects.
        Internally React stores hooks in an ordered array per component.
        This is why hooks cannot be called conditionally.
    """)

    class HooksRuntime:
        """Simulates React's hooks fiber for one component."""
        def __init__(self):
            self.hooks: list = []
            self.cursor: int = 0
            self.effects: list = []
            self.cleanups: list = []
            self.render_count: int = 0

        def reset_cursor(self):
            self.cursor = 0
            self.effects.clear()

        def use_state(self, initial):
            idx = self.cursor
            if idx >= len(self.hooks):
                self.hooks.append(initial)
            self.cursor += 1
            value = self.hooks[idx]

            def set_state(new_val):
                self.hooks[idx] = new_val

            return value, set_state

        def use_effect(self, callback: Callable, deps: Optional[list]):
            idx = self.cursor
            if idx >= len(self.hooks):
                self.hooks.append(None)  # prev deps
                self.effects.append(callback)
            else:
                prev_deps = self.hooks[idx]
                should_run = (
                    deps is None or prev_deps is None or
                    any(a != b for a, b in zip(deps, prev_deps))
                    or len(deps) != len(prev_deps)
                )
                if should_run:
                    self.effects.append(callback)
            self.hooks[idx] = deps
            self.cursor += 1

        def use_memo(self, factory: Callable, deps: list):
            idx = self.cursor
            if idx >= len(self.hooks):
                val = factory()
                self.hooks.append((val, deps))
                self.cursor += 1
                return val
            prev_val, prev_deps = self.hooks[idx]
            changed = any(a != b for a, b in zip(deps, prev_deps))
            if changed or len(deps) != len(prev_deps):
                val = factory()
                self.hooks[idx] = (val, deps)
                self.cursor += 1
                return val
            self.cursor += 1
            return prev_val

        def use_ref(self, initial=None):
            idx = self.cursor
            if idx >= len(self.hooks):
                ref = {"current": initial}
                self.hooks.append(ref)
            self.cursor += 1
            return self.hooks[idx]

        def flush_effects(self):
            for eff in self.effects:
                cleanup = eff()
                if callable(cleanup):
                    self.cleanups.append(cleanup)

    runtime = HooksRuntime()

    def counter_component(rt: HooksRuntime):
        rt.reset_cursor()
        rt.render_count += 1
        count, set_count = rt.use_state(0)
        label = rt.use_memo(lambda: f"Count is {count}", [count])
        render_ref = rt.use_ref(0)
        render_ref["current"] = rt.render_count
        rt.use_effect(lambda: print(f"      Effect: {label}"), [count])
        print(f"    Render #{rt.render_count}: {label}, "
              f"ref={render_ref['current']}")
        return count, set_count

    print("\n  Simulating hooks-based Counter component:")
    count, set_count = counter_component(runtime)
    runtime.flush_effects()
    set_count(1)
    count, set_count = counter_component(runtime)
    runtime.flush_effects()
    set_count(1)  # same value
    count, set_count = counter_component(runtime)
    runtime.flush_effects()

    explain("""
        useState   -- returns [value, setter]; triggers re-render on set.
        useEffect  -- runs after render when deps change; returns cleanup.
        useMemo    -- memoizes expensive computation; recomputes when deps change.
        useCallback-- useMemo but for functions (same mechanism).
        useRef     -- mutable container that persists across renders
                      without triggering re-render.
    """)

    # --- 1.4 Reconciliation ---
    header("1.4 Reconciliation Algorithm Basics", 2)
    explain("""
        React's reconciler uses two heuristics to achieve O(n) diffing:
        1. Elements of different types produce different trees (full replace).
        2. The 'key' prop hints which children are stable across renders.

        Without keys, React matches children by index, which causes
        unnecessary re-creation when items are reordered.
    """)

    def reconcile_children(old_keys: list, new_keys: list) -> list:
        ops = []
        old_set = set(old_keys)
        new_set = set(new_keys)
        for k in old_keys:
            if k not in new_set:
                ops.append(f"REMOVE <Item key={k}>")
        for k in new_keys:
            if k not in old_set:
                ops.append(f"INSERT <Item key={k}>")
        # Detect moves
        common = [k for k in new_keys if k in old_set]
        old_indices = {k: i for i, k in enumerate(old_keys) if k in new_set}
        for i, k in enumerate(common):
            if i > 0 and old_indices.get(k, 0) < old_indices.get(common[i-1], 0):
                ops.append(f"MOVE   <Item key={k}>")
        return ops

    print("\n  List reconciliation with keys:")
    print(f"    Old: [A, B, C, D]")
    print(f"    New: [D, A, C, E]")
    for op in reconcile_children(["A","B","C","D"], ["D","A","C","E"]):
        print(f"      {op}")

    # --- 1.5 React Server Components ---
    header("1.5 React Server Components (RSC)", 2)
    explain("""
        React Server Components (RSC) run ONLY on the server.
        They never ship JavaScript to the client.

        Benefits:
        - Zero client-side JS for server components
        - Direct database/filesystem access
        - Automatic code splitting
        - Streaming HTML to client

        Rules:
        - Server Components CANNOT use hooks (useState, useEffect)
        - Server Components CANNOT use browser APIs
        - Server Components CAN import Client Components
        - Client Components CANNOT import Server Components
          (but can accept them as children via props)
    """)
    code_example("Server Component (Next.js App Router)", """
        // app/users/page.tsx  (Server Component by default)
        async function UsersPage() {
          const users = await db.query('SELECT * FROM users'); // direct DB
          return (
            <div>
              {users.map(u => <UserCard key={u.id} user={u} />)}
            </div>
          );
        }

        // components/UserCard.tsx
        'use client'  // <-- opt-in to Client Component
        import { useState } from 'react';
        function UserCard({ user }) {
          const [expanded, setExpanded] = useState(false);
          return <div onClick={() => setExpanded(!expanded)}>...</div>;
        }
    """)

    # --- 1.6 Error Boundaries ---
    header("1.6 Error Boundaries Pattern", 2)

    class ErrorBoundary:
        """Simulates React's ErrorBoundary (class component pattern)."""
        def __init__(self, fallback: str = "Something went wrong"):
            self.fallback = fallback
            self.has_error = False
            self.error: Optional[Exception] = None

        def render(self, child_render: Callable):
            try:
                result = child_render()
                if self.has_error:
                    self.has_error = False
                    self.error = None
                return result
            except Exception as e:
                self.has_error = True
                self.error = e
                print(f"    ErrorBoundary caught: {e}")
                return self.fallback

    boundary = ErrorBoundary(fallback="<FallbackUI />")

    def good_component():
        return "<UserProfile data={...} />"

    def bad_component():
        raise ValueError("Cannot read property 'name' of undefined")

    print(f"\n  Good render: {boundary.render(good_component)}")
    print(f"  Bad render:  {boundary.render(bad_component)}")

    explain("""
        Error Boundaries catch JS errors in the component tree below them.
        They do NOT catch errors in:
        - Event handlers (use try/catch)
        - Async code (promises)
        - Server-side rendering
        - Errors in the boundary itself
    """)


# ============================================================================
#  CHAPTER 2: Next.js Architecture
# ============================================================================

def chapter2_nextjs():
    header("CHAPTER 2: Next.js Architecture")

    # --- 2.1 Rendering Strategies ---
    header("2.1 Rendering Strategies", 2)

    class RenderingSimulator:
        def __init__(self):
            self.server_time = 0
            self.client_time = 0
            self.ttfb = 0

        def csr(self, data_fetch_ms: int = 200):
            """Client-Side Rendering: blank HTML + JS bundle fetches data."""
            self.ttfb = 10  # minimal HTML
            self.client_time = 150 + data_fetch_ms  # parse JS + fetch
            total = self.ttfb + self.client_time
            return {
                "strategy": "CSR",
                "ttfb_ms": self.ttfb,
                "first_paint_ms": self.ttfb + 150,
                "content_ready_ms": total,
                "seo": "Poor (empty HTML)",
                "caching": "CDN for static assets only",
            }

        def ssr(self, data_fetch_ms: int = 200):
            """Server-Side Rendering: full HTML per request."""
            self.server_time = 50 + data_fetch_ms
            self.ttfb = self.server_time
            self.client_time = 80  # hydration
            return {
                "strategy": "SSR",
                "ttfb_ms": self.ttfb,
                "first_paint_ms": self.ttfb,
                "content_ready_ms": self.ttfb + self.client_time,
                "seo": "Excellent (full HTML)",
                "caching": "Optional (Cache-Control)",
            }

        def ssg(self):
            """Static Site Generation: pre-built at build time."""
            self.ttfb = 5  # served from CDN
            self.client_time = 80  # hydration
            return {
                "strategy": "SSG",
                "ttfb_ms": self.ttfb,
                "first_paint_ms": self.ttfb,
                "content_ready_ms": self.ttfb + self.client_time,
                "seo": "Excellent",
                "caching": "Full CDN cache",
            }

        def isr(self, revalidate_sec: int = 60):
            """Incremental Static Regeneration."""
            self.ttfb = 5  # cached
            self.client_time = 80
            return {
                "strategy": f"ISR (revalidate={revalidate_sec}s)",
                "ttfb_ms": self.ttfb,
                "first_paint_ms": self.ttfb,
                "content_ready_ms": self.ttfb + self.client_time,
                "seo": "Excellent",
                "caching": f"CDN, regenerates every {revalidate_sec}s",
            }

    sim = RenderingSimulator()
    for result in [sim.csr(), sim.ssr(), sim.ssg(), sim.isr()]:
        print(f"\n  {result['strategy']}:")
        for k, v in result.items():
            if k != "strategy":
                print(f"    {k:22s} = {v}")

    explain("""
        Decision guide:
        - CSR:  Dashboards, authenticated apps (no SEO needed)
        - SSR:  Dynamic, personalized pages needing SEO
        - SSG:  Marketing pages, blogs, docs (rarely changing)
        - ISR:  E-commerce product pages (semi-dynamic)
    """)

    # --- 2.2 App Router vs Pages Router ---
    header("2.2 App Router vs Pages Router", 2)
    comparison = {
        "Feature":           ["Pages Router",           "App Router (v13+)"],
        "File convention":   ["pages/about.tsx",        "app/about/page.tsx"],
        "Layouts":           ["_app.tsx (global only)", "layout.tsx (nested)"],
        "Default rendering": ["Client Components",      "Server Components"],
        "Data fetching":     ["getServerSideProps etc.", "async components + fetch"],
        "Streaming":         ["Not supported",          "Suspense + streaming"],
        "Loading UI":        ["Manual",                 "loading.tsx"],
        "Error UI":          ["Manual",                 "error.tsx"],
        "Metadata":          ["next/head",              "metadata export / generateMetadata"],
    }
    max_feat = max(len(k) for k in comparison)
    max_old = max(len(v[0]) for v in comparison.values())
    for feat, (old, new) in comparison.items():
        print(f"    {feat:<{max_feat}}  {old:<{max_old}}  {new}")

    # --- 2.3 Data Fetching in App Router ---
    header("2.3 Data Fetching Patterns (App Router)", 2)
    code_example("Server Component data fetching", """
        // app/products/page.tsx
        export default async function ProductsPage() {
          // This fetch runs on the server (no useEffect needed!)
          const products = await fetch('https://api.example.com/products', {
            next: { revalidate: 3600 }  // ISR: revalidate every hour
          }).then(r => r.json());

          return <ProductList products={products} />;
        }

        // Parallel data fetching
        export default async function DashboardPage() {
          const [users, orders, revenue] = await Promise.all([
            fetchUsers(),
            fetchOrders(),
            fetchRevenue(),
          ]);
          return <Dashboard users={users} orders={orders} revenue={revenue} />;
        }
    """)
    code_example("Client Component data fetching with SWR", """
        'use client'
        import useSWR from 'swr';

        function SearchResults({ query }) {
          const { data, error, isLoading } = useSWR(
            `/api/search?q=${query}`,
            fetcher,
            { revalidateOnFocus: false }
          );
          if (isLoading) return <Skeleton />;
          if (error) return <ErrorMessage />;
          return <ResultsList results={data} />;
        }
    """)

    # --- 2.4 Middleware & Edge Runtime ---
    header("2.4 Middleware and Edge Runtime", 2)
    explain("""
        Next.js Middleware runs BEFORE the request reaches your pages.
        It runs on the Edge Runtime (V8 isolates, not Node.js).

        Common use cases:
        - Authentication checks
        - A/B testing (rewrite to different variants)
        - Geolocation-based redirects
        - Rate limiting
        - Bot detection
    """)
    code_example("middleware.ts", """
        import { NextResponse } from 'next/server';
        import type { NextRequest } from 'next/server';

        export function middleware(request: NextRequest) {
          const token = request.cookies.get('session');

          // Redirect unauthenticated users
          if (!token && request.nextUrl.pathname.startsWith('/dashboard')) {
            return NextResponse.redirect(new URL('/login', request.url));
          }

          // Add geo header
          const country = request.geo?.country || 'US';
          const response = NextResponse.next();
          response.headers.set('x-country', country);
          return response;
        }

        export const config = {
          matcher: ['/dashboard/:path*', '/api/:path*'],
        };
    """)

    # --- 2.5 Route Handlers ---
    header("2.5 Route Handlers (API Routes in App Router)", 2)
    code_example("app/api/users/route.ts", """
        import { NextRequest, NextResponse } from 'next/server';

        // GET /api/users
        export async function GET(request: NextRequest) {
          const { searchParams } = new URL(request.url);
          const page = searchParams.get('page') || '1';
          const users = await db.users.findMany({ skip: (+page - 1) * 20 });
          return NextResponse.json(users);
        }

        // POST /api/users
        export async function POST(request: NextRequest) {
          const body = await request.json();
          const user = await db.users.create({ data: body });
          return NextResponse.json(user, { status: 201 });
        }
    """)

    # --- 2.6 Image/Font Optimization ---
    header("2.6 Image & Font Optimization", 2)
    explain("""
        next/image:
        - Automatic WebP/AVIF conversion
        - Lazy loading by default
        - Prevents Cumulative Layout Shift (reserves space)
        - Responsive srcset generation
        - On-demand optimization (not at build time)

        next/font:
        - Zero layout shift (size-adjust CSS descriptor)
        - Self-hosted (no requests to Google Fonts)
        - Automatic font subsetting
        - CSS variable integration
    """)
    code_example("Optimized Image & Font", """
        // app/layout.tsx
        import { Inter } from 'next/font/google';
        const inter = Inter({ subsets: ['latin'] });

        export default function Layout({ children }) {
          return (
            <html className={inter.className}>
              <body>{children}</body>
            </html>
          );
        }

        // Using next/image
        import Image from 'next/image';
        <Image
          src="/hero.jpg"
          alt="Hero"
          width={1200}
          height={600}
          priority        // above the fold = eager load
          placeholder="blur"
          blurDataURL="data:image/..."
        />
    """)


# ============================================================================
#  CHAPTER 3: Web Performance
# ============================================================================

def chapter3_performance():
    header("CHAPTER 3: Web Performance")

    # --- 3.1 Core Web Vitals ---
    header("3.1 Core Web Vitals", 2)

    class CoreWebVitals:
        THRESHOLDS = {
            "LCP": {"good": 2500, "poor": 4000, "unit": "ms",
                    "desc": "Largest Contentful Paint - when main content is visible"},
            "INP": {"good": 200, "poor": 500, "unit": "ms",
                    "desc": "Interaction to Next Paint - input responsiveness"},
            "CLS": {"good": 0.1, "poor": 0.25, "unit": "score",
                    "desc": "Cumulative Layout Shift - visual stability"},
        }

        @classmethod
        def assess(cls, metric: str, value: float) -> str:
            t = cls.THRESHOLDS[metric]
            if value <= t["good"]:
                return "GOOD"
            elif value <= t["poor"]:
                return "NEEDS IMPROVEMENT"
            return "POOR"

        @classmethod
        def report(cls, lcp: float, inp: float, cls_score: float):
            results = {
                "LCP": (lcp, cls.assess("LCP", lcp)),
                "INP": (inp, cls.assess("INP", inp)),
                "CLS": (cls_score, cls.assess("CLS", cls_score)),
            }
            print("\n  Core Web Vitals Report:")
            for metric, (val, grade) in results.items():
                t = cls.THRESHOLDS[metric]
                unit = t["unit"]
                print(f"    {metric}: {val}{unit} -> [{grade}]")
                print(f"         {t['desc']}")
                print(f"         Thresholds: good <= {t['good']}, "
                      f"poor > {t['poor']}")
            return results

    CoreWebVitals.report(lcp=1800, inp=150, cls_score=0.05)
    print()
    CoreWebVitals.report(lcp=3500, inp=350, cls_score=0.2)

    # --- 3.2 Performance Budget ---
    header("3.2 Performance Budget Calculator", 2)

    class PerformanceBudget:
        def __init__(self, total_kb: int = 300, connection: str = "3G"):
            self.total_kb = total_kb
            self.speeds = {
                "3G": 1500,     # 1.5 Mbps -> ~187 KB/s
                "4G": 12000,    # 12 Mbps -> ~1500 KB/s
                "broadband": 50000,
            }
            self.connection = connection

        def allocate(self) -> dict:
            budget = {
                "framework":   int(self.total_kb * 0.30),
                "app_code":    int(self.total_kb * 0.25),
                "styles":      int(self.total_kb * 0.10),
                "fonts":       int(self.total_kb * 0.15),
                "images":      int(self.total_kb * 0.15),
                "third_party": int(self.total_kb * 0.05),
            }
            return budget

        def estimate_load_time(self) -> float:
            speed_kbps = self.speeds[self.connection] / 8  # KB/s
            return self.total_kb / speed_kbps

    budget = PerformanceBudget(total_kb=300, connection="3G")
    alloc = budget.allocate()
    print(f"\n  Performance Budget: {budget.total_kb}KB total ({budget.connection})")
    for cat, kb in alloc.items():
        bar = "#" * (kb // 5)
        print(f"    {cat:15s} {kb:4d}KB  {bar}")
    print(f"    Estimated load time: {budget.estimate_load_time():.1f}s on {budget.connection}")

    # --- 3.3 Critical Rendering Path ---
    header("3.3 Critical Rendering Path", 2)

    class CriticalRenderingPath:
        def simulate(self):
            steps = [
                ("1. DNS Lookup",        50,  "Resolve domain to IP"),
                ("2. TCP Connection",    100, "Three-way handshake"),
                ("3. TLS Handshake",     100, "Certificate exchange + key agreement"),
                ("4. HTTP Request",      20,  "Send GET / request"),
                ("5. Server Response",   200, "Server processes, sends HTML"),
                ("6. HTML Parsing",      50,  "Build DOM tree"),
                ("7. CSS Parsing",       30,  "Build CSSOM tree"),
                ("8. Render Tree",       10,  "Combine DOM + CSSOM"),
                ("9. Layout",           10,   "Calculate element positions"),
                ("10. Paint",           20,   "Rasterize pixels to layers"),
                ("11. Composite",        5,   "Combine layers, display"),
            ]
            total = 0
            print("\n  Critical Rendering Path:")
            for step, ms, desc in steps:
                total += ms
                bar = "=" * (ms // 10)
                print(f"    {step:25s} {ms:4d}ms {bar}  {desc}")
            print(f"    {'TOTAL':25s} {total:4d}ms")
            print("\n    Optimization targets:")
            print("    - Reduce DNS: use dns-prefetch, keep on few domains")
            print("    - Skip TLS: use HTTP/2, TLS 1.3 (1-RTT)")
            print("    - Faster TTFB: CDN, edge computing, caching")
            print("    - Unblock render: inline critical CSS, async JS")

    CriticalRenderingPath().simulate()

    # --- 3.4 Bundle Optimization ---
    header("3.4 Bundle Size Optimization", 2)

    class BundleOptimizer:
        def __init__(self):
            self.modules = {
                "react":       45, "react-dom": 130, "next": 90,
                "lodash":      72, "moment":    290, "date-fns": 12,
                "axios":       14, "swr":        12,
                "chart.js":   205, "recharts":  165,
                "framer-motion": 105, "classnames": 1,
            }

        def tree_shake(self, used_exports: dict) -> dict:
            """Estimate size after tree-shaking (% of exports used)."""
            result = {}
            for mod, pct in used_exports.items():
                original = self.modules.get(mod, 0)
                shaken = int(original * pct)
                saved = original - shaken
                result[mod] = {"original": original, "after": shaken,
                               "saved": saved}
            return result

        def suggest_alternatives(self) -> list:
            return [
                ("lodash (72KB)",      "lodash-es + tree-shaking or native methods"),
                ("moment (290KB)",     "date-fns (12KB) or dayjs (2KB)"),
                ("chart.js (205KB)",   "Consider recharts or lighter alternative"),
                ("axios (14KB)",       "fetch API (0KB) for simple cases"),
                ("framer-motion (105KB)", "CSS transitions for simple animations"),
            ]

    opt = BundleOptimizer()
    results = opt.tree_shake({
        "lodash": 0.15, "date-fns": 0.30, "react": 1.0, "react-dom": 1.0,
    })
    print("\n  Tree-shaking results:")
    for mod, info in results.items():
        print(f"    {mod:15s}: {info['original']:4d}KB -> "
              f"{info['after']:4d}KB (saved {info['saved']}KB)")

    print("\n  Library alternatives:")
    for lib, alt in opt.suggest_alternatives():
        print(f"    {lib:28s} -> {alt}")

    # --- 3.5 Resource Hints ---
    header("3.5 Resource Hints", 2)
    resource_hints = [
        ("dns-prefetch", '<link rel="dns-prefetch" href="//api.example.com">',
         "Resolve DNS early for third-party domains"),
        ("preconnect",   '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
         "DNS + TCP + TLS handshake early"),
        ("preload",      '<link rel="preload" href="/font.woff2" as="font" type="font/woff2" crossorigin>',
         "Fetch critical resource for current page NOW"),
        ("prefetch",     '<link rel="prefetch" href="/next-page.js">',
         "Fetch resource for NEXT navigation (low priority)"),
        ("prerender",    '<link rel="prerender" href="/likely-next-page">',
         "Render entire page in background (deprecated, use Speculation Rules)"),
    ]
    print()
    for name, html, desc in resource_hints:
        print(f"  {name}:")
        print(f"    {html}")
        print(f"    Purpose: {desc}\n")

    # --- 3.6 Image Optimization ---
    header("3.6 Image Optimization Strategies", 2)

    class ImageOptimizer:
        FORMATS = {
            "JPEG":  {"quality_range": "60-85%", "best_for": "photographs",
                      "transparency": False, "size_factor": 1.0},
            "PNG":   {"quality_range": "lossless",  "best_for": "icons, screenshots",
                      "transparency": True, "size_factor": 1.5},
            "WebP":  {"quality_range": "75-85%", "best_for": "all (modern)",
                      "transparency": True, "size_factor": 0.7},
            "AVIF":  {"quality_range": "60-80%", "best_for": "all (newest)",
                      "transparency": True, "size_factor": 0.5},
            "SVG":   {"quality_range": "vector",    "best_for": "icons, logos",
                      "transparency": True, "size_factor": 0.1},
        }

        @classmethod
        def srcset_example(cls):
            return textwrap.dedent("""
                <img
                  srcset="hero-480w.webp 480w,
                          hero-800w.webp 800w,
                          hero-1200w.webp 1200w"
                  sizes="(max-width: 600px) 480px,
                         (max-width: 1000px) 800px,
                         1200px"
                  src="hero-800w.webp"
                  alt="Hero image"
                  loading="lazy"
                  decoding="async"
                />
            """)

    print("\n  Image Format Comparison (100KB JPEG baseline):")
    for fmt, info in ImageOptimizer.FORMATS.items():
        est_size = int(100 * info["size_factor"])
        alpha = "Yes" if info["transparency"] else "No"
        print(f"    {fmt:5s}: ~{est_size:3d}KB  alpha={alpha:3s}  "
              f"quality={info['quality_range']:10s}  best for: {info['best_for']}")
    code_example("Responsive images with srcset", ImageOptimizer.srcset_example())

    # --- 3.7 Caching ---
    header("3.7 Caching Strategies", 2)

    cache_headers = [
        ("Static assets (JS/CSS/fonts)",
         "Cache-Control: public, max-age=31536000, immutable",
         "Content-hashed filenames enable forever caching"),
        ("HTML pages",
         "Cache-Control: no-cache",
         "Always revalidate (no-cache != no-store)"),
        ("API responses",
         "Cache-Control: public, max-age=60, stale-while-revalidate=300",
         "Serve stale while fetching fresh in background"),
        ("Sensitive data",
         "Cache-Control: private, no-store",
         "Never cache on shared caches, don't persist"),
    ]
    print()
    for resource, header_val, note in cache_headers:
        print(f"  {resource}:")
        print(f"    {header_val}")
        print(f"    Note: {note}\n")

    # --- 3.8 Lighthouse Scoring ---
    header("3.8 Lighthouse Scoring Simulation", 2)

    class LighthouseSimulator:
        WEIGHTS = {
            "FCP": 0.10, "SI": 0.10, "LCP": 0.25,
            "TBT": 0.30, "CLS": 0.25,
        }

        @staticmethod
        def metric_score(metric: str, value: float) -> int:
            """Simplified scoring (real Lighthouse uses log-normal curves)."""
            thresholds = {
                "FCP": (1800, 3000), "SI":  (3400, 5800),
                "LCP": (2500, 4000), "TBT": (200, 600),
                "CLS": (0.1, 0.25),
            }
            good, poor = thresholds[metric]
            if value <= good:
                return 100 - int(50 * value / good)
            elif value <= poor:
                return 50 - int(50 * (value - good) / (poor - good))
            return max(0, int(10 * poor / value))

        @classmethod
        def calculate(cls, metrics: dict) -> dict:
            scores = {}
            for m, v in metrics.items():
                scores[m] = cls.metric_score(m, v)
            total = sum(scores[m] * cls.WEIGHTS[m] for m in scores)
            return {"individual": scores, "overall": round(total)}

    metrics = {"FCP": 1200, "SI": 2800, "LCP": 2000, "TBT": 150, "CLS": 0.05}
    result = LighthouseSimulator.calculate(metrics)
    print(f"\n  Lighthouse Performance Score: {result['overall']}/100")
    print(f"  Breakdown (weights):")
    for m, s in result["individual"].items():
        w = LighthouseSimulator.WEIGHTS[m]
        print(f"    {m:4s}: {s:3d}/100  (weight: {w:.0%})")

    metrics_slow = {"FCP": 3500, "SI": 6000, "LCP": 5000, "TBT": 800, "CLS": 0.3}
    result2 = LighthouseSimulator.calculate(metrics_slow)
    print(f"\n  Slow site score: {result2['overall']}/100")
    for m, s in result2["individual"].items():
        print(f"    {m:4s}: {s:3d}/100")


# ============================================================================
#  CHAPTER 4: CSS Architecture
# ============================================================================

def chapter4_css():
    header("CHAPTER 4: CSS Architecture")

    # --- 4.1 Specificity Calculator ---
    header("4.1 CSS Specificity Calculator", 2)
    explain("""
        CSS specificity determines which rule wins when selectors conflict.
        It's calculated as a tuple: (inline, IDs, classes/attrs, elements).

        - Inline styles:          (1, 0, 0, 0)
        - #id:                    (0, 1, 0, 0)
        - .class, [attr], :hover: (0, 0, 1, 0)
        - element, ::pseudo:      (0, 0, 0, 1)
        - *, combinators:         (0, 0, 0, 0)
        - !important:             overrides everything (avoid!)
    """)

    def calculate_specificity(selector: str) -> tuple:
        """Simplified CSS specificity calculator."""
        import re
        s = selector.strip()
        inline = 0
        ids = len(re.findall(r'#[\w-]+', s))
        # Remove IDs to avoid double counting
        s_no_id = re.sub(r'#[\w-]+', '', s)
        classes = len(re.findall(r'\.[\w-]+', s_no_id))
        attrs = len(re.findall(r'\[[\w-]', s_no_id))
        pseudoclasses = len(re.findall(r':(?!:)[\w-]+', s_no_id))
        # :not() itself has zero specificity, but its contents do
        # (simplified - not handling :not() internals here)
        classes_total = classes + attrs + pseudoclasses
        # Remove classes/attrs/pseudo to count elements
        s_clean = re.sub(r'\.[\w-]+', '', s_no_id)
        s_clean = re.sub(r'\[.*?\]', '', s_clean)
        s_clean = re.sub(r'::[\w-]+', '', s_clean)  # pseudo-elements
        s_clean = re.sub(r':[\w-]+', '', s_clean)
        pseudo_elements = len(re.findall(r'::[\w-]+', s_no_id))
        elements = len(re.findall(r'(?:^|[\s>+~])[\w]+', s_clean))
        elements += pseudo_elements
        return (inline, ids, classes_total, elements)

    test_selectors = [
        "*",
        "h1",
        "h1.title",
        "#main .content p",
        "nav#main ul.menu li.active a:hover",
        "div > p:first-child",
        "input[type='text']",
    ]
    print("\n  Specificity calculations:")
    for sel in test_selectors:
        spec = calculate_specificity(sel)
        print(f"    {sel:45s} -> ({spec[0]},{spec[1]},{spec[2]},{spec[3]})")

    explain("""
        Higher specificity wins. If equal, last rule wins (cascade).
        Best practice: keep specificity LOW and flat.
        Use classes (.btn) instead of IDs (#submit-btn).
    """)

    # --- 4.2 Flexbox vs Grid ---
    header("4.2 Flexbox vs Grid Decision Tree", 2)

    def layout_decision(two_dimensional: bool, content_driven: bool,
                        overlap_needed: bool) -> str:
        if overlap_needed:
            return "Grid (grid-area for overlapping)"
        if two_dimensional:
            return "Grid (rows AND columns)"
        if content_driven:
            return "Flexbox (content determines size)"
        return "Flexbox (one-dimensional flow)"

    scenarios = [
        ("Navigation bar",        False, True,  False),
        ("Card grid layout",      True,  False, False),
        ("Holy grail layout",     True,  False, False),
        ("Centering single item", False, True,  False),
        ("Image gallery overlay", True,  False, True),
        ("Form fields in a row",  False, True,  False),
    ]
    print("\n  Layout Decision Guide:")
    for name, twod, content, overlap in scenarios:
        result = layout_decision(twod, content, overlap)
        print(f"    {name:25s} -> {result}")

    code_example("Flexbox vs Grid", """
        /* Flexbox: 1D layout, content-driven sizing */
        .nav { display: flex; gap: 1rem; align-items: center; }
        .nav-item { flex: 0 0 auto; }  /* don't grow/shrink */
        .nav-spacer { flex: 1; }        /* push items apart */

        /* Grid: 2D layout, container-driven sizing */
        .dashboard {
          display: grid;
          grid-template-columns: 250px 1fr 300px;
          grid-template-rows: auto 1fr auto;
          grid-template-areas:
            "sidebar header  aside"
            "sidebar content aside"
            "sidebar footer  aside";
          gap: 1rem;
        }
    """)

    # --- 4.3 Styling Approaches ---
    header("4.3 CSS-in-JS vs CSS Modules vs Utility-first", 2)
    approaches = {
        "CSS-in-JS (styled-components)": {
            "pros": ["Scoped by default", "Dynamic styles via props",
                     "Co-located with components"],
            "cons": ["Runtime overhead", "Bundle size (+12KB)",
                     "SSR complexity", "Hydration mismatch risk"],
            "trend": "Declining (RSC incompatible)",
        },
        "CSS Modules": {
            "pros": ["Zero runtime", "Scoped class names", "Standard CSS",
                     "Works with RSC"],
            "cons": ["File switching", "Limited dynamic styles",
                     "Class name composition verbose"],
            "trend": "Stable (Next.js default)",
        },
        "Utility-first (Tailwind CSS)": {
            "pros": ["No naming", "Consistent design tokens",
                     "Tiny production CSS (purged)", "Fast prototyping"],
            "cons": ["Long class strings", "Learning curve",
                     "HTML readability", "Custom designs need config"],
            "trend": "Rising (dominant in 2024-2026)",
        },
    }
    for approach, info in approaches.items():
        print(f"\n  {approach}:")
        print(f"    Trend: {info['trend']}")
        print(f"    Pros:  {', '.join(info['pros'])}")
        print(f"    Cons:  {', '.join(info['cons'])}")

    # --- 4.4 Responsive Design ---
    header("4.4 Responsive Design Patterns", 2)
    code_example("Mobile-first breakpoints", """
        /* Mobile first: start small, add complexity */
        .card { padding: 1rem; }                        /* mobile */

        @media (min-width: 640px) {                     /* sm */
          .card { padding: 1.5rem; display: flex; }
        }
        @media (min-width: 1024px) {                    /* lg */
          .card { padding: 2rem; max-width: 800px; }
        }

        /* Container Queries (modern) */
        .card-container { container-type: inline-size; }

        @container (min-width: 400px) {
          .card { display: grid; grid-template-columns: 1fr 2fr; }
        }
    """)
    explain("""
        Container Queries are a game-changer:
        - Components respond to their container size, not viewport.
        - Truly reusable components that adapt to their context.
        - Supported in all modern browsers (2023+).
    """)

    # --- 4.5 Animation Performance ---
    header("4.5 Animation Performance", 2)
    print("\n  CSS Properties and Rendering Cost:")
    layers = [
        ("transform, opacity",     "Composite only",  "FAST",
         "GPU-accelerated, no layout/paint"),
        ("color, background",      "Paint + Composite", "MODERATE",
         "Repaint but no layout recalc"),
        ("width, height, margin",  "Layout + Paint + Composite", "SLOW",
         "Triggers full layout recalculation"),
        ("top, left, right",       "Layout + Paint + Composite", "SLOW",
         "Use transform: translate() instead"),
    ]
    for prop, pipeline, speed, note in layers:
        print(f"    {prop:28s} [{speed:8s}] {pipeline}")
        print(f"    {'':28s}           {note}")

    code_example("Performant animation", """
        /* BAD: triggers layout */
        .box { transition: left 0.3s; }
        .box:hover { left: 100px; }

        /* GOOD: composite only */
        .box { transition: transform 0.3s; will-change: transform; }
        .box:hover { transform: translateX(100px); }

        /* will-change: use sparingly, remove when not animating */
    """)


# ============================================================================
#  CHAPTER 5: State Management
# ============================================================================

def chapter5_state():
    header("CHAPTER 5: State Management")

    # --- 5.1 Decision Tree ---
    header("5.1 Local vs Global State Decision", 2)

    def state_decision(shared_across_routes: bool, server_data: bool,
                       frequently_updated: bool, form_state: bool) -> str:
        if form_state:
            return "Local state (useState / useReducer) or react-hook-form"
        if server_data:
            return "Server state library (TanStack Query / SWR)"
        if not shared_across_routes:
            return "Local state (useState) or lift state up"
        if frequently_updated:
            return "Atomic state (Jotai / Zustand) - avoids re-render storms"
        return "Context API (simple, built-in) or Zustand"

    scenarios = [
        ("Modal open/close",          False, False, False, False),
        ("User authentication",       True,  True,  False, False),
        ("Shopping cart",             True,  False, True,  False),
        ("Form input values",        False, False, True,  True),
        ("API data (products list)", True,  True,  False, False),
        ("Theme (dark/light)",        True,  False, False, False),
        ("Real-time notifications",   True,  True,  True,  False),
    ]
    print("\n  State Management Decision Guide:")
    for name, shared, server, freq, form in scenarios:
        result = state_decision(shared, server, freq, form)
        print(f"    {name:30s} -> {result}")

    # --- 5.2 Redux Pattern ---
    header("5.2 Redux Pattern Simulation", 2)
    explain("""
        Redux = single source of truth with predictable state updates.
        Flow: UI dispatches Action -> Middleware -> Reducer -> new State -> UI
    """)

    class ReduxStore:
        def __init__(self, reducer: Callable, initial_state: dict,
                     middleware: list = None):
            self._state = initial_state
            self._reducer = reducer
            self._listeners: list = []
            self._middleware = middleware or []

        @property
        def state(self) -> dict:
            return self._state.copy()

        def subscribe(self, listener: Callable):
            self._listeners.append(listener)

        def dispatch(self, action: dict):
            # Run through middleware chain
            for mw in self._middleware:
                action = mw(self, action)
                if action is None:
                    return  # middleware can swallow actions

            old_state = self._state
            self._state = self._reducer(self._state, action)
            if self._state != old_state:
                for listener in self._listeners:
                    listener(self._state)

    def todo_reducer(state: dict, action: dict) -> dict:
        t = action["type"]
        if t == "ADD_TODO":
            return {**state, "todos": state["todos"] + [
                {"id": len(state["todos"]) + 1,
                 "text": action["text"], "done": False}
            ]}
        elif t == "TOGGLE_TODO":
            return {**state, "todos": [
                {**todo, "done": not todo["done"]}
                if todo["id"] == action["id"] else todo
                for todo in state["todos"]
            ]}
        elif t == "SET_FILTER":
            return {**state, "filter": action["filter"]}
        return state

    def logger_middleware(store, action):
        print(f"      [middleware] dispatch: {action['type']}")
        return action

    store = ReduxStore(
        todo_reducer,
        {"todos": [], "filter": "all"},
        middleware=[logger_middleware],
    )
    store.subscribe(lambda s: print(f"      [subscriber] state updated: "
                                    f"{len(s['todos'])} todos"))

    print("\n  Redux Todo Store Demo:")
    store.dispatch({"type": "ADD_TODO", "text": "Learn React"})
    store.dispatch({"type": "ADD_TODO", "text": "Learn Redux"})
    store.dispatch({"type": "TOGGLE_TODO", "id": 1})
    print(f"    Final state: {json.dumps(store.state, indent=6)}")

    explain("""
        Modern Redux (Redux Toolkit) simplifies this significantly:
        - createSlice(): auto-generates action creators + reducer
        - Immer: write "mutable" code that produces immutable updates
        - RTK Query: built-in data fetching + caching (like React Query)
    """)

    # --- 5.3 Context Pitfalls ---
    header("5.3 Context API Pitfalls", 2)

    class ContextSimulator:
        def __init__(self):
            self.value = {}
            self.consumers: list = []
            self.render_counts: dict = defaultdict(int)

        def provide(self, value: dict):
            changed = value != self.value
            self.value = value
            if changed:
                for name in self.consumers:
                    self.render_counts[name] += 1

        def consume(self, component_name: str):
            if component_name not in self.consumers:
                self.consumers.append(component_name)
            self.render_counts[component_name] += 1

    ctx = ContextSimulator()
    ctx.consume("Header")
    ctx.consume("Sidebar")
    ctx.consume("Footer")

    print("\n  Context re-render problem:")
    print("    UserContext has { user, theme, notifications }")
    ctx.provide({"user": "Alice", "theme": "dark", "notifications": 5})
    print(f"    Initial renders: {dict(ctx.render_counts)}")

    ctx.provide({"user": "Alice", "theme": "dark", "notifications": 6})
    print(f"    After notification update: {dict(ctx.render_counts)}")
    print("    ^ ALL consumers re-render even though only notifications changed!")

    explain("""
        Solutions:
        1. Split context: separate UserContext, ThemeContext, NotificationContext
        2. Memoize consumers: React.memo + useMemo on context value
        3. Use a proper state manager for frequently-changing state
        4. Use 'use' hook (React 19) with selective subscriptions
    """)

    # --- 5.4 Modern Alternatives ---
    header("5.4 Modern State Libraries Mental Models", 2)

    libs = {
        "Zustand": {
            "model": "Simple store with hooks (like a global useState)",
            "size": "~1KB",
            "example": "const useStore = create(set => ({ count: 0, inc: () => set(s => ({ count: s.count + 1 })) }))",
            "best_for": "Simple global state, replacing Redux",
        },
        "Jotai": {
            "model": "Atoms (bottom-up) - each piece of state is independent",
            "size": "~2KB",
            "example": "const countAtom = atom(0); // use: const [count, setCount] = useAtom(countAtom)",
            "best_for": "Fine-grained reactivity, derived state",
        },
        "Recoil": {
            "model": "Atoms + selectors (graph-based state)",
            "size": "~20KB",
            "example": "const countState = atom({ key: 'count', default: 0 })",
            "best_for": "Complex derived state, async selectors",
        },
        "TanStack Query": {
            "model": "Server state cache with auto-refetch",
            "size": "~12KB",
            "example": "const { data } = useQuery({ queryKey: ['users'], queryFn: fetchUsers })",
            "best_for": "Any data fetched from APIs",
        },
    }
    for name, info in libs.items():
        print(f"\n  {name} ({info['size']}):")
        print(f"    Model:    {info['model']}")
        print(f"    Best for: {info['best_for']}")

    # --- 5.5 Optimistic Updates ---
    header("5.5 Optimistic Updates Pattern", 2)

    class OptimisticUpdater:
        def __init__(self):
            self.items = [
                {"id": 1, "text": "Buy groceries", "done": False},
                {"id": 2, "text": "Read book", "done": False},
            ]
            self.rollback_state = None

        def toggle_optimistic(self, item_id: int,
                              server_succeeds: bool = True):
            # 1. Save rollback state
            self.rollback_state = [i.copy() for i in self.items]
            # 2. Immediately update UI
            for item in self.items:
                if item["id"] == item_id:
                    item["done"] = not item["done"]
                    print(f"    [Optimistic] Toggled '{item['text']}' "
                          f"-> done={item['done']}")
            # 3. Send to server
            print(f"    [Server] Sending update...")
            if server_succeeds:
                print(f"    [Server] Success! Optimistic state confirmed.")
            else:
                # 4. Rollback on failure
                self.items = self.rollback_state
                print(f"    [Server] FAILED! Rolling back...")
                for item in self.items:
                    if item["id"] == item_id:
                        print(f"    [Rollback] '{item['text']}' "
                              f"back to done={item['done']}")

    print("\n  Optimistic update - success:")
    updater = OptimisticUpdater()
    updater.toggle_optimistic(1, server_succeeds=True)
    print("\n  Optimistic update - failure with rollback:")
    updater2 = OptimisticUpdater()
    updater2.toggle_optimistic(1, server_succeeds=False)


# ============================================================================
#  CHAPTER 6: Frontend Testing
# ============================================================================

def chapter6_testing():
    header("CHAPTER 6: Frontend Testing")

    # --- 6.1 Testing Trophy ---
    header("6.1 Testing Trophy (vs Pyramid)", 2)
    explain("""
        Traditional Testing Pyramid:        Frontend Testing Trophy:
              /\\                                   ___
             /E2E\\   Few                          /E2E\\  Few
            /------\\                             /------\\
           / Integ. \\  Some                     /        \\
          /----------\\                         / Integr.  \\  Most!
         /   Unit     \\  Many                 /            \\
        /--------------\\                     /--------------\\
                                             /   Unit (logic) \\  Some
                                            /------------------\\
                                              Static Analysis    Always

        Kent C. Dodds' Testing Trophy emphasizes INTEGRATION tests
        because they give the best confidence-to-effort ratio.

        "Write tests. Not too many. Mostly integration."
    """)

    # --- 6.2 Component Testing ---
    header("6.2 Component Testing Patterns", 2)

    class TestRunner:
        def __init__(self):
            self.results: list = []
            self.total = 0
            self.passed = 0

        def test(self, name: str, fn: Callable):
            self.total += 1
            try:
                fn()
                self.passed += 1
                self.results.append(("PASS", name))
                print(f"    PASS: {name}")
            except AssertionError as e:
                self.results.append(("FAIL", name, str(e)))
                print(f"    FAIL: {name} - {e}")
            except Exception as e:
                self.results.append(("FAIL", name, str(e)))
                print(f"    FAIL: {name} - {e}")

        def summary(self):
            print(f"\n    Results: {self.passed}/{self.total} passed")

    # Simulate a simple component
    class MockDOM:
        """Simulates a rendered component for testing."""
        def __init__(self):
            self.elements: dict = {}
            self.events: dict = defaultdict(list)

        def render(self, component_html: dict):
            self.elements = component_html

        def get_by_text(self, text: str) -> Optional[dict]:
            for el in self.elements.get("children", []):
                if isinstance(el, dict) and el.get("text") == text:
                    return el
                if isinstance(el, str) and text in el:
                    return {"tag": "text", "text": el}
            return None

        def get_by_role(self, role: str) -> Optional[dict]:
            for el in self.elements.get("children", []):
                if isinstance(el, dict) and el.get("role") == role:
                    return el
            return None

        def fire_event(self, element: dict, event: str):
            handler = element.get(f"on{event}")
            if handler:
                handler()

    runner = TestRunner()
    print("\n  Component test examples:")

    code_example("Testing Library pattern (render -> find -> assert)", """
        import { render, screen, fireEvent } from '@testing-library/react';

        test('counter increments on click', () => {
          // Arrange
          render(<Counter initialCount={0} />);

          // Act
          fireEvent.click(screen.getByRole('button', { name: /increment/i }));

          // Assert
          expect(screen.getByText('Count: 1')).toBeInTheDocument();
        });

        test('search filters results', async () => {
          render(<SearchPage />);
          const input = screen.getByRole('searchbox');

          await userEvent.type(input, 'react');

          // Wait for async results
          expect(await screen.findByText('React Documentation'))
            .toBeInTheDocument();
          expect(screen.queryByText('Vue Guide')).not.toBeInTheDocument();
        });
    """)

    # Simulate tests in Python
    dom = MockDOM()
    count = [0]

    def render_counter():
        dom.render({
            "tag": "div",
            "children": [
                {"tag": "span", "text": f"Count: {count[0]}"},
                {"tag": "button", "role": "button", "text": "increment",
                 "onclick": lambda: count.__setitem__(0, count[0] + 1)},
            ],
        })

    render_counter()

    def test_renders_initial():
        assert dom.get_by_text("Count: 0") is not None

    def test_increments():
        btn = dom.get_by_role("button")
        dom.fire_event(btn, "click")
        render_counter()
        assert dom.get_by_text("Count: 1") is not None

    runner.test("renders initial count", test_renders_initial)
    runner.test("increments on click", test_increments)
    runner.summary()

    # --- 6.3 Integration Testing ---
    header("6.3 Integration Testing Patterns", 2)
    explain("""
        Integration tests verify multiple units working together.
        In frontend: render a page/feature, interact like a user,
        and verify the result.

        Key principles:
        - Test user behavior, not implementation details.
        - Don't test internal state; test what the user sees.
        - Mock API boundaries (MSW - Mock Service Worker).
        - Avoid testing library internals.
    """)
    code_example("Integration test with MSW", """
        import { rest } from 'msw';
        import { setupServer } from 'msw/node';

        const server = setupServer(
          rest.get('/api/users', (req, res, ctx) => {
            return res(ctx.json([
              { id: 1, name: 'Alice' },
              { id: 2, name: 'Bob' },
            ]));
          })
        );

        beforeAll(() => server.listen());
        afterEach(() => server.resetHandlers());
        afterAll(() => server.close());

        test('displays user list from API', async () => {
          render(<UserList />);
          expect(screen.getByText('Loading...')).toBeInTheDocument();
          expect(await screen.findByText('Alice')).toBeInTheDocument();
          expect(screen.getByText('Bob')).toBeInTheDocument();
        });

        test('handles API error gracefully', async () => {
          server.use(
            rest.get('/api/users', (req, res, ctx) =>
              res(ctx.status(500)))
          );
          render(<UserList />);
          expect(await screen.findByText('Failed to load users'))
            .toBeInTheDocument();
        });
    """)

    # --- 6.4 E2E Testing ---
    header("6.4 E2E Testing with Playwright", 2)
    code_example("Playwright test example", """
        import { test, expect } from '@playwright/test';

        test('user can complete checkout', async ({ page }) => {
          await page.goto('/products');

          // Add item to cart
          await page.getByRole('button', { name: 'Add to Cart' }).first().click();
          await expect(page.getByTestId('cart-count')).toHaveText('1');

          // Go to checkout
          await page.getByRole('link', { name: 'Cart' }).click();
          await page.getByRole('button', { name: 'Checkout' }).click();

          // Fill form
          await page.getByLabel('Email').fill('test@example.com');
          await page.getByLabel('Card number').fill('4242424242424242');
          await page.getByRole('button', { name: 'Pay' }).click();

          // Verify success
          await expect(page.getByText('Order confirmed')).toBeVisible();
        });

        // Playwright config
        // playwright.config.ts
        export default defineConfig({
          webServer: { command: 'npm run dev', port: 3000 },
          use: { baseURL: 'http://localhost:3000' },
          projects: [
            { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
            { name: 'mobile', use: { ...devices['iPhone 13'] } },
          ],
        });
    """)

    # --- 6.5 Accessibility Testing ---
    header("6.5 Accessibility Testing (WCAG)", 2)

    class AccessibilityChecker:
        RULES = [
            ("img-alt",       "All <img> must have alt text",
             "WCAG 1.1.1 Non-text Content"),
            ("button-label",  "Buttons must have accessible name",
             "WCAG 4.1.2 Name, Role, Value"),
            ("color-contrast","Text must have 4.5:1 contrast ratio (AA)",
             "WCAG 1.4.3 Contrast (Minimum)"),
            ("heading-order", "Headings must be in logical order (h1->h2->h3)",
             "WCAG 1.3.1 Info and Relationships"),
            ("focus-visible", "Focus indicator must be visible",
             "WCAG 2.4.7 Focus Visible"),
            ("keyboard-nav",  "All interactive elements must be keyboard accessible",
             "WCAG 2.1.1 Keyboard"),
            ("aria-roles",    "ARIA roles must be valid",
             "WCAG 4.1.2 Name, Role, Value"),
            ("form-labels",   "Form inputs must have associated labels",
             "WCAG 1.3.1 Info and Relationships"),
        ]

        @classmethod
        def audit(cls, elements: list) -> list:
            violations = []
            for el in elements:
                if el.get("tag") == "img" and not el.get("alt"):
                    violations.append(("img-alt", el.get("src", "?")))
                if el.get("tag") == "button" and not (
                    el.get("text") or el.get("aria-label")):
                    violations.append(("button-label", "unnamed button"))
                if el.get("tag") == "input" and not el.get("label"):
                    violations.append(("form-labels", el.get("name", "?")))
            return violations

    test_elements = [
        {"tag": "img", "src": "/logo.png", "alt": "Company logo"},
        {"tag": "img", "src": "/hero.jpg"},  # missing alt!
        {"tag": "button", "text": "Submit"},
        {"tag": "button", "aria-label": None},  # missing label!
        {"tag": "input", "name": "email"},  # missing label!
        {"tag": "input", "name": "password", "label": "Password"},
    ]
    violations = AccessibilityChecker.audit(test_elements)
    print("\n  Accessibility Audit Results:")
    for rule, detail in violations:
        matching = [r for r in AccessibilityChecker.RULES if r[0] == rule]
        wcag = matching[0][2] if matching else ""
        print(f"    VIOLATION: [{rule}] {detail}")
        print(f"              {wcag}")
    print(f"\n    Total violations: {len(violations)}")

    explain("""
        Tools for accessibility testing:
        - axe-core: automated testing engine (jest-axe, @axe-core/playwright)
        - Lighthouse: includes accessibility audit
        - Screen reader testing: VoiceOver (Mac), NVDA (Windows)
        - eslint-plugin-jsx-a11y: catches issues at dev time
    """)

    # --- 6.6 Visual Regression ---
    header("6.6 Visual Regression Testing", 2)
    explain("""
        Visual regression detects unintended UI changes by comparing
        screenshots pixel-by-pixel or using perceptual diffing.

        Workflow:
        1. Capture baseline screenshots (approved state)
        2. Run tests -> capture new screenshots
        3. Diff: compare new vs baseline
        4. If different: review and approve or fix

        Tools:
        - Playwright: built-in screenshot comparison
        - Chromatic: visual testing SaaS (by Storybook team)
        - Percy (BrowserStack): cross-browser visual testing
        - BackstopJS: open-source visual regression
    """)

    def simulate_visual_diff(baseline: list, current: list) -> dict:
        total_pixels = len(baseline)
        diff_pixels = sum(1 for a, b in zip(baseline, current) if a != b)
        pct = (diff_pixels / total_pixels) * 100
        return {
            "total_pixels": total_pixels,
            "changed_pixels": diff_pixels,
            "change_pct": round(pct, 2),
            "status": "PASS" if pct < 0.1 else "REVIEW" if pct < 1.0 else "FAIL",
        }

    baseline = [1, 1, 1, 2, 2, 3, 3, 3, 4, 4] * 100
    current =  [1, 1, 1, 2, 2, 3, 3, 5, 4, 4] * 100  # 1 pixel changed
    result = simulate_visual_diff(baseline, current)
    print(f"\n  Visual diff: {result['changed_pixels']}/{result['total_pixels']} "
          f"pixels changed ({result['change_pct']}%) -> {result['status']}")


# ============================================================================
#  CHAPTER 7: Frontend Security
# ============================================================================

def chapter7_security():
    header("CHAPTER 7: Frontend Security")

    # --- 7.1 XSS Prevention ---
    header("7.1 XSS (Cross-Site Scripting) Prevention", 2)

    class XSSSimulator:
        @staticmethod
        def sanitize_html(untrusted: str) -> str:
            """Basic HTML entity encoding to prevent XSS."""
            replacements = {
                "&": "&amp;", "<": "&lt;", ">": "&gt;",
                '"': "&quot;", "'": "&#x27;", "/": "&#x2F;",
            }
            result = untrusted
            for char, entity in replacements.items():
                result = result.replace(char, entity)
            return result

        @staticmethod
        def is_safe_url(url: str) -> bool:
            """Block javascript: and data: URLs."""
            normalized = url.strip().lower()
            dangerous = ["javascript:", "data:", "vbscript:"]
            return not any(normalized.startswith(d) for d in dangerous)

    xss_payloads = [
        '<script>alert("XSS")</script>',
        '<img src=x onerror="steal(document.cookie)">',
        "javascript:alert('XSS')",
        '<div onmouseover="evil()">hover me</div>',
    ]

    print("\n  XSS Sanitization Demo:")
    for payload in xss_payloads:
        sanitized = XSSSimulator.sanitize_html(payload)
        print(f"    Input:     {payload}")
        print(f"    Sanitized: {sanitized}\n")

    print("  URL validation:")
    test_urls = [
        "https://example.com",
        "javascript:alert(1)",
        "data:text/html,<script>evil()</script>",
        "/safe/relative/path",
    ]
    for url in test_urls:
        safe = XSSSimulator.is_safe_url(url)
        print(f"    {url:50s} -> {'SAFE' if safe else 'BLOCKED'}")

    explain("""
        React automatically escapes JSX expressions (innerHTML is safe).
        BUT these are still dangerous:
        - dangerouslySetInnerHTML (obvious)
        - href={userInput} (javascript: URLs)
        - eval(), new Function(), setTimeout(string)
        - Server-side template injection
    """)

    # --- 7.2 CSRF ---
    header("7.2 CSRF (Cross-Site Request Forgery)", 2)
    explain("""
        CSRF: attacker tricks user's browser into making authenticated
        requests to your API.

        Attack scenario:
        1. User is logged into bank.com (has session cookie)
        2. User visits evil.com
        3. evil.com has: <img src="bank.com/transfer?to=attacker&amount=1000">
        4. Browser sends request WITH bank.com cookies!

        Defenses:
        1. CSRF Token: server generates token, client sends in header/body
        2. SameSite cookies: SameSite=Lax or Strict
        3. Check Origin/Referer headers
        4. Custom headers (X-Requested-With) - won't be sent cross-origin
    """)

    class CSRFProtection:
        def __init__(self):
            self.tokens: dict = {}

        def generate_token(self, session_id: str) -> str:
            token = hashlib.sha256(
                f"{session_id}{time.time()}".encode()
            ).hexdigest()[:32]
            self.tokens[session_id] = token
            return token

        def validate_token(self, session_id: str, token: str) -> bool:
            expected = self.tokens.get(session_id)
            if not expected:
                return False
            # Constant-time comparison to prevent timing attacks
            return hashlib.sha256(expected.encode()).digest() == \
                   hashlib.sha256(token.encode()).digest()

    csrf = CSRFProtection()
    token = csrf.generate_token("session-abc")
    print(f"\n  CSRF Token: {token}")
    print(f"  Valid token: {csrf.validate_token('session-abc', token)}")
    print(f"  Bad token:   {csrf.validate_token('session-abc', 'fake-token')}")

    # --- 7.3 Content Security Policy ---
    header("7.3 Content Security Policy (CSP)", 2)

    class CSPBuilder:
        def __init__(self):
            self.directives: dict = {}

        def add(self, directive: str, *sources: str) -> "CSPBuilder":
            self.directives[directive] = list(sources)
            return self

        def build(self) -> str:
            parts = []
            for directive, sources in self.directives.items():
                parts.append(f"{directive} {' '.join(sources)}")
            return "; ".join(parts)

    csp = (CSPBuilder()
           .add("default-src", "'self'")
           .add("script-src", "'self'", "'nonce-abc123'")
           .add("style-src", "'self'", "'unsafe-inline'")
           .add("img-src", "'self'", "data:", "https://cdn.example.com")
           .add("connect-src", "'self'", "https://api.example.com")
           .add("font-src", "'self'", "https://fonts.gstatic.com")
           .add("frame-ancestors", "'none'")
           .add("base-uri", "'self'")
           .add("form-action", "'self'"))

    csp_header = csp.build()
    print(f"\n  Content-Security-Policy:")
    for directive in csp_header.split("; "):
        print(f"    {directive}")

    explain("""
        CSP blocks:
        - Inline scripts (unless nonce/hash matches)
        - eval() and similar dynamic code execution
        - Loading resources from unauthorized origins
        - Framing your site (clickjacking prevention)

        Start with report-only mode to find violations before enforcing:
        Content-Security-Policy-Report-Only: ...
    """)

    # --- 7.4 Subresource Integrity ---
    header("7.4 Subresource Integrity (SRI)", 2)

    def generate_sri_hash(content: str) -> str:
        digest = hashlib.sha384(content.encode()).hexdigest()
        import base64
        b64 = base64.b64encode(
            hashlib.sha384(content.encode()).digest()
        ).decode()
        return f"sha384-{b64}"

    example_js = "console.log('hello');"
    sri_hash = generate_sri_hash(example_js)
    print(f"\n  SRI hash for script: {sri_hash[:40]}...")
    code_example("SRI in HTML", f"""
        <script
          src="https://cdn.example.com/lib.js"
          integrity="{sri_hash}"
          crossorigin="anonymous"
        ></script>

        <!-- If CDN is compromised and content changes,
             browser refuses to execute the script! -->
    """)

    # --- 7.5 Authentication Patterns ---
    header("7.5 Authentication Patterns", 2)

    auth_patterns = {
        "JWT in localStorage": {
            "flow": "Login -> server returns JWT -> store in localStorage -> send in Authorization header",
            "pros": ["Stateless", "Easy to implement"],
            "cons": ["XSS vulnerable (JS can read localStorage)",
                     "Cannot revoke easily"],
            "verdict": "AVOID for sensitive apps",
        },
        "JWT in httpOnly cookie": {
            "flow": "Login -> server sets httpOnly cookie -> automatically sent with requests",
            "pros": ["XSS-safe (JS cannot read httpOnly cookies)",
                     "Automatic inclusion"],
            "cons": ["Need CSRF protection", "Cookie size limits"],
            "verdict": "RECOMMENDED",
        },
        "Session-based": {
            "flow": "Login -> server creates session -> sends session ID cookie -> server validates on each request",
            "pros": ["Easy revocation", "Server controls session",
                     "Battle-tested"],
            "cons": ["Server state required", "Scaling needs sticky sessions or shared store"],
            "verdict": "GOOD for server-rendered apps",
        },
        "OAuth 2.0 + PKCE": {
            "flow": "Redirect to provider -> user authorizes -> callback with code -> exchange for tokens",
            "pros": ["Delegated auth", "No password handling",
                     "PKCE prevents code interception"],
            "cons": ["Complex flow", "Provider dependency"],
            "verdict": "USE for third-party login (Google, GitHub)",
        },
    }

    for name, info in auth_patterns.items():
        print(f"\n  {name}: [{info['verdict']}]")
        print(f"    Flow: {info['flow']}")
        print(f"    Pros: {', '.join(info['pros'])}")
        print(f"    Cons: {', '.join(info['cons'])}")

    # --- 7.6 CORS ---
    header("7.6 CORS (Cross-Origin Resource Sharing)", 2)

    class CORSSimulator:
        def __init__(self, allowed_origins: list, allowed_methods: list,
                     allow_credentials: bool = False):
            self.allowed_origins = allowed_origins
            self.allowed_methods = allowed_methods
            self.allow_credentials = allow_credentials

        def handle_preflight(self, origin: str, method: str) -> dict:
            """Simulate preflight (OPTIONS) response."""
            if origin in self.allowed_origins or "*" in self.allowed_origins:
                return {
                    "Access-Control-Allow-Origin": origin,
                    "Access-Control-Allow-Methods": ", ".join(self.allowed_methods),
                    "Access-Control-Allow-Headers": "Content-Type, Authorization",
                    "Access-Control-Max-Age": "86400",
                    "Access-Control-Allow-Credentials": str(self.allow_credentials).lower(),
                    "status": 204,
                    "allowed": True,
                }
            return {"status": 403, "allowed": False,
                    "reason": f"Origin {origin} not allowed"}

        def handle_request(self, origin: str, method: str) -> dict:
            if method in ("GET", "HEAD", "POST"):
                content_type = "application/x-www-form-urlencoded"
                is_simple = True
            else:
                is_simple = False

            if not is_simple:
                preflight = self.handle_preflight(origin, method)
                if not preflight["allowed"]:
                    return preflight

            if origin in self.allowed_origins:
                return {
                    "Access-Control-Allow-Origin": origin,
                    "status": 200, "allowed": True,
                }
            return {"status": 403, "allowed": False,
                    "reason": f"Origin {origin} not allowed"}

    cors = CORSSimulator(
        allowed_origins=["https://myapp.com", "https://staging.myapp.com"],
        allowed_methods=["GET", "POST", "PUT", "DELETE"],
        allow_credentials=True,
    )

    print("\n  CORS Request Simulation:")
    test_requests = [
        ("https://myapp.com",     "GET"),
        ("https://myapp.com",     "PUT"),
        ("https://evil.com",      "GET"),
        ("https://evil.com",      "DELETE"),
    ]
    for origin, method in test_requests:
        result = cors.handle_request(origin, method)
        status = "ALLOWED" if result["allowed"] else "BLOCKED"
        reason = result.get("reason", "")
        print(f"    {method:6s} from {origin:30s} -> {status} {reason}")

    explain("""
        CORS key points:
        - Browser-enforced (server sends headers, browser decides)
        - Simple requests (GET/POST with simple headers) skip preflight
        - Preflight (OPTIONS) sent for PUT/DELETE/custom headers
        - credentials: include requires specific origin (not *)
        - CORS is NOT a security boundary for server-to-server calls
    """)


# ============================================================================
#  Main
# ============================================================================

def main():
    print("=" * 72)
    print("  FRONTEND ENGINEERING - Comprehensive Learning Module")
    print("  React | Next.js | Performance | CSS | State | Testing | Security")
    print("=" * 72)

    chapter1_react_core()
    chapter2_nextjs()
    chapter3_performance()
    chapter4_css()
    chapter5_state()
    chapter6_testing()
    chapter7_security()

    header("LEARNING COMPLETE")
    explain("""
        Frontend engineering is about delivering fast, accessible,
        and secure user experiences. Key takeaways:

        1. React: understand VDOM diffing, hooks rules, and RSC.
        2. Next.js: choose the right rendering strategy per page.
        3. Performance: measure Core Web Vitals, budget your bundles.
        4. CSS: keep specificity flat, use Grid/Flexbox appropriately.
        5. State: separate server state from client state.
        6. Testing: write integration tests, test user behavior.
        7. Security: sanitize output, use CSP, prefer httpOnly cookies.

        Recommended learning path:
        React fundamentals -> Next.js App Router -> Performance optimization
        -> CSS architecture -> State management -> Testing -> Security
    """)


if __name__ == "__main__":
    main()
