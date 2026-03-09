#!/usr/bin/env python3
"""
design_patterns.py - デザインパターン完全ガイド：FAANG Tech Lead を目指すエンジニアのために

「パターンを知っている」と「パターンを使いこなせる」は天と地ほど違う。
GoF の23パターンを暗記するのではなく、
"なぜこの構造が必要になるのか" を体で理解するためのファイル。

実行方法:
    python design_patterns.py

標準ライブラリのみ使用。
"""

from __future__ import annotations

import abc
import copy
import enum
import functools
import queue
import threading
import time
import concurrent.futures
from typing import (
    Any, Callable, Dict, Generic, Iterator, List, Optional, Protocol,
    Sequence, Set, Tuple, TypeVar,
)
from dataclasses import dataclass, field
from collections import defaultdict


# ============================================================
# ユーティリティ
# ============================================================

def section(title: str) -> None:
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)
    print()


def subsection(title: str) -> None:
    print()
    print(f"  ── {title} ──")
    print()


def question(text: str) -> None:
    print(f"  [考えてほしい疑問] {text}")
    print()


def task(text: str) -> None:
    print(f"  [実装してみよう] {text}")
    print()


def point(text: str) -> None:
    print(f"    > {text}")


def demo(label: str, value: Any) -> None:
    print(f"    {label}: {value}")


# ============================================================
# 1. 生成パターン (Creational Patterns)
# ============================================================

# --------------------------------------------------
# 1-1. Singleton (スレッドセーフ版 + メタクラス版)
# --------------------------------------------------

class SingletonMeta(type):
    """メタクラス版 Singleton。
    __call__ をオーバーライドして、インスタンス生成を制御する。
    Python ではモジュールレベル変数が事実上シングルトンになるが、
    明示的にクラスで制御したい場合に使う。
    """
    _instances: Dict[type, Any] = {}
    _lock = threading.Lock()

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls not in cls._instances:
            with cls._lock:
                # ダブルチェックロッキング
                if cls not in cls._instances:
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]


class AppConfig(metaclass=SingletonMeta):
    """アプリケーション設定 ── Singleton の典型例。"""
    def __init__(self) -> None:
        self.debug = False
        self.db_url = "sqlite:///app.db"
        self.max_connections = 10


class ThreadSafeSingleton:
    """デコレータ方式のスレッドセーフ Singleton。
    メタクラスより直感的でテストもしやすい。
    """
    _instance: Optional[ThreadSafeSingleton] = None
    _lock = threading.Lock()

    def __new__(cls) -> ThreadSafeSingleton:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self.registry: Dict[str, Any] = {}


def demo_singleton() -> None:
    subsection("1-1. Singleton パターン")
    print("    メタクラス版:")
    cfg1 = AppConfig()
    cfg2 = AppConfig()
    demo("cfg1 is cfg2", cfg1 is cfg2)
    demo("id(cfg1)", id(cfg1))
    demo("id(cfg2)", id(cfg2))

    print()
    print("    スレッドセーフ版 (__new__):")
    s1 = ThreadSafeSingleton()
    s1.registry["key"] = "value"
    s2 = ThreadSafeSingleton()
    demo("s1 is s2", s1 is s2)
    demo("s2.registry", s2.registry)

    question("Singleton はグローバル変数と何が違うのか？テストしづらくなる理由は？")
    task("Singleton を使わずにモジュールレベル変数で設定管理を書き直してみよう。")


# --------------------------------------------------
# 1-2. Factory Method + Abstract Factory
# --------------------------------------------------

class Document(abc.ABC):
    """ドキュメントの抽象基底クラス。"""
    @abc.abstractmethod
    def render(self) -> str: ...


class PDFDocument(Document):
    def __init__(self, content: str) -> None:
        self.content = content

    def render(self) -> str:
        return f"[PDF] {self.content} (binary stream)"


class HTMLDocument(Document):
    def __init__(self, content: str) -> None:
        self.content = content

    def render(self) -> str:
        return f"<html><body>{self.content}</body></html>"


class MarkdownDocument(Document):
    def __init__(self, content: str) -> None:
        self.content = content

    def render(self) -> str:
        return f"# Document\n\n{self.content}"


class DocumentFactory(abc.ABC):
    """Factory Method: サブクラスに生成を委ねる。"""
    @abc.abstractmethod
    def create_document(self, content: str) -> Document: ...

    def generate(self, content: str) -> str:
        doc = self.create_document(content)
        return doc.render()


class PDFFactory(DocumentFactory):
    def create_document(self, content: str) -> Document:
        return PDFDocument(content)


class HTMLFactory(DocumentFactory):
    def create_document(self, content: str) -> Document:
        return HTMLDocument(content)


class MarkdownFactory(DocumentFactory):
    def create_document(self, content: str) -> Document:
        return MarkdownDocument(content)


# Abstract Factory: 関連オブジェクト群をまとめて生成
class Exporter(abc.ABC):
    @abc.abstractmethod
    def export_header(self, title: str) -> str: ...
    @abc.abstractmethod
    def export_body(self, text: str) -> str: ...
    @abc.abstractmethod
    def export_footer(self) -> str: ...


class HTMLExporter(Exporter):
    def export_header(self, title: str) -> str:
        return f"<h1>{title}</h1>"
    def export_body(self, text: str) -> str:
        return f"<p>{text}</p>"
    def export_footer(self) -> str:
        return "<footer>Generated by DesignPatterns</footer>"


class PlainTextExporter(Exporter):
    def export_header(self, title: str) -> str:
        return f"=== {title} ==="
    def export_body(self, text: str) -> str:
        return text
    def export_footer(self) -> str:
        return "---\nGenerated by DesignPatterns"


def get_exporter(fmt: str) -> Exporter:
    """Simple Factory 関数。"""
    factories = {"html": HTMLExporter, "text": PlainTextExporter}
    cls = factories.get(fmt)
    if cls is None:
        raise ValueError(f"Unknown format: {fmt}")
    return cls()


def demo_factory() -> None:
    subsection("1-2. Factory Method + Abstract Factory")

    print("    Factory Method:")
    for factory_cls in [PDFFactory, HTMLFactory, MarkdownFactory]:
        factory = factory_cls()
        result = factory.generate("Hello Design Patterns")
        demo(factory_cls.__name__, result)

    print()
    print("    Abstract Factory:")
    for fmt in ["html", "text"]:
        exporter = get_exporter(fmt)
        header = exporter.export_header("Report")
        body = exporter.export_body("Design patterns are powerful.")
        footer = exporter.export_footer()
        demo(f"{fmt} output", f"{header} | {body} | {footer}")

    question("Factory Method と Abstract Factory はいつ使い分けるか？")


# --------------------------------------------------
# 1-3. Builder
# --------------------------------------------------

@dataclass
class HTTPRequest:
    method: str = "GET"
    url: str = ""
    headers: Dict[str, str] = field(default_factory=dict)
    query_params: Dict[str, str] = field(default_factory=dict)
    body: Optional[str] = None
    timeout: int = 30

    def __str__(self) -> str:
        parts = [f"{self.method} {self.url}"]
        if self.query_params:
            qs = "&".join(f"{k}={v}" for k, v in self.query_params.items())
            parts[0] += f"?{qs}"
        for k, v in self.headers.items():
            parts.append(f"  {k}: {v}")
        if self.body:
            parts.append(f"  Body: {self.body[:50]}...")
        return "\n".join(parts)


class HTTPRequestBuilder:
    """Builder パターン ── メソッドチェーンで複雑なオブジェクトを構築。"""

    def __init__(self) -> None:
        self._request = HTTPRequest()

    def method(self, method: str) -> HTTPRequestBuilder:
        self._request.method = method
        return self

    def url(self, url: str) -> HTTPRequestBuilder:
        self._request.url = url
        return self

    def header(self, key: str, value: str) -> HTTPRequestBuilder:
        self._request.headers[key] = value
        return self

    def query(self, key: str, value: str) -> HTTPRequestBuilder:
        self._request.query_params[key] = value
        return self

    def body(self, body: str) -> HTTPRequestBuilder:
        self._request.body = body
        return self

    def timeout(self, seconds: int) -> HTTPRequestBuilder:
        self._request.timeout = seconds
        return self

    def build(self) -> HTTPRequest:
        if not self._request.url:
            raise ValueError("URL is required")
        return self._request


class SQLQueryBuilder:
    """SQL構築の Builder。"""

    def __init__(self) -> None:
        self._select: List[str] = []
        self._from: str = ""
        self._where: List[str] = []
        self._order_by: List[str] = []
        self._limit: Optional[int] = None
        self._joins: List[str] = []

    def select(self, *columns: str) -> SQLQueryBuilder:
        self._select.extend(columns)
        return self

    def from_table(self, table: str) -> SQLQueryBuilder:
        self._from = table
        return self

    def where(self, condition: str) -> SQLQueryBuilder:
        self._where.append(condition)
        return self

    def join(self, table: str, on: str) -> SQLQueryBuilder:
        self._joins.append(f"JOIN {table} ON {on}")
        return self

    def order_by(self, column: str, desc: bool = False) -> SQLQueryBuilder:
        direction = "DESC" if desc else "ASC"
        self._order_by.append(f"{column} {direction}")
        return self

    def limit(self, n: int) -> SQLQueryBuilder:
        self._limit = n
        return self

    def build(self) -> str:
        if not self._select or not self._from:
            raise ValueError("SELECT and FROM are required")
        parts = [f"SELECT {', '.join(self._select)}"]
        parts.append(f"FROM {self._from}")
        for j in self._joins:
            parts.append(j)
        if self._where:
            parts.append(f"WHERE {' AND '.join(self._where)}")
        if self._order_by:
            parts.append(f"ORDER BY {', '.join(self._order_by)}")
        if self._limit is not None:
            parts.append(f"LIMIT {self._limit}")
        return " ".join(parts)


