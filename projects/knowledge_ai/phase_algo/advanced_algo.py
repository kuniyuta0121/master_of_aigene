"""
phase_algo/advanced_algo.py
============================
アルゴリズム上級編 - FAANG Hard レベル

algo_foundations.py の続き。以下を実装:
  1. グラフ: BFS/DFS テンプレート・トポロジカルソート・有向グラフのSCC
  2. Trie（前置木）: 文字列検索・オートコンプリート
  3. Segment Tree: 区間クエリ・区間更新
  4. バックトラッキング: 排列・組み合わせ・N-Queens・ナンプレ
  5. 文字列: KMP・ローリングハッシュ
  6. 単調スタック: 次の大きな要素・ヒストグラム最大矩形
  7. 高度な DP: 区間DP・ビットマスクDP

実行方法:
  python advanced_algo.py

考えてほしい疑問:
  Q1. BFS と DFS の使い分けは？（最短路 vs 経路存在・連結成分）
  Q2. Trie の検索が O(m) で済む理由は？（m=クエリ長）
  Q3. Segment Tree はなぜ O(log n) でクエリを答えられるか？
  Q4. バックトラッキングのプルーニングが計算量を劇的に削減する理由は？
  Q5. KMP アルゴリズムの「失敗関数」は何を記録しているか？
"""

from __future__ import annotations

from collections import deque, defaultdict
from typing import Any


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. グラフアルゴリズム
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class GraphAlgorithms:
    """BFS/DFS テンプレートと応用問題"""

    @staticmethod
    def bfs(graph: dict[int, list[int]], start: int) -> list[int]:
        """
        BFS（幅優先探索）テンプレート
        用途: 最短路（重みなし）、レベル順探索、最短距離

        時間: O(V + E)
        空間: O(V)

        考えてほしい疑問:
          ・BFS でどうやって最短距離を記録するか？（dist 配列）
          ・有向グラフと無向グラフで何が変わるか？
        """
        visited = {start}
        queue = deque([start])
        order = []

        while queue:
            node = queue.popleft()
            order.append(node)
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return order

    @staticmethod
    def dfs_iterative(graph: dict[int, list[int]], start: int) -> list[int]:
        """
        DFS（深さ優先探索）- 反復版（スタックオーバーフロー対策）
        用途: 連結成分、トポロジカルソート前処理、サイクル検出

        時間: O(V + E)

        [実装してみよう] 再帰版も実装して挙動を比較する
        """
        visited = set()
        stack = [start]
        order = []

        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            order.append(node)
            for neighbor in reversed(graph.get(node, [])):  # 順序を保つために reversed
                if neighbor not in visited:
                    stack.append(neighbor)

        return order

    @staticmethod
    def shortest_path_bfs(graph: dict[int, list[int]], start: int, end: int
                          ) -> tuple[int, list[int]]:
        """
        BFS による最短経路（重みなしグラフ）
        LeetCode でよく使うテンプレート
        """
        if start == end:
            return 0, [start]

        visited = {start}
        queue = deque([(start, [start])])

        while queue:
            node, path = queue.popleft()
            for neighbor in graph.get(node, []):
                if neighbor == end:
                    return len(path), path + [neighbor]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return -1, []  # 到達不可

    @staticmethod
    def topological_sort(graph: dict[int, list[int]]) -> list[int] | None:
        """
        トポロジカルソート（Kahn's algorithm - BFS ベース）
        用途: 依存関係の解決、コースの前提条件チェック
        LeetCode 207 (Course Schedule) 相当

        時間: O(V + E)

        考えてほしい疑問:
          ・サイクルがあるとどうなるか？（None を返す = 不可能）
          ・DFS でもトポロジカルソートできる（後順探索）
        """
        in_degree = defaultdict(int)
        for node, neighbors in graph.items():
            in_degree.setdefault(node, 0)
            for nbr in neighbors:
                in_degree[nbr] += 1

        queue = deque([node for node, deg in in_degree.items() if deg == 0])
        order = []

        while queue:
            node = queue.popleft()
            order.append(node)
            for neighbor in graph.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return order if len(order) == len(in_degree) else None  # サイクル検出

    @staticmethod
    def word_ladder(begin_word: str, end_word: str, word_list: list[str]) -> int:
        """
        Word Ladder - BFS の典型的応用問題
        LeetCode 127 (Hard) → Googleで実際に出た

        1文字ずつ変えて beginWord から endWord に辿り着く最短ステップ数

        考えてほしい疑問:
          ・なぜ BFS が最短を保証するか？（各ステップで1文字だけ変わる）
          ・双方向 BFS でどう高速化できるか？
        """
        word_set = set(word_list)
        if end_word not in word_set:
            return 0

        queue = deque([(begin_word, 1)])
        visited = {begin_word}

        while queue:
            word, steps = queue.popleft()
            for i in range(len(word)):
                for c in "abcdefghijklmnopqrstuvwxyz":
                    new_word = word[:i] + c + word[i+1:]
                    if new_word == end_word:
                        return steps + 1
                    if new_word in word_set and new_word not in visited:
                        visited.add(new_word)
                        queue.append((new_word, steps + 1))

        return 0

    @staticmethod
    def clone_graph_dfs(adj: list[list[int]]) -> dict[int, list[int]]:
        """
        グラフのディープコピー - DFS 応用
        LeetCode 133 (Medium)
        """
        if not adj:
            return {}

        n = len(adj)
        cloned: dict[int, list[int]] = {}
        visited = set()

        def dfs(node: int) -> None:
            if node in visited:
                return
            visited.add(node)
            cloned[node] = list(adj[node])
            for neighbor in adj[node]:
                dfs(neighbor)

        for i in range(n):
            dfs(i)

        return cloned


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. Trie（前置木）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TrieNode:
    def __init__(self):
        self.children: dict[str, "TrieNode"] = {}
        self.is_end: bool = False
        self.count: int = 0         # このプレフィックスで始まる単語数


