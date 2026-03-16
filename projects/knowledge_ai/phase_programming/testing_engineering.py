#!/usr/bin/env python3
"""
=============================================================================
テストエンジニアリング完全ガイド — FAANG レベル
=============================================================================
Python stdlib のみ。unittest / random / textwrap 等で
テストピラミッド、テストダブル、TDD、Property-Based Testing、
Mutation Testing、Contract Testing を実装・実演する。

実行: python testing_engineering.py
=============================================================================
"""

import unittest
import random
import ast
import copy
import json
import textwrap
import re
import time
from unittest.mock import MagicMock, patch, call
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
from abc import ABC, abstractmethod
from collections import defaultdict

# ============================================================================
# 0. Tier 別ロードマップ
# ============================================================================
TIERS = {
    "Tier 1 — 最優先 (今すぐ)": [
        "テストピラミッド (Unit 70% / Integration 20% / E2E 10%)",
        "テストダブル 5種 (Dummy, Stub, Spy, Mock, Fake)",
        "TDD Red-Green-Refactor サイクル",
        "Arrange-Act-Assert パターン",
        "unittest / pytest の基本",
    ],
    "Tier 2 — 重要 (3ヶ月以内)": [
        "Property-Based Testing (不変条件で網羅的検証)",
        "Coverage の罠 (Line vs Branch vs Mutation Score)",
        "Object Mother / Test Data Builder",
        "Flaky Test の原因と対策",
        "BDD (Given-When-Then)",
    ],
    "Tier 3 — 差別化 (6ヶ月以内)": [
        "Mutation Testing (テスト品質の計測)",
        "Contract Testing (Consumer-Driven Contract)",
        "テストの独立性設計 (shared state 排除)",
        "パフォーマンステスト基礎",
    ],
    "Tier 4 — 専門性 (1年以内)": [
        "Chaos Engineering 的テスト",
        "Visual Regression Testing",
        "テスト戦略の組織設計",
        "テストインフラ (CI/CD パイプライン最適化)",
    ],
}


# ============================================================================
# 1. テストピラミッド
# ============================================================================
"""
テストピラミッド — Mike Cohn のモデル

         /  E2E  \\          10%  遅い・脆い・高コスト
        / ——————— \\
       / Integration\\       20%  中速・中コスト
      / ———————————— \\
     /   Unit Tests   \\    70%  高速・安定・低コスト
    / —————————————————— \\

ROI 分析:
  Unit:        コスト=低  速度=ms    安定性=高  → ROI 最高
  Integration: コスト=中  速度=sec   安定性=中  → ROI 中
  E2E:         コスト=高  速度=min   安定性=低  → ROI 低 (だが必要)
"""


# --- 1a. Unit Test 対象: ビジネスロジック ----------------------------------
class PricingEngine:
    """商品価格を計算するエンジン"""

    def calculate(self, base_price: float, quantity: int,
                  discount_pct: float = 0) -> float:
        if base_price < 0:
            raise ValueError("base_price は 0 以上")
        if quantity < 1:
            raise ValueError("quantity は 1 以上")
        if not (0 <= discount_pct <= 100):
            raise ValueError("discount_pct は 0〜100")
        subtotal = base_price * quantity
        discount = subtotal * (discount_pct / 100)
        return round(subtotal - discount, 2)

    def bulk_discount(self, base_price: float, quantity: int) -> float:
        """数量割引: 10個以上で10%, 100個以上で20%"""
        if quantity >= 100:
            return self.calculate(base_price, quantity, 20)
        elif quantity >= 10:
            return self.calculate(base_price, quantity, 10)
        return self.calculate(base_price, quantity, 0)


class TestPricingEngine(unittest.TestCase):
    """Unit Test: pytest 風パターンを unittest で再現"""

    def setUp(self):
        """fixture 相当"""
        self.engine = PricingEngine()

    # --- parametrize 相当 (subTest) ---
    def test_calculate_parametrized(self):
        """複数ケースを parametrize 風にテスト"""
        cases = [
            # (base, qty, discount, expected)
            (100, 1, 0, 100.0),
            (100, 5, 10, 450.0),
            (99.99, 3, 50, 149.99),
            (0, 1, 0, 0.0),
        ]
        for base, qty, disc, expected in cases:
            with self.subTest(base=base, qty=qty, disc=disc):
                result = self.engine.calculate(base, qty, disc)
                self.assertAlmostEqual(result, expected, places=2)

    def test_calculate_invalid_inputs(self):
        """異常系: ValueError が出ることを検証"""
        with self.assertRaises(ValueError):
            self.engine.calculate(-1, 1)
        with self.assertRaises(ValueError):
            self.engine.calculate(100, 0)
        with self.assertRaises(ValueError):
            self.engine.calculate(100, 1, 150)

    def test_bulk_discount_tiers(self):
        """数量割引の境界値テスト"""
        self.assertEqual(self.engine.bulk_discount(100, 9), 900.0)    # 割引なし
        self.assertEqual(self.engine.bulk_discount(100, 10), 900.0)   # 10% off
        self.assertEqual(self.engine.bulk_discount(100, 100), 8000.0) # 20% off


