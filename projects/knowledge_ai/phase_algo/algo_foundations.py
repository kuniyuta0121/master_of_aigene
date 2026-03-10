"""
phase_algo/algo_foundations.py
========================================
アルゴリズム & データ構造 - FAANG面接レベル

なぜこれが必要か:
  Google / Tesla / IBM の面接では、まず「コーディング面接」がある。
  どんなにMLが得意でも、Binary Search を実装できないと落とされる。
  LeetCode Medium を確実に解き、Hard を時間内に方向性まで出せること
  が FAANG通過の最低ライン。

このフェーズで学ぶこと:
  - 計算量の分析 (時間計算量・空間計算量)
  - 頻出パターン: Two Pointers, Sliding Window, Binary Search
  - データ構造: Heap, Trie, Union-Find, Segment Tree
  - グラフ: BFS/DFS, Dijkstra, Topological Sort, Union-Find
  - 動的計画法: メモ化、タブレーション、最適部分構造
  - 文字列: KMP, Rabin-Karp, Sliding Window

実行方法:
  python algo_foundations.py

考えてほしい疑問:
  Q1. O(n log n) と O(n²) は n=10^6 のとき何秒差になるか？
  Q2. 再帰とメモ化の違いは何か？（スタックオーバーフローリスク）
  Q3. ハッシュテーブルの最悪計算量が O(n) になるのはなぜか？
  Q4. グラフの BFS と DFS はどう使い分けるか？（最短路 vs 経路探索）
  Q5. Segment Tree は何を解決するためのデータ構造か？
"""

import heapq
import time
from collections import defaultdict, deque
from functools import lru_cache
from typing import Optional


# ─── 計算量の体感 ───────────────────────────────────────────

def benchmark_complexity() -> None:
    """
    O(n), O(n log n), O(n²) の実際の時間差を体感する

    [実装してみよう]
      n = 10^7 で O(n log n) と O(n²) の差を計算してみる
      Google のサーバーが 10^9 ops/sec として何秒かかるか？
    """
    import math

    print("╔═══════════════════════════════════════════════════════╗")
    print("║   Phase Algo: アルゴリズム & データ構造 基礎           ║")
    print("╚═══════════════════════════════════════════════════════╝")

    print("\n📊 計算量の比較（n = 10^6、10^9 ops/sec と仮定）")
    print("─" * 60)

    n_values = [10**3, 10**4, 10**5, 10**6]
    ops_per_sec = 10**9  # CPU速度の概算

    header = f"{'計算量':15s}" + "".join(f"n={n:>8,}" for n in n_values)
    print(header)
    print("─" * len(header))

    complexities = [
        ("O(log n)",   lambda n: math.log2(n)),
        ("O(n)",       lambda n: n),
        ("O(n log n)", lambda n: n * math.log2(n)),
        ("O(n²)",      lambda n: n ** 2),
        ("O(2^n)",     lambda n: min(2**n, 10**30)),  # 大きすぎる場合はキャップ
    ]

    for name, func in complexities:
        row = f"{name:15s}"
        for n in n_values:
            ops = func(n)
            secs = ops / ops_per_sec
            if secs < 0.001:
                row += f"{'< 1ms':>12s}"
            elif secs < 1:
                row += f"{secs*1000:>10.1f}ms"
            elif secs < 3600:
                row += f"{secs:>10.2f}s"
            else:
                row += f"{'∞ (不可)':>12s}"
        print(row)

    print("""
重要な直感:
  n=10^6 のデータに対して O(n²) は不可能（27分以上）
  O(n log n) は 0.02秒 → ソート・ヒープ操作の目標計算量
  面接では「このアルゴリズムの計算量は？」が必ず聞かれる
""")


# ─── パターン1: Two Pointers ────────────────────────────────