class Trie:
    """
    Trie（前置木・トライ木）: 文字列を効率的に格納・検索

    用途:
      ・オートコンプリート（Google 検索の候補表示）
      ・スペルチェッカー
      ・IP アドレスのルーティングテーブル
      ・文字列の最長共通プレフィックス

    計算量:
      挿入・検索・削除: O(m)  m = 文字列の長さ
      空間: O(N × m)  N = 単語数

    ハッシュマップとの比較:
      ハッシュマップ: O(m) 検索、プレフィックス検索が不可
      Trie: O(m) 検索、プレフィックス検索が O(m) で可能
    """

    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
            node.count += 1
        node.is_end = True

    def search(self, word: str) -> bool:
        """完全一致検索 O(m)"""
        node = self.root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end

    def starts_with(self, prefix: str) -> bool:
        """プレフィックス検索 O(m)"""
        node = self.root
        for char in prefix:
            if char not in node.children:
                return False
            node = node.children[char]
        return True

    def autocomplete(self, prefix: str) -> list[str]:
        """
        プレフィックスに続く全単語を返す（オートコンプリート）
        LeetCode 1268 相当
        """
        node = self.root
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]

        # DFS で全単語を収集
        results = []

        def dfs(n: TrieNode, current: str) -> None:
            if n.is_end:
                results.append(current)
            for c, child in sorted(n.children.items()):
                dfs(child, current + c)

        dfs(node, prefix)
        return results

    def count_prefix(self, prefix: str) -> int:
        """プレフィックスで始まる単語の数"""
        node = self.root
        for char in prefix:
            if char not in node.children:
                return 0
            node = node.children[char]
        return node.count

    def delete(self, word: str) -> bool:
        """
        単語の削除 - 参照カウントを使った実装
        [実装してみよう] 後置削除（子が不要になったノードを消す）で実装する
        """
        def _delete(node: TrieNode, word: str, depth: int) -> bool:
            if depth == len(word):
                if not node.is_end:
                    return False
                node.is_end = False
                return len(node.children) == 0

            char = word[depth]
            if char not in node.children:
                return False

            should_delete = _delete(node.children[char], word, depth + 1)
            if should_delete:
                del node.children[char]
                return not node.is_end and len(node.children) == 0
            return False

        return _delete(self.root, word, 0)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. Segment Tree（セグメント木）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class SegmentTree:
    """
    Segment Tree: 区間クエリ・点更新を O(log n) で処理

    用途:
      ・区間の最小/最大/和を高速に求める
      ・点更新後の区間クエリ
      ・Fenwick Tree（BIT）より柔軟

    計算量:
      構築: O(n)
      点更新: O(log n)
      区間クエリ: O(log n)

    vs. 累積和:
      累積和: クエリ O(1)、更新 O(n)
      Segment Tree: クエリ O(log n)、更新 O(log n)
      → 更新が頻繁なら Segment Tree が優れる

    考えてほしい疑問:
      ・なぜノードを 4n のサイズで確保するか？（最悪ケースの葉の数）
      ・Lazy Propagation とは何か？（区間更新を O(log n) にする技法）
    """

    def __init__(self, data: list[int], operation=min, identity: int = float("inf")):
        self.n = len(data)
        self.op = operation
        self.identity = identity
        self.tree = [identity] * (4 * self.n)
        self._build(data, 1, 0, self.n - 1)

    def _build(self, data: list[int], node: int, start: int, end: int) -> None:
        if start == end:
            self.tree[node] = data[start]
            return
        mid = (start + end) // 2
        self._build(data, 2 * node, start, mid)
        self._build(data, 2 * node + 1, mid + 1, end)
        self.tree[node] = self.op(self.tree[2 * node], self.tree[2 * node + 1])

    def update(self, idx: int, value: int, node: int = 1,
               start: int = 0, end: int = -1) -> None:
        """点更新: arr[idx] = value  O(log n)"""
        if end == -1:
            end = self.n - 1
        if start == end:
            self.tree[node] = value
            return
        mid = (start + end) // 2
        if idx <= mid:
            self.update(idx, value, 2 * node, start, mid)
        else:
            self.update(idx, value, 2 * node + 1, mid + 1, end)
        self.tree[node] = self.op(self.tree[2 * node], self.tree[2 * node + 1])

    def query(self, l: int, r: int, node: int = 1,
              start: int = 0, end: int = -1) -> int:
        """区間クエリ: op(arr[l..r])  O(log n)"""
        if end == -1:
            end = self.n - 1
        if r < start or end < l:
            return self.identity
        if l <= start and end <= r:
            return self.tree[node]
        mid = (start + end) // 2
        return self.op(
            self.query(l, r, 2 * node, start, mid),
            self.query(l, r, 2 * node + 1, mid + 1, end)
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. バックトラッキング
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Backtracking:
    """
    バックトラッキング: 全探索 + 枝刈り

    テンプレート:
      def backtrack(state):
          if is_solution(state):
              result.append(state.copy())
              return
          for choice in get_choices(state):
              if is_valid(state, choice):
                  make_choice(state, choice)     # 選択
                  backtrack(state)               # 再帰
                  undo_choice(state, choice)     # 巻き戻し ← 重要!

    考えてほしい疑問:
      ・バックトラッキングと DP の違いは？
        → DP: 重複する部分問題を使い回す
        → バックトラッキング: 全探索（最適化より列挙に向く）
    """

    @staticmethod
    def permutations(nums: list[int]) -> list[list[int]]:
        """
        全排列を生成
        LeetCode 46 (Medium)
        時間: O(n! × n)
        """
        result = []

        def backtrack(current: list[int], remaining: list[int]) -> None:
            if not remaining:
                result.append(current[:])
                return
            for i, num in enumerate(remaining):
                current.append(num)
                backtrack(current, remaining[:i] + remaining[i+1:])
                current.pop()  # 巻き戻し

        backtrack([], nums)
        return result

    @staticmethod
    def subsets(nums: list[int]) -> list[list[int]]:
        """
        全部分集合を生成
        LeetCode 78 (Medium)
        時間: O(2^n × n)
        """
        result = []

        def backtrack(start: int, current: list[int]) -> None:
            result.append(current[:])
            for i in range(start, len(nums)):
                current.append(nums[i])
                backtrack(i + 1, current)
                current.pop()

        backtrack(0, [])
        return result

    @staticmethod
    def n_queens(n: int) -> list[list[str]]:
        """
        N-Queens: n×n のボードに n 個のクイーンを互いに攻撃しない配置
        LeetCode 51 (Hard) → FAANG頻出

        時間: O(n!)  最悪だが実際は枝刈りで大幅削減

        考えてほしい疑問:
          ・列・左斜め・右斜めの判定を O(1) にする方法は？（ビット演算）
          ・n=8 の解の数はいくつか？（92通り）
        """
        solutions = []
        cols = set()
        pos_diag = set()  # row + col が同じ = 右上↗の斜め
        neg_diag = set()  # row - col が同じ = 左上↖の斜め

        board = [["." for _ in range(n)] for _ in range(n)]

        def backtrack(row: int) -> None:
            if row == n:
                solutions.append(["".join(r) for r in board])
                return
            for col in range(n):
                if col in cols or (row + col) in pos_diag or (row - col) in neg_diag:
                    continue  # 枝刈り: 攻撃範囲内はスキップ

                # 選択
                cols.add(col)
                pos_diag.add(row + col)
                neg_diag.add(row - col)
                board[row][col] = "Q"

                backtrack(row + 1)

                # 巻き戻し
                cols.remove(col)
                pos_diag.remove(row + col)
                neg_diag.remove(row - col)
                board[row][col] = "."

        backtrack(0)
        return solutions

    @staticmethod
    def combination_sum(candidates: list[int], target: int) -> list[list[int]]:
        """
        和が target になる組み合わせ（重複使用可）
        LeetCode 39 (Medium)
        """
        candidates.sort()
        result = []

        def backtrack(start: int, current: list[int], remaining: int) -> None:
            if remaining == 0:
                result.append(current[:])
                return
            for i in range(start, len(candidates)):
                if candidates[i] > remaining:
                    break  # ソート済みなので枝刈り可能
                current.append(candidates[i])
                backtrack(i, current, remaining - candidates[i])  # i から（重複使用可）
                current.pop()

        backtrack(0, [], target)
        return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. 文字列アルゴリズム
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def kmp_search(text: str, pattern: str) -> list[int]:
    """
    KMP（Knuth-Morris-Pratt）パターンマッチング

    ナイーブ法: O(n × m)
    KMP:        O(n + m)  ← 失敗関数で比較をスキップ

    失敗関数 (partial match table):
      lps[i] = pattern[0..i] の最長の「真の接頭辞かつ接尾辞」の長さ
      例: "ABABC" → lps = [0, 0, 1, 2, 0]
      "ABA" の最長の真の接頭辞かつ接尾辞は "A" (長さ1)

    考えてほしい疑問:
      ・「失敗関数」を使うことで何をスキップできるか？
      ・Rabin-Karp はハッシュを使う別のアプローチ → 使い分けは？

    時間: O(n + m), 空間: O(m)
    """
    n, m = len(text), len(pattern)
    if m == 0:
        return []

    # 失敗関数（LPS配列）の構築
    lps = [0] * m
    length = 0
    i = 1
    while i < m:
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        elif length > 0:
            length = lps[length - 1]  # スキップ（比較を巻き戻す）
        else:
            lps[i] = 0
            i += 1

    # マッチング
    matches = []
    i = j = 0  # i: text のインデックス, j: pattern のインデックス
    while i < n:
        if text[i] == pattern[j]:
            i += 1
            j += 1
        if j == m:
            matches.append(i - j)
            j = lps[j - 1]  # 次のマッチ位置にスキップ
        elif i < n and text[i] != pattern[j]:
            if j > 0:
                j = lps[j - 1]
            else:
                i += 1

    return matches


def rolling_hash_search(text: str, pattern: str) -> list[int]:
    """
    ローリングハッシュ（Rabin-Karp）
    ウィンドウをスライドしながらハッシュを O(1) で更新

    用途: 重複部分文字列の検出、複数パターンの同時検索
    """
    n, m = len(text), len(pattern)
    if m > n:
        return []

    BASE = 31
    MOD = (1 << 61) - 1  # メルセンヌ素数（衝突が少ない）

    def char_val(c: str) -> int:
        return ord(c) - ord('a') + 1

    # パターンのハッシュ
    pattern_hash = 0
    for c in pattern:
        pattern_hash = (pattern_hash * BASE + char_val(c)) % MOD

    # テキストの最初のウィンドウのハッシュ
    window_hash = 0
    high_power = 1
    for i, c in enumerate(text[:m]):
        window_hash = (window_hash * BASE + char_val(c)) % MOD
        if i < m - 1:
            high_power = high_power * BASE % MOD

    matches = []
    if window_hash == pattern_hash and text[:m] == pattern:
        matches.append(0)

    for i in range(n - m):
        # ハッシュを O(1) で更新: 左端を引いて右端を加える
        window_hash = (window_hash - char_val(text[i]) * high_power) % MOD
        window_hash = (window_hash * BASE + char_val(text[i + m])) % MOD

        if window_hash == pattern_hash:
            if text[i+1:i+1+m] == pattern:  # 衝突確認
                matches.append(i + 1)

    return matches


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. 単調スタック
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def next_greater_element(nums: list[int]) -> list[int]:
    """
    各要素の「次の大きな要素」を求める
    LeetCode 496 (Medium)

    単調スタック: 要素が単調増加（または減少）を保つスタック
    O(n²) を O(n) に削減

    時間: O(n)
    """
    n = len(nums)
    result = [-1] * n
    stack = []  # インデックスのスタック（単調減少）

    for i in range(n):
        # スタックの top より大きい要素が見つかった → それが「次の大きな要素」
        while stack and nums[i] > nums[stack[-1]]:
            idx = stack.pop()
            result[idx] = nums[i]
        stack.append(i)

    return result


def largest_rectangle_in_histogram(heights: list[int]) -> int:
    """
    ヒストグラムの最大矩形面積
    LeetCode 84 (Hard) → Googleで頻出

    時間: O(n)  単調スタック使用

    考えてほしい疑問:
      ・スタックが「高さの単調増加」を保つとき、
        各バーが「最も低いバー」になれる矩形の幅はどう計算するか？
    """
    stack = [-1]  # センチネル
    max_area = 0

    for i, h in enumerate(heights + [0]):  # 最後に0を追加して残りのスタックを処理
        while stack[-1] != -1 and heights[stack[-1]] >= h:
            height = heights[stack.pop()]
            width = i - stack[-1] - 1
            max_area = max(max_area, height * width)
        stack.append(i)

    return max_area


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. 高度な DP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def matrix_chain_multiplication(dims: list[int]) -> int:
    """
    行列連鎖乗算: 最小計算コスト
    区間 DP の典型例

    問題: n 個の行列 M1, M2, ..., Mn の積を計算するとき
    括弧の付け方で計算量が大きく変わる。最小化せよ。

    dp[i][j] = i番目からj番目の行列の積を計算する最小コスト

    時間: O(n³), 空間: O(n²)
    """
    n = len(dims) - 1  # 行列の数
    dp = [[0] * n for _ in range(n)]

    # length: 区間の長さ
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            dp[i][j] = float("inf")
            for k in range(i, j):
                # M[i..k] × M[k+1..j] の分割コスト
                cost = dp[i][k] + dp[k+1][j] + dims[i] * dims[k+1] * dims[j+1]
                dp[i][j] = min(dp[i][j], cost)

    return dp[0][n-1]


def traveling_salesman_bitmask(dist: list[list[int]]) -> int:
    """
    巡回セールスマン問題 - ビットマスク DP
    LeetCode 847 相当

    dp[mask][i] = 頂点集合 mask を訪問して頂点 i にいるときの最小コスト
    mask: ビットで訪問済み頂点を表現（n=20以下なら実用的）

    時間: O(2^n × n²), 空間: O(2^n × n)
    ← 指数時間だが n≦20 では実用的（DP なしは n!）

    考えてほしい疑問:
      ・n=20 のとき 2^20 × 20² = 400M → 実用ギリギリ。n=25 は？
    """
    n = len(dist)
    INF = float("inf")
    # dp[mask][i]: mask の頂点を訪問して i にいるときの最小コスト
    dp = [[INF] * n for _ in range(1 << n)]
    dp[1][0] = 0  # 頂点0から開始（ビット0が立っている）

    for mask in range(1 << n):
        for u in range(n):
            if not (mask >> u & 1) or dp[mask][u] == INF:
                continue
            for v in range(n):
                if mask >> v & 1:
                    continue  # 既に訪問済み
                new_mask = mask | (1 << v)
                dp[new_mask][v] = min(dp[new_mask][v], dp[mask][u] + dist[u][v])

    # 全頂点訪問後、出発点(0)に戻るコスト
    all_visited = (1 << n) - 1
    return min(dp[all_visited][u] + dist[u][0] for u in range(1, n))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# テスト実行
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_all_tests() -> None:
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   Advanced Algorithms - FAANG Hard Level                   ║")
    print("╚════════════════════════════════════════════════════════════╝")

    print("\n" + "━" * 60)
    print("🌐 1. グラフ")
    print("━" * 60)

    graph = {0: [1, 2], 1: [3], 2: [3, 4], 3: [5], 4: [5], 5: []}
    bfs_order = GraphAlgorithms.bfs(graph, 0)
    dfs_order = GraphAlgorithms.dfs_iterative(graph, 0)
    topo = GraphAlgorithms.topological_sort(graph)
    print(f"  BFS順序: {bfs_order}")
    print(f"  DFS順序: {dfs_order}")
    print(f"  トポロジカルソート: {topo}")

    # Word Ladder
    result = GraphAlgorithms.word_ladder("hit", "cog", ["hot","dot","dog","lot","log","cog"])
    assert result == 5, f"Expected 5, got {result}"
    print(f"  Word Ladder (hit→cog): {result} ステップ ✅")

    # サイクル検出
    cyclic_graph = {0: [1], 1: [2], 2: [0]}
    assert GraphAlgorithms.topological_sort(cyclic_graph) is None
    print(f"  サイクル検出: ✅")

    print("\n" + "━" * 60)
    print("🌳 2. Trie")
    print("━" * 60)

    trie = Trie()
    words = ["python", "pytorch", "pandas", "numpy", "pyspark", "tensorflow"]
    for w in words:
        trie.insert(w)

    assert trie.search("python") == True
    assert trie.search("pyth") == False
    assert trie.starts_with("py") == True

    suggestions = trie.autocomplete("py")
    print(f"  'py' のオートコンプリート: {suggestions}")
    print(f"  'py' で始まる単語数: {trie.count_prefix('py')}")
    print(f"  'tensor' 検索: {trie.search('tensor')} (False=正常) ✅")

    print("\n" + "━" * 60)
    print("📊 3. Segment Tree")
    print("━" * 60)

    data = [3, 1, 4, 1, 5, 9, 2, 6]
    seg_min = SegmentTree(data, min, float("inf"))
    seg_sum = SegmentTree(data, lambda a, b: a + b, 0)

    print(f"  データ: {data}")
    print(f"  区間[2,5]の最小値: {seg_min.query(2, 5)}  (期待値: 1)")
    print(f"  区間[0,7]の合計:   {seg_sum.query(0, 7)}  (期待値: 31)")

    seg_min.update(3, 0)  # data[3] = 0 に更新
    print(f"  data[3]=0 に更新後, 区間[2,5]の最小値: {seg_min.query(2, 5)}  (期待値: 0) ✅")

    print("\n" + "━" * 60)
    print("🔍 4. バックトラッキング")
    print("━" * 60)

    perms = Backtracking.permutations([1, 2, 3])
    print(f"  [1,2,3]の全排列: {len(perms)}通り (期待: 6) ✅")

    subs = Backtracking.subsets([1, 2, 3])
    print(f"  [1,2,3]の全部分集合: {len(subs)}通り (期待: 8) ✅")

    queens_4 = Backtracking.n_queens(4)
    queens_8 = Backtracking.n_queens(8)
    print(f"  4-Queens: {len(queens_4)}通り (期待: 2) ✅")
    print(f"  8-Queens: {len(queens_8)}通り (期待: 92) ✅")

    combos = Backtracking.combination_sum([2, 3, 6, 7], 7)
    print(f"  組み合わせ和=7: {combos} ✅")

    print("\n" + "━" * 60)
    print("📝 5. 文字列アルゴリズム")
    print("━" * 60)

    text = "AABAACAADAABAABA"
    pattern = "AABA"
    kmp_result = kmp_search(text, pattern)
    print(f"  KMP: '{pattern}' in '{text[:10]}...' → 位置{kmp_result} ✅")

    rk_result = rolling_hash_search("abcabcabc", "abc")
    print(f"  Rolling Hash: 'abc' in 'abcabcabc' → 位置{rk_result} ✅")

    print("\n" + "━" * 60)
    print("📚 6. 単調スタック + 高度なDP")
    print("━" * 60)

    nge = next_greater_element([4, 1, 2, 5, 3])
    print(f"  次の大きな要素 [4,1,2,5,3]: {nge}  (期待: [5,2,5,-1,-1]) ✅")

    hist_area = largest_rectangle_in_histogram([2, 1, 5, 6, 2, 3])
    assert hist_area == 10, f"Expected 10, got {hist_area}"
    print(f"  ヒストグラム最大矩形 [2,1,5,6,2,3]: {hist_area}  (期待: 10) ✅")

    # 区間DP
    dims = [40, 20, 30, 10, 30]  # 行列: 40×20, 20×30, 30×10, 10×30
    mc_cost = matrix_chain_multiplication(dims)
    print(f"  行列連鎖乗算 (最小コスト): {mc_cost}  (期待: 26000) ✅")

    # TSP ビットマスク DP
    dist_tsp = [[0, 10, 15, 20], [10, 0, 35, 25], [15, 35, 0, 30], [20, 25, 30, 0]]
    tsp_cost = traveling_salesman_bitmask(dist_tsp)
    print(f"  TSP (4都市): {tsp_cost}  (期待: 80) ✅")

    print("\n" + "═" * 60)
    print("✅ 全テスト通過！")
    print("  [実装してみよう]")
    print("  1. Segment Tree に Lazy Propagation を追加（区間更新を O(log n) に）")
    print("  2. Trie に正規表現マッチング（.が任意の文字）を追加")
    print("  3. Word Ladder を双方向 BFS で高速化する")
    print("  4. Dijkstra に負の辺対応（Bellman-Ford）を追加")

    print("""
  ★ 優先度順まとめ (この順で覚える):

  【Tier 1: 最優先 — 面接・実務で即必要】
    - Graph (BFS/DFS/Dijkstra — 最短経路・連結性)
    - Backtracking (N-Queens, Permutations, Subsets)

  【Tier 2: 重要 — 実務で頻出】
    - Trie (Prefix Tree — 文字列検索・オートコンプリート)
    - KMP文字列検索 (パターンマッチング・failure関数)
    - Matrix Chain DP (区間DP入門)

  【Tier 3: 上級 — シニア以上で差がつく】
    - Segment Tree (区間クエリ・RMQ・Lazy Propagation)
    - Bitmask DP (TSP・部分集合列挙)
    - Topological Sort応用 (依存関係解析・ビルド順序)

  【Tier 4: 専門 — Staff+/特定ドメインで必要】
    - Suffix Array (文字列の全接尾辞ソート)
    - Heavy-Light Decomposition (木のパスクエリ)
    - Centroid Decomposition (木の分割統治)
""")


if __name__ == "__main__":
    run_all_tests()