# --- 1b. Integration Test 対象: 外部依存 ---------------------------------
class UserRepository:
    """DB アクセス層 (本来は PostgreSQL 等)"""
    def __init__(self, db_connection):
        self.db = db_connection

    def find_by_id(self, user_id: int) -> Optional[dict]:
        return self.db.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        )

    def save(self, user: dict) -> int:
        return self.db.execute(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            (user["name"], user["email"])
        )


class InMemoryDB:
    """Fake DB — Integration Test 用の簡易実装"""
    def __init__(self):
        self.users = {}
        self._next_id = 1

    def execute(self, query: str, params: tuple = ()):
        if query.startswith("SELECT"):
            user_id = params[0]
            return self.users.get(user_id)
        elif query.startswith("INSERT"):
            uid = self._next_id
            self._next_id += 1
            self.users[uid] = {"id": uid, "name": params[0], "email": params[1]}
            return uid
        return None


class TestUserRepositoryIntegration(unittest.TestCase):
    """Integration Test: Fake DB を使ったリポジトリテスト"""

    def setUp(self):
        self.db = InMemoryDB()
        self.repo = UserRepository(self.db)

    def test_save_and_find(self):
        user = {"name": "Alice", "email": "alice@example.com"}
        user_id = self.repo.save(user)
        found = self.repo.find_by_id(user_id)
        self.assertIsNotNone(found)
        self.assertEqual(found["name"], "Alice")

    def test_find_nonexistent(self):
        result = self.repo.find_by_id(9999)
        self.assertIsNone(result)


# --- 1c. E2E Test: シナリオテスト -----------------------------------------
class OrderService:
    """注文サービス — 複数レイヤーをまたぐ"""
    def __init__(self, pricing: PricingEngine, user_repo: UserRepository,
                 notifier=None):
        self.pricing = pricing
        self.user_repo = user_repo
        self.notifier = notifier

    def place_order(self, user_id: int, item_price: float,
                    quantity: int) -> dict:
        user = self.user_repo.find_by_id(user_id)
        if not user:
            raise ValueError("ユーザーが見つかりません")
        total = self.pricing.bulk_discount(item_price, quantity)
        order = {"user": user["name"], "total": total, "status": "confirmed"}
        if self.notifier:
            self.notifier.send(user["email"], f"注文確定: ¥{total}")
        return order


class TestOrderE2E(unittest.TestCase):
    """E2E Test: 注文フロー全体を通しでテスト"""

    def test_full_order_flow(self):
        # Arrange — 全レイヤーを構築
        db = InMemoryDB()
        repo = UserRepository(db)
        notifier = MagicMock()
        pricing = PricingEngine()
        service = OrderService(pricing, repo, notifier)

        user_id = repo.save({"name": "Bob", "email": "bob@example.com"})

        # Act
        order = service.place_order(user_id, 500, 20)

        # Assert
        self.assertEqual(order["status"], "confirmed")
        self.assertEqual(order["total"], 9000.0)  # 20個 → 10% off
        notifier.send.assert_called_once()


# ============================================================================
# 2. テストダブル完全ガイド
# ============================================================================

# --- 2a. インターフェース定義 ---
class PaymentGateway(ABC):
    """外部決済サービスのインターフェース"""
    @abstractmethod
    def charge(self, amount: float, card_token: str) -> dict:
        pass

    @abstractmethod
    def refund(self, transaction_id: str) -> bool:
        pass


# --- Dummy: パラメータ埋めにだけ使う。中身は空 ---
class DummyPaymentGateway(PaymentGateway):
    """Dummy: テスト対象が決済を使わないケースで渡す"""
    def charge(self, amount, card_token):
        raise NotImplementedError("Dummy — 呼ばれるべきでない")

    def refund(self, transaction_id):
        raise NotImplementedError("Dummy — 呼ばれるべきでない")


# --- Stub: 固定値を返す ---
class StubPaymentGateway(PaymentGateway):
    """Stub: 常に成功を返す"""
    def charge(self, amount, card_token):
        return {"transaction_id": "txn_stub_001", "status": "success"}

    def refund(self, transaction_id):
        return True


# --- Spy: 呼び出しを記録 ---
class SpyPaymentGateway(PaymentGateway):
    """Spy: 呼び出し回数・引数を記録"""
    def __init__(self):
        self.charge_calls: List[Tuple[float, str]] = []
        self.refund_calls: List[str] = []

    def charge(self, amount, card_token):
        self.charge_calls.append((amount, card_token))
        return {"transaction_id": f"txn_spy_{len(self.charge_calls)}", "status": "success"}

    def refund(self, transaction_id):
        self.refund_calls.append(transaction_id)
        return True


# --- Mock: 期待値を設定して検証 ---
class MockPaymentGateway(PaymentGateway):
    """Mock: 期待される呼び出しを事前設定 → verify で検証"""
    def __init__(self):
        self._expected_charges: List[Tuple[float, str]] = []
        self._actual_charges: List[Tuple[float, str]] = []

    def expect_charge(self, amount: float, card_token: str):
        self._expected_charges.append((amount, card_token))

    def charge(self, amount, card_token):
        self._actual_charges.append((amount, card_token))
        return {"transaction_id": "txn_mock", "status": "success"}

    def refund(self, transaction_id):
        return True

    def verify(self) -> bool:
        return self._expected_charges == self._actual_charges