class TwoPointers:
    """
    Two Pointers パターン
    左右から挟み込む、または同方向で追跡する。
    O(n²) を O(n) に落とせることが多い。
    """

    @staticmethod
    def two_sum_sorted(nums: list[int], target: int) -> tuple[int, int]:
        """
        ソート済み配列で target を足す2数のインデックスを返す
        LeetCode 167 相当

        時間: O(n), 空間: O(1)
        """
        left, right = 0, len(nums) - 1
        while left < right:
            s = nums[left] + nums[right]
            if s == target:
                return (left, right)
            elif s < target:
                left += 1
            else:
                right -= 1
        return (-1, -1)

    @staticmethod
    def container_with_most_water(heights: list[int]) -> int:
        """
        最大の水量を求める
        LeetCode 11 相当 (Medium → Googleでよく出る)

        時間: O(n), 空間: O(1)

        考えてほしい疑問:
          なぜ高い方のポインターを動かしても意味がないのか？
        """
        left, right = 0, len(heights) - 1
        max_water = 0
        while left < right:
            h = min(heights[left], heights[right])
            max_water = max(max_water, h * (right - left))
            # 低い方を動かす（高い方を動かしても面積は減るだけ）
            if heights[left] < heights[right]:
                left += 1
            else:
                right -= 1
        return max_water

    @staticmethod
    def three_sum(nums: list[int]) -> list[list[int]]:
        """
        3つの数の和が0になる組み合わせを返す（重複なし）
        LeetCode 15 相当 (Medium)

        時間: O(n²), 空間: O(1) (結果除く)
        """
        nums.sort()
        result = []
        for i in range(len(nums) - 2):
            if i > 0 and nums[i] == nums[i - 1]:
                continue  # 重複スキップ
            left, right = i + 1, len(nums) - 1
            while left < right:
                s = nums[i] + nums[left] + nums[right]
                if s == 0:
                    result.append([nums[i], nums[left], nums[right]])
                    while left < right and nums[left] == nums[left + 1]:
                        left += 1
                    while left < right and nums[right] == nums[right - 1]:
                        right -= 1
                    left += 1
                    right -= 1
                elif s < 0:
                    left += 1
                else:
                    right -= 1
        return result


# ─── パターン2: Sliding Window ──────────────────────────────

class SlidingWindow:
    """
    Sliding Window パターン
    連続部分列の問題に有効。O(n²) を O(n) に。
    """

    @staticmethod
    def max_sum_subarray(nums: list[int], k: int) -> int:
        """
        長さ k の連続部分配列の最大和
        時間: O(n), 空間: O(1)
        """
        window_sum = sum(nums[:k])
        max_sum = window_sum
        for i in range(k, len(nums)):
            window_sum += nums[i] - nums[i - k]
            max_sum = max(max_sum, window_sum)
        return max_sum

    @staticmethod
    def longest_substring_without_repeat(s: str) -> int:
        """
        重複文字のない最長部分文字列の長さ
        LeetCode 3 相当 (Medium) → FAANG頻出

        時間: O(n), 空間: O(min(m,n)) m=文字集合サイズ

        考えてほしい疑問:
          last_seen[char] を使うことで left を O(1) で更新できる理由は？
        """
        last_seen: dict[str, int] = {}
        left = 0
        max_len = 0
        for right, char in enumerate(s):
            if char in last_seen and last_seen[char] >= left:
                left = last_seen[char] + 1
            last_seen[char] = right
            max_len = max(max_len, right - left + 1)
        return max_len

    @staticmethod
    def min_window_substring(s: str, t: str) -> str:
        """
        t の全文字を含む s の最小部分文字列
        LeetCode 76 (Hard) → Googleで実際に出た

        時間: O(|s| + |t|), 空間: O(|t|)
        """
        from collections import Counter
        need = Counter(t)
        missing = len(t)
        left = result_left = 0
        result_right = float("inf")

        for right, char in enumerate(s, 1):
            if need[char] > 0:
                missing -= 1
            need[char] -= 1

            if missing == 0:
                # 左端を縮める
                while need[s[left]] < 0:
                    need[s[left]] += 1
                    left += 1
                if right - left < result_right - result_left:
                    result_left, result_right = left, right
                # 左端を1つ進める（次の窓を探す）
                need[s[left]] += 1
                missing += 1
                left += 1

        return s[result_left:result_right] if result_right != float("inf") else ""


# ─── パターン3: Binary Search ───────────────────────────────

