#!/usr/bin/env python3
"""
phase_programming/python_advanced.py
=====================================
Python 上級機能 - FAANG テックリード/PM を目指すための完全ガイド

なぜこれが必要か:
  Pythonは「書ける」だけではFAANGでは通用しない。
  メタプログラミング、非同期処理、型システム、パフォーマンス最適化
  ── これらを深く理解して初めて「Pythonが得意」と言える。
  面接では「デコレータの仕組みを説明してください」
  「asyncioはなぜGILの制約を受けないのか」が飛んでくる。

このフェーズで学ぶこと:
  1. 非同期プログラミング (async/await, asyncio)
  2. メタプログラミング (デコレータ, メタクラス, descriptor)
  3. 型システム (TypeVar, Generic, Protocol, TypeGuard)
  4. パフォーマンス最適化 (__slots__, lru_cache, profiling)
  5. コンテキストマネージャとリソース管理
  6. イテレータ・ジェネレータの深掘り
  7. テスト技法 (mock, patch, property-based)
  8. Pythonic イディオム (walrus, match-case, EAFP)

実行方法:
  python python_advanced.py

標準ライブラリのみ使用。外部依存なし。

考えてほしい疑問:
  Q1. asyncio はなぜ GIL の制約を受けないのか？（I/Oバウンドだから）
  Q2. Pythonの型ヒントはランタイムで何もしない。なぜ有用か？
  Q3. なぜPythonはC/Go/Rustの100倍遅いのか？
  Q4. メタクラスとクラスデコレータはどう使い分けるか？
  Q5. EAFP と LBYL の使い分けは？
  Q6. Generator の send() はどんな場面で使うか？
  Q7. __slots__ は「万能の最適化」か？（継承との相互作用は？）
  Q8. Protocol と ABC の使い分けは？
"""

from __future__ import annotations