# --- Fake: 簡易実装 (InMemory) ---
class FakePaymentGateway(PaymentGateway):
    """Fake: メモリ上で残高管理する簡易決済"""
    def __init__(self, initial_balance: float = 10000):
        self.balance = initial_balance
        self.transactions: Dict[str, dict] = {}

    def charge(self, amount, card_token):
        if amount > self.balance:
            return {"transaction_id": None, "status": "declined"}
        txn_id = f"txn_fake_{len(self.transactions) + 1}"
        self.balance -= amount
        self.transactions[txn_id] = {"amount": amount, "refunded": False}
        return {"transaction_id": txn_id, "status": "success"}

    def refund(self, transaction_id):
        txn = self.transactions.get(transaction_id)
        if not txn or txn["refunded"]:
            return False
        self.balance += txn["amount"]
        txn["refunded"] = True
        return True


class TestTestDoubles(unittest.TestCase):
    """テストダブル 5種の動作確認"""

    def test_stub_always_succeeds(self):
        gw = StubPaymentGateway()
        result = gw.charge(9999, "tok_any")
        self.assertEqual(result["status"], "success")

    def test_spy_records_calls(self):
        gw = SpyPaymentGateway()
        gw.charge(100, "tok_a")
        gw.charge(200, "tok_b")
        self.assertEqual(len(gw.charge_calls), 2)
        self.assertEqual(gw.charge_calls[0], (100, "tok_a"))

    def test_mock_verifies_expectations(self):
        gw = MockPaymentGateway()
        gw.expect_charge(500, "tok_x")
        gw.charge(500, "tok_x")
        self.assertTrue(gw.verify())

    def test_mock_fails_on_wrong_call(self):
        gw = MockPaymentGateway()
        gw.expect_charge(500, "tok_x")
        gw.charge(999, "tok_y")  # 期待と異なる
        self.assertFalse(gw.verify())

    def test_fake_manages_balance(self):
        gw = FakePaymentGateway(initial_balance=1000)
        r1 = gw.charge(600, "tok")
        self.assertEqual(r1["status"], "success")
        self.assertEqual(gw.balance, 400)

        r2 = gw.charge(500, "tok")  # 残高不足
        self.assertEqual(r2["status"], "declined")

        gw.refund(r1["transaction_id"])
        self.assertEqual(gw.balance, 1000)


# ============================================================================
# 3. TDD Red-Green-Refactor — Stack を TDD で作る
# ============================================================================
"""
TDD サイクル:
  1. RED    — 失敗するテストを書く
  2. GREEN  — 最小限のコードで通す
  3. REFACTOR — 重複を除去、設計改善
"""


# --- Step 1: RED → テストを先に書く ---
class TestStack(unittest.TestCase):
    """Stack の TDD テスト (全ステップのテストをまとめて記載)"""

    def test_new_stack_is_empty(self):
        """RED→GREEN: Step 1"""
        s = Stack()
        self.assertTrue(s.is_empty())
        self.assertEqual(len(s), 0)

    def test_push_makes_non_empty(self):
        """RED→GREEN: Step 2"""
        s = Stack()
        s.push(42)
        self.assertFalse(s.is_empty())
        self.assertEqual(len(s), 1)

    def test_pop_returns_last_pushed(self):
        """RED→GREEN: Step 3 — LIFO の検証"""
        s = Stack()
        s.push("a")
        s.push("b")
        self.assertEqual(s.pop(), "b")
        self.assertEqual(s.pop(), "a")

    def test_pop_empty_raises(self):
        """RED→GREEN: Step 4 — 異常系"""
        s = Stack()
        with self.assertRaises(IndexError):
            s.pop()

    def test_peek_does_not_remove(self):
        """RED→GREEN: Step 5"""
        s = Stack()
        s.push(1)
        self.assertEqual(s.peek(), 1)
        self.assertEqual(len(s), 1)  # 要素は残る


# --- Step 2: GREEN → 実装 ---
class Stack:
    """TDD で駆動された Stack 実装"""

    def __init__(self):
        self._items: list = []

    def push(self, item: Any) -> None:
        self._items.append(item)

    def pop(self) -> Any:
        if self.is_empty():
            raise IndexError("pop from empty stack")
        return self._items.pop()

    def peek(self) -> Any:
        if self.is_empty():
            raise IndexError("peek from empty stack")
        return self._items[-1]

    def is_empty(self) -> bool:
        return len(self._items) == 0

    def __len__(self) -> int:
        return len(self._items)

    # --- Step 3: REFACTOR → イテラブル対応を追加 ---
    def __iter__(self):
        return reversed(self._items)

    def __repr__(self):
        return f"Stack({list(reversed(self._items))})"