class BinarySearch:
    """
    Binary Search パターン
    「ソートされた空間での探索」だけでなく
    「答えに対するバイナリサーチ」が重要。
    """

    @staticmethod
    def search_rotated(nums: list[int], target: int) -> int:
        """
        回転したソート済み配列でのサーチ
        LeetCode 33 (Medium) → 頻出

        時間: O(log n)
        """
        left, right = 0, len(nums) - 1
        while left <= right:
            mid = (left + right) // 2
            if nums[mid] == target:
                return mid
            # 左半分がソートされている
            if nums[left] <= nums[mid]:
                if nums[left] <= target < nums[mid]:
                    right = mid - 1
                else:
                    left = mid + 1
            # 右半分がソートされている
            else:
                if nums[mid] < target <= nums[right]:
                    left = mid + 1
                else:
                    right = mid - 1
        return -1

    @staticmethod
    def koko_eating_bananas(piles: list[int], h: int) -> int:
        """
        「答えへのバイナリサーチ」の典型例
        LeetCode 875 (Medium)

        コンセプト: 「速度 k で食べると h 時間以内に終わるか？」
                   という条件をバイナリサーチ

        考えてほしい疑問:
          なぜ「答えにバイナリサーチ」できるのか？
          → 単調性（k が大きいほど必ず速く食べられる）があるから
        """
        import math

        def can_finish(speed: int) -> bool:
            return sum(math.ceil(p / speed) for p in piles) <= h

        left, right = 1, max(piles)
        while left < right:
            mid = (left + right) // 2
            if can_finish(mid):
                right = mid
            else:
                left = mid + 1
        return left


# ─── データ構造1: Heap（優先度付きキュー） ──────────────────

class HeapProblems:
    """
    Heap は「常に最小/最大を O(log n) で取り出す」構造
    Python の heapq は最小ヒープ（最大ヒープは値を負にする）

    考えてほしい疑問:
      Priority Queue と Heap の違いは何か？（インターフェースと実装）
    """

    @staticmethod
    def k_largest_elements(nums: list[int], k: int) -> list[int]:
        """
        上位 k 要素を返す
        LeetCode 215 相当

        時間: O(n log k), 空間: O(k)
        ※ O(n log n) のソートより速い（k << n のとき）
        """
        # サイズ k の最小ヒープを維持
        heap: list[int] = []
        for num in nums:
            heapq.heappush(heap, num)
            if len(heap) > k:
                heapq.heappop(heap)  # 最小値を除去
        return sorted(heap, reverse=True)

    @staticmethod
    def merge_k_sorted_lists(lists: list[list[int]]) -> list[int]:
        """
        k 個のソート済みリストをマージ
        LeetCode 23 相当 (Hard) → 頻出

        時間: O(N log k) N=総要素数, k=リスト数
        """
        result = []
        # ヒープ: (値, リストのインデックス, 要素のインデックス)
        heap = []
        for i, lst in enumerate(lists):
            if lst:
                heapq.heappush(heap, (lst[0], i, 0))

        while heap:
            val, list_idx, elem_idx = heapq.heappop(heap)
            result.append(val)
            next_idx = elem_idx + 1
            if next_idx < len(lists[list_idx]):
                heapq.heappush(heap, (lists[list_idx][next_idx], list_idx, next_idx))

        return result

    @staticmethod
    def find_median_from_stream() -> None:
        """
        ストリームデータの中央値をリアルタイムで維持
        LeetCode 295 (Hard) → Google/Meta頻出

        アイデア: 最大ヒープ（小さい半分）+ 最小ヒープ（大きい半分）
        """
        max_heap: list[int] = []  # 負の値で最大ヒープ模倣
        min_heap: list[int] = []

        def add_num(num: int) -> None:
            heapq.heappush(max_heap, -num)
            # max_heap の最大 <= min_heap の最小 を保証
            heapq.heappush(min_heap, -heapq.heappop(max_heap))
            # サイズバランス
            if len(min_heap) > len(max_heap):
                heapq.heappush(max_heap, -heapq.heappop(min_heap))

        def find_median() -> float:
            if len(max_heap) == len(min_heap):
                return (-max_heap[0] + min_heap[0]) / 2
            return float(-max_heap[0])

        # テスト
        for n in [5, 15, 1, 3, 8, 7, 9, 2]:
            add_num(n)
        print(f"  中央値テスト: データ [5,15,1,3,8,7,9,2] → {find_median()}")