import asyncio
import contextlib
import contextvars
import functools
import heapq
import inspect
import io
import itertools
import math
import os
import struct
import sys
import textwrap
import threading
import time
import timeit
import types
import unittest
import unittest.mock
import weakref
from abc import ABC, abstractmethod
from array import array
from bisect import bisect_left, insort
from collections import OrderedDict, defaultdict, deque, namedtuple
from contextlib import ExitStack, asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import (
    Annotated,
    Any,
    Callable,
    ClassVar,
    Generator,
    Generic,
    Iterator,
    Literal,
    NamedTuple,
    Optional,
    Protocol,
    TypeVar,
    Union,
    get_args,
    get_type_hints,
    overload,
    runtime_checkable,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ユーティリティ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def section(title: str) -> None:
    print()
    print("=" * 64)
    print(f"  {title}")
    print("=" * 64)
    print()


def subsection(title: str) -> None:
    print()
    print(f"  -- {title} --")
    print()


def question(text: str) -> None:
    print(f"  [考えてほしい疑問] {text}")
    print()


def task(text: str) -> None:
    print(f"  [実装してみよう] {text}")
    print()


def point(text: str) -> None:
    print(f"    > {text}")


def demo(label: str, value: Any = None) -> None:
    if value is not None:
        print(f"    {label}: {value}")
    else:
        print(f"    {label}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 非同期プログラミング (Async/Await)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def chapter_1_async():
    """
    非同期プログラミングの核心:
      - シングルスレッドで並行処理を実現
      - I/O待ち時間を別のタスクに使う「協調的マルチタスク」
      - threading と違いロックが不要（シングルスレッドだから）

    なぜ asyncio は GIL の制約を受けないか？
      GIL は「CPU処理」をシングルスレッドに制限するもの。
      asyncio は I/O 待ちの間に別のタスクを進めるだけで、
      CPUバウンド処理を並列化するわけではない。
      つまり GIL の制約対象と asyncio の守備範囲は違う。
    """
    section("1. 非同期プログラミング (Async/Await)")

    # ── 1.1 基本: async/await ──
    subsection("1.1 async/await の基本")

    async def fetch_data(name: str, delay: float) -> str:
        """I/O処理をシミュレート"""
        print(f"      [{name}] 開始 (待機 {delay}s)")
        await asyncio.sleep(delay)
        print(f"      [{name}] 完了")
        return f"{name}_result"

    async def basic_demo():
        """逐次 vs 並行の速度差"""
        # 逐次実行
        start = time.perf_counter()
        r1 = await fetch_data("task_A", 0.1)
        r2 = await fetch_data("task_B", 0.1)
        sequential_time = time.perf_counter() - start
        demo(f"逐次実行: {r1}, {r2} ({sequential_time:.3f}s)")

        # 並行実行 (asyncio.gather)
        start = time.perf_counter()
        r1, r2 = await asyncio.gather(
            fetch_data("task_A", 0.1),
            fetch_data("task_B", 0.1),
        )
        concurrent_time = time.perf_counter() - start
        demo(f"並行実行: {r1}, {r2} ({concurrent_time:.3f}s)")
        demo(f"速度向上: {sequential_time / concurrent_time:.1f}x")

    asyncio.run(basic_demo())

    question("逐次では0.2s、並行では0.1sで終わる。なぜ？")
    point("gather は両タスクを同時に開始し、最長の待ち時間だけで済む")

    # ── 1.2 asyncio.create_task ──
    subsection("1.2 asyncio.create_task - タスクのスケジューリング")

    async def create_task_demo():
        """create_task はタスクを即座にスケジュールする"""
        async def background_job(n: int) -> int:
            await asyncio.sleep(0.05)
            return n * n

        # create_task で即座にスケジュール
        tasks = [asyncio.create_task(background_job(i)) for i in range(5)]
        # 他の処理を挟める
        demo("タスクをスケジュールした。他の仕事を挟む...")
        await asyncio.sleep(0.01)
        # 結果を回収
        results = [await t for t in tasks]
        demo(f"create_task 結果: {results}")

    asyncio.run(create_task_demo())

    point("create_task は gather と違い、タスクを個別に管理できる")
    point("キャンセル: task.cancel() で途中停止可能")

    # ── 1.3 Semaphore で並行度制御 ──
    subsection("1.3 Semaphore - 並行度の制御")

    async def semaphore_demo():
        """
        Semaphore: 同時に実行できるタスク数を制限
        実用例: API レート制限、DB コネクションプール
        """
        sem = asyncio.Semaphore(2)  # 最大2並行
        active = 0

        async def limited_task(name: str) -> str:
            nonlocal active
            async with sem:
                active += 1
                demo(f"[{name}] 実行中 (同時実行数: {active})")
                await asyncio.sleep(0.05)
                active -= 1
                return f"{name}_done"

        results = await asyncio.gather(*[
            limited_task(f"job_{i}") for i in range(6)
        ])
        demo(f"全タスク完了: {len(results)}件")

    asyncio.run(semaphore_demo())

    question("Semaphore(2) にしたのに6タスク実行できるのはなぜ？")
    point("同時実行数が2に制限されるだけ。順番に2つずつ処理される。")

    # ── 1.4 async generator ──
    subsection("1.4 Async Generator / Async Context Manager")

    async def async_gen_demo():
        # Async generator: yield を使った非同期ストリーム
        async def async_counter(n: int):
            """非同期ジェネレータ: データストリーム処理に最適"""
            for i in range(n):
                await asyncio.sleep(0.01)
                yield i * i

        results = []
        async for val in async_counter(5):
            results.append(val)
        demo(f"Async generator results: {results}")

        # Async context manager
        class AsyncResource:
            """非同期リソース管理"""
            async def __aenter__(self):
                demo("非同期リソース獲得")
                await asyncio.sleep(0.01)
                return self

            async def __aexit__(self, *exc):
                demo("非同期リソース解放")
                await asyncio.sleep(0.01)

            async def query(self) -> str:
                await asyncio.sleep(0.01)
                return "query_result"

        async with AsyncResource() as res:
            result = await res.query()
            demo(f"クエリ結果: {result}")

    asyncio.run(async_gen_demo())

    # ── 1.5 asyncio vs threading vs multiprocessing ──
    subsection("1.5 asyncio vs threading vs multiprocessing 比較")

    print(textwrap.dedent("""\
    +------------------+----------------+----------------+-----------------+
    | 特性             | asyncio        | threading      | multiprocessing |
    +------------------+----------------+----------------+-----------------+
    | 並行/並列        | 並行(concurrent)| 並行(concurrent)| 並列(parallel)  |
    | GIL制約          | 関係なし(I/O)  | CPU処理に影響  | GIL回避         |
    | メモリ           | 最小           | スレッド分     | プロセス分(大)  |
    | 適用場面         | I/Oバウンド    | I/O + レガシー | CPUバウンド     |
    | デバッグ難易度   | 中             | 高(race cond.) | 中              |
    | コンテキスト切替 | 自発的(await)  | OS依存         | OS依存          |
    +------------------+----------------+----------------+-----------------+
    """))

    question("asyncio はなぜ race condition が起きにくいか？")
    point("await の位置でしかタスク切り替えが起きない（協調的マルチタスク）")
    point("threading は OS がいつでも切り替えるため、予測不能な割り込みが起きる")

    # ── 1.6 簡易HTTPサーバー (asyncioのみ) ──
    subsection("1.6 asyncio ベースの簡易 HTTP サーバー/クライアント")

    async def http_demo():
        """asyncio.start_server で HTTP サーバーを実装"""
        async def handle_client(
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
        ):
            data = await reader.read(1024)
            request_line = data.decode().split("\r\n")[0]
            demo(f"サーバー受信: {request_line}")

            response_body = '{"status": "ok", "message": "Hello from asyncio!"}'
            response = (
                "HTTP/1.1 200 OK\r\n"
                f"Content-Length: {len(response_body)}\r\n"
                "Content-Type: application/json\r\n"
                "\r\n"
                f"{response_body}"
            )
            writer.write(response.encode())
            await writer.drain()
            writer.close()
            await writer.wait_closed()

        # サーバー起動
        server = await asyncio.start_server(handle_client, "127.0.0.1", 0)
        addr = server.sockets[0].getsockname()
        demo(f"サーバー起動: {addr}")

        # クライアント接続
        reader, writer = await asyncio.open_connection(addr[0], addr[1])
        writer.write(b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")
        await writer.drain()

        response = await reader.read(4096)
        body = response.decode().split("\r\n\r\n", 1)[1]
        demo(f"クライアント受信: {body}")

        writer.close()
        await writer.wait_closed()
        server.close()
        await server.wait_closed()

    asyncio.run(http_demo())
    point("aiohttp を使わなくても asyncio だけで HTTP 通信は可能")

    task("WebSocket 風の双方向通信を asyncio.start_server で実装してみよう")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. メタプログラミング
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def chapter_2_metaprogramming():
    """
    メタプログラミング = 「コードを書くコード」
    Pythonでは デコレータ、メタクラス、descriptor が三本柱。
    """
    section("2. メタプログラミング")

    # ── 2.1 デコレータ基礎 ──
    subsection("2.1 デコレータ - 関数を包む関数")

    # --- @timer ---
    def timer(func: Callable) -> Callable:
        """実行時間を計測するデコレータ"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            demo(f"@timer: {func.__name__} took {elapsed:.6f}s")
            return result
        return wrapper

    @timer
    def slow_function():
        total = sum(range(100_000))
        return total

    result = slow_function()
    demo(f"結果: {result}")
    demo(f"関数名保持 (functools.wraps): {slow_function.__name__}")

    point("functools.wraps がないと __name__ は 'wrapper' になってしまう")

    # --- @retry (引数ありデコレータ) ---
    subsection("2.2 引数ありデコレータ: @retry")

    def retry(max_attempts: int = 3, delay: float = 0.01):
        """リトライデコレータ（引数あり）
        構造: retry(args) -> decorator(func) -> wrapper(*args)
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                for attempt in range(1, max_attempts + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        demo(f"@retry: {func.__name__} attempt {attempt} failed: {e}")
                        time.sleep(delay)
                raise last_exception  # type: ignore
            return wrapper
        return decorator

    call_count = 0

    @retry(max_attempts=3, delay=0.01)
    def flaky_api_call():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("サーバー不安定")
        return "success"

    result = flaky_api_call()
    demo(f"@retry 結果: {result} ({call_count}回目で成功)")

    # --- @validate_types ---
    subsection("2.3 型バリデーションデコレータ: @validate_types")

    def validate_types(func: Callable) -> Callable:
        """型ヒントに基づくランタイム型チェック"""
        hints = get_type_hints(func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            for param_name, value in bound.arguments.items():
                if param_name in hints and param_name != "return":
                    expected = hints[param_name]
                    if not isinstance(value, expected):
                        raise TypeError(
                            f"{param_name}: expected {expected.__name__}, "
                            f"got {type(value).__name__}"
                        )
            return func(*args, **kwargs)
        return wrapper

    @validate_types
    def add_numbers(a: int, b: int) -> int:
        return a + b

    demo(f"add_numbers(3, 4) = {add_numbers(3, 4)}")
    try:
        add_numbers(3, "4")  # type: ignore
    except TypeError as e:
        demo(f"型エラー検出: {e}")

    # --- @cache (手動実装) ---
    subsection("2.4 キャッシュデコレータ: @cache 手動実装")

    def simple_cache(func: Callable) -> Callable:
        """LRU Cache を手動実装（OrderedDict使用）"""
        cache: OrderedDict = OrderedDict()
        max_size = 128

        @functools.wraps(func)
        def wrapper(*args):
            if args in cache:
                cache.move_to_end(args)
                return cache[args]
            result = func(*args)
            cache[args] = result
            if len(cache) > max_size:
                cache.popitem(last=False)
            return result

        wrapper.cache = cache  # type: ignore
        return wrapper

    @simple_cache
    def fibonacci(n: int) -> int:
        if n < 2:
            return n
        return fibonacci(n - 1) + fibonacci(n - 2)

    demo(f"fibonacci(30) = {fibonacci(30)}")
    demo(f"キャッシュサイズ: {len(fibonacci.cache)}")

    # --- クラスデコレータ ---
    subsection("2.5 クラスデコレータ")

    def singleton(cls):
        """シングルトンパターンをデコレータで実現"""
        instances: dict = {}

        @functools.wraps(cls, updated=[])
        def get_instance(*args, **kwargs):
            if cls not in instances:
                instances[cls] = cls(*args, **kwargs)
            return instances[cls]

        return get_instance

    @singleton
    class DatabaseConnection:
        def __init__(self):
            self.id = id(self)

    conn1 = DatabaseConnection()
    conn2 = DatabaseConnection()
    demo(f"同一インスタンスか？: {conn1.id == conn2.id}")

    # ── 2.6 メタクラス ──
    subsection("2.6 メタクラス - クラスを生成するクラス")

    print(textwrap.dedent("""\
        クラスの生成プロセス:
          1. class文を解析
          2. type(name, bases, namespace) を呼ぶ
          3. type.__new__ でクラスオブジェクトを作成
          4. type.__init__ で初期化

        メタクラス = この type を置き換えるもの
    """))

    class RegistryMeta(type):
        """登録メタクラス: 全サブクラスを自動追跡"""
        _registry: dict[str, type] = {}

        def __new__(mcs, name, bases, namespace):
            cls = super().__new__(mcs, name, bases, namespace)
            if bases:  # ベースクラス自体は登録しない
                mcs._registry[name] = cls
            return cls

    class Plugin(metaclass=RegistryMeta):
        """プラグインの基底クラス"""
        pass

    class AuthPlugin(Plugin):
        pass

    class CachePlugin(Plugin):
        pass

    demo(f"登録済みプラグイン: {list(RegistryMeta._registry.keys())}")

    point("メタクラスは強力だが複雑。大抵は __init_subclass__ で代替可能")

    # ── 2.7 __init_subclass__ (Python 3.6+) ──
    subsection("2.7 __init_subclass__ - メタクラスの軽量版")

    class Validator:
        """サブクラスに required_fields 属性を強制"""
        _validators: list[type] = []

        def __init_subclass__(cls, **kwargs):
            super().__init_subclass__(**kwargs)
            if not hasattr(cls, "required_fields"):
                raise TypeError(f"{cls.__name__} must define 'required_fields'")
            Validator._validators.append(cls)

    class EmailValidator(Validator):
        required_fields = ["to", "subject", "body"]

    class PhoneValidator(Validator):
        required_fields = ["number", "country_code"]

    demo(f"バリデータ一覧: {[v.__name__ for v in Validator._validators]}")

    # ── 2.8 Descriptor Protocol ──
    subsection("2.8 Descriptor Protocol (__get__, __set__)")

    class TypedField:
        """型チェック付きフィールド（descriptor）"""
        def __init__(self, expected_type: type):
            self.expected_type = expected_type
            self.name = ""

        def __set_name__(self, owner: type, name: str):
            """Python 3.6+: フィールド名を自動取得"""
            self.name = f"_{name}"

        def __get__(self, obj, objtype=None):
            if obj is None:
                return self
            return getattr(obj, self.name, None)

        def __set__(self, obj, value):
            if not isinstance(value, self.expected_type):
                raise TypeError(
                    f"{self.name}: expected {self.expected_type.__name__}, "
                    f"got {type(value).__name__}"
                )
            setattr(obj, self.name, value)

    class User:
        name = TypedField(str)
        age = TypedField(int)

        def __init__(self, name: str, age: int):
            self.name = name
            self.age = age

    user = User("Alice", 30)
    demo(f"User: name={user.name}, age={user.age}")

    try:
        user.age = "thirty"  # type: ignore
    except TypeError as e:
        demo(f"Descriptor 型エラー: {e}")

    point("property も descriptor の一種。@property は __get__/__set__ の糖衣構文")

    # ── 2.9 dataclass の内部実装 ──
    subsection("2.9 @dataclass が裏でやっていること")

    print(textwrap.dedent("""\
        @dataclass はクラスに以下を自動生成する:
          - __init__: フィールドから引数を生成
          - __repr__: フィールドを表示
          - __eq__: フィールド同士の比較
          - __hash__: frozen=True の場合
          - __lt__ 等: order=True の場合

        「自分で書いたら退屈なボイラープレート」を自動生成する。
    """))

    def manual_dataclass(cls):
        """@dataclass を手動で再実装（簡易版）"""
        annotations = cls.__annotations__
        fields = list(annotations.keys())

        # __init__ を動的生成
        def __init__(self, **kwargs):
            for f in fields:
                setattr(self, f, kwargs.get(f))

        def __repr__(self):
            vals = ", ".join(f"{f}={getattr(self, f)!r}" for f in fields)
            return f"{cls.__name__}({vals})"

        def __eq__(self, other):
            if not isinstance(other, cls):
                return NotImplemented
            return all(getattr(self, f) == getattr(other, f) for f in fields)

        cls.__init__ = __init__
        cls.__repr__ = __repr__
        cls.__eq__ = __eq__
        return cls

    @manual_dataclass
    class Point:
        x: float
        y: float

    p = Point(x=1.0, y=2.0)
    demo(f"手動 dataclass: {p}")
    demo(f"等値比較: {p == Point(x=1.0, y=2.0)}")

    # ── 2.10 ABC vs Protocol ──
    subsection("2.10 ABC (名目的型) vs Protocol (構造的型)")

    # ABC: 継承が必要（名目的型付け / nominal subtyping）
    class Drawable(ABC):
        @abstractmethod
        def draw(self) -> str:
            ...

    class Circle(Drawable):
        def draw(self) -> str:
            return "O"

    # Protocol: 継承不要（構造的型付け / structural subtyping）
    @runtime_checkable
    class Renderable(Protocol):
        def render(self) -> str:
            ...

    class Button:
        """Protocol を継承していないが、render() があるので Renderable"""
        def render(self) -> str:
            return "<button>Click</button>"

    demo(f"Circle は Drawable か: {isinstance(Circle(), Drawable)}")
    demo(f"Button は Renderable か: {isinstance(Button(), Renderable)}")

    print(textwrap.dedent("""
        使い分け:
          ABC: 「このクラスは必ずXXXを実装せよ」と強制したいとき
          Protocol: 既存コードを変更せずに互換性を定義したいとき
          → Go の interface に近いのが Protocol
          → Java の abstract class に近いのが ABC
    """))

    question("Django の Model は ABC とメタクラスのどちらを使っている？なぜ？")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. 型システム (Type Hints Advanced)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def chapter_3_type_system():
    """
    Pythonの型ヒントはランタイムで何もしない。なぜ有用か？
      1. IDE のオートコンプリートが効く
      2. mypy/pyright でバグを実行前に検出
      3. ドキュメントとして機能（型が仕様書）
      4. リファクタリングの安全性が上がる
    """
    section("3. 型システム (Type Hints Advanced)")

    # ── 3.1 TypeVar と Generic ──
    subsection("3.1 TypeVar と Generic[T]")

    T = TypeVar("T")
    K = TypeVar("K")
    V = TypeVar("V")

    class Stack(Generic[T]):
        """型安全なスタック"""
        def __init__(self) -> None:
            self._items: list[T] = []

        def push(self, item: T) -> None:
            self._items.append(item)

        def pop(self) -> T:
            if not self._items:
                raise IndexError("empty stack")
            return self._items.pop()

        def peek(self) -> T:
            if not self._items:
                raise IndexError("empty stack")
            return self._items[-1]

        def __len__(self) -> int:
            return len(self._items)

        def __repr__(self) -> str:
            return f"Stack({self._items})"

    int_stack: Stack[int] = Stack()
    int_stack.push(1)
    int_stack.push(2)
    int_stack.push(3)
    demo(f"Stack[int]: {int_stack}")
    demo(f"pop: {int_stack.pop()}")

    str_stack: Stack[str] = Stack()
    str_stack.push("hello")
    str_stack.push("world")
    demo(f"Stack[str]: {str_stack}")

    # Bounded TypeVar
    Numeric = TypeVar("Numeric", int, float)

    def safe_divide(a: Numeric, b: Numeric) -> float:
        if b == 0:
            raise ValueError("division by zero")
        return float(a) / float(b)

    demo(f"safe_divide(10, 3) = {safe_divide(10, 3):.4f}")

    # ── 3.2 Literal と TypeGuard ──
    subsection("3.2 Literal, TypeGuard")

    # Literal: 特定の値のみを許可
    Direction = Literal["north", "south", "east", "west"]

    def move(direction: Direction, steps: int) -> str:
        return f"Moving {direction} by {steps} steps"

    demo(move("north", 5))

    # TypeGuard: 型を絞り込む関数
    # Python 3.10+ だが、typing_extensions でも利用可
    def is_string_list(val: list[Any]) -> bool:
        """TypeGuard[list[str]] の概念デモ"""
        return all(isinstance(item, str) for item in val)

    mixed: list[Any] = ["a", "b", "c"]
    if is_string_list(mixed):
        demo(f"文字列リスト確認: {mixed}")

    point("TypeGuard は mypy に『この条件が True なら型はXXX』と教えるもの")

    # ── 3.3 Protocol (再掲: 構造的型付け) ──
    subsection("3.3 Protocol - 構造的型付けの威力")

    @runtime_checkable
    class Comparable(Protocol):
        def __lt__(self, other: Any) -> bool: ...
        def __eq__(self, other: object) -> bool: ...

    Comp = TypeVar("Comp", bound="Comparable")

    def find_min(items: list[Any]) -> Any:
        """Protocol ベースの汎用 min 関数"""
        if not items:
            raise ValueError("empty list")
        result = items[0]
        for item in items[1:]:
            if item < result:
                result = item
        return result

    demo(f"find_min([3,1,4,1,5]) = {find_min([3, 1, 4, 1, 5])}")
    demo(f"find_min(['c','a','b']) = {find_min(['c', 'a', 'b'])}")

    # ── 3.4 overload デコレータ ──
    subsection("3.4 @overload - 引数の型に応じた戻り値型")

    # overload は mypy 用のマーカー。ランタイムでは最後の実装が使われる。
    @overload
    def process(data: str) -> list[str]: ...
    @overload
    def process(data: int) -> list[int]: ...

    def process(data):
        """実際の実装（ランタイムで呼ばれる）"""
        if isinstance(data, str):
            return list(data)
        elif isinstance(data, int):
            return list(range(data))
        raise TypeError(f"unsupported type: {type(data)}")

    demo(f'process("abc") = {process("abc")}')
    demo(f"process(5) = {process(5)}")

    point("@overload は mypy のため。ランタイムでは型による分岐を自分で書く")

    # ── 3.5 Annotated ──
    subsection("3.5 Annotated - 型にメタデータを付与")

    # Annotated は型+メタデータの組み合わせ
    PositiveInt = Annotated[int, "must be positive"]
    Email = Annotated[str, "must be valid email"]

    demo(f"  PositiveInt = {PositiveInt}")
    demo(f"  Email = {Email}")
    demo(f"  メタデータ取得: {get_args(PositiveInt)}")  # (int, 'must be positive')

    point("FastAPI/Pydantic は Annotated を使って依存性注入やバリデーションを実現")

    # ── 3.6 mypy で検出できるバグ ──
    subsection("3.6 mypy で検出できるバグの具体例")

    print(textwrap.dedent("""\
        # 例1: None チェック漏れ
        def get_user(id: int) -> Optional[User]:
            ...
        user = get_user(1)
        print(user.name)  # mypy: "Optional[User]" has no attribute "name"

        # 例2: 型の不一致
        def add(a: int, b: int) -> int:
            return a + b
        add(1, "2")  # mypy: Argument 2 has incompatible type "str"

        # 例3: 戻り値の型ミス
        def is_valid(x: int) -> bool:
            return x  # mypy: Incompatible return value type

        # 例4: dict のキー存在チェック漏れ
        data: dict[str, int] = {}
        val: int = data["key"]  # mypy は警告しないが TypedDict なら検出可能

        ポイント: 型ヒントは「ドキュメント」ではなく「検証可能な仕様」
    """))

    question("Pythonの型ヒントはランタイムで何もしない。なぜ有用か？")
    point("IDE補完、静的解析でのバグ検出、ドキュメント、リファクタ安全性")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. パフォーマンス最適化
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def chapter_4_performance():
    """
    なぜPythonはC/Go/Rustの100倍遅いのか？
      1. インタプリタ: 機械語に事前コンパイルしない
      2. 動的型付け: 毎回型チェックが必要
      3. GIL: CPUバウンドの並列化が不可能
      4. オブジェクトのオーバーヘッド: int ですら 28バイト

    → だからこそ、Pythonでは「書き方」で10倍以上の差が出る
    """
    section("4. パフォーマンス最適化")

    # ── 4.1 __slots__ でメモリ削減 ──
    subsection("4.1 __slots__ - メモリ削減の実測")

    class PointWithDict:
        def __init__(self, x: float, y: float):
            self.x = x
            self.y = y

    class PointWithSlots:
        __slots__ = ("x", "y")

        def __init__(self, x: float, y: float):
            self.x = x
            self.y = y

    # メモリ比較
    p_dict = PointWithDict(1.0, 2.0)
    p_slots = PointWithSlots(1.0, 2.0)

    size_dict = sys.getsizeof(p_dict)
    size_slots = sys.getsizeof(p_slots)
    # __dict__ があるとさらにオーバーヘッド
    if hasattr(p_dict, "__dict__"):
        size_dict += sys.getsizeof(p_dict.__dict__)

    demo(f"PointWithDict  サイズ: {size_dict} bytes")
    demo(f"PointWithSlots サイズ: {size_slots} bytes")
    demo(f"削減率: {(1 - size_slots / size_dict) * 100:.0f}%")

    point("__slots__ は __dict__ を廃止してメモリを節約する")
    point("ただし動的な属性追加ができなくなる")

    question("__slots__ を使ったクラスを継承するとどうなるか？")
    point("子クラスでも __slots__ を定義しないと __dict__ が復活する")

    # ── 4.2 generator vs list comprehension ──
    subsection("4.2 Generator vs List Comprehension - メモリ比較")

    # List comprehension: 全てメモリに展開
    list_comp = [i * i for i in range(10_000)]
    list_size = sys.getsizeof(list_comp)

    # Generator: 遅延評価
    gen_expr = (i * i for i in range(10_000))
    gen_size = sys.getsizeof(gen_expr)

    demo(f"List comprehension サイズ: {list_size:,} bytes")
    demo(f"Generator expression サイズ: {gen_size:,} bytes")
    demo(f"メモリ効率: generator は {list_size // gen_size}x 少ない")

    point("sum(), max(), any() に渡すなら generator で十分")
    point("例: sum(x*x for x in range(10000)) -- リストを作らない")

    # ── 4.3 lru_cache / cache でメモ化 ──
    subsection("4.3 functools.lru_cache - メモ化")

    def fib_naive(n: int) -> int:
        if n < 2:
            return n
        return fib_naive(n - 1) + fib_naive(n - 2)

    @functools.lru_cache(maxsize=None)
    def fib_cached(n: int) -> int:
        if n < 2:
            return n
        return fib_cached(n - 1) + fib_cached(n - 2)

    # 速度比較
    start = time.perf_counter()
    fib_naive(30)
    naive_time = time.perf_counter() - start

    start = time.perf_counter()
    fib_cached(30)
    cached_time = time.perf_counter() - start

    demo(f"fib_naive(30):  {naive_time:.4f}s")
    demo(f"fib_cached(30): {cached_time:.6f}s")
    if cached_time > 0:
        demo(f"高速化: {naive_time / max(cached_time, 1e-9):.0f}x")
    demo(f"キャッシュ情報: {fib_cached.cache_info()}")

    point("lru_cache(maxsize=None) は Python 3.9+ の @cache と同等")
    point("引数が hashable でないと使えない（list, dict は不可）")

    # ── 4.4 bisect / heapq / deque ──
    subsection("4.4 bisect / heapq / deque の正しい使い方")

    # bisect: ソート済みリストへの挿入/検索
    sorted_list: list[int] = []
    for val in [5, 1, 8, 3, 9, 2, 7]:
        insort(sorted_list, val)
    demo(f"insort 結果: {sorted_list}")

    # 二分探索で値を検索
    idx = bisect_left(sorted_list, 5)
    demo(f"bisect_left(5) -> index {idx}, value {sorted_list[idx]}")

    # heapq: 優先度キュー
    tasks = [(3, "low"), (1, "critical"), (2, "medium")]
    heapq.heapify(tasks)
    demo(f"heapq (最小値から取得):")
    while tasks:
        priority, name = heapq.heappop(tasks)
        demo(f"  priority={priority}, task={name}")

    # deque: 両端キュー (O(1) 追加/削除)
    ring_buffer: deque[int] = deque(maxlen=5)
    for i in range(8):
        ring_buffer.append(i)
    demo(f"deque(maxlen=5) に 0-7 を追加: {list(ring_buffer)}")
    point("maxlen を設定するとリングバッファとして使える")

    # ── 4.5 struct.pack でバイナリデータ処理 ──
    subsection("4.5 struct.pack - バイナリデータ処理")

    # ネットワークプロトコルやファイルフォーマットの解析に必須
    # Format: ! = network byte order, H = unsigned short, I = unsigned int
    header = struct.pack("!HHI", 0x0800, 80, 12345678)
    demo(f"パック済みバイナリ: {header.hex()}")

    protocol, port, seq = struct.unpack("!HHI", header)
    demo(f"アンパック: protocol=0x{protocol:04x}, port={port}, seq={seq}")

    point("ネットワークプログラミングでは byte order に注意")
    point("! = big-endian (ネットワーク標準), < = little-endian (x86)")

    # ── 4.6 array.array vs list ──
    subsection("4.6 array.array vs list - メモリ比較")

    n = 10_000
    int_list = list(range(n))
    int_array = array("i", range(n))  # 'i' = signed int (4 bytes)

    list_size = sys.getsizeof(int_list) + sum(sys.getsizeof(x) for x in int_list[:100]) * (n // 100)
    array_size = sys.getsizeof(int_array)

    demo(f"list[int] 推定サイズ:  {list_size:>10,} bytes")
    demo(f"array('i') サイズ:     {array_size:>10,} bytes")

    point("array.array は値を直接格納（ポインタのオーバーヘッドなし）")
    point("numpy が使えない環境での数値配列に有用")

    # ── 4.7 timeit でプロファイリング ──
    subsection("4.7 timeit / cProfile でのプロファイリング")

    # timeit: マイクロベンチマーク
    list_time = timeit.timeit(
        "sum(range(1000))", number=1000
    )
    gen_time = timeit.timeit(
        "sum(x for x in range(1000))", number=1000
    )
    demo(f"sum(range(1000)):         {list_time:.4f}s / 1000回")
    demo(f"sum(x for x in range()): {gen_time:.4f}s / 1000回")
    point("range は C 実装なので generator より速いことがある")

    # cProfile のデモ（出力をキャプチャ）
    import cProfile
    import pstats

    def profile_target():
        total = 0
        for i in range(10_000):
            total += i * i
        return total

    profiler = cProfile.Profile()
    profiler.enable()
    profile_target()
    profiler.disable()

    stream = io.StringIO()
    ps = pstats.Stats(profiler, stream=stream).sort_stats("cumulative")
    ps.print_stats(3)
    demo("cProfile 結果 (上位3件):")
    for line in stream.getvalue().strip().split("\n")[:8]:
        print(f"      {line}")

    question("なぜPythonはC/Go/Rustの100倍遅いのか？")
    print(textwrap.dedent("""\
        1. インタプリタ: バイトコード → CPython VM で逐次実行
        2. 動的型付け: 演算のたびに型チェック・ディスパッチ
        3. GIL: マルチコア活用不可（CPUバウンド）
        4. オブジェクトコスト: int 1つで 28 bytes (C は 4 bytes)

        対策: NumPy/C拡張 / PyPy / Cython / 適切なアルゴリズム選択
    """))

    task("同じアルゴリズムを Python と Go で実装して速度差を実測してみよう")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. コンテキストマネージャとリソース管理
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def chapter_5_context_managers():
    """
    with文の裏側: __enter__ と __exit__
    リソースリーク防止の最も Pythonic な方法
    """
    section("5. コンテキストマネージャとリソース管理")

    # ── 5.1 手動実装 ──
    subsection("5.1 __enter__ / __exit__ 手動実装")

    class Timer:
        """計測タイマー（コンテキストマネージャ）"""
        def __init__(self, label: str):
            self.label = label
            self.elapsed: float = 0

        def __enter__(self):
            self.start = time.perf_counter()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.elapsed = time.perf_counter() - self.start
            demo(f"[Timer] {self.label}: {self.elapsed:.4f}s")
            # False を返すと例外は伝播する（True なら抑制）
            return False

    with Timer("sum calculation") as t:
        total = sum(range(1_000_000))
    demo(f"結果: {total}, 経過: {t.elapsed:.4f}s")

    # __exit__ での例外処理
    class SuppressErrors:
        """特定の例外を抑制するコンテキストマネージャ"""
        def __init__(self, *exceptions):
            self.exceptions = exceptions
            self.exception = None

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type and issubclass(exc_type, self.exceptions):
                self.exception = exc_val
                demo(f"[Suppress] 例外を抑制: {exc_val}")
                return True  # 例外を抑制
            return False

    with SuppressErrors(ValueError, KeyError):
        raise ValueError("テストエラー")
    demo("ValueError は抑制され、ここに到達")

    # ── 5.2 contextlib.contextmanager ──
    subsection("5.2 contextlib.contextmanager - ジェネレータで簡潔に")

    @contextmanager
    def temporary_directory(prefix: str = "tmp"):
        """一時ディレクトリを模倣（実際のファイル操作なし）"""
        path = f"/tmp/{prefix}_{id(prefix)}"
        demo(f"ディレクトリ作成: {path}")
        try:
            yield path
        finally:
            demo(f"ディレクトリ削除: {path}")

    with temporary_directory("test") as tmpdir:
        demo(f"作業中: {tmpdir}")

    point("yield の前が __enter__、yield の後が __exit__")
    point("try/finally で確実にクリーンアップ")

    # ── 5.3 ExitStack ──
    subsection("5.3 contextlib.ExitStack - 複数リソースの動的管理")

    @contextmanager
    def mock_resource(name: str):
        demo(f"  [{name}] 獲得")
        try:
            yield name
        finally:
            demo(f"  [{name}] 解放")

    with ExitStack() as stack:
        resources = []
        for name in ["DB", "Cache", "Queue"]:
            r = stack.enter_context(mock_resource(name))
            resources.append(r)
        demo(f"全リソース獲得: {resources}")
    demo("ExitStack: 全リソースが逆順で解放された")

    point("動的に数が変わるリソースに最適（例: N個のDB接続）")

    # ── 5.4 async context manager ──
    subsection("5.4 Async Context Manager")

    @asynccontextmanager
    async def async_db_connection(dsn: str):
        demo(f"非同期DB接続開始: {dsn}")
        await asyncio.sleep(0.01)
        try:
            yield {"connection": dsn, "status": "connected"}
        finally:
            await asyncio.sleep(0.01)
            demo(f"非同期DB接続終了: {dsn}")

    async def async_cm_demo():
        async with async_db_connection("postgres://localhost/db") as conn:
            demo(f"クエリ実行中: {conn}")

    asyncio.run(async_cm_demo())

    # ── 5.5 ContextVar ──
    subsection("5.5 ContextVar - asyncio 用のスレッドローカル代替")

    request_id: contextvars.ContextVar[str] = contextvars.ContextVar("request_id")

    async def process_request(rid: str):
        request_id.set(rid)
        await asyncio.sleep(0.01)
        demo(f"  処理中 request_id={request_id.get()}")

    async def contextvar_demo():
        """各タスクが独立した ContextVar を持つ"""
        await asyncio.gather(
            process_request("req-001"),
            process_request("req-002"),
            process_request("req-003"),
        )

    asyncio.run(contextvar_demo())

    point("threading.local の asyncio 版。タスクごとに独立した値を保持")
    point("FastAPI の request context などで活用される")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. イテレータ・ジェネレータの深掘り
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def chapter_6_iterators():
    """
    Python のイテレータプロトコル:
      __iter__(): イテレータオブジェクトを返す
      __next__(): 次の要素を返す。なければ StopIteration を送出
    """
    section("6. イテレータ・ジェネレータの深掘り")

    # ── 6.1 __iter__ / __next__ 手動実装 ──
    subsection("6.1 イテレータプロトコル手動実装")

    class FibonacciIterator:
        """フィボナッチ数列イテレータ（上限あり）"""
        def __init__(self, max_value: int):
            self.max_value = max_value
            self.a, self.b = 0, 1

        def __iter__(self):
            return self

        def __next__(self) -> int:
            if self.a > self.max_value:
                raise StopIteration
            current = self.a
            self.a, self.b = self.b, self.a + self.b
            return current

    fibs = list(FibonacciIterator(100))
    demo(f"Fibonacci (<=100): {fibs}")

    # ── 6.2 yield from ──
    subsection("6.2 yield from - サブジェネレータ委任")

    def flatten(nested):
        """ネストされたリストを再帰的にフラット化"""
        for item in nested:
            if isinstance(item, (list, tuple)):
                yield from flatten(item)
            else:
                yield item

    nested = [1, [2, 3], [4, [5, 6]], 7]
    demo(f"flatten({nested}) = {list(flatten(nested))}")

    # yield from でサブジェネレータの戻り値を受け取る
    def accumulator():
        total = 0
        while True:
            value = yield total
            if value is None:
                return total
            total += value

    def delegator():
        result = yield from accumulator()
        demo(f"accumulator 最終値: {result}")

    gen = delegator()
    next(gen)  # 初期化
    gen.send(10)
    gen.send(20)
    gen.send(30)
    try:
        gen.send(None)  # 終了
    except StopIteration:
        pass

    # ── 6.3 send() / throw() / close() ──
    subsection("6.3 Generator の send() / throw() / close()")

    def running_average():
        """
        send() で値を受け取り、移動平均を返すコルーチン
        これが asyncio 以前の「協調的マルチタスク」
        """
        total = 0.0
        count = 0
        average = None
        while True:
            value = yield average
            if value is None:
                break
            total += value
            count += 1
            average = total / count

    avg = running_average()
    next(avg)  # 初期化（最初の yield まで進める）
    demo(f"send(10) -> avg = {avg.send(10)}")
    demo(f"send(20) -> avg = {avg.send(20)}")
    demo(f"send(30) -> avg = {avg.send(30)}")
    avg.close()  # ジェネレータを明示的に終了

    point("send() は yield 式に値を送り込む")
    point("throw() はジェネレータ内で例外を発生させる")
    point("close() は GeneratorExit を送出して終了")

    # ── 6.4 itertools の実用パターン ──
    subsection("6.4 itertools 実用パターン")

    # chain: 複数のイテラブルを連結
    demo(f"chain: {list(itertools.chain([1,2], [3,4], [5]))}")

    # product: デカルト積
    demo(f"product: {list(itertools.product('AB', '12'))}")

    # combinations / permutations
    demo(f"combinations('ABCD', 2): {list(itertools.combinations('ABCD', 2))}")
    demo(f"permutations('ABC', 2): {list(itertools.permutations('ABC', 2))}")

    # groupby: 連続する同じ値をグループ化（ソート済みデータに使う）
    data = sorted([("A", 1), ("B", 2), ("A", 3), ("B", 4)], key=lambda x: x[0])
    groups = {
        k: [v for _, v in g]
        for k, g in itertools.groupby(data, key=lambda x: x[0])
    }
    demo(f"groupby: {groups}")

    # islice: イテレータのスライス
    demo(f"islice(count(), 5, 10): {list(itertools.islice(itertools.count(), 5, 10))}")

    # accumulate: 累積演算
    demo(f"accumulate([1,2,3,4,5]): {list(itertools.accumulate([1,2,3,4,5]))}")

    # starmap: 引数展開して map
    demo(f"starmap(pow, [(2,3),(3,2)]): {list(itertools.starmap(pow, [(2,3),(3,2)]))}")

    # ── 6.5 無限イテレータ ──
    subsection("6.5 無限イテレータ: count, cycle, repeat")

    # count: 無限カウンター
    counter = itertools.count(start=10, step=3)
    demo(f"count(10, 3) 最初の5個: {[next(counter) for _ in range(5)]}")

    # cycle: 無限ループ
    cycler = itertools.cycle(["R", "G", "B"])
    demo(f"cycle(['R','G','B']) x 7: {[next(cycler) for _ in range(7)]}")

    # repeat
    demo(f"repeat('x', 4): {list(itertools.repeat('x', 4))}")

    # ── 6.6 ジェネレータパイプライン ──
    subsection("6.6 ジェネレータベースのパイプライン処理")

    def read_data():
        """データソース（模擬）"""
        raw = [
            "Alice,30,Engineering",
            "Bob,25,Marketing",
            "Charlie,35,Engineering",
            "Diana,28,Marketing",
            "Eve,32,Engineering",
        ]
        for line in raw:
            yield line

    def parse_csv(lines):
        """CSVパース"""
        for line in lines:
            name, age, dept = line.split(",")
            yield {"name": name, "age": int(age), "dept": dept}

    def filter_dept(records, dept: str):
        """部門フィルタ"""
        for record in records:
            if record["dept"] == dept:
                yield record

    def extract_names(records):
        """名前抽出"""
        for record in records:
            yield record["name"]

    # パイプライン: read -> parse -> filter -> extract
    pipeline = extract_names(
        filter_dept(
            parse_csv(read_data()),
            "Engineering"
        )
    )
    engineers = list(pipeline)
    demo(f"Engineering メンバー: {engineers}")

    point("各ステージは遅延評価。メモリ使用量は O(1)")
    point("Unix パイプ (cat | grep | sort) と同じ考え方")

    task("ログファイルを読み込み、エラーだけ抽出するパイプラインを作ってみよう")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. テスト技法
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def chapter_7_testing():
    """
    テストダブルの分類:
      Stub: 決まった値を返す
      Fake: 簡易的な実装（インメモリDB等）
      Spy:  呼び出しを記録する
      Mock: 期待通りに呼ばれたか検証する
    """
    section("7. テスト技法")

    # ── 7.1 unittest.mock 基礎 ──
    subsection("7.1 unittest.mock - Mock と MagicMock")

    from unittest.mock import MagicMock, Mock, patch, call

    # Mock の基本
    mock_api = Mock()
    mock_api.get_user.return_value = {"id": 1, "name": "Alice"}
    result = mock_api.get_user(user_id=1)
    demo(f"Mock 結果: {result}")
    demo(f"呼び出し確認: {mock_api.get_user.called}")
    demo(f"呼び出し引数: {mock_api.get_user.call_args}")

    # MagicMock: マジックメソッドも自動的にモック
    magic = MagicMock()
    magic.__len__.return_value = 42
    demo(f"MagicMock len: {len(magic)}")
    magic.__getitem__.return_value = "item"
    demo(f"MagicMock [0]: {magic[0]}")

    # ── 7.2 side_effect ──
    subsection("7.2 side_effect - エラーシミュレーション")

    # side_effect で例外を発生させる
    mock_db = Mock()
    mock_db.connect.side_effect = ConnectionError("DB接続失敗")

    try:
        mock_db.connect()
    except ConnectionError as e:
        demo(f"side_effect 例外: {e}")

    # side_effect でリストを指定すると順番に返す
    mock_api2 = Mock()
    mock_api2.fetch.side_effect = [
        {"status": 500},  # 1回目: エラー
        {"status": 200, "data": "ok"},  # 2回目: 成功
    ]
    demo(f"1回目: {mock_api2.fetch()}")
    demo(f"2回目: {mock_api2.fetch()}")

    # side_effect で関数を指定
    mock_calc = Mock()
    mock_calc.add.side_effect = lambda a, b: a + b
    demo(f"side_effect 関数: {mock_calc.add(3, 4)}")

    # ── 7.3 patch ──
    subsection("7.3 patch - モジュールレベルのモック")

    # patch でモジュール内の関数/クラスを差し替え
    import os.path

    with patch("os.path.exists") as mock_exists:
        mock_exists.return_value = True
        demo(f"patch後の os.path.exists('/fake'): {os.path.exists('/fake')}")

    demo(f"patch解除後の os.path.exists('/fake'): {os.path.exists('/fake')}")

    point("patch はコンテキストマネージャとしてもデコレータとしても使える")

    # ── 7.4 テストダブルの実装例 ──
    subsection("7.4 テストダブル: Stub, Fake, Spy, Mock の違い")

    # --- Stub: 固定値を返す ---
    class UserRepositoryStub:
        def find_by_id(self, user_id: int) -> dict:
            return {"id": user_id, "name": "Test User", "active": True}

    stub = UserRepositoryStub()
    demo(f"Stub: {stub.find_by_id(1)}")

    # --- Fake: 簡易的だが動く実装 ---
    class InMemoryUserRepository:
        def __init__(self):
            self._users: dict[int, dict] = {}

        def save(self, user: dict) -> None:
            self._users[user["id"]] = user

        def find_by_id(self, user_id: int) -> dict | None:
            return self._users.get(user_id)

    fake_repo = InMemoryUserRepository()
    fake_repo.save({"id": 1, "name": "Alice"})
    demo(f"Fake: {fake_repo.find_by_id(1)}")

    # --- Spy: 呼び出しを記録 ---
    class SpyLogger:
        def __init__(self):
            self.logs: list[str] = []

        def log(self, message: str) -> None:
            self.logs.append(message)

    spy = SpyLogger()
    spy.log("action_1")
    spy.log("action_2")
    demo(f"Spy 記録: {spy.logs}")

    # --- Mock: 期待値を検証 ---
    mock_notifier = Mock()
    mock_notifier.send("user@example.com", "Welcome!")
    mock_notifier.send.assert_called_once_with("user@example.com", "Welcome!")
    demo("Mock: assert_called_once_with 通過")

    print(textwrap.dedent("""
        使い分け:
          Stub: 依存オブジェクトの戻り値を固定したいとき
          Fake: 本物に近い動作が必要だがDBは使いたくないとき
          Spy:  何が呼ばれたか記録したいとき
          Mock: 特定のメソッドが特定の引数で呼ばれたか検証したいとき
    """))

    # ── 7.5 Property-Based テスト ──
    subsection("7.5 Property-Based テストの考え方")

    print(textwrap.dedent("""\
        従来のテスト:
          assert sort([3, 1, 2]) == [1, 2, 3]  # 具体例

        Property-Based テスト:
          任意のリスト xs に対して:
            - sort(xs) の長さは len(xs) と同じ
            - sort(xs) の各要素は元のリストに含まれる
            - sort(xs)[i] <= sort(xs)[i+1] が全てのiで成立

        ツール: hypothesis (Python), QuickCheck (Haskell)
    """))

    # 手動での Property-Based テストデモ
    import random

    def test_sort_properties():
        """ソートの性質を100個のランダム入力でテスト"""
        for _ in range(100):
            xs = [random.randint(-100, 100) for _ in range(random.randint(0, 50))]
            sorted_xs = sorted(xs)

            # Property 1: 長さが同じ
            assert len(sorted_xs) == len(xs), "length mismatch"

            # Property 2: ソート済み
            for i in range(len(sorted_xs) - 1):
                assert sorted_xs[i] <= sorted_xs[i + 1], "not sorted"

            # Property 3: 要素が同じ（マルチセットとして）
            assert sorted(xs) == sorted(sorted_xs), "elements differ"

        demo("Property-Based テスト: 100ケース全て通過")

    test_sort_properties()

    # ── 7.6 Fixture パターン ──
    subsection("7.6 Fixture パターン")

    class TestFixture:
        """テスト用の共通セットアップ/ティアダウン"""
        def setup(self):
            self.db = InMemoryUserRepository()
            self.db.save({"id": 1, "name": "Alice", "role": "admin"})
            self.db.save({"id": 2, "name": "Bob", "role": "user"})
            demo("Fixture: セットアップ完了")
            return self

        def teardown(self):
            demo("Fixture: ティアダウン完了")

    fixture = TestFixture().setup()
    demo(f"Fixture データ: {fixture.db.find_by_id(1)}")
    fixture.teardown()

    point("pytest では @pytest.fixture デコレータで宣言的に書ける")
    point("scope='session' で全テストで共有するFixtureも定義可能")

    task("@retry デコレータのテストを Mock と side_effect で書いてみよう")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 8. Pythonic イディオム
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def chapter_8_pythonic():
    """
    「Pythonらしいコード」とは何か。
    読みやすく、効率的で、Python の設計思想に沿ったコード。
    """
    section("8. Pythonic イディオム")

    # ── 8.1 EAFP vs LBYL ──
    subsection("8.1 EAFP vs LBYL")

    data: dict[str, Any] = {"user": {"name": "Alice", "age": 30}}

    # LBYL (Look Before You Leap) - Java/C++ 的
    if "user" in data and "name" in data["user"]:
        name_lbyl = data["user"]["name"]
        demo(f"LBYL: {name_lbyl}")

    # EAFP (Easier to Ask Forgiveness than Permission) - Pythonic
    try:
        name_eafp = data["user"]["name"]
        demo(f"EAFP: {name_eafp}")
    except (KeyError, TypeError):
        name_eafp = "unknown"

    print(textwrap.dedent("""
        EAFP が Pythonic な理由:
          1. 例外処理が高速に最適化されている（正常パスは速い）
          2. TOCTOU 問題を回避（チェックと使用の間に状態が変わりうる）
          3. ダックタイピングと相性が良い
          4. コードが DRY になる（チェックと使用が分離しない）
    """))

    # ── 8.2 Walrus Operator (:=) ──
    subsection("8.2 Walrus Operator (:=) - Python 3.8+")

    # 従来のパターン
    numbers = [1, 5, 3, 8, 2, 9, 4]
    filtered_old = []
    for n in numbers:
        square = n * n
        if square > 20:
            filtered_old.append(square)

    # Walrus operator
    filtered_new = [
        sq for n in numbers
        if (sq := n * n) > 20
    ]
    demo(f"Walrus operator: {filtered_new}")

    # while ループでの活用
    import re
    text = "Error: 404, Warning: disk, Error: 500, Info: ok"
    errors = []
    pos = 0
    pattern = re.compile(r"Error: (\w+)")
    while (match := pattern.search(text, pos)):
        errors.append(match.group(1))
        pos = match.end()
    demo(f"Walrus + while: errors = {errors}")

    point(":= は『計算結果を変数に束縛しつつ、式として使う』")
    point("乱用すると読みにくい。条件式とwhile で使うのが主な用途")

    # ── 8.3 match-case (Python 3.10+) ──
    subsection("8.3 match-case - 構造的パターンマッチ (Python 3.10+)")

    def process_command(command: dict) -> str:
        """構造的パターンマッチでコマンドを処理"""
        match command:
            case {"action": "move", "direction": d, "steps": s}:
                return f"Moving {d} by {s} steps"
            case {"action": "attack", "target": t}:
                return f"Attacking {t}"
            case {"action": "heal", "amount": a} if a > 0:
                return f"Healing for {a} HP"
            case {"action": action}:
                return f"Unknown action: {action}"
            case _:
                return "Invalid command"

    commands = [
        {"action": "move", "direction": "north", "steps": 3},
        {"action": "attack", "target": "dragon"},
        {"action": "heal", "amount": 50},
        {"action": "dance"},
        "invalid",
    ]

    for cmd in commands:
        demo(f"  {cmd} -> {process_command(cmd)}")

    # クラスパターン
    @dataclass
    class HttpResponse:
        status: int
        body: str

    def handle_response(resp: HttpResponse) -> str:
        match resp:
            case HttpResponse(status=200, body=b):
                return f"OK: {b[:20]}"
            case HttpResponse(status=404):
                return "Not Found"
            case HttpResponse(status=s) if 500 <= s < 600:
                return f"Server Error: {s}"
            case _:
                return f"Status: {resp.status}"

    responses = [
        HttpResponse(200, "Hello World"),
        HttpResponse(404, ""),
        HttpResponse(503, "Service Unavailable"),
    ]
    for resp in responses:
        demo(f"  {resp} -> {handle_response(resp)}")

    point("match-case は単純な if-elif ではない。構造の分解ができる")
    point("ガード条件 (if ...) で追加のフィルタリングが可能")

    # ── 8.4 引数の種類 ──
    subsection("8.4 引数: *args, **kwargs, /, *")

    def api_function(
        path: str,       # positional or keyword
        /,               # これより前は positional-only
        method: str = "GET",  # keyword or positional
        *,               # これより後は keyword-only
        timeout: int = 30,
        headers: dict | None = None,
    ) -> str:
        return f"{method} {path} (timeout={timeout})"

    # 正しい呼び出し
    demo(f'api_function("/users"): {api_function("/users")}')
    demo(f'api_function("/users", "POST", timeout=10): '
         f'{api_function("/users", "POST", timeout=10)}')

    # エラーになる呼び出し
    try:
        api_function(path="/users")  # type: ignore
    except TypeError as e:
        demo(f"positional-only エラー: {e}")

    print(textwrap.dedent("""
        引数の種類:
          def f(a, b, /, c, d, *, e, f):
                ^^^^      ^^^^      ^^^^
            positional-   通常   keyword-
              only                 only

        なぜ重要か:
          - API設計で意図を明確にする
          - 引数名の変更がbreaking changeにならない (positional-only)
          - キーワード強制で可読性を上げる (keyword-only)
    """))

    # ── 8.5 ダンダーメソッド ──
    subsection("8.5 __all__, __slots__, __repr__, __hash__, __eq__")

    class Money:
        """金額クラス（イミュータブル値オブジェクト）"""
        __slots__ = ("_amount", "_currency")

        def __init__(self, amount: float, currency: str = "JPY"):
            object.__setattr__(self, "_amount", amount)
            object.__setattr__(self, "_currency", currency)

        def __repr__(self) -> str:
            return f"Money({self._amount}, '{self._currency}')"

        def __eq__(self, other: object) -> bool:
            if not isinstance(other, Money):
                return NotImplemented
            return self._amount == other._amount and self._currency == other._currency

        def __hash__(self) -> int:
            return hash((self._amount, self._currency))

        def __add__(self, other: Money) -> Money:
            if self._currency != other._currency:
                raise ValueError(f"通貨不一致: {self._currency} vs {other._currency}")
            return Money(self._amount + other._amount, self._currency)

        def __setattr__(self, name: str, value: Any) -> None:
            raise AttributeError("Money is immutable")

    m1 = Money(1000, "JPY")
    m2 = Money(2000, "JPY")
    demo(f"Money: {m1}")
    demo(f"Money + Money: {m1 + m2}")
    demo(f"hash: {hash(m1)}")
    demo(f"等値: {m1 == Money(1000, 'JPY')}")

    # dict のキーに使える（hashable だから）
    prices = {Money(100, "USD"): "cheap", Money(1000, "USD"): "expensive"}
    demo(f"dict キー: {prices[Money(100, 'USD')]}")

    try:
        m1._amount = 9999  # type: ignore
    except AttributeError as e:
        demo(f"イミュータブル: {e}")

    # ── 8.6 namedtuple vs dataclass vs TypedDict ──
    subsection("8.6 namedtuple vs dataclass vs TypedDict")

    # namedtuple: イミュータブル、軽量、タプルの機能を持つ
    Color = namedtuple("Color", ["r", "g", "b"])
    red = Color(255, 0, 0)
    demo(f"namedtuple: {red}, r={red.r}")

    # NamedTuple (typing版): 型ヒント付き
    class Coordinate(NamedTuple):
        lat: float
        lon: float
        label: str = ""

    tokyo = Coordinate(35.6762, 139.6503, "Tokyo")
    demo(f"NamedTuple: {tokyo}")

    # dataclass: ミュータブル、メソッド追加可能
    @dataclass
    class Product:
        name: str
        price: float
        stock: int = 0

        @property
        def is_available(self) -> bool:
            return self.stock > 0

    product = Product("Widget", 9.99, 10)
    demo(f"dataclass: {product}, available={product.is_available}")

    # frozen dataclass: イミュータブル
    @dataclass(frozen=True)
    class FrozenProduct:
        name: str
        price: float

    fp = FrozenProduct("Gadget", 19.99)
    try:
        fp.price = 29.99  # type: ignore
    except Exception as e:
        demo(f"frozen dataclass: {type(e).__name__}: {e}")

    # TypedDict: dict の型を定義（ランタイムはただの dict）
    from typing import TypedDict

    class UserDict(TypedDict):
        name: str
        age: int
        email: str

    user_dict: UserDict = {"name": "Alice", "age": 30, "email": "alice@example.com"}
    demo(f"TypedDict: {user_dict}")
    demo(f"TypedDict type: {type(user_dict)}")  # ただの dict

    print(textwrap.dedent("""
        使い分け:
          namedtuple: 座標、色など immutable な値の組。軽量。
          dataclass:  メソッドが必要な構造体。ミュータブルなデータ。
          TypedDict:  JSON/APIレスポンスの型定義。dict として扱いたい。
          frozen DC:  dict キーに使いたい値オブジェクト。
    """))

    # ── 8.7 match-case による型パターン ──
    subsection("8.7 高度なパターンマッチ: シーケンス/マッピング/型")

    def analyze_data(data: Any) -> str:
        match data:
            case []:
                return "空リスト"
            case [x]:
                return f"要素1つ: {x}"
            case [x, y]:
                return f"ペア: ({x}, {y})"
            case [x, *rest]:
                return f"先頭 {x}, 残り {len(rest)} 個"
            case str() as s if len(s) > 10:
                return f"長い文字列: {s[:10]}..."
            case int(n) if n > 0:
                return f"正の整数: {n}"
            case _:
                return f"その他: {type(data).__name__}"

    test_data = [
        [],
        [42],
        [1, 2],
        [1, 2, 3, 4, 5],
        "Hello World from Python",
        42,
        -1,
    ]
    for d in test_data:
        demo(f"  {d!r:30s} -> {analyze_data(d)}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 9. 総合演習: 実践的な設計パターン
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def chapter_9_practical():
    """
    ここまでの知識を組み合わせた実践的な実装例
    """
    section("9. 総合演習: 実践的な設計パターン")

    # ── 9.1 Observer パターン (ジェネリクス + デコレータ) ──
    subsection("9.1 Observer パターン")

    E = TypeVar("E")

    class EventEmitter(Generic[E]):
        """型安全なイベントエミッター"""
        def __init__(self):
            self._listeners: dict[str, list[Callable]] = defaultdict(list)

        def on(self, event: str) -> Callable:
            """デコレータとして使える"""
            def decorator(func: Callable) -> Callable:
                self._listeners[event].append(func)
                return func
            return decorator

        def emit(self, event: str, data: E) -> None:
            for listener in self._listeners.get(event, []):
                listener(data)

    emitter: EventEmitter[dict] = EventEmitter()

    @emitter.on("user_created")
    def send_welcome_email(user: dict):
        demo(f"  Email送信: {user['name']} さんへようこそ!")

    @emitter.on("user_created")
    def log_creation(user: dict):
        demo(f"  ログ記録: ユーザー {user['name']} を作成")

    @emitter.on("user_deleted")
    def cleanup(user: dict):
        demo(f"  クリーンアップ: {user['name']} のデータ削除")

    demo("user_created イベント発火:")
    emitter.emit("user_created", {"name": "Alice", "email": "alice@example.com"})

    # ── 9.2 Pipeline パターン (ジェネレータ + コンテキストマネージャ) ──
    subsection("9.2 Pipeline パターン - データ処理チェーン")

    class Pipeline:
        """関数合成によるデータパイプライン"""
        def __init__(self, data):
            self._data = data
            self._steps: list[Callable] = []

        def pipe(self, func: Callable) -> Pipeline:
            self._steps.append(func)
            return self  # メソッドチェーン

        def execute(self):
            result = self._data
            for step in self._steps:
                result = step(result)
            return result

    result = (
        Pipeline(range(20))
        .pipe(lambda data: [x for x in data if x % 2 == 0])   # 偶数フィルタ
        .pipe(lambda data: [x * x for x in data])              # 二乗
        .pipe(lambda data: [x for x in data if x > 50])        # 50超フィルタ
        .pipe(sorted)                                           # ソート
        .execute()
    )
    demo(f"Pipeline 結果: {result}")

    # ── 9.3 Repository パターン (ABC + dataclass) ──
    subsection("9.3 Repository パターン - ABC + dataclass")

    T = TypeVar("T")

    @dataclass
    class Entity:
        id: int
        name: str
        created_at: float = field(default_factory=time.time)

    class Repository(ABC, Generic[T]):
        @abstractmethod
        def save(self, entity: T) -> None: ...

        @abstractmethod
        def find_by_id(self, id: int) -> T | None: ...

        @abstractmethod
        def find_all(self) -> list[T]: ...

        @abstractmethod
        def delete(self, id: int) -> bool: ...

    class InMemoryRepository(Repository[Entity]):
        def __init__(self):
            self._store: dict[int, Entity] = {}

        def save(self, entity: Entity) -> None:
            self._store[entity.id] = entity

        def find_by_id(self, id: int) -> Entity | None:
            return self._store.get(id)

        def find_all(self) -> list[Entity]:
            return list(self._store.values())

        def delete(self, id: int) -> bool:
            return self._store.pop(id, None) is not None

    repo = InMemoryRepository()
    repo.save(Entity(1, "Alice"))
    repo.save(Entity(2, "Bob"))
    repo.save(Entity(3, "Charlie"))

    demo(f"find_by_id(1): {repo.find_by_id(1)}")
    demo(f"find_all: {[e.name for e in repo.find_all()]}")
    demo(f"delete(2): {repo.delete(2)}")
    demo(f"残り: {[e.name for e in repo.find_all()]}")

    # ── 9.4 Circuit Breaker (非同期 + デコレータ + 状態管理) ──
    subsection("9.4 Circuit Breaker パターン")

    class CircuitBreaker:
        """
        サーキットブレーカー:
          CLOSED  -> 正常。失敗がしきい値を超えたら OPEN へ
          OPEN    -> 即座にエラー。一定時間後 HALF_OPEN へ
          HALF_OPEN -> 次の呼び出しが成功なら CLOSED, 失敗なら OPEN
        """
        class State(Enum):
            CLOSED = auto()
            OPEN = auto()
            HALF_OPEN = auto()

        def __init__(self, failure_threshold: int = 3, recovery_time: float = 1.0):
            self.failure_threshold = failure_threshold
            self.recovery_time = recovery_time
            self.state = self.State.CLOSED
            self.failure_count = 0
            self.last_failure_time = 0.0

        def __call__(self, func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if self.state == self.State.OPEN:
                    if time.time() - self.last_failure_time > self.recovery_time:
                        self.state = self.State.HALF_OPEN
                        demo(f"  [CB] {self.state.name}")
                    else:
                        raise RuntimeError(f"Circuit is OPEN for {func.__name__}")

                try:
                    result = func(*args, **kwargs)
                    if self.state == self.State.HALF_OPEN:
                        self.state = self.State.CLOSED
                        self.failure_count = 0
                        demo(f"  [CB] -> {self.state.name}")
                    return result
                except Exception as e:
                    self.failure_count += 1
                    self.last_failure_time = time.time()
                    if self.failure_count >= self.failure_threshold:
                        self.state = self.State.OPEN
                        demo(f"  [CB] -> {self.state.name} (failures={self.failure_count})")
                    raise
            return wrapper

    cb = CircuitBreaker(failure_threshold=3, recovery_time=0.1)
    call_counter = 0

    @cb
    def unreliable_service():
        nonlocal call_counter
        call_counter += 1
        if call_counter <= 4:
            raise ConnectionError("service down")
        return "success"

    for i in range(6):
        try:
            result = unreliable_service()
            demo(f"  呼び出し {i+1}: {result}")
        except (ConnectionError, RuntimeError) as e:
            demo(f"  呼び出し {i+1}: {e}")
        time.sleep(0.05)

    # ── 9.5 型安全な設定管理 (descriptor + dataclass) ──
    subsection("9.5 型安全な設定管理")

    class EnvVar:
        """環境変数から設定を読み込む descriptor"""
        def __init__(self, env_key: str, default: Any = None, cast: type = str):
            self.env_key = env_key
            self.default = default
            self.cast = cast
            self.attr_name = ""

        def __set_name__(self, owner, name):
            self.attr_name = f"_{name}"

        def __get__(self, obj, objtype=None):
            if obj is None:
                return self
            cached = getattr(obj, self.attr_name, None)
            if cached is not None:
                return cached
            raw = os.environ.get(self.env_key, self.default)
            if raw is not None:
                value = self.cast(raw)
                setattr(obj, self.attr_name, value)
                return value
            return None

    class AppConfig:
        debug = EnvVar("APP_DEBUG", "false", lambda x: x.lower() == "true")
        port = EnvVar("APP_PORT", "8080", int)
        db_url = EnvVar("DATABASE_URL", "sqlite:///local.db")

    config = AppConfig()
    demo(f"debug: {config.debug}")
    demo(f"port: {config.port}")
    demo(f"db_url: {config.db_url}")

    point("descriptor + 環境変数で 12-Factor App の設定管理を実現")

    # ── 9.6 非同期ワーカープール ──
    subsection("9.6 非同期ワーカープール (asyncio + Semaphore)")

    async def worker_pool_demo():
        results: list[tuple[int, str]] = []

        async def worker(task_id: int, sem: asyncio.Semaphore) -> tuple[int, str]:
            async with sem:
                await asyncio.sleep(0.02)
                result = (task_id, f"result_{task_id}")
                results.append(result)
                return result

        sem = asyncio.Semaphore(3)  # 最大3ワーカー
        tasks = [worker(i, sem) for i in range(10)]
        await asyncio.gather(*tasks)

        demo(f"全タスク完了: {len(results)} 件")
        demo(f"結果サンプル: {results[:3]}...")

    asyncio.run(worker_pool_demo())

    task("この非同期ワーカープールに進捗報告機能を追加してみよう")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 10. 面接でよく聞かれるポイントまとめ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def chapter_10_interview():
    section("10. 面接でよく聞かれるポイントまとめ")

    topics = [
        ("GIL とは？", (
            "Global Interpreter Lock。CPython で一度に1スレッドしか "
            "Pythonバイトコードを実行できない。\n"
            "    対策: multiprocessing(CPUバウンド), asyncio(I/Oバウンド), "
            "C拡張で GIL を解放"
        )),
        ("デコレータの仕組み", (
            "@decorator は糖衣構文。func = decorator(func) と同じ。\n"
            "    引数ありの場合: @decorator(arg) は func = decorator(arg)(func)"
        )),
        ("__new__ vs __init__", (
            "__new__: インスタンスを生成（cls を受け取る）\n"
            "    __init__: インスタンスを初期化（self を受け取る）\n"
            "    __new__ で生成を制御: シングルトン、イミュータブル型の拡張"
        )),
        ("MRO (Method Resolution Order)", (
            "多重継承時のメソッド探索順序。C3 線形化アルゴリズム。\n"
            "    MyClass.mro() で確認可能。super() は MRO に従う。"
        )),
        ("is vs ==", (
            "is: 同一オブジェクト (id が同じ)\n"
            "    ==: 等値 (__eq__ で定義される)\n"
            "    None のチェックは必ず is を使う: if x is None"
        )),
        ("深いコピー vs 浅いコピー", (
            "浅いコピー: copy.copy() -- ネストしたオブジェクトは共有\n"
            "    深いコピー: copy.deepcopy() -- 全てを再帰的にコピー\n"
            "    list[:], dict.copy() は浅いコピー"
        )),
        ("ジェネレータの利点", (
            "遅延評価でメモリ O(1)。パイプライン処理に最適。\n"
            "    大規模ファイル処理: for line in open('huge.txt') は generator"
        )),
        ("async/await の動作原理", (
            "イベントループがタスクを管理。await で制御を返す。\n"
            "    シングルスレッド + 協調的マルチタスク。\n"
            "    I/O 待ちの間に他のタスクを進める。"
        )),
    ]

    for topic, explanation in topics:
        print(f"  Q: {topic}")
        print(f"    A: {explanation}")
        print()

    print(textwrap.dedent("""\
    FAANG面接のコツ:
      1. 「なぜ」を説明できること（How だけでなく Why）
      2. トレードオフを語れること（メリットだけでなくデメリット）
      3. 実務での経験を交えること（「前のプロジェクトで...」）
      4. 代替案を提示できること（「Xもあるが、Yの方が適切。なぜなら...」）
    """))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# メイン実行
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    print("=" * 64)
    print("  Python Advanced Features - FAANG 対策完全ガイド")
    print("  標準ライブラリのみ。外部依存なし。")
    print("=" * 64)

    chapter_1_async()
    chapter_2_metaprogramming()
    chapter_3_type_system()
    chapter_4_performance()
    chapter_5_context_managers()
    chapter_6_iterators()
    chapter_7_testing()
    chapter_8_pythonic()
    chapter_9_practical()
    chapter_10_interview()

    print()
    print("=" * 64)
    print("  全チャプター完了!")
    print()
    print("  次のステップ:")
    print("    1. [実装してみよう] のタスクに取り組む")
    print("    2. 各 [考えてほしい疑問] に自分の言葉で答える")
    print("    3. mypy python_advanced.py で型チェックを体験")
    print("    4. polyglot_guide.py で他言語との比較を学ぶ")
    print("=" * 64)


if __name__ == "__main__":
    main()