# ============================================================================
# 4. Property-Based Testing
# ============================================================================
class PropertyBasedTester:
    """
    Hypothesis 風の Property-Based Testing を stdlib で実装。
    ランダム入力 → 不変条件 (property) を検証 → 違反時に shrink。
    """

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.results: List[dict] = []

    def generate_int_list(self, max_len: int = 20,
                          value_range: Tuple[int, int] = (-100, 100)) -> list:
        """ランダムな整数リストを生成"""
        length = self.rng.randint(0, max_len)
        return [self.rng.randint(*value_range) for _ in range(length)]

    def generate_string(self, max_len: int = 30) -> str:
        """ランダムな文字列を生成"""
        chars = "abcdefghijklmnopqrstuvwxyz0123456789 "
        length = self.rng.randint(0, max_len)
        return "".join(self.rng.choice(chars) for _ in range(length))

    def shrink_list(self, lst: list) -> List[list]:
        """
        Shrinking: 反例が見つかったら、最小の反例を探す。
        戦略: 要素を減らす / 値を小さくする
        """
        candidates = []
        # 要素を1つずつ除去
        for i in range(len(lst)):
            candidates.append(lst[:i] + lst[i + 1:])
        # 値を半分にする
        for i in range(len(lst)):
            if lst[i] != 0:
                shrunk = lst[:]
                shrunk[i] = lst[i] // 2
                candidates.append(shrunk)
        # 空リスト
        if lst:
            candidates.append([])
        return candidates

    def check_property(self, name: str, generator: Callable,
                       prop: Callable[[Any], bool],
                       num_tests: int = 100) -> dict:
        """プロパティを num_tests 回検証"""
        for i in range(num_tests):
            inp = generator()
            try:
                if not prop(inp):
                    # 反例発見 → shrink
                    minimal = self._find_minimal(inp, prop)
                    result = {
                        "property": name, "status": "FAILED",
                        "counterexample": inp, "shrunk_to": minimal,
                        "iterations": i + 1,
                    }
                    self.results.append(result)
                    return result
            except Exception as e:
                result = {
                    "property": name, "status": "ERROR",
                    "counterexample": inp, "error": str(e),
                    "iterations": i + 1,
                }
                self.results.append(result)
                return result

        result = {"property": name, "status": "PASSED", "iterations": num_tests}
        self.results.append(result)
        return result

    def _find_minimal(self, failing_input: Any,
                      prop: Callable[[Any], bool],
                      max_shrinks: int = 100) -> Any:
        """shrinking で最小反例を探索（max_shrinks で無限ループ防止）"""
        if not isinstance(failing_input, list):
            return failing_input
        current = failing_input
        shrink_count = 0
        improved = True
        while improved and shrink_count < max_shrinks:
            improved = False
            for candidate in self.shrink_list(current):
                if candidate == current:
                    continue
                shrink_count += 1
                try:
                    if not prop(candidate):
                        current = candidate
                        improved = True
                        break
                except Exception:
                    current = candidate
                    improved = True
                    break
        return current


def demo_property_based_testing():
    """Property-Based Testing のデモ"""
    print("\n" + "=" * 60)
    print("4. Property-Based Testing デモ")
    print("=" * 60)

    tester = PropertyBasedTester(seed=42)

    # --- プロパティ 1: sorted の冪等性 ---
    r1 = tester.check_property(
        "sort は冪等 (2回 sort しても結果同じ)",
        tester.generate_int_list,
        lambda xs: sorted(sorted(xs)) == sorted(xs),
    )
    print(f"  {r1['property']}: {r1['status']}")

    # --- プロパティ 2: sorted の長さ保存 ---
    r2 = tester.check_property(
        "sort は長さを保存する",
        tester.generate_int_list,
        lambda xs: len(sorted(xs)) == len(xs),
    )
    print(f"  {r2['property']}: {r2['status']}")

    # --- プロパティ 3: sorted の要素保存 ---
    r3 = tester.check_property(
        "sort は要素を保存する (multiset 一致)",
        tester.generate_int_list,
        lambda xs: sorted(sorted(xs)) == sorted(xs),
    )
    print(f"  {r3['property']}: {r3['status']}")

    # --- プロパティ 4: reverse の involution ---
    r4 = tester.check_property(
        "reverse(reverse(xs)) == xs",
        tester.generate_int_list,
        lambda xs: list(reversed(list(reversed(xs)))) == xs,
    )
    print(f"  {r4['property']}: {r4['status']}")

    # --- プロパティ 5: 意図的に失敗するプロパティ ---
    def buggy_abs(xs):
        """バグ: 負の値を正しく扱えない偽 abs"""
        return all(x >= 0 for x in xs)  # 負の値があれば失敗

    r5 = tester.check_property(
        "全要素が非負 (これは失敗する)",
        tester.generate_int_list,
        buggy_abs,
    )
    print(f"  {r5['property']}: {r5['status']}")
    if r5["status"] == "FAILED":
        print(f"    反例: {r5['counterexample']}")
        print(f"    shrink 後: {r5['shrunk_to']}")