# ─── データ構造2: Union-Find（素集合データ構造） ────────────

class UnionFind:
    """
    Union-Find は「グループ管理」に特化したデータ構造
    グラフの連結成分、クラスタリング、クラスキャン検出に使用

    考えてほしい疑問:
      path compression と union by rank で計算量がどう変わるか？
      → アッカーマン関数の逆数 α(n) ≈ 定数 → ほぼ O(1)
    """

    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.num_components = n

    def find(self, x: int) -> int:
        """経路圧縮付き find"""
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # 経路圧縮
        return self.parent[x]

    def union(self, x: int, y: int) -> bool:
        """union by rank で木の高さを最小化"""
        px, py = self.find(x), self.find(y)
        if px == py:
            return False  # 既に同じグループ（サイクル検出）
        if self.rank[px] < self.rank[py]:
            px, py = py, px
        self.parent[py] = px
        if self.rank[px] == self.rank[py]:
            self.rank[px] += 1
        self.num_components -= 1
        return True

    def connected(self, x: int, y: int) -> bool:
        return self.find(x) == self.find(y)


def solve_number_of_islands(grid: list[list[str]]) -> int:
    """
    島の数を数える - Union-Find による実装
    LeetCode 200 (Medium) → 頻出中の頻出

    時間: O(m*n * α(m*n)) ≈ O(m*n)

    考えてほしい疑問:
      BFS/DFS でも解ける → どちらが面接で好まれるか？
      → Union-Find は「動的に変化するグラフ」に強い
    """
    if not grid:
        return 0
    m, n = len(grid), len(grid[0])
    uf = UnionFind(m * n)
    land_count = 0

    for i in range(m):
        for j in range(n):
            if grid[i][j] == "1":
                land_count += 1
                for di, dj in [(0, 1), (1, 0)]:
                    ni, nj = i + di, j + dj
                    if 0 <= ni < m and 0 <= nj < n and grid[ni][nj] == "1":
                        if uf.union(i * n + j, ni * n + nj):
                            land_count -= 1

    return land_count


# ─── 動的計画法（DP） ────────────────────────────────────────

class DynamicProgramming:
    """
    動的計画法: 「重複する部分問題」を記憶して解く

    DP の設計ステップ:
      1. 状態定義: dp[i] が何を表すか
      2. 遷移式: dp[i] を dp[i-1] などで表す
      3. 基底条件: dp[0] の値
      4. 答えの取り出し方

    考えてほしい疑問:
      メモ化（トップダウン）とタブレーション（ボトムアップ）の違いは？
      → メモ化は再帰 + キャッシュ、タブレーションはループ
    """

    @staticmethod
    def longest_common_subsequence(s1: str, s2: str) -> int:
        """
        最長共通部分列（LCS）
        LeetCode 1143 (Medium) → 文字列 DP の基礎

        時間: O(m*n), 空間: O(m*n) → O(n) に最適化可能

        dp[i][j] = s1[:i] と s2[:j] の LCS 長
        """
        m, n = len(s1), len(s2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i - 1] == s2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

        return dp[m][n]

    @staticmethod
    def coin_change(coins: list[int], amount: int) -> int:
        """
        最小枚数でおつりを作る
        LeetCode 322 (Medium) → DP基礎中の基礎

        時間: O(amount * len(coins)), 空間: O(amount)
        """
        dp = [float("inf")] * (amount + 1)
        dp[0] = 0
        for a in range(1, amount + 1):
            for coin in coins:
                if coin <= a:
                    dp[a] = min(dp[a], dp[a - coin] + 1)
        return dp[amount] if dp[amount] != float("inf") else -1

    @staticmethod
    @lru_cache(maxsize=None)
    def edit_distance(word1: str, word2: str) -> int:
        """
        編集距離（Levenshtein距離）: メモ化再帰版
        LeetCode 72 (Hard)

        spell checker、DNA配列比較、diff ツールで使われる

        考えてほしい疑問:
          lru_cache を使うとタブレーションより遅い場合があるのはなぜか？
          （関数呼び出しのオーバーヘッド）
        """
        if not word1:
            return len(word2)
        if not word2:
            return len(word1)
        if word1[0] == word2[0]:
            return DynamicProgramming.edit_distance(word1[1:], word2[1:])
        return 1 + min(
            DynamicProgramming.edit_distance(word1[1:], word2),    # 削除
            DynamicProgramming.edit_distance(word1, word2[1:]),    # 挿入
            DynamicProgramming.edit_distance(word1[1:], word2[1:]) # 置換
        )