def demo_builder() -> None:
    subsection("1-3. Builder パターン")

    print("    HTTP Request Builder:")
    req = (
        HTTPRequestBuilder()
        .method("POST")
        .url("https://api.example.com/users")
        .header("Content-Type", "application/json")
        .header("Authorization", "Bearer token123")
        .query("version", "2")
        .body('{"name": "Yuta", "role": "engineer"}')
        .timeout(10)
        .build()
    )
    print(f"    {req}")

    print()
    print("    SQL Query Builder:")
    sql = (
        SQLQueryBuilder()
        .select("u.name", "u.email", "o.total")
        .from_table("users u")
        .join("orders o", "u.id = o.user_id")
        .where("o.total > 1000")
        .where("u.active = 1")
        .order_by("o.total", desc=True)
        .limit(10)
        .build()
    )
    demo("SQL", sql)

    question("Builder と コンストラクタ引数の違いは？いつ Builder を選ぶべきか？")
    task("Builderに validate() メソッドを追加して、build() 前に整合性チェックを入れてみよう。")


# --------------------------------------------------
# 1-4. Prototype
# --------------------------------------------------

@dataclass
class GameCharacter:
    """Prototype パターン ── 既存オブジェクトのクローンで新しいオブジェクトを作る。"""
    name: str
    level: int
    skills: List[str]
    inventory: Dict[str, int]

    def shallow_clone(self) -> GameCharacter:
        return copy.copy(self)

    def deep_clone(self) -> GameCharacter:
        return copy.deepcopy(self)


def demo_prototype() -> None:
    subsection("1-4. Prototype パターン")

    original = GameCharacter(
        name="Hero", level=10,
        skills=["fireball", "heal"],
        inventory={"potion": 5, "sword": 1},
    )

    shallow = original.shallow_clone()
    shallow.name = "ShallowClone"
    shallow.skills.append("thunder")  # 元も変わる！

    deep = original.deep_clone()
    deep.name = "DeepClone"
    deep.skills.append("ice_storm")  # 元は変わらない

    demo("original.skills", original.skills)
    demo("shallow.skills", shallow.skills)
    demo("deep.skills   ", deep.skills)
    demo("original.skills is shallow.skills", original.skills is shallow.skills)
    demo("original.skills is deep.skills   ", original.skills is deep.skills)

    question("浅いコピーと深いコピーの違いが問題になる実務シナリオは？")


# ============================================================
# 2. 構造パターン (Structural Patterns)
# ============================================================

# --------------------------------------------------
# 2-1. Adapter
# --------------------------------------------------

class LegacyPaymentGateway:
    """レガシーAPI ── XML ベースの決済システム。"""
    def process_xml_payment(self, xml_data: str) -> str:
        return f"LegacyGateway processed: {xml_data[:30]}..."


class ModernPaymentInterface(Protocol):
    """新しい API インターフェース。"""
    def pay(self, amount: float, currency: str) -> str: ...


class PaymentAdapter:
    """Adapter ── レガシー API を新しいインターフェースに変換。"""
    def __init__(self, legacy: LegacyPaymentGateway) -> None:
        self._legacy = legacy

    def pay(self, amount: float, currency: str) -> str:
        xml = f"<payment><amount>{amount}</amount><currency>{currency}</currency></payment>"
        return self._legacy.process_xml_payment(xml)


def demo_adapter() -> None:
    subsection("2-1. Adapter パターン")

    legacy = LegacyPaymentGateway()
    adapter = PaymentAdapter(legacy)
    result = adapter.pay(99.99, "JPY")
    demo("adapter.pay(99.99, 'JPY')", result)

    question("Adapter と Facade の違いは？ Adapter は1対1変換、Facade は多対1統合。")


# --------------------------------------------------
# 2-2. Decorator (GoF版 + Python デコレータ)
# --------------------------------------------------

class DataSource(abc.ABC):
    @abc.abstractmethod
    def write(self, data: str) -> None: ...
    @abc.abstractmethod
    def read(self) -> str: ...


class FileDataSource(DataSource):
    def __init__(self) -> None:
        self._data = ""

    def write(self, data: str) -> None:
        self._data = data

    def read(self) -> str:
        return self._data


class DataSourceDecorator(DataSource):
    """GoF Decorator ── 基底デコレータ。"""
    def __init__(self, wrapped: DataSource) -> None:
        self._wrapped = wrapped

    def write(self, data: str) -> None:
        self._wrapped.write(data)

    def read(self) -> str:
        return self._wrapped.read()


class EncryptionDecorator(DataSourceDecorator):
    """暗号化デコレータ (簡易版: ROT13)。"""
    def write(self, data: str) -> None:
        import codecs
        encrypted = codecs.encode(data, "rot13")
        super().write(encrypted)

    def read(self) -> str:
        import codecs
        return codecs.decode(super().read(), "rot13")


class CompressionDecorator(DataSourceDecorator):
    """圧縮デコレータ (簡易版: 繰り返し文字の除去シミュレーション)。"""
    def write(self, data: str) -> None:
        compressed = f"[compressed:{len(data)}]{data[:20]}"
        super().write(compressed)

    def read(self) -> str:
        raw = super().read()
        return raw  # 実際は解凍処理


# Python デコレータとの対応
def log_calls(func: Callable) -> Callable:
    """Python デコレータ ── GoF Decorator に相当する関数ラッパー。"""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        result = func(*args, **kwargs)
        return result
    return wrapper