# ============================================================================
# 5. Mutation Testing
# ============================================================================
class MutationTester:
    """
    Mutation Testing ミニ実装。
    ソースコードの AST を変異させ、テストが検出できるか計測。
    """

    # --- 変異オペレーター定義 ---
    MUTATIONS = {
        "negate_comparison": {
            ast.Gt: ast.LtE,   # >  → <=
            ast.Lt: ast.GtE,   # <  → >=
            ast.Eq: ast.NotEq, # == → !=
            ast.GtE: ast.Lt,   # >= → <
            ast.LtE: ast.Gt,   # <= → >
        },
        "swap_arithmetic": {
            ast.Add: ast.Sub,  # + → -
            ast.Sub: ast.Add,  # - → +
            ast.Mult: ast.Div, # * → /
        },
    }

    @staticmethod
    def apply_comparison_mutation(source: str) -> List[Tuple[str, str]]:
        """比較演算子を反転した変異体を生成"""
        mutants = []
        # 簡易実装: 文字列レベルで置換
        replacements = [
            (">=", "< ", "comparison: >= → <"),
            ("<=", "> ", "comparison: <= → >"),
            ("==", "!=", "comparison: == → !="),
            ("!=", "==", "comparison: != → =="),
        ]
        for old, new, desc in replacements:
            if old in source:
                mutated = source.replace(old, new, 1)
                mutants.append((mutated, desc))
        return mutants

    @staticmethod
    def apply_arithmetic_mutation(source: str) -> List[Tuple[str, str]]:
        """算術演算子を変更した変異体を生成"""
        mutants = []
        # +/- の交換 (文字列連結の + を避けるため数値コンテキストのみ)
        replacements = [
            (" + ", " - ", "arithmetic: + → -"),
            (" - ", " + ", "arithmetic: - → +"),
            (" * ", " / ", "arithmetic: * → /"),
        ]
        for old, new, desc in replacements:
            if old in source:
                mutated = source.replace(old, new, 1)
                mutants.append((mutated, desc))
        return mutants

    @staticmethod
    def calculate_mutation_score(killed: int, total: int) -> float:
        """Mutation Score = killed mutants / total mutants"""
        if total == 0:
            return 1.0
        return killed / total


def demo_mutation_testing():
    """Mutation Testing の概念デモ"""
    print("\n" + "=" * 60)
    print("5. Mutation Testing デモ")
    print("=" * 60)

    # テスト対象関数
    def is_adult(age: int) -> bool:
        return age >= 18

    # テストスイート
    def test_suite(func):
        """テストを実行し、全パスなら True"""
        try:
            assert func(20) == True,  "20歳は成人"
            assert func(18) == True,  "18歳は成人"
            assert func(17) == False, "17歳は未成年"
            assert func(0) == False,  "0歳は未成年"
            return True
        except (AssertionError, Exception):
            return False

    # 変異体を手動で作成してテスト
    mutants = [
        ("age > 18",  lambda age: age > 18),       # >= を > に変更
        ("age >= 17", lambda age: age >= 17),       # 18 を 17 に変更
        ("age <= 18", lambda age: age <= 18),       # >= を <= に反転
        ("age >= 19", lambda age: age >= 19),       # 18 を 19 に変更
        ("return True", lambda age: True),          # 常に True を返す
    ]

    killed = 0
    total = len(mutants)

    for desc, mutant_func in mutants:
        try:
            # テストスイートが変異体を検出(テスト失敗)できるか?
            all_pass = True
            try:
                assert mutant_func(20) == True
                assert mutant_func(18) == True
                assert mutant_func(17) == False
                assert mutant_func(0) == False
            except AssertionError:
                all_pass = False

            if not all_pass:
                killed += 1
                status = "KILLED   (テストが検出)"
            else:
                status = "SURVIVED (テストが見逃し!)"
        except Exception:
            killed += 1
            status = "KILLED   (例外で検出)"

        print(f"  変異: {desc:20s} → {status}")

    score = MutationTester.calculate_mutation_score(killed, total)
    print(f"\n  Mutation Score: {killed}/{total} = {score:.0%}")
    print(f"  → {'良好' if score >= 0.8 else '要改善: テスト追加が必要'}")


# ============================================================================
# 6. Contract Testing (Consumer-Driven Contract)
# ============================================================================
@dataclass
class ContractExpectation:
    """API 契約の1つの期待値"""
    method: str                    # GET, POST, etc.
    path: str                      # /api/users/1
    expected_status: int           # 200
    expected_body_keys: List[str]  # ["id", "name", "email"]
    expected_types: Dict[str, type] = field(default_factory=dict)


@dataclass
class Contract:
    """Consumer-Driven Contract"""
    consumer: str                          # 消費者サービス名
    provider: str                          # 提供者サービス名
    expectations: List[ContractExpectation] = field(default_factory=list)


class ContractVerifier:
    """Provider が契約を満たすか検証"""

    def __init__(self, provider_handler: Callable):
        self.handler = provider_handler  # (method, path) → (status, body)

    def verify(self, contract: Contract) -> List[dict]:
        """全契約を検証し、結果を返す"""
        results = []
        for exp in contract.expectations:
            status, body = self.handler(exp.method, exp.path)
            errors = []

            # ステータスコード検証
            if status != exp.expected_status:
                errors.append(
                    f"Status: expected {exp.expected_status}, got {status}"
                )

            # レスポンスキー検証
            if isinstance(body, dict):
                missing = set(exp.expected_body_keys) - set(body.keys())
                if missing:
                    errors.append(f"Missing keys: {missing}")

                # 型検証
                for key, expected_type in exp.expected_types.items():
                    if key in body and not isinstance(body[key], expected_type):
                        errors.append(
                            f"Type mismatch: {key} expected "
                            f"{expected_type.__name__}, "
                            f"got {type(body[key]).__name__}"
                        )

            results.append({
                "endpoint": f"{exp.method} {exp.path}",
                "passed": len(errors) == 0,
                "errors": errors,
            })
        return results