# ─── グラフ: Dijkstra ────────────────────────────────────────

def dijkstra(graph: dict[int, list[tuple[int, int]]], src: int) -> dict[int, int]:
    """
    Dijkstra 最短経路（重み付きグラフ）
    Google Maps, カーナビ, ゲームのパスファインディングで使用

    時間: O((V + E) log V) with ヒープ

    考えてほしい疑問:
      負の重みがある場合に Dijkstra が失敗する理由は？
      → Bellman-Ford を使う（O(VE) だが負の辺に対応）
    """
    dist = defaultdict(lambda: float("inf"))
    dist[src] = 0
    heap = [(0, src)]

    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue  # 古いエントリはスキップ
        for v, weight in graph.get(u, []):
            if dist[u] + weight < dist[v]:
                dist[v] = dist[u] + weight
                heapq.heappush(heap, (dist[v], v))

    return dict(dist)


# ─── 面接で実際に出た問題（Google難易度） ───────────────────

def design_lru_cache(capacity: int):
    """
    LRU キャッシュを O(1) で実装せよ
    LeetCode 146 (Medium) → システム設計×アルゴリズムの融合問題

    アイデア: HashMap + 双方向連結リスト
      - HashMap: key → ノード (O(1) アクセス)
      - 双方向リスト: 順序管理 (O(1) 挿入・削除)

    考えてほしい疑問:
      なぜ「双方向」連結リストが必要か？（単方向では O(n) になる部分は？）
    """
    from collections import OrderedDict

    cache: OrderedDict = OrderedDict()

    def get(key: int) -> int:
        if key not in cache:
            return -1
        cache.move_to_end(key)  # 最近使用に移動
        return cache[key]

    def put(key: int, value: int) -> None:
        if key in cache:
            cache.move_to_end(key)
        cache[key] = value
        if len(cache) > capacity:
            cache.popitem(last=False)  # 最も古いアイテムを削除

    return get, put


# ─── テスト実行 ──────────────────────────────────────────────

def run_tests() -> None:
    print("\n" + "═" * 60)
    print("🧪 実装テスト")
    print("─" * 60)

    # Two Pointers
    assert TwoPointers.two_sum_sorted([2, 7, 11, 15], 9) == (0, 1)
    assert TwoPointers.container_with_most_water([1, 8, 6, 2, 5, 4, 8, 3, 7]) == 49
    print("  ✅ Two Pointers: PASS")

    # Sliding Window
    assert SlidingWindow.max_sum_subarray([2, 3, 4, 1, 5], 3) == 10
    assert SlidingWindow.longest_substring_without_repeat("abcabcbb") == 3
    assert SlidingWindow.min_window_substring("ADOBECODEBANC", "ABC") == "BANC"
    print("  ✅ Sliding Window: PASS")

    # Binary Search
    assert BinarySearch.search_rotated([4, 5, 6, 7, 0, 1, 2], 0) == 4
    assert BinarySearch.koko_eating_bananas([3, 6, 7, 11], 8) == 4
    print("  ✅ Binary Search: PASS")

    # Heap
    assert HeapProblems.k_largest_elements([3, 2, 1, 5, 6, 4], 2) == [6, 5]
    assert HeapProblems.merge_k_sorted_lists([[1, 4, 5], [1, 3, 4], [2, 6]]) == [1, 1, 2, 3, 4, 4, 5, 6]
    HeapProblems.find_median_from_stream()
    print("  ✅ Heap: PASS")

    # Union-Find
    grid = [["1","1","0","0","0"],
            ["1","1","0","0","0"],
            ["0","0","1","0","0"],
            ["0","0","0","1","1"]]
    assert solve_number_of_islands(grid) == 3
    print("  ✅ Union-Find / Islands: PASS")

    # DP
    assert DynamicProgramming.longest_common_subsequence("abcde", "ace") == 3
    assert DynamicProgramming.coin_change([1, 5, 11], 15) == 3
    assert DynamicProgramming.edit_distance("horse", "ros") == 3
    print("  ✅ Dynamic Programming: PASS")

    # LRU Cache
    get, put = design_lru_cache(2)
    put(1, 1)
    put(2, 2)
    assert get(1) == 1
    put(3, 3)
    assert get(2) == -1  # evicted
    print("  ✅ LRU Cache: PASS")

    print("\n  全テスト通過！")