def retry(max_retries: int = 3) -> Callable:
    """パラメータ付き Python デコレータ。"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
            raise RuntimeError(f"Failed after {max_retries} retries") from last_error
        return wrapper
    return decorator


def demo_decorator() -> None:
    subsection("2-2. Decorator パターン")

    print("    GoF Decorator (オブジェクト包装):")
    source: DataSource = FileDataSource()
    encrypted = EncryptionDecorator(source)
    compressed = CompressionDecorator(encrypted)

    compressed.write("Hello Design Patterns!")
    demo("raw storage", source.read())
    demo("through compression", compressed.read())

    print()
    print("    Python デコレータ (関数ラッパー):")

    @log_calls
    def add(a: int, b: int) -> int:
        return a + b

    demo("add(3, 4)", add(3, 4))

    call_count = 0

    @retry(max_retries=3)
    def flaky_operation() -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("Network error")
        return "Success!"

    demo("flaky_operation()", flaky_operation())
    demo("call_count", call_count)

    question("GoF Decorator と Python @decorator の共通点と相違点は？")


# --------------------------------------------------
# 2-3. Proxy
# --------------------------------------------------

class HeavyResource(abc.ABC):
    @abc.abstractmethod
    def process(self, data: str) -> str: ...


class RealHeavyResource(HeavyResource):
    """重いリソース ── 初期化に時間がかかる。"""
    def __init__(self) -> None:
        self._loaded = True  # 本来はDB接続やモデルロード

    def process(self, data: str) -> str:
        return f"Processed: {data}"


class LazyProxy(HeavyResource):
    """遅延ロード Proxy ── 初回アクセスまでリソースを作らない。"""
    def __init__(self) -> None:
        self._resource: Optional[RealHeavyResource] = None

    def process(self, data: str) -> str:
        if self._resource is None:
            self._resource = RealHeavyResource()
        return self._resource.process(data)


class CachingProxy(HeavyResource):
    """キャッシュ Proxy ── 同じリクエストの結果を再利用。"""
    def __init__(self, resource: HeavyResource) -> None:
        self._resource = resource
        self._cache: Dict[str, str] = {}

    def process(self, data: str) -> str:
        if data not in self._cache:
            self._cache[data] = self._resource.process(data)
        return self._cache[data]


class AccessControlProxy(HeavyResource):
    """アクセス制御 Proxy ── 権限チェック。"""
    def __init__(self, resource: HeavyResource, allowed_users: Set[str]) -> None:
        self._resource = resource
        self._allowed = allowed_users
        self._current_user = "anonymous"

    def set_user(self, user: str) -> None:
        self._current_user = user

    def process(self, data: str) -> str:
        if self._current_user not in self._allowed:
            return f"ACCESS DENIED for user '{self._current_user}'"
        return self._resource.process(data)


def demo_proxy() -> None:
    subsection("2-3. Proxy パターン")

    print("    Lazy Proxy:")
    lazy = LazyProxy()
    demo("Before process, resource loaded", lazy._resource is not None)
    demo("lazy.process('test')", lazy.process("test"))
    demo("After process, resource loaded", lazy._resource is not None)

    print()
    print("    Caching Proxy:")
    real = RealHeavyResource()
    cached = CachingProxy(real)
    demo("First call ", cached.process("query1"))
    demo("Second call (cached)", cached.process("query1"))
    demo("Cache contents", list(cached._cache.keys()))

    print()
    print("    Access Control Proxy:")
    acl = AccessControlProxy(RealHeavyResource(), {"admin", "yuta"})
    acl.set_user("anonymous")
    demo("anonymous", acl.process("secret data"))
    acl.set_user("yuta")
    demo("yuta     ", acl.process("secret data"))


# --------------------------------------------------
# 2-4. Facade
# --------------------------------------------------

class _AuthService:
    def authenticate(self, token: str) -> bool:
        return token.startswith("valid_")

    def get_user_id(self, token: str) -> str:
        return f"user_{token[6:]}"


class _InventoryService:
    def check_stock(self, product_id: str) -> int:
        stocks = {"P001": 10, "P002": 0, "P003": 5}
        return stocks.get(product_id, 0)

    def reserve(self, product_id: str, qty: int) -> bool:
        return self.check_stock(product_id) >= qty


class _PaymentService:
    def charge(self, user_id: str, amount: float) -> str:
        return f"CHARGE-{user_id}-{amount}"


class _NotificationService:
    def send_email(self, user_id: str, message: str) -> str:
        return f"Email to {user_id}: {message}"


class OrderFacade:
    """Facade ── 複雑なサブシステム群を単一インターフェースで提供。
    クライアントは4つのサービスの存在を知る必要がない。
    """
    def __init__(self) -> None:
        self._auth = _AuthService()
        self._inventory = _InventoryService()
        self._payment = _PaymentService()
        self._notification = _NotificationService()

    def place_order(self, token: str, product_id: str, qty: int, price: float) -> Dict[str, str]:
        if not self._auth.authenticate(token):
            return {"status": "error", "message": "Authentication failed"}

        user_id = self._auth.get_user_id(token)

        if not self._inventory.reserve(product_id, qty):
            return {"status": "error", "message": f"Product {product_id} out of stock"}

        charge_id = self._payment.charge(user_id, price * qty)
        email_result = self._notification.send_email(user_id, f"Order confirmed: {charge_id}")

        return {"status": "success", "charge_id": charge_id, "notification": email_result}


def demo_facade() -> None:
    subsection("2-4. Facade パターン")
    facade = OrderFacade()

    demo("Valid order  ", facade.place_order("valid_yuta", "P001", 2, 29.99))
    demo("Bad auth     ", facade.place_order("invalid", "P001", 1, 29.99))
    demo("Out of stock ", facade.place_order("valid_yuta", "P002", 1, 9.99))

    question("Facade はいつ作るべきか？全部 Facade にしたら何が起きる？")


# --------------------------------------------------
# 2-5. Composite
# --------------------------------------------------

class FileSystemEntry(abc.ABC):
    def __init__(self, name: str) -> None:
        self.name = name

    @abc.abstractmethod
    def get_size(self) -> int: ...

    @abc.abstractmethod
    def display(self, indent: int = 0) -> str: ...


class File(FileSystemEntry):
    def __init__(self, name: str, size: int) -> None:
        super().__init__(name)
        self.size = size

    def get_size(self) -> int:
        return self.size

    def display(self, indent: int = 0) -> str:
        return " " * indent + f"  {self.name} ({self.size}B)"


class Directory(FileSystemEntry):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.children: List[FileSystemEntry] = []

    def add(self, entry: FileSystemEntry) -> Directory:
        self.children.append(entry)
        return self

    def get_size(self) -> int:
        return sum(child.get_size() for child in self.children)

    def display(self, indent: int = 0) -> str:
        lines = [" " * indent + f"  {self.name}/ ({self.get_size()}B)"]
        for child in self.children:
            lines.append(child.display(indent + 2))
        return "\n".join(lines)


def demo_composite() -> None:
    subsection("2-5. Composite パターン")

    root = Directory("project")
    src = Directory("src")
    src.add(File("main.py", 1200))
    src.add(File("utils.py", 800))

    tests = Directory("tests")
    tests.add(File("test_main.py", 600))

    root.add(src)
    root.add(tests)
    root.add(File("README.md", 200))

    print(root.display(indent=4))
    demo("Total size", f"{root.get_size()}B")

    question("Composite と通常のツリー構造の違いは？統一インターフェースの利点は？")


# ============================================================
# 3. 振る舞いパターン (Behavioral Patterns)
# ============================================================

# --------------------------------------------------
# 3-1. Strategy
# --------------------------------------------------

class SortStrategy(Protocol):
    def sort(self, data: List[int]) -> List[int]: ...


class BubbleSort:
    def sort(self, data: List[int]) -> List[int]:
        arr = data[:]
        n = len(arr)
        for i in range(n):
            for j in range(0, n - i - 1):
                if arr[j] > arr[j + 1]:
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
        return arr


class QuickSort:
    def sort(self, data: List[int]) -> List[int]:
        if len(data) <= 1:
            return data[:]
        pivot = data[len(data) // 2]
        left = [x for x in data if x < pivot]
        mid = [x for x in data if x == pivot]
        right = [x for x in data if x > pivot]
        return self.sort(left) + mid + self.sort(right)


class InsertionSort:
    def sort(self, data: List[int]) -> List[int]:
        arr = data[:]
        for i in range(1, len(arr)):
            key = arr[i]
            j = i - 1
            while j >= 0 and arr[j] > key:
                arr[j + 1] = arr[j]
                j -= 1
            arr[j + 1] = key
        return arr


class Sorter:
    """Context ── Strategy を切り替えてソートアルゴリズムを変更。"""
    def __init__(self, strategy: SortStrategy) -> None:
        self._strategy = strategy

    def set_strategy(self, strategy: SortStrategy) -> None:
        self._strategy = strategy

    def sort(self, data: List[int]) -> List[int]:
        return self._strategy.sort(data)


# 支払い方式の Strategy
class PaymentStrategy(Protocol):
    def pay(self, amount: float) -> str: ...


class CreditCardPayment:
    def __init__(self, card_number: str) -> None:
        self._card = card_number

    def pay(self, amount: float) -> str:
        return f"Paid {amount} with card ending {self._card[-4:]}"


class PayPayPayment:
    def __init__(self, account: str) -> None:
        self._account = account

    def pay(self, amount: float) -> str:
        return f"Paid {amount} via PayPay ({self._account})"


class BankTransfer:
    def __init__(self, bank: str) -> None:
        self._bank = bank

    def pay(self, amount: float) -> str:
        return f"Paid {amount} via bank transfer ({self._bank})"


def demo_strategy() -> None:
    subsection("3-1. Strategy パターン")

    data = [38, 27, 43, 3, 9, 82, 10]
    print("    Sort Strategy:")
    for strategy_cls in [BubbleSort, QuickSort, InsertionSort]:
        sorter = Sorter(strategy_cls())
        demo(f"{strategy_cls.__name__:14s}", sorter.sort(data))

    print()
    print("    Payment Strategy:")
    payments: List[PaymentStrategy] = [
        CreditCardPayment("4111111111111234"),
        PayPayPayment("yuta@paypay"),
        BankTransfer("MUFG"),
    ]
    for p in payments:
        demo("payment", p.pay(1500))

    question("Strategy と if-else の分岐、どちらが適切かの判断基準は？")


# --------------------------------------------------
# 3-2. Observer / Pub-Sub
# --------------------------------------------------

class EventBus:
    """Observer パターン (Pub-Sub 方式)。
    GoF Observer はサブジェクトとオブザーバーの1対多だが、
    EventBus はイベント名ベースでより疎結合。
    """
    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)

    def subscribe(self, event: str, callback: Callable) -> None:
        self._subscribers[event].append(callback)

    def unsubscribe(self, event: str, callback: Callable) -> None:
        self._subscribers[event].remove(callback)

    def publish(self, event: str, data: Any = None) -> None:
        for callback in self._subscribers.get(event, []):
            callback(data)


def demo_observer() -> None:
    subsection("3-2. Observer / Pub-Sub パターン")

    bus = EventBus()
    log: List[str] = []

    def on_user_created(data: Any) -> None:
        log.append(f"EmailService: Welcome email to {data['email']}")

    def on_user_created_analytics(data: Any) -> None:
        log.append(f"Analytics: New user registered: {data['name']}")

    def on_order_placed(data: Any) -> None:
        log.append(f"Inventory: Reduce stock for {data['product']}")

    bus.subscribe("user.created", on_user_created)
    bus.subscribe("user.created", on_user_created_analytics)
    bus.subscribe("order.placed", on_order_placed)

    bus.publish("user.created", {"name": "Yuta", "email": "yuta@example.com"})
    bus.publish("order.placed", {"product": "Keyboard", "qty": 1})

    for entry in log:
        demo("event", entry)

    question("Observer と Pub-Sub の違いは？イベント駆動の欠点は何か？")


# --------------------------------------------------
# 3-3. Command (Undo/Redo)
# --------------------------------------------------

class Command(abc.ABC):
    @abc.abstractmethod
    def execute(self) -> None: ...
    @abc.abstractmethod
    def undo(self) -> None: ...


class TextEditor:
    def __init__(self) -> None:
        self.content = ""

    def __repr__(self) -> str:
        return f"TextEditor('{self.content}')"


class InsertCommand(Command):
    def __init__(self, editor: TextEditor, text: str, position: int) -> None:
        self._editor = editor
        self._text = text
        self._position = position

    def execute(self) -> None:
        self._editor.content = (
            self._editor.content[:self._position]
            + self._text
            + self._editor.content[self._position:]
        )

    def undo(self) -> None:
        self._editor.content = (
            self._editor.content[:self._position]
            + self._editor.content[self._position + len(self._text):]
        )


class DeleteCommand(Command):
    def __init__(self, editor: TextEditor, position: int, length: int) -> None:
        self._editor = editor
        self._position = position
        self._length = length
        self._deleted_text = ""

    def execute(self) -> None:
        self._deleted_text = self._editor.content[self._position:self._position + self._length]
        self._editor.content = (
            self._editor.content[:self._position]
            + self._editor.content[self._position + self._length:]
        )

    def undo(self) -> None:
        self._editor.content = (
            self._editor.content[:self._position]
            + self._deleted_text
            + self._editor.content[self._position:]
        )


class CommandHistory:
    """Undo/Redo スタック。"""
    def __init__(self) -> None:
        self._undo_stack: List[Command] = []
        self._redo_stack: List[Command] = []

    def execute(self, command: Command) -> None:
        command.execute()
        self._undo_stack.append(command)
        self._redo_stack.clear()

    def undo(self) -> None:
        if not self._undo_stack:
            return
        cmd = self._undo_stack.pop()
        cmd.undo()
        self._redo_stack.append(cmd)

    def redo(self) -> None:
        if not self._redo_stack:
            return
        cmd = self._redo_stack.pop()
        cmd.execute()
        self._undo_stack.append(cmd)


def demo_command() -> None:
    subsection("3-3. Command パターン (Undo/Redo)")

    editor = TextEditor()
    history = CommandHistory()

    history.execute(InsertCommand(editor, "Hello", 0))
    demo("Insert 'Hello'  ", editor)

    history.execute(InsertCommand(editor, " World", 5))
    demo("Insert ' World' ", editor)

    history.execute(InsertCommand(editor, "!", 11))
    demo("Insert '!'      ", editor)

    history.undo()
    demo("Undo             ", editor)

    history.undo()
    demo("Undo             ", editor)

    history.redo()
    demo("Redo             ", editor)

    history.execute(DeleteCommand(editor, 0, 5))
    demo("Delete 0..5      ", editor)

    history.undo()
    demo("Undo delete      ", editor)

    task("MacroCommand を実装してみよう。複数コマンドを一括実行・一括Undoする。")


# --------------------------------------------------
# 3-4. State
# --------------------------------------------------

class OrderState(abc.ABC):
    @abc.abstractmethod
    def confirm(self, order: Order) -> str: ...
    @abc.abstractmethod
    def ship(self, order: Order) -> str: ...
    @abc.abstractmethod
    def deliver(self, order: Order) -> str: ...
    @abc.abstractmethod
    def cancel(self, order: Order) -> str: ...
    @abc.abstractmethod
    def name(self) -> str: ...


class DraftState(OrderState):
    def confirm(self, order: Order) -> str:
        order._state = ConfirmedState()
        return "Order confirmed"
    def ship(self, order: Order) -> str:
        return "Cannot ship a draft order"
    def deliver(self, order: Order) -> str:
        return "Cannot deliver a draft order"
    def cancel(self, order: Order) -> str:
        order._state = CancelledState()
        return "Draft order cancelled"
    def name(self) -> str:
        return "DRAFT"


class ConfirmedState(OrderState):
    def confirm(self, order: Order) -> str:
        return "Already confirmed"
    def ship(self, order: Order) -> str:
        order._state = ShippedState()
        return "Order shipped"
    def deliver(self, order: Order) -> str:
        return "Cannot deliver before shipping"
    def cancel(self, order: Order) -> str:
        order._state = CancelledState()
        return "Confirmed order cancelled (refund initiated)"
    def name(self) -> str:
        return "CONFIRMED"


class ShippedState(OrderState):
    def confirm(self, order: Order) -> str:
        return "Already past confirmation"
    def ship(self, order: Order) -> str:
        return "Already shipped"
    def deliver(self, order: Order) -> str:
        order._state = DeliveredState()
        return "Order delivered"
    def cancel(self, order: Order) -> str:
        return "Cannot cancel a shipped order"
    def name(self) -> str:
        return "SHIPPED"


class DeliveredState(OrderState):
    def confirm(self, order: Order) -> str:
        return "Already delivered"
    def ship(self, order: Order) -> str:
        return "Already delivered"
    def deliver(self, order: Order) -> str:
        return "Already delivered"
    def cancel(self, order: Order) -> str:
        return "Cannot cancel a delivered order"
    def name(self) -> str:
        return "DELIVERED"


class CancelledState(OrderState):
    def confirm(self, order: Order) -> str:
        return "Cannot confirm a cancelled order"
    def ship(self, order: Order) -> str:
        return "Cannot ship a cancelled order"
    def deliver(self, order: Order) -> str:
        return "Cannot deliver a cancelled order"
    def cancel(self, order: Order) -> str:
        return "Already cancelled"
    def name(self) -> str:
        return "CANCELLED"


class Order:
    """State パターン ── 注文の状態遷移を各 State クラスに委譲。"""
    def __init__(self, order_id: str) -> None:
        self.order_id = order_id
        self._state: OrderState = DraftState()

    @property
    def state(self) -> str:
        return self._state.name()

    def confirm(self) -> str:
        return self._state.confirm(self)

    def ship(self) -> str:
        return self._state.ship(self)

    def deliver(self) -> str:
        return self._state.deliver(self)

    def cancel(self) -> str:
        return self._state.cancel(self)


def demo_state() -> None:
    subsection("3-4. State パターン")

    order = Order("ORD-001")
    transitions = [
        ("confirm", order.confirm),
        ("ship",    order.ship),
        ("cancel",  order.cancel),  # shipped だからキャンセル不可
        ("deliver", order.deliver),
        ("deliver", order.deliver),  # 既に配達済み
    ]
    for action_name, action in transitions:
        result = action()
        demo(f"{action_name:8s} -> state={order.state:12s}", result)

    question("State パターンと巨大な if/elif の違いは？状態が20個あったら？")


# --------------------------------------------------
# 3-5. Template Method
# --------------------------------------------------

class DataPipeline(abc.ABC):
    """Template Method ── 処理の骨格を定義し、各ステップはサブクラスに任せる。"""

    def run(self, source: str) -> Dict[str, Any]:
        raw = self.extract(source)
        cleaned = self.transform(raw)
        result = self.load(cleaned)
        return {"source": source, "records": len(cleaned), "destination": result}

    @abc.abstractmethod
    def extract(self, source: str) -> List[Dict[str, Any]]: ...

    @abc.abstractmethod
    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]: ...

    @abc.abstractmethod
    def load(self, data: List[Dict[str, Any]]) -> str: ...


class CSVPipeline(DataPipeline):
    def extract(self, source: str) -> List[Dict[str, Any]]:
        return [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}]

    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [{"name": d["name"].upper(), "age": int(d["age"])} for d in data]

    def load(self, data: List[Dict[str, Any]]) -> str:
        return f"database (inserted {len(data)} records)"


class APIPipeline(DataPipeline):
    def extract(self, source: str) -> List[Dict[str, Any]]:
        return [{"id": 1, "status": "active"}, {"id": 2, "status": "inactive"}]

    def transform(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [d for d in data if d["status"] == "active"]

    def load(self, data: List[Dict[str, Any]]) -> str:
        return f"data_warehouse (upserted {len(data)} records)"


def demo_template_method() -> None:
    subsection("3-5. Template Method パターン")

    for pipeline_cls in [CSVPipeline, APIPipeline]:
        pipeline = pipeline_cls()
        result = pipeline.run("source_endpoint")
        demo(pipeline_cls.__name__, result)

    question("Template Method と Strategy の違いは？継承 vs 委譲。")


# --------------------------------------------------
# 3-6. Chain of Responsibility
# --------------------------------------------------

class Handler(abc.ABC):
    def __init__(self) -> None:
        self._next: Optional[Handler] = None

    def set_next(self, handler: Handler) -> Handler:
        self._next = handler
        return handler

    def handle(self, request: Dict[str, Any]) -> Optional[str]:
        if self._next:
            return self._next.handle(request)
        return None


class AuthenticationHandler(Handler):
    def handle(self, request: Dict[str, Any]) -> Optional[str]:
        if not request.get("token"):
            return "REJECTED: No authentication token"
        if request["token"] != "valid_token":
            return "REJECTED: Invalid token"
        return super().handle(request)


class RateLimitHandler(Handler):
    def __init__(self) -> None:
        super().__init__()
        self._request_counts: Dict[str, int] = defaultdict(int)
        self._limit = 5

    def handle(self, request: Dict[str, Any]) -> Optional[str]:
        ip = request.get("ip", "unknown")
        self._request_counts[ip] += 1
        if self._request_counts[ip] > self._limit:
            return f"REJECTED: Rate limit exceeded for {ip}"
        return super().handle(request)


class ValidationHandler(Handler):
    def handle(self, request: Dict[str, Any]) -> Optional[str]:
        if not request.get("body"):
            return "REJECTED: Empty request body"
        if len(request["body"]) > 1000:
            return "REJECTED: Request body too large"
        return super().handle(request)


class LoggingHandler(Handler):
    def __init__(self) -> None:
        super().__init__()
        self.logs: List[str] = []

    def handle(self, request: Dict[str, Any]) -> Optional[str]:
        self.logs.append(f"Request from {request.get('ip', '?')}: {request.get('path', '/')}")
        return super().handle(request)


def demo_chain_of_responsibility() -> None:
    subsection("3-6. Chain of Responsibility パターン")

    logger = LoggingHandler()
    auth = AuthenticationHandler()
    rate = RateLimitHandler()
    validator = ValidationHandler()

    # チェーン構築: logger -> auth -> rate -> validator
    logger.set_next(auth).set_next(rate).set_next(validator)

    requests = [
        {"token": "valid_token", "ip": "1.2.3.4", "body": "data", "path": "/api"},
        {"ip": "5.6.7.8", "body": "data", "path": "/api"},  # no token
        {"token": "valid_token", "ip": "1.2.3.4", "path": "/api"},  # no body
    ]

    for req in requests:
        result = logger.handle(req)
        demo(f"req(token={str(req.get('token', 'N/A'))[:5]:5s})", result or "PASSED all checks")

    question("Chain of Responsibility とミドルウェアパターンの共通点は？")


# --------------------------------------------------
# 3-7. Iterator
# --------------------------------------------------

class BinaryTreeNode:
    def __init__(self, value: int, left: Optional[BinaryTreeNode] = None,
                 right: Optional[BinaryTreeNode] = None) -> None:
        self.value = value
        self.left = left
        self.right = right


class InOrderIterator:
    """カスタムイテレータ ── 中順走査。"""
    def __init__(self, root: Optional[BinaryTreeNode]) -> None:
        self._stack: List[BinaryTreeNode] = []
        self._push_left(root)

    def _push_left(self, node: Optional[BinaryTreeNode]) -> None:
        while node:
            self._stack.append(node)
            node = node.left

    def __iter__(self) -> InOrderIterator:
        return self

    def __next__(self) -> int:
        if not self._stack:
            raise StopIteration
        node = self._stack.pop()
        self._push_left(node.right)
        return node.value


def inorder_generator(node: Optional[BinaryTreeNode]) -> Iterator[int]:
    """ジェネレータ版 ── Python ではこちらが圧倒的にシンプル。"""
    if node:
        yield from inorder_generator(node.left)
        yield node.value
        yield from inorder_generator(node.right)


class PaginatedIterator:
    """ページネーション ── API レスポンスの遅延取得をシミュレート。"""
    def __init__(self, total_items: int, page_size: int = 3) -> None:
        self._total = total_items
        self._page_size = page_size
        self._offset = 0

    def __iter__(self) -> PaginatedIterator:
        return self

    def __next__(self) -> List[int]:
        if self._offset >= self._total:
            raise StopIteration
        page = list(range(self._offset, min(self._offset + self._page_size, self._total)))
        self._offset += self._page_size
        return page


def demo_iterator() -> None:
    subsection("3-7. Iterator パターン")

    #       4
    #      / \
    #     2   6
    #    / \ / \
    #   1  3 5  7
    tree = BinaryTreeNode(4,
        BinaryTreeNode(2, BinaryTreeNode(1), BinaryTreeNode(3)),
        BinaryTreeNode(6, BinaryTreeNode(5), BinaryTreeNode(7)),
    )

    demo("InOrderIterator  ", list(InOrderIterator(tree)))
    demo("inorder_generator", list(inorder_generator(tree)))

    print()
    print("    Paginated Iterator:")
    for page in PaginatedIterator(10, page_size=3):
        demo("page", page)

    question("カスタムイテレータとジェネレータ、どちらを使うべきか？")


# --------------------------------------------------
# 3-8. Mediator
# --------------------------------------------------

class ChatRoom:
    """Mediator ── コンポーネント間の通信を集中管理。
    各 User は他の User を直接知らない。
    """
    def __init__(self, name: str) -> None:
        self.name = name
        self._users: Dict[str, ChatUser] = {}
        self.message_log: List[str] = []

    def register(self, user: ChatUser) -> None:
        self._users[user.name] = user
        user.room = self

    def send(self, message: str, sender: ChatUser, recipient: Optional[str] = None) -> None:
        if recipient:
            target = self._users.get(recipient)
            if target:
                entry = f"[DM] {sender.name} -> {recipient}: {message}"
                self.message_log.append(entry)
                target.receive(sender.name, message)
        else:
            entry = f"[ALL] {sender.name}: {message}"
            self.message_log.append(entry)
            for name, user in self._users.items():
                if name != sender.name:
                    user.receive(sender.name, message)


class ChatUser:
    def __init__(self, name: str) -> None:
        self.name = name
        self.room: Optional[ChatRoom] = None
        self.inbox: List[str] = []

    def send(self, message: str, to: Optional[str] = None) -> None:
        if self.room:
            self.room.send(message, self, to)

    def receive(self, sender: str, message: str) -> None:
        self.inbox.append(f"{sender}: {message}")


def demo_mediator() -> None:
    subsection("3-8. Mediator パターン")

    room = ChatRoom("design-patterns")
    alice = ChatUser("Alice")
    bob = ChatUser("Bob")
    charlie = ChatUser("Charlie")

    room.register(alice)
    room.register(bob)
    room.register(charlie)

    alice.send("Hello everyone!")
    bob.send("Hi Alice!", to="Alice")
    charlie.send("Strategy vs State?")

    for msg in room.message_log:
        demo("log", msg)

    print()
    demo("Alice's inbox ", alice.inbox)
    demo("Bob's inbox   ", bob.inbox)
    demo("Charlie's inbox", charlie.inbox)

    question("Mediator が God Object になるリスクは？どう防ぐ？")


# ============================================================
# 4. モダンパターン (Modern/Enterprise Patterns)
# ============================================================

# --------------------------------------------------
# 4-1. Repository パターン
# --------------------------------------------------

T = TypeVar("T")


@dataclass
class User:
    id: int
    name: str
    email: str
    active: bool = True


class Repository(abc.ABC, Generic[T]):
    """Repository ── データアクセスを抽象化。
    ビジネスロジックは永続化層の詳細を知らない。
    """
    @abc.abstractmethod
    def find_by_id(self, id: int) -> Optional[T]: ...
    @abc.abstractmethod
    def find_all(self) -> List[T]: ...
    @abc.abstractmethod
    def save(self, entity: T) -> None: ...
    @abc.abstractmethod
    def delete(self, id: int) -> None: ...


class InMemoryUserRepository(Repository[User]):
    def __init__(self) -> None:
        self._store: Dict[int, User] = {}

    def find_by_id(self, id: int) -> Optional[User]:
        return self._store.get(id)

    def find_all(self) -> List[User]:
        return list(self._store.values())

    def save(self, entity: User) -> None:
        self._store[entity.id] = entity

    def delete(self, id: int) -> None:
        self._store.pop(id, None)

    def find_active(self) -> List[User]:
        return [u for u in self._store.values() if u.active]


def demo_repository() -> None:
    subsection("4-1. Repository パターン")

    repo = InMemoryUserRepository()
    repo.save(User(1, "Alice", "alice@example.com"))
    repo.save(User(2, "Bob", "bob@example.com"))
    repo.save(User(3, "Charlie", "charlie@example.com", active=False))

    demo("find_by_id(1)", repo.find_by_id(1))
    demo("find_all     ", [u.name for u in repo.find_all()])
    demo("find_active  ", [u.name for u in repo.find_active()])

    repo.delete(2)
    demo("after delete(2)", [u.name for u in repo.find_all()])

    question("Repository と DAO (Data Access Object) の違いは？")


# --------------------------------------------------
# 4-2. Unit of Work
# --------------------------------------------------

class UnitOfWork:
    """Unit of Work ── 複数の変更をまとめてコミット/ロールバック。
    データベーストランザクションの抽象化。
    """
    def __init__(self, repo: InMemoryUserRepository) -> None:
        self._repo = repo
        self._new: List[User] = []
        self._dirty: List[User] = []
        self._deleted: List[int] = []
        self._committed = False

    def register_new(self, user: User) -> None:
        self._new.append(user)

    def register_dirty(self, user: User) -> None:
        self._dirty.append(user)

    def register_deleted(self, user_id: int) -> None:
        self._deleted.append(user_id)

    def commit(self) -> str:
        results = []
        for user in self._new:
            self._repo.save(user)
            results.append(f"INSERT {user.name}")
        for user in self._dirty:
            self._repo.save(user)
            results.append(f"UPDATE {user.name}")
        for uid in self._deleted:
            self._repo.delete(uid)
            results.append(f"DELETE id={uid}")
        self._committed = True
        self._new.clear()
        self._dirty.clear()
        self._deleted.clear()
        return f"Committed: {', '.join(results)}"

    def rollback(self) -> str:
        count = len(self._new) + len(self._dirty) + len(self._deleted)
        self._new.clear()
        self._dirty.clear()
        self._deleted.clear()
        return f"Rolled back {count} pending operations"


def demo_unit_of_work() -> None:
    subsection("4-2. Unit of Work パターン")

    repo = InMemoryUserRepository()
    repo.save(User(1, "Alice", "alice@example.com"))

    uow = UnitOfWork(repo)
    uow.register_new(User(2, "Bob", "bob@example.com"))
    uow.register_dirty(User(1, "Alice Updated", "alice_new@example.com"))
    uow.register_deleted(999)

    demo("Before commit", [u.name for u in repo.find_all()])
    demo("Commit result", uow.commit())
    demo("After commit ", [u.name for u in repo.find_all()])

    # ロールバックのデモ
    uow2 = UnitOfWork(repo)
    uow2.register_new(User(10, "Ghost", "ghost@example.com"))
    demo("Rollback     ", uow2.rollback())
    demo("After rollback", [u.name for u in repo.find_all()])


# --------------------------------------------------
# 4-3. Dependency Injection
# --------------------------------------------------

class Logger(Protocol):
    def log(self, message: str) -> None: ...


class ConsoleLogger:
    def __init__(self) -> None:
        self.messages: List[str] = []

    def log(self, message: str) -> None:
        self.messages.append(f"[CONSOLE] {message}")


class FileLogger:
    def __init__(self) -> None:
        self.messages: List[str] = []

    def log(self, message: str) -> None:
        self.messages.append(f"[FILE] {message}")


class UserService:
    """手動 DI ── コンストラクタでロガーを注入。"""
    def __init__(self, repo: Repository[User], logger: Logger) -> None:
        self._repo = repo
        self._logger = logger

    def create_user(self, id: int, name: str, email: str) -> User:
        user = User(id, name, email)
        self._repo.save(user)
        self._logger.log(f"User created: {name}")
        return user


class SimpleDIContainer:
    """シンプルな DI コンテナ。
    サービスロケータとの違い: コンテナは起動時に1回だけ使い、
    以降はコンストラクタ経由で依存を注入する。
    """
    def __init__(self) -> None:
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}

    def register(self, name: str, factory: Callable, singleton: bool = False) -> None:
        self._factories[name] = (factory, singleton)

    def resolve(self, name: str) -> Any:
        if name in self._singletons:
            return self._singletons[name]
        entry = self._factories.get(name)
        if entry is None:
            raise KeyError(f"Service '{name}' not registered")
        factory, is_singleton = entry
        instance = factory(self)
        if is_singleton:
            self._singletons[name] = instance
        return instance


def demo_dependency_injection() -> None:
    subsection("4-3. Dependency Injection パターン")

    print("    手動 DI:")
    repo = InMemoryUserRepository()
    logger = ConsoleLogger()
    service = UserService(repo, logger)
    service.create_user(1, "Yuta", "yuta@example.com")
    demo("logger.messages", logger.messages)
    demo("repo contents  ", [u.name for u in repo.find_all()])

    print()
    print("    DI Container:")
    container = SimpleDIContainer()
    container.register("logger", lambda c: ConsoleLogger(), singleton=True)
    container.register("repo", lambda c: InMemoryUserRepository(), singleton=True)
    container.register("user_service",
        lambda c: UserService(c.resolve("repo"), c.resolve("logger")))

    svc = container.resolve("user_service")
    svc.create_user(1, "ContainerUser", "container@example.com")
    resolved_logger = container.resolve("logger")
    demo("DI container logger", resolved_logger.messages)

    question("DI は必ずフレームワークが必要か？手動 DI の利点と欠点は？")


# --------------------------------------------------
# 4-4. Service Locator (アンチパターンとしての側面)
# --------------------------------------------------

class ServiceLocator:
    """Service Locator ── DI との比較。
    サービスを中央レジストリから取得。DI と異なり、
    依存がコンストラクタに現れないため、テストしにくい。
    """
    _services: Dict[str, Any] = {}

    @classmethod
    def register(cls, name: str, service: Any) -> None:
        cls._services[name] = service

    @classmethod
    def get(cls, name: str) -> Any:
        service = cls._services.get(name)
        if service is None:
            raise KeyError(f"Service '{name}' not found")
        return service

    @classmethod
    def clear(cls) -> None:
        cls._services.clear()


class OrderService:
    """Service Locator を使うサービス ── 依存が隠蔽される。"""
    def place_order(self, product: str) -> str:
        logger = ServiceLocator.get("logger")  # 隠れた依存！
        logger.log(f"Order placed: {product}")
        return f"Order for {product} placed"


def demo_service_locator() -> None:
    subsection("4-4. Service Locator (vs DI)")

    ServiceLocator.clear()
    sl_logger = ConsoleLogger()
    ServiceLocator.register("logger", sl_logger)

    order_svc = OrderService()
    demo("place_order", order_svc.place_order("Laptop"))
    demo("logger.messages", sl_logger.messages)

    print()
    point("Service Locator の問題点:")
    point("  1. 依存がコンストラクタに現れない (隠れた結合)")
    point("  2. テスト時にグローバル状態のリセットが必要")
    point("  3. コンパイル時に依存の不足を検出できない")
    point("DI を使えばこれらの問題はすべて解消される。")
    ServiceLocator.clear()


# --------------------------------------------------
# 4-5. Specification パターン
# --------------------------------------------------

class Specification(abc.ABC):
    """Specification ── ビジネスルールをオブジェクトとして表現し、組み合わせる。"""
    @abc.abstractmethod
    def is_satisfied_by(self, candidate: Any) -> bool: ...

    def and_(self, other: Specification) -> Specification:
        return AndSpecification(self, other)

    def or_(self, other: Specification) -> Specification:
        return OrSpecification(self, other)

    def not_(self) -> Specification:
        return NotSpecification(self)


class AndSpecification(Specification):
    def __init__(self, left: Specification, right: Specification) -> None:
        self._left = left
        self._right = right

    def is_satisfied_by(self, candidate: Any) -> bool:
        return self._left.is_satisfied_by(candidate) and self._right.is_satisfied_by(candidate)


class OrSpecification(Specification):
    def __init__(self, left: Specification, right: Specification) -> None:
        self._left = left
        self._right = right

    def is_satisfied_by(self, candidate: Any) -> bool:
        return self._left.is_satisfied_by(candidate) or self._right.is_satisfied_by(candidate)


class NotSpecification(Specification):
    def __init__(self, spec: Specification) -> None:
        self._spec = spec

    def is_satisfied_by(self, candidate: Any) -> bool:
        return not self._spec.is_satisfied_by(candidate)


@dataclass
class Product:
    name: str
    price: float
    category: str
    in_stock: bool


class PriceSpec(Specification):
    def __init__(self, max_price: float) -> None:
        self._max = max_price

    def is_satisfied_by(self, candidate: Product) -> bool:
        return candidate.price <= self._max


class CategorySpec(Specification):
    def __init__(self, category: str) -> None:
        self._category = category

    def is_satisfied_by(self, candidate: Product) -> bool:
        return candidate.category == self._category


class InStockSpec(Specification):
    def is_satisfied_by(self, candidate: Product) -> bool:
        return candidate.in_stock


def demo_specification() -> None:
    subsection("4-5. Specification パターン")

    products = [
        Product("Laptop", 1200, "electronics", True),
        Product("Mouse", 25, "electronics", True),
        Product("Book", 15, "books", True),
        Product("Monitor", 500, "electronics", False),
        Product("Keyboard", 80, "electronics", True),
    ]

    affordable_electronics = (
        PriceSpec(100)
        .and_(CategorySpec("electronics"))
        .and_(InStockSpec())
    )

    cheap_or_books = PriceSpec(30).or_(CategorySpec("books"))

    demo("Affordable electronics", [p.name for p in products if affordable_electronics.is_satisfied_by(p)])
    demo("Cheap or books        ", [p.name for p in products if cheap_or_books.is_satisfied_by(p)])

    question("Specification パターンと filter() + lambda の使い分けは？")


# --------------------------------------------------
# 4-6. Null Object パターン
# --------------------------------------------------

class AbstractLogger(abc.ABC):
    @abc.abstractmethod
    def info(self, msg: str) -> str: ...
    @abc.abstractmethod
    def error(self, msg: str) -> str: ...


class RealLogger(AbstractLogger):
    def info(self, msg: str) -> str:
        return f"INFO: {msg}"

    def error(self, msg: str) -> str:
        return f"ERROR: {msg}"


class NullLogger(AbstractLogger):
    """Null Object ── None チェックを排除。
    何もしないが、インターフェースに準拠。
    """
    def info(self, msg: str) -> str:
        return ""

    def error(self, msg: str) -> str:
        return ""


class AppWithLogger:
    def __init__(self, logger: Optional[AbstractLogger] = None) -> None:
        self._logger = logger or NullLogger()

    def do_work(self) -> str:
        info_result = self._logger.info("Starting work")
        # None チェック不要！
        return info_result or "(no log output)"


def demo_null_object() -> None:
    subsection("4-6. Null Object パターン")

    app_with = AppWithLogger(RealLogger())
    app_without = AppWithLogger()  # logger=None -> NullLogger

    demo("With logger   ", app_with.do_work())
    demo("Without logger", app_without.do_work())

    point("Null Object により 'if logger is not None' が不要になる。")
    point("Optional を使わず、常に有効なオブジェクトを保証する。")


# ============================================================
# 5. 並行処理パターン (Concurrency Patterns)
# ============================================================

# --------------------------------------------------
# 5-1. Producer-Consumer
# --------------------------------------------------

def demo_producer_consumer() -> None:
    subsection("5-1. Producer-Consumer パターン")

    q: queue.Queue = queue.Queue(maxsize=5)
    results: List[str] = []
    stop_event = threading.Event()

    def producer(name: str, items: List[str]) -> None:
        for item in items:
            q.put(item)
            results.append(f"Produced: {item}")

    def consumer(name: str) -> None:
        while not stop_event.is_set() or not q.empty():
            try:
                item = q.get(timeout=0.1)
                results.append(f"Consumed: {item}")
                q.task_done()
            except queue.Empty:
                continue

    producer_thread = threading.Thread(target=producer, args=("P1", ["A", "B", "C", "D"]))
    consumer_thread = threading.Thread(target=consumer, args=("C1",))

    consumer_thread.start()
    producer_thread.start()

    producer_thread.join()
    q.join()  # 全アイテムが処理されるまで待つ
    stop_event.set()
    consumer_thread.join()

    for r in results:
        demo("event", r)

    question("Producer が Consumer より速い場合、何が起きるか？ maxsize の役割は？")


# --------------------------------------------------
# 5-2. Thread Pool
# --------------------------------------------------

def demo_thread_pool() -> None:
    subsection("5-2. Thread Pool (concurrent.futures)")

    def heavy_task(n: int) -> str:
        # CPU-bound 処理のシミュレーション
        total = sum(range(n * 10000))
        return f"Task({n}): sum={total}"

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(heavy_task, i): i for i in range(5)}
        for future in concurrent.futures.as_completed(futures):
            task_id = futures[future]
            demo(f"completed task {task_id}", future.result())

    question("ThreadPoolExecutor vs ProcessPoolExecutor の使い分けは？GIL の影響は？")


# --------------------------------------------------
# 5-3. Read-Write Lock
# --------------------------------------------------

class ReadWriteLock:
    """Readers-Writer Lock ── 複数の読み取りは同時OK、書き込みは排他。"""
    def __init__(self) -> None:
        self._readers = 0
        self._readers_lock = threading.Lock()
        self._write_lock = threading.Lock()

    def acquire_read(self) -> None:
        with self._readers_lock:
            self._readers += 1
            if self._readers == 1:
                self._write_lock.acquire()

    def release_read(self) -> None:
        with self._readers_lock:
            self._readers -= 1
            if self._readers == 0:
                self._write_lock.release()

    def acquire_write(self) -> None:
        self._write_lock.acquire()

    def release_write(self) -> None:
        self._write_lock.release()


class SharedData:
    def __init__(self) -> None:
        self.data: Dict[str, int] = {"counter": 0}
        self.lock = ReadWriteLock()


def demo_read_write_lock() -> None:
    subsection("5-3. Read-Write Lock")

    shared = SharedData()
    log: List[str] = []

    def reader(name: str) -> None:
        shared.lock.acquire_read()
        value = shared.data["counter"]
        log.append(f"{name} read: {value}")
        shared.lock.release_read()

    def writer(name: str, value: int) -> None:
        shared.lock.acquire_write()
        shared.data["counter"] = value
        log.append(f"{name} wrote: {value}")
        shared.lock.release_write()

    threads = [
        threading.Thread(target=reader, args=("R1",)),
        threading.Thread(target=reader, args=("R2",)),
        threading.Thread(target=writer, args=("W1", 42)),
        threading.Thread(target=reader, args=("R3",)),
        threading.Thread(target=writer, args=("W2", 100)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    for entry in log:
        demo("rw_lock", entry)

    point("複数 Reader は同時にアクセスできるが、Writer はすべてを排他する。")


# --------------------------------------------------
# 5-4. Future/Promise
# --------------------------------------------------

def demo_future_promise() -> None:
    subsection("5-4. Future/Promise パターン")

    def fetch_user(user_id: int) -> Dict[str, Any]:
        time.sleep(0.01)
        return {"id": user_id, "name": f"User_{user_id}"}

    def fetch_orders(user_id: int) -> List[Dict[str, Any]]:
        time.sleep(0.01)
        return [{"order_id": i, "amount": i * 100} for i in range(1, 3)]

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        # 非同期に2つのタスクを開始
        user_future = executor.submit(fetch_user, 1)
        orders_future = executor.submit(fetch_orders, 1)

        # 結果を待つ
        user = user_future.result(timeout=5)
        orders = orders_future.result(timeout=5)

        demo("user   ", user)
        demo("orders ", orders)

    # コールバック
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        callback_results: List[str] = []

        def on_complete(future: concurrent.futures.Future) -> None:
            callback_results.append(f"Callback received: {future.result()}")

        f = executor.submit(fetch_user, 42)
        f.add_done_callback(on_complete)
        f.result()  # 完了を待つ
        # コールバック実行を少し待つ
        time.sleep(0.05)
        demo("callback", callback_results)

    question("Future.result() はブロッキング。非同期IO (asyncio) との違いは？")


# --------------------------------------------------
# 5-5. Actor Model
# --------------------------------------------------

class Actor:
    """シンプルなアクターシステム。
    各アクターは独自のスレッドとメールボックス (queue) を持つ。
    メッセージパッシングで通信し、共有状態を持たない。
    """
    def __init__(self, name: str) -> None:
        self.name = name
        self._mailbox: queue.Queue = queue.Queue()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.processed: List[str] = []

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)

    def send(self, message: Any) -> None:
        self._mailbox.put(message)

    def _run(self) -> None:
        while self._running:
            try:
                message = self._mailbox.get(timeout=0.1)
                self.on_receive(message)
                self._mailbox.task_done()
            except queue.Empty:
                continue

    def on_receive(self, message: Any) -> None:
        self.processed.append(f"{self.name} received: {message}")


class CounterActor(Actor):
    """状態を持つアクター。"""
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.count = 0

    def on_receive(self, message: Any) -> None:
        if message == "increment":
            self.count += 1
        elif message == "decrement":
            self.count -= 1
        self.processed.append(f"{self.name}: count={self.count}")


def demo_actor_model() -> None:
    subsection("5-5. Actor Model")

    counter = CounterActor("CounterActor")
    counter.start()

    for _ in range(3):
        counter.send("increment")
    counter.send("decrement")

    # メッセージが処理されるまで少し待つ
    time.sleep(0.3)
    counter.stop()

    for entry in counter.processed:
        demo("actor", entry)

    point("Actor Model: 共有メモリではなくメッセージパッシングで並行性を実現。")
    point("Erlang/Akka の基本概念。Python では asyncio + actor ライブラリで実現可能。")
    question("Actor Model と Producer-Consumer の違いは？")


# ============================================================
# 6. アンチパターン (Anti-Patterns)
# ============================================================

def demo_anti_patterns() -> None:
    subsection("6. アンチパターン")

    print("    --- God Object / God Class ---")
    point("臭い: 1クラスに数千行、あらゆる責務が混在")
    point("例:  class Application が DB接続、UI描画、ビジネスロジック、ログを全部持つ")
    point("解決: Single Responsibility Principle に従い分割")
    print()

    # Bad example
    class GodObject:
        """アンチパターンの例 ── 何でもやるクラス。"""
        def __init__(self) -> None:
            self.users: List[str] = []
            self.orders: List[str] = []
            self.logs: List[str] = []

        def add_user(self, name: str) -> None:
            self.users.append(name)
            self.logs.append(f"Added user: {name}")

        def place_order(self, order: str) -> None:
            self.orders.append(order)
            self.logs.append(f"Placed order: {order}")

        def generate_report(self) -> str:
            return f"Users: {len(self.users)}, Orders: {len(self.orders)}"

        def send_email(self, to: str, body: str) -> str:
            self.logs.append(f"Email to {to}")
            return f"Sent to {to}"

    god = GodObject()
    god.add_user("Alice")
    god.place_order("ORD-1")
    demo("GodObject report", god.generate_report())
    point("^ このクラスは4つの責務を持っている。分割すべき。")

    print()
    print("    --- Spaghetti Code ---")
    point("臭い: 深いネスト、goto 的なフロー、関数が200行以上")
    point("解決: 関数分割、Early Return、Guard Clause")

    # Bad example
    def spaghetti_process(data: Dict) -> str:
        """スパゲッティの例。"""
        if data:
            if "type" in data:
                if data["type"] == "A":
                    if "value" in data:
                        if data["value"] > 0:
                            return "Processed A"
                        else:
                            return "Invalid A value"
                    else:
                        return "Missing value"
                else:
                    return "Unknown type"
            else:
                return "No type"
        else:
            return "No data"

    # Clean version
    def clean_process(data: Dict) -> str:
        """Guard Clause で改善した版。"""
        if not data:
            return "No data"
        if "type" not in data:
            return "No type"
        if data["type"] != "A":
            return "Unknown type"
        if "value" not in data:
            return "Missing value"
        if data["value"] <= 0:
            return "Invalid A value"
        return "Processed A"

    demo("spaghetti", spaghetti_process({"type": "A", "value": 5}))
    demo("clean    ", clean_process({"type": "A", "value": 5}))
    point("Guard Clause でネストを排除。読みやすさが劇的に向上。")

    print()
    print("    --- Lava Flow (死んだコードの堆積) ---")
    point("臭い: コメントアウトされたコード、使われていない関数、'TODO: remove' が3年前")
    point("解決: バージョン管理を信頼し、不要なコードは削除する")
    point("      CI に dead code 検出ツール (vulture 等) を導入")

    print()
    print("    --- Golden Hammer ---")
    point("臭い: 「すべてをマイクロサービスにしよう」「すべてを NoSQL にしよう」")
    point("解決: 問題に適した技術を選択する。トレードオフを明確にする。")
    point("例:  月間100リクエストのサービスに Kubernetes は Golden Hammer")

    print()
    print("    --- Premature Optimization ---")
    point("臭い: プロファイリングなしで最適化、読みにくいコード")
    point("Donald Knuth: 'Premature optimization is the root of all evil'")
    point("解決: 1. まず正しく動かす 2. プロファイリング 3. ボトルネックのみ最適化")
    print()

    task("自分のプロジェクトで God Object や Lava Flow がないか探してみよう。")


# ============================================================
# 7. SOLID原則とパターンの関係
# ============================================================

def demo_solid() -> None:
    subsection("7. SOLID原則とパターンの関係")

    # --- S: Single Responsibility ---
    print("    [S] Single Responsibility Principle")
    point("1クラス = 1つの変更理由")

    class UserValidator:
        def validate(self, name: str, email: str) -> bool:
            return bool(name) and "@" in email

    class UserPersistence:
        def save(self, name: str, email: str) -> str:
            return f"Saved: {name}"

    class UserNotifier:
        def notify(self, email: str) -> str:
            return f"Notified: {email}"

    # 3つの責務が3つのクラスに分離
    v = UserValidator()
    p = UserPersistence()
    n = UserNotifier()
    if v.validate("Yuta", "yuta@example.com"):
        demo("SRP", f"{p.save('Yuta', 'yuta@example.com')} -> {n.notify('yuta@example.com')}")

    # --- O: Open/Closed ---
    print()
    print("    [O] Open/Closed Principle")
    point("拡張に対して開いている、修正に対して閉じている")
    point("Strategy パターンで新しいアルゴリズムを追加しても既存コードを変更しない")
    point("Decorator パターンで新しい機能を追加しても元のクラスを変更しない")

    class Shape(abc.ABC):
        @abc.abstractmethod
        def area(self) -> float: ...

    class Circle(Shape):
        def __init__(self, radius: float) -> None:
            self.radius = radius
        def area(self) -> float:
            return 3.14159 * self.radius ** 2

    class Rectangle(Shape):
        def __init__(self, w: float, h: float) -> None:
            self.w, self.h = w, h
        def area(self) -> float:
            return self.w * self.h

    # 新しい Shape を追加しても AreaCalculator は変更不要
    shapes: List[Shape] = [Circle(5), Rectangle(3, 4)]
    total = sum(s.area() for s in shapes)
    demo("OCP total area", f"{total:.2f}")

    # --- L: Liskov Substitution ---
    print()
    print("    [L] Liskov Substitution Principle")
    point("サブタイプは親タイプと置き換え可能でなければならない")
    point("違反例: Rectangle を継承した Square で setWidth が setHeight も変える")

    class Bird(abc.ABC):
        @abc.abstractmethod
        def move(self) -> str: ...

    class FlyingBird(Bird):
        def move(self) -> str:
            return "flying"

    class Penguin(Bird):
        def move(self) -> str:
            return "walking"  # fly() を持たない ── LSP を守っている

    birds: List[Bird] = [FlyingBird(), Penguin()]
    for b in birds:
        demo("LSP bird.move()", b.move())

    # --- I: Interface Segregation ---
    print()
    print("    [I] Interface Segregation Principle")
    point("クライアントが使わないメソッドに依存すべきでない")

    class Readable(Protocol):
        def read(self) -> str: ...

    class Writable(Protocol):
        def write(self, data: str) -> None: ...

    class ReadOnlyFile:
        def __init__(self, content: str) -> None:
            self._content = content
        def read(self) -> str:
            return self._content
        # write は持たない ── ISP を守っている

    rof = ReadOnlyFile("read-only content")
    demo("ISP read", rof.read())

    # --- D: Dependency Inversion ---
    print()
    print("    [D] Dependency Inversion Principle")
    point("上位モジュールは下位モジュールに依存しない。両者は抽象に依存する。")
    point("Repository パターンが典型例: ビジネスロジックは Repository 抽象に依存")

    # マッピング表
    print()
    print("    SOLID と パターンの対応:")
    mapping = [
        ("S - Single Responsibility", "Facade, Command, Mediator"),
        ("O - Open/Closed          ", "Strategy, Decorator, Template Method"),
        ("L - Liskov Substitution   ", "Factory Method, State"),
        ("I - Interface Segregation ", "Adapter, Proxy, Protocol"),
        ("D - Dependency Inversion  ", "Repository, DI, Abstract Factory"),
    ]
    for principle, patterns in mapping:
        demo(principle, patterns)

    question("SOLID を全部守ったコードは本当に良いコードか？Over-engineering のリスクは？")


# ============================================================
# 8. 面接での使い方
# ============================================================

def demo_interview_guide() -> None:
    subsection("8. 面接での使い方")

    print("    --- パターン選択の思考フレームワーク ---")
    print()
    point("Step 1: 問題の種類を特定する")
    point("  - オブジェクト生成の複雑さ? -> 生成パターン")
    point("  - クラス間の関係の整理?      -> 構造パターン")
    point("  - オブジェクト間の通信?      -> 振る舞いパターン")
    print()

    point("Step 2: 制約を確認する")
    point("  - スケーラビリティ要件は？")
    point("  - チームの規模と経験レベルは？")
    point("  - 変更の頻度が高い箇所は？")
    print()

    point("Step 3: パターン選択の説明テンプレート")
    print()
    print('    "この問題では [問題の説明] が課題です。')
    print('     [パターン名] を使うことで、')
    print('     [具体的なメリット] が得られます。')
    print('     トレードオフとして [デメリット] がありますが、')
    print('     [なぜ許容できるか] の理由で適切だと考えます。"')
    print()

    # 実例
    print("    --- 具体的な回答例 ---")
    print()
    print("    Q: 通知システムを設計してください。")
    print("    A: Observer/Pub-Sub パターンを採用します。")
    point("理由: 通知の種類 (email, push, SMS) が今後増える可能性が高い")
    point("メリット: 新しい通知チャネル追加時に既存コード変更不要 (OCP)")
    point("トレードオフ: イベントの流れが追いにくくなる")
    point("対策: イベントカタログと監視ダッシュボードで可視化")
    print()

    print("    Q: 複数の支払い方法をサポートしてください。")
    print("    A: Strategy パターンを採用します。")
    point("理由: 支払い方法ごとのロジックが独立している")
    point("メリット: 新しい支払い方法を追加するだけで拡張可能")
    point("if-else との比較: 支払い方法が5つ以上なら Strategy が保守性で勝る")
    print()

    print("    --- Over-engineering vs Under-engineering ---")
    print()
    point("Over-engineering の兆候:")
    point("  - 「将来的に必要になるかも」で3層の抽象化")
    point("  - 2つしかないバリエーションに Abstract Factory")
    point("  - 変更されることのない箇所への Strategy")
    print()
    point("Under-engineering の兆候:")
    point("  - 同じ条件分岐が3箇所以上にコピペ")
    point("  - 新機能追加のたびに既存テストが壊れる")
    point("  - 1ファイルが1000行を超えて成長し続けている")
    print()
    point("判断基準: YAGNI (You Ain't Gonna Need It)")
    point("  - 今の要件に必要か？ -> YES なら導入")
    point("  - 近い将来(1-2スプリント)確実に必要？ -> YES なら導入")
    point("  - いつか必要かも？ -> NO。必要になったらリファクタ")
    print()

    task("自分のプロジェクトの1機能を選び、どのパターンが適用可能か分析してみよう。")
    task("パターン選択の説明テンプレートを使って、チームメイトに説明する練習をしよう。")


# ============================================================
# メイン実行
# ============================================================

def main() -> None:
    print()
    print("=" * 70)
    print("  Design Patterns 完全ガイド")
    print("  FAANG Tech Lead / PM を目指すエンジニアのために")
    print("=" * 70)
    print()
    print("  GoF 23パターンの暗記ではなく、")
    print("  「なぜこの構造が必要になるのか」を体で理解する。")
    print()

    # --- 1. 生成パターン ---
    section("1. 生成パターン (Creational Patterns)")
    demo_singleton()
    demo_factory()
    demo_builder()
    demo_prototype()

    # --- 2. 構造パターン ---
    section("2. 構造パターン (Structural Patterns)")
    demo_adapter()
    demo_decorator()
    demo_proxy()
    demo_facade()
    demo_composite()

    # --- 3. 振る舞いパターン ---
    section("3. 振る舞いパターン (Behavioral Patterns)")
    demo_strategy()
    demo_observer()
    demo_command()
    demo_state()
    demo_template_method()
    demo_chain_of_responsibility()
    demo_iterator()
    demo_mediator()

    # --- 4. モダンパターン ---
    section("4. モダンパターン (Modern/Enterprise Patterns)")
    demo_repository()
    demo_unit_of_work()
    demo_dependency_injection()
    demo_service_locator()
    demo_specification()
    demo_null_object()

    # --- 5. 並行処理パターン ---
    section("5. 並行処理パターン (Concurrency Patterns)")
    demo_producer_consumer()
    demo_thread_pool()
    demo_read_write_lock()
    demo_future_promise()
    demo_actor_model()

    # --- 6. アンチパターン ---
    section("6. アンチパターン (Anti-Patterns)")
    demo_anti_patterns()

    # --- 7. SOLID原則 ---
    section("7. SOLID原則とパターンの関係")
    demo_solid()

    # --- 8. 面接ガイド ---
    section("8. 面接での使い方")
    demo_interview_guide()

    print()
    print("=" * 70)
    print("  完了！全パターンのデモが正常に実行されました。")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