# --- 後方互換性チェッカー ---
class BackwardCompatibilityChecker:
    """API スキーマの後方互換性を検証"""

    @staticmethod
    def check(old_schema: dict, new_schema: dict) -> List[str]:
        """
        後方互換性違反を検出。
        ルール:
          - フィールド削除 → 違反
          - 必須フィールド追加 → 違反
          - 型変更 → 違反
          - オプショナルフィールド追加 → OK
        """
        violations = []

        old_fields = old_schema.get("fields", {})
        new_fields = new_schema.get("fields", {})

        # 削除されたフィールド
        for name in old_fields:
            if name not in new_fields:
                violations.append(f"BREAKING: フィールド '{name}' が削除された")

        # 型変更
        for name in old_fields:
            if name in new_fields:
                if old_fields[name]["type"] != new_fields[name]["type"]:
                    violations.append(
                        f"BREAKING: '{name}' の型が "
                        f"{old_fields[name]['type']} → "
                        f"{new_fields[name]['type']} に変更"
                    )

        # 新しい必須フィールド
        for name in new_fields:
            if name not in old_fields:
                if new_fields[name].get("required", False):
                    violations.append(
                        f"BREAKING: 必須フィールド '{name}' が追加された"
                    )

        return violations


def demo_contract_testing():
    """Contract Testing デモ"""
    print("\n" + "=" * 60)
    print("6. Contract Testing デモ")
    print("=" * 60)

    # --- Provider のモック実装 ---
    def user_service_handler(method, path):
        if method == "GET" and path == "/api/users/1":
            return 200, {"id": 1, "name": "Alice", "email": "alice@example.com"}
        if method == "POST" and path == "/api/users":
            return 201, {"id": 2, "name": "Bob", "email": "bob@example.com"}
        return 404, {"error": "Not found"}

    # --- Consumer が定義する契約 ---
    contract = Contract(
        consumer="OrderService",
        provider="UserService",
        expectations=[
            ContractExpectation(
                method="GET", path="/api/users/1",
                expected_status=200,
                expected_body_keys=["id", "name", "email"],
                expected_types={"id": int, "name": str},
            ),
            ContractExpectation(
                method="POST", path="/api/users",
                expected_status=201,
                expected_body_keys=["id", "name"],
            ),
        ],
    )

    verifier = ContractVerifier(user_service_handler)
    results = verifier.verify(contract)

    print(f"\n  契約: {contract.consumer} → {contract.provider}")
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  [{status}] {r['endpoint']}")
        for e in r["errors"]:
            print(f"         {e}")

    # --- 後方互換性チェック ---
    print("\n  --- 後方互換性チェック ---")
    old_api = {
        "fields": {
            "id":    {"type": "int", "required": True},
            "name":  {"type": "str", "required": True},
            "email": {"type": "str", "required": True},
        }
    }
    new_api_ok = {
        "fields": {
            "id":    {"type": "int", "required": True},
            "name":  {"type": "str", "required": True},
            "email": {"type": "str", "required": True},
            "avatar": {"type": "str", "required": False},  # optional 追加 → OK
        }
    }
    new_api_breaking = {
        "fields": {
            "id":       {"type": "str", "required": True},  # int → str 型変更!
            "name":     {"type": "str", "required": True},
            # email 削除!
            "phone":    {"type": "str", "required": True},   # 必須追加!
        }
    }

    v1 = BackwardCompatibilityChecker.check(old_api, new_api_ok)
    print(f"  v1 → v2 (互換): {len(v1)} 違反 {'(OK)' if not v1 else ''}")

    v2 = BackwardCompatibilityChecker.check(old_api, new_api_breaking)
    print(f"  v1 → v3 (破壊): {len(v2)} 違反")
    for v in v2:
        print(f"    {v}")


# ============================================================================
# 7. テストアーキテクチャ
# ============================================================================

# --- 7a. Arrange-Act-Assert パターン ---
class TestAAA(unittest.TestCase):
    """Arrange-Act-Assert の明示的な3分割"""

    def test_discount_calculation(self):
        # Arrange (準備)
        engine = PricingEngine()
        base_price = 1000
        quantity = 5
        discount = 15

        # Act (実行)
        result = engine.calculate(base_price, quantity, discount)

        # Assert (検証)
        self.assertEqual(result, 4250.0)


# --- 7b. Given-When-Then (BDD) ---
class BDDScenario:
    """BDD スタイルのシナリオ記述ヘルパー"""

    def __init__(self, description: str):
        self.description = description
        self._given_desc = ""
        self._when_desc = ""
        self._then_desc = ""
        self._context: dict = {}
        self._result: Any = None

    def given(self, desc: str, setup: Callable[[], dict]) -> "BDDScenario":
        self._given_desc = desc
        self._context = setup()
        return self

    def when(self, desc: str, action: Callable[[dict], Any]) -> "BDDScenario":
        self._when_desc = desc
        self._result = action(self._context)
        return self

    def then(self, desc: str, assertion: Callable[[Any], bool]) -> bool:
        self._then_desc = desc
        passed = assertion(self._result)
        status = "PASS" if passed else "FAIL"
        return passed