# ─── FAANG面接のアドバイス ───────────────────────────────────

def interview_strategy() -> None:
    print("\n" + "═" * 60)
    print("🎯 FAANG コーディング面接 攻略戦略")
    print("─" * 60)
    print("""
面接の進め方（45分）:
  5分: 問題を理解し、エッジケースを確認
  5分: アプローチを口頭で説明（brute force → optimal）
  20分: コーディング（クリーンに書く・途中で話す）
  10分: テスト（自分でケースを作って通す）
  5分: 計算量を分析

絶対やってはいけないこと:
  ❌ 黙ってコーディングする（面接官は思考プロセスを見ている）
  ❌ いきなり最適解を書こうとする（brute force から始める）
  ❌ エッジケースを後回しにする（[] や 1要素から考える）
  ❌ 動くか不安なままコードを渡す（自分でテストする）

Google でよく出るパターン（出現率順）:
  1. Two Pointers / Sliding Window  (30%)
  2. Graph BFS/DFS                  (25%)
  3. Dynamic Programming            (20%)
  4. Binary Search（答えへのBS含む）(15%)
  5. Heap / Priority Queue          (10%)

練習ロードマップ:
  Week 1-2: Array, String, Hashmap (LeetCode Easy全問)
  Week 3-4: Two Pointers, Sliding Window (Medium)
  Week 5-6: Tree, Graph BFS/DFS (Medium)
  Week 7-8: DP (Medium → Hard)
  Week 9-10: Heap, Union-Find, Binary Search (Hard)
  Week 11-12: Mock Interview（時間計測して本番想定）

テックリードとして知っておくべきこと:
  面接を「設計し採点する側」になったとき、何を見るか：
  ・コードの可読性（命名・関数分割）
  ・計算量の意識（なぜその解法か説明できるか）
  ・コミュニケーション（チームメンバーとして働けるか）
""")


def main():
    benchmark_complexity()
    run_tests()
    interview_strategy()

    print("\n✅ 完了！次のステップ:")
    print("  → LeetCode: https://leetcode.com/study-plan/")
    print("    目標: 3ヶ月で Medium 100問 + Hard 30問")
    print("  → NeetCode 150: 頻出パターンを体系的に網羅")
    print("  → [実装してみよう] Trie, Segment Tree, Topological Sort を追加実装")

    print("""
  ★ 優先度順まとめ (この順で覚える):

  【Tier 1: 最優先 — 面接・実務で即必要】
    - Two Pointers (対向・同方向・fast/slow)
    - Binary Search (基本・答えへのBS・lower/upper bound)
    - HashMap活用 (Two Sum系・頻度カウント・grouping)
    - BFS/DFS基礎 (グラフ探索・木の走査・連結成分)

  【Tier 2: 重要 — 実務で頻出】
    - Sliding Window (固定長・可変長・最大/最小部分配列)
    - Heap / Priority Queue (Top-K・マージK個のソート済みリスト)
    - 基本DP (Fibonacci型・Knapsack・最長部分列)

  【Tier 3: 上級 — シニア以上で差がつく】
    - Union-Find (連結成分・サイクル検出・Kruskal)
    - Topological Sort (DAG・タスクスケジューリング)
    - Interval問題 (マージ・挿入・最小会議室数)

  【Tier 4: 専門 — Staff+/特定ドメインで必要】
    - Monotonic Stack (Next Greater Element・ヒストグラム最大矩形)
    - 座標圧縮 (大きな座標空間の効率的処理)
    - Mo's Algorithm (オフラインクエリ処理)
""")


if __name__ == "__main__":
    main()