# --- 7c. Object Mother ---
class UserMother:
    """Object Mother: テスト用オブジェクトの生成ファクトリ"""

    @staticmethod
    def default() -> dict:
        return {"id": 1, "name": "Default User", "email": "default@test.com",
                "role": "member", "active": True}

    @staticmethod
    def admin() -> dict:
        user = UserMother.default()
        user.update({"id": 100, "name": "Admin User",
                     "email": "admin@test.com", "role": "admin"})
        return user

    @staticmethod
    def inactive() -> dict:
        user = UserMother.default()
        user.update({"active": False, "name": "Inactive User"})
        return user


# --- 7d. Test Data Builder ---
class UserBuilder:
    """Test Data Builder: メソッドチェーンでテストデータ構築"""

    def __init__(self):
        self._data = {
            "id": 1, "name": "Test User",
            "email": "test@test.com", "role": "member", "active": True,
        }

    def with_name(self, name: str) -> "UserBuilder":
        self._data["name"] = name
        return self

    def with_email(self, email: str) -> "UserBuilder":
        self._data["email"] = email
        return self

    def with_role(self, role: str) -> "UserBuilder":
        self._data["role"] = role
        return self

    def inactive(self) -> "UserBuilder":
        self._data["active"] = False
        return self

    def build(self) -> dict:
        return dict(self._data)


class TestBuilderPattern(unittest.TestCase):
    """Object Mother / Builder のテスト"""

    def test_object_mother(self):
        admin = UserMother.admin()
        self.assertEqual(admin["role"], "admin")

    def test_builder_pattern(self):
        user = (UserBuilder()
                .with_name("Charlie")
                .with_role("admin")
                .inactive()
                .build())
        self.assertEqual(user["name"], "Charlie")
        self.assertEqual(user["role"], "admin")
        self.assertFalse(user["active"])


# --- 7e. Flaky Test の原因と対策 ---
FLAKY_TEST_CAUSES = """
Flaky Test の原因と対策:

1. 時間依存
   原因: datetime.now() をハードコード
   対策: Clock インジェクション / freeze_time

2. 順序依存
   原因: テスト間で共有状態を変更
   対策: setUp/tearDown で状態リセット / テスト独立化

3. 並行性
   原因: マルチスレッドでの非決定的な実行順
   対策: 適切な同期 / 決定的なテスト設計

4. 外部依存
   原因: ネットワーク/DB/ファイルシステムの不安定性
   対策: テストダブル / コンテナ化

5. リソース枯渇
   原因: ポート競合、ディスクフル
   対策: 動的ポート割当 / テスト後のクリーンアップ

6. 浮動小数点
   原因: 0.1 + 0.2 != 0.3
   対策: assertAlmostEqual / Decimal 使用
"""


# ============================================================================
# 8. Coverage の罠
# ============================================================================
def demo_coverage_trap():
    """Coverage の罠: 100% でもバグがある例"""
    print("\n" + "=" * 60)
    print("8. Coverage の罠")
    print("=" * 60)

    # --- バグがある関数 ---
    def divide(a: int, b: int) -> float:
        """バグ: ゼロ除算チェックが不完全"""
        if b == 0:
            return 0  # バグ! 例外を投げるべき
        return a / b

    # --- 100% Line Coverage を達成するテスト ---
    test_results = []

    # テスト1: 正常系
    assert divide(10, 2) == 5.0
    test_results.append("divide(10, 2) == 5.0: PASS")

    # テスト2: ゼロ除算 (Line Coverage は通る)
    assert divide(10, 0) == 0  # テストは通る。しかしバグ!
    test_results.append("divide(10, 0) == 0:   PASS (しかしバグ!)")

    print("\n  --- Line Coverage 100% でもバグがある例 ---")
    for t in test_results:
        print(f"  {t}")

    print("""
  問題: divide(10, 0) が 0 を返すのは仕様違反。
  Line Coverage は全行を実行したことを保証するが、
  「正しい動作」を保証しない。

  Coverage の種類と信頼度:

  | 種類             | 信頼度 | 説明                           |
  |-----------------|--------|-------------------------------|
  | Line Coverage   | 低     | 各行が実行されたか              |
  | Branch Coverage | 中     | if/else の全分岐を通過したか    |
  | Path Coverage   | 高     | 全パスの組み合わせを網羅         |
  | Mutation Score  | 最高   | テストがバグを検出する能力の計測  |

  → Mutation Score が最も信頼性の高い品質指標。
    Line Coverage 80%+ は最低ライン。
    Branch Coverage + Mutation Testing が理想。""")


# --- Branch Coverage vs Line Coverage の違い ---
class TestBranchCoverage(unittest.TestCase):
    """Branch Coverage の重要性を示すテスト"""

    def classify_age(self, age: int) -> str:
        if age < 0:
            return "invalid"
        elif age < 13:
            return "child"
        elif age < 20:
            return "teen"
        else:
            return "adult"

    def test_line_coverage_only(self):
        """Line Coverage は高いが Branch Coverage は不十分"""
        self.assertEqual(self.classify_age(25), "adult")
        # → 1つの分岐しかテストしていない

    def test_full_branch_coverage(self):
        """全分岐をテスト"""
        self.assertEqual(self.classify_age(-1), "invalid")
        self.assertEqual(self.classify_age(5), "child")
        self.assertEqual(self.classify_age(15), "teen")
        self.assertEqual(self.classify_age(25), "adult")
        # 境界値も追加
        self.assertEqual(self.classify_age(0), "child")
        self.assertEqual(self.classify_age(12), "child")
        self.assertEqual(self.classify_age(13), "teen")
        self.assertEqual(self.classify_age(19), "teen")
        self.assertEqual(self.classify_age(20), "adult")


# ============================================================================
# メイン実行
# ============================================================================
def print_tiers():
    """Tier 別ロードマップを表示"""
    print("=" * 60)
    print("テストエンジニアリング — Tier 別ロードマップ")
    print("=" * 60)
    for tier, items in TIERS.items():
        print(f"\n  {tier}:")
        for item in items:
            print(f"    - {item}")


def run_unit_tests():
    """unittest を実行"""
    print("\n" + "=" * 60)
    print("ユニットテスト実行結果")
    print("=" * 60)
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_classes = [
        TestPricingEngine,
        TestUserRepositoryIntegration,
        TestOrderE2E,
        TestTestDoubles,
        TestStack,
        TestAAA,
        TestBuilderPattern,
        TestBranchCoverage,
    ]
    for cls in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result


def demo_bdd():
    """BDD シナリオのデモ"""
    print("\n" + "=" * 60)
    print("7. BDD (Given-When-Then) デモ")
    print("=" * 60)

    scenario = BDDScenario("大量注文で割引が適用される")

    result = (scenario
        .given("100個の商品を注文する顧客",
               lambda: {"engine": PricingEngine(), "price": 50, "qty": 100})
        .when("割引価格を計算する",
              lambda ctx: ctx["engine"].bulk_discount(ctx["price"], ctx["qty"]))
        .then("20%割引が適用される",
              lambda result: result == 4000.0))

    status = "PASS" if result else "FAIL"
    print(f"  シナリオ: {scenario.description}")
    print(f"  Given: {scenario._given_desc}")
    print(f"  When:  {scenario._when_desc}")
    print(f"  Then:  {scenario._then_desc}")
    print(f"  結果:  [{status}]")


def main():
    print_tiers()

    # テストダブルの比較表
    print("\n" + "=" * 60)
    print("2. テストダブル比較表")
    print("=" * 60)
    print("""
  | 種類   | 振る舞い     | 検証       | 用途                    |
  |--------|-------------|-----------|------------------------|
  | Dummy  | 何もしない   | しない     | パラメータ埋め            |
  | Stub   | 固定値を返す | しない     | 間接入力の制御            |
  | Spy    | 記録する     | 後から検証 | 呼び出しの確認            |
  | Mock   | 期待値設定   | 自動検証   | インタラクション検証       |
  | Fake   | 簡易実装     | しない     | InMemoryDB 等の代替実装  |
    """)

    # TDD の流れを説明
    print("=" * 60)
    print("3. TDD Red-Green-Refactor (Stack 実装の流れ)")
    print("=" * 60)
    print("""
  Step 1 [RED]:      test_new_stack_is_empty   → Stack クラスがない → FAIL
  Step 2 [GREEN]:    class Stack + is_empty()  → テスト通過
  Step 3 [RED]:      test_push                 → push() がない → FAIL
  Step 4 [GREEN]:    push() 実装               → テスト通過
  Step 5 [RED]:      test_pop                  → pop() がない → FAIL
  Step 6 [GREEN]:    pop() 実装 (LIFO)         → テスト通過
  Step 7 [RED]:      test_pop_empty_raises     → 空 pop 未対応 → FAIL
  Step 8 [GREEN]:    空チェック追加             → テスト通過
  Step 9 [REFACTOR]: __iter__, __repr__ 追加   → テスト維持しつつ設計改善

  ポイント:
    - 1テストずつ追加 → 最小限の実装 → リファクタ
    - テストが常に「正しい仕様書」になる
    - 過剰実装を防ぐ (YAGNI)
    """)

    # 各デモ実行
    demo_property_based_testing()
    demo_mutation_testing()
    demo_contract_testing()
    demo_bdd()

    # ユニットテスト実行
    result = run_unit_tests()

    # サマリー
    print("\n" + "=" * 60)
    print("サマリー")
    print("=" * 60)
    total = result.testsRun
    failures = len(result.failures) + len(result.errors)
    print(f"  テスト実行: {total}")
    print(f"  成功: {total - failures}")
    print(f"  失敗: {failures}")
    print(f"\n  Flaky Test 原因:")
    for line in FLAKY_TEST_CAUSES.strip().split("\n")[:8]:
        print(f"  {line}")
    print("\n  次のステップ:")
    print("    1. pytest + coverage を導入して実プロジェクトに適用")
    print("    2. Mutation Testing (mutmut) でテスト品質を計測")
    print("    3. Contract Testing (Pact) でマイクロサービス間を検証")


if __name__ == "__main__":
    main()
