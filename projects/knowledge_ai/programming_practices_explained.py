#!/usr/bin/env python3
"""
Programming Practices - 深掘り解説
"""
import textwrap

SEP = "=" * 70
THIN = "-" * 70

def title(text):
    print(f"\n{SEP}\n  {text}\n{SEP}")

def heading(text):
    print(f"\n{THIN}\n  {text}\n{THIN}")

def p(text):
    for line in textwrap.dedent(text).strip().split("\n"):
        print(f"  {line}")

def interview(text):
    print()
    print("  【面接向けに整理すると】")
    for line in textwrap.dedent(text).strip().split("\n"):
        print(f"  {line}")

def misconception(wrong, right):
    print(f"\n  ⚠ よくある誤解: {wrong}")
    print(f"  → 正確には: {right}")


# ======================================================================
#  第1章: テスト戦略 — なぜテストを書くのか、どう書くのか
# ======================================================================

def chapter_1_test_strategy():
    title("第1章: テスト戦略 — テストピラミッドからテストダブルまで")

    p("""
    まず全体像:
    テストは「品質を確認する作業」ではなく「変更を安全に進めるための基盤」。
    コードベースが成長するほど、価値はバグ検出よりも変更耐性に移る。

    手動確認だけに依存すると:
    - リリース前の確認がボトルネックになる
    - 人によって確認観点がぶれる
    - 回帰不具合を継続的に防げない

    自動テストの役割:
    - 仕様を実行可能な形で固定する
    - 変更時に壊れた箇所を早く知らせる
    - チームで同じ品質基準を共有する

    ただし「テストを書けばよい」ではなく、種類ごとの特性に合わせた配分設計が必要。
    それがテスト戦略であり、この章ではその設計原則を扱う。
    """)

    # --- テストピラミッド ---
    heading("1-1. テストピラミッド (Test Pyramid)")

    p("""
    まず全体像: この節では「1-1. テストピラミッド (Test Pyramid)」を、定義 -> 仕組み -> 実務上の判断の順で整理する。
    Mike Cohn が提唱した「テストピラミッド」は、テスト戦略の基本モデルだ。

    ピラミッドの形を想像してほしい:

             /\\
            / E2E \\           全体の約 10%
           /--------\\
          / 統合テスト \\       全体の約 20%
         /--------------\\
        /  単体テスト      \\   全体の約 70%
       /--------------------\\

    下に行くほど「数が多く、速く、安定し、安い」。
    上に行くほど「数が少なく、遅く、脆く、高い」。

    なぜこの比率なのか？ 理由はROI（投資対効果）だ。
    """)

    p("""
    各レベルのコスト比較:

    | レベル      | 実行速度   | 1テストの書く時間 | 安定性 | 保守コスト |
    |-------------|-----------|-------------------|--------|-----------|
    | 単体テスト   | ~1ms      | 5-10分            | 高     | 低        |
    | 統合テスト   | ~1秒      | 15-30分           | 中     | 中        |
    | E2Eテスト   | ~30秒-数分 | 1-2時間           | 低     | 高        |

    アナロジーで考えよう。
    車の品質を確認するとき:
    - 単体テスト = 各部品を個別にチェック（ボルトの強度、ブレーキパッドの厚さ）
    - 統合テスト = 部品を組み合わせてチェック（エンジン+トランスミッション）
    - E2Eテスト = 完成した車で実際に走る（公道テスト）

    公道テストだけで品質を保証しようとしたら、
    ボルト1本の不良を見つけるのに毎回車を走らせなければならない。
    コストが爆発する。だから部品レベルのチェックを厚くするのだ。
    """)

    misconception(
        "E2Eテストをたくさん書けば安心",
        "E2Eテストは脆く遅い。CIが30分かかるようになり、Flakyテスト（たまに失敗するテスト）が増え、"
        "誰もテスト結果を信用しなくなる。これを「アイスクリームコーン・アンチパターン」と呼ぶ"
    )

    interview("""
    Q: テストピラミッドについて説明してください。
    A: テストピラミッドは、単体テストを最も多く(70%)、統合テストを中程度(20%)、
       E2Eテストを少なく(10%)書く戦略です。下層ほど高速・安定・低コストで
       ROIが高い。上層は必要だが、数を絞ってFlakyテストの増加を防ぎます。
       実務ではCIの実行時間が10分を超えると開発者がテストを無視し始めるため、
       この比率を意識してパイプラインを設計します。
    """)

    # --- 単体テスト ---
    heading("1-2. 単体テスト (Unit Test)")

    p("""
    まず全体像: この節では「1-2. 単体テスト (Unit Test)」を、定義 -> 仕組み -> 実務上の判断の順で整理する。
    単体テスト（ユニットテスト）は「1つの関数やクラスのメソッドを、
    外部依存なしでテストする」ものだ。

    「外部依存なし」が重要なポイントだ。
    データベース、ファイルシステム、ネットワーク、現在時刻 ——
    これらに依存するとテストが遅くなり、環境依存で失敗しやすくなる。

    単体テストの構造には「Arrange-Act-Assert (AAA)」パターンを使う:

    def test_discount_calculation():
        # Arrange (準備): テスト対象と入力データを用意
        engine = PricingEngine()
        base_price = 1000
        quantity = 5
        discount = 15  # 15%

        # Act (実行): テスト対象のメソッドを1回だけ呼ぶ
        result = engine.calculate(base_price, quantity, discount)

        # Assert (検証): 期待値と比較
        assert result == 4250.0

    なぜAAAが重要か？
    テストが「何を」「どう」「どうなるべきか」の3つに分かれているので、
    テストが失敗したとき、どこに問題があるかすぐわかる。
    Arrangeが複雑すぎるなら、テスト対象の設計が悪い（依存が多すぎる）。
    Actが複数行あるなら、テストが2つのことをテストしている。
    Assertが多すぎるなら、テストを分割すべき。
    """)

    p("""
    境界値テスト (Boundary Value Analysis):
    バグは「境界」に潜む。0, 1, 最大値, 最大値+1, 空, null を必ずテストする。

    例: 年齢による区分
    - age = -1  → 無効（境界外）
    - age = 0   → 子供（境界値）
    - age = 12  → 子供（境界直前）
    - age = 13  → ティーン（境界値）
    - age = 19  → ティーン（境界直前）
    - age = 20  → 大人（境界値）

    「13歳はティーンか子供か」という境界でバグが起きやすい。
    >= と > を間違えるだけでバグになるからだ。
    """)

    # --- 統合テスト ---
    heading("1-3. 統合テスト (Integration Test)")

    p("""
    まず全体像: この節では「1-3. 統合テスト (Integration Test)」を、定義 -> 仕組み -> 実務上の判断の順で整理する。
    統合テスト（インテグレーションテスト）は
    「複数のコンポーネントを組み合わせて、連携が正しく動くかテストする」ものだ。

    単体テストとの違いは「外部依存を含む」こと。
    ただし、本番のデータベースやAPIを使うのではなく、
    テスト用の軽量な代替を使うことが多い:

    - テスト用DB: SQLiteのインメモリモード、Testcontainers
    - テスト用API: WireMock、モックサーバー
    - テスト用メッセージキュー: 組み込みKafka

    統合テストが答える問い:
    「RepositoryクラスはDBに正しくデータを保存・取得できるか？」
    「OrderServiceはUserServiceとPaymentServiceを正しく連携させるか？」

    単体テストでは各クラスを個別にテストするが、
    クラス間のインターフェースの不一致は単体テストでは見つからない。
    統合テストがその隙間を埋める。
    """)

    misconception(
        "統合テストは単体テストの上位互換だから、統合テストだけ書けばいい",
        "統合テストは遅く、失敗原因の特定が難しい。"
        "バグの場所を絞り込むには単体テストが必要。両方書くことで初めて網羅性と効率性を両立できる"
    )

    # --- E2Eテスト ---
    heading("1-4. E2Eテスト (End-to-End Test)")

    p("""
    この節の狙い: 「1-4. E2Eテスト (End-to-End Test)」を単語暗記ではなく、なぜ必要かまでつながる形で理解する。
    E2Eテスト（エンドツーエンドテスト）は
    「ユーザーの操作フロー全体を、本番に近い環境でテストする」ものだ。

    Webアプリなら、ブラウザを自動操作してボタンをクリックし、
    画面遷移を確認し、DBに正しくデータが保存されているか検証する。

    ツール: Selenium, Playwright, Cypress, Puppeteer

    E2Eテストの問題点:
    1. 遅い: ブラウザ起動、ページロード、アニメーション待ちで数十秒～数分
    2. 脆い: UIの微小な変更で壊れる（ボタンのIDが変わるだけで失敗）
    3. Flaky: ネットワーク遅延、非同期処理のタイミングで不安定
    4. 高コスト: 書くのも直すのも時間がかかる

    だから「最も重要なユーザーフロー」だけをE2Eテストにする。
    例: ログイン → 商品をカートに入れる → 決済 → 注文確認
    このフローが壊れたらビジネスが止まるから、E2Eでカバーする価値がある。
    """)

    # --- TDD / BDD ---
    heading("1-5. TDD (Test-Driven Development)")

    p("""
    先に結論: 「1-5. TDD (Test-Driven Development)」は実装と設計判断に直結する。背景とトレードオフを押さえる。
    TDD（テスト駆動開発）は「テストを先に書き、テストが通るコードを後から書く」
    開発手法だ。Kent Beck が提唱した。

    TDDの3ステップ（Red-Green-Refactorサイクル）:

    1. RED:    失敗するテストを1つ書く（まだ実装がないので赤く失敗する）
    2. GREEN:  テストが通る最小限のコードを書く（きれいでなくていい）
    3. REFACTOR: テストを維持しながら、コードをきれいにする

    このサイクルを数分単位で繰り返す。

    なぜTDDが有効か？
    - 仕様を先に明確にする: テストを書くことで「何を作るか」が曖昧なまま実装に入ることを防ぐ
    - 過剰実装を防ぐ (YAGNI): テストが求める最小限だけ実装するので、不要な機能を作らない
    - リファクタリングの安全網: テストがあるからコードを大胆に変更できる
    - ドキュメントになる: テストが「このコードは何をすべきか」の仕様書になる

    TDDの具体例 ── Stackクラスを作る:

    # Step 1 [RED]: テストを書く → Stack クラスがないので失敗
    def test_new_stack_is_empty():
        s = Stack()
        assert s.is_empty() == True
        assert len(s) == 0

    # Step 2 [GREEN]: 最小限の実装
    class Stack:
        def __init__(self):
            self._items = []
        def is_empty(self):
            return len(self._items) == 0
        def __len__(self):
            return len(self._items)

    # Step 3 [RED]: 次のテスト → push がないので失敗
    def test_push():
        s = Stack()
        s.push(42)
        assert not s.is_empty()

    # Step 4 [GREEN]: push を実装 ... 以下繰り返し
    """)

    misconception(
        "TDDは全てのコードに適用すべき",
        "TDDはビジネスロジック（計算、バリデーション、状態遷移）に最も効果的。"
        "UIやインフラ層のコードはTDDに向かないことが多い。道具として使い分けるのが正解"
    )

    heading("1-6. BDD (Behavior-Driven Development)")

    p("""
    この節の狙い: 「1-6. BDD (Behavior-Driven Development)」を単語暗記ではなく、なぜ必要かまでつながる形で理解する。
    BDD（振る舞い駆動開発）は、TDDを「ビジネス要件の言葉で書く」ように拡張したものだ。
    Dan North が提唱した。

    TDDとBDDの違い:
    - TDD: 「このメソッドにこの入力を渡すとこの出力が返る」（技術者視点）
    - BDD: 「この状況で、この操作をすると、こうなる」（ビジネス視点）

    BDDのフォーマット「Given-When-Then」:

    Feature: 大量注文の割引
      Scenario: 100個以上の注文で20%割引
        Given: 顧客が商品を選択している
        When:  100個の注文を確定する
        Then:  合計金額に20%の割引が適用される

    このフォーマットの利点:
    - 非エンジニア（PM、デザイナー、ビジネス担当者）が読める
    - 仕様の曖昧さが減る（「100個ちょうどは割引対象か？」が明確になる）
    - テストコードがそのまま仕様書になる

    ツール: Cucumber (Java/JS), Behave (Python), SpecFlow (.NET)
    """)

    heading("1-5b. Flaky Test (不安定なテスト) の原因と対策")

    p("""
    先に結論: 「1-5b. Flaky Test (不安定なテスト) の原因と対策」は実装と設計判断に直結する。背景とトレードオフを押さえる。
    Flaky Test とは「同じコード・同じ入力でも、通ったり失敗したりするテスト」だ。
    CIが赤くなっても「ああ、またあのFlakyテストか」と無視されるようになると、
    テストスイート全体の信頼性が崩壊する。

    Flaky Test の原因と対策:

    1. 時間依存:
       原因: datetime.now() をハードコード
       対策: Clock インジェクション（時刻を外部から注入）
             freezegun ライブラリで時刻を固定

       ❌ def is_business_hours():
              return 9 <= datetime.now().hour < 18
       ✅ def is_business_hours(clock=datetime.now):
              return 9 <= clock().hour < 18

    2. 順序依存:
       原因: テスト間で共有状態（グローバル変数、DB）を変更
       対策: 各テストで setUp/tearDown を使い状態をリセット
             テスト間の依存を排除（各テストが独立に実行可能）

    3. 並行性の非決定性:
       原因: マルチスレッドでの実行順序がランダム
       対策: 同期メカニズム（Event, Lock）を正しく使う
             テストではシングルスレッドで実行

    4. 外部依存:
       原因: ネットワーク、外部API、ファイルシステムの不安定さ
       対策: テストダブル（Mock, Stub, Fake）で外部を隔離
             Testcontainers で再現可能な環境を構築

    5. リソース競合:
       原因: ポート番号の競合、ディスクフル、ファイルロック
       対策: 動的ポート割当、一時ディレクトリの使用、テスト後のクリーンアップ

    6. 浮動小数点:
       原因: 0.1 + 0.2 != 0.3 (IEEE 754の仕様)
       対策: assertAlmostEqual / math.isclose を使う
             金額計算には Decimal 型を使う

    Flaky Testの検出方法:
    - 同じコミットでテストを10回実行し、結果が異なるテストを探す
    - CI でテスト結果の履歴を追跡（特定のテストの失敗率を可視化）
    - quarantine（隔離）: Flakyなテストを一時的に分離して修正に集中
    """)

    interview("""
    Q: TDDとBDDの違いは何ですか？
    A: TDDは技術者が「関数の入出力」をテストとして先に書く手法です。
       BDDはその考え方をビジネス要件レベルに拡張し、
       Given-When-Then形式で「振る舞い」を記述します。
       TDDは実装の正しさ、BDDはビジネス要件の正しさを検証する点が異なります。
       実務では両方を併用することが多く、BDDでE2E/統合テストを、
       TDDで単体テストを書くのが一般的です。
    """)

    # --- テストダブル ---
    heading("1-7. テストダブル (Test Double)")

    p("""
    まず全体像: この節では「1-7. テストダブル (Test Double)」を、定義 -> 仕組み -> 実務上の判断の順で整理する。
    テストダブルとは「テスト時に本物の依存オブジェクトの代わりに使う偽物」の総称だ。
    映画のスタントダブル（代役）から名前が来ている。
    Gerard Meszaros が『xUnit Test Patterns』で5種類に分類した。

    なぜテストダブルが必要か？
    OrderService が PaymentGateway（外部決済API）に依存しているとする。
    テストのたびに本物の決済APIを呼ぶわけにはいかない:
    - 実際にお金が動いてしまう
    - APIが遅い（テストが遅くなる）
    - APIがダウンしているとテストが失敗する
    - エラーケース（残高不足、タイムアウト）を再現できない

    だから「偽物の決済API」を使う。その偽物の種類が5つある。
    """)

    p("""
    ┌──────────┬──────────────────────────────────────────────────────┐
    │ 種類      │ 役割と特徴                                          │
    ├──────────┼──────────────────────────────────────────────────────┤
    │ Dummy    │ 引数を埋めるためだけに渡す。中身は空。呼ばれたらエラー  │
    │          │ 例: テスト対象がloggerを受け取るが、テスト内容と無関係  │
    ├──────────┼──────────────────────────────────────────────────────┤
    │ Stub     │ 固定値を返す。テスト対象への「入力」を制御する         │
    │          │ 例: get_user() が常に {"name": "Alice"} を返す        │
    ├──────────┼──────────────────────────────────────────────────────┤
    │ Spy      │ Stub + 呼び出しを記録する。「後から」検証する          │
    │          │ 例: send_email() が何回、どんな引数で呼ばれたか記録   │
    ├──────────┼──────────────────────────────────────────────────────┤
    │ Mock     │ 期待する呼び出しを事前に設定し、自動で検証する         │
    │          │ 例: charge(500, "tok_x") が正確に1回呼ばれることを期待│
    ├──────────┼──────────────────────────────────────────────────────┤
    │ Fake     │ 本物の簡易実装。動作するが本番には使わない             │
    │          │ 例: InMemoryDatabase（SQLの代わりにdictで保存）        │
    └──────────┴──────────────────────────────────────────────────────┘

    使い分けの判断基準:
    - 「呼ばれたかどうか」を検証したい → Mock or Spy
    - 「返り値を制御したい」だけ → Stub
    - 「本物に近い動作がほしい」 → Fake
    - 「引数を埋めるだけ」 → Dummy
    """)

    p("""
    Python での実装例:

    # --- Stub: 固定値を返す ---
    class StubPaymentGateway:
        def charge(self, amount, card_token):
            return {"status": "success", "transaction_id": "txn_stub_001"}

    # --- Spy: 呼び出しを記録 ---
    class SpyPaymentGateway:
        def __init__(self):
            self.charge_calls = []
        def charge(self, amount, card_token):
            self.charge_calls.append((amount, card_token))
            return {"status": "success"}

    # テストで検証:
    spy = SpyPaymentGateway()
    service.process_order(spy)
    assert len(spy.charge_calls) == 1
    assert spy.charge_calls[0] == (500, "tok_abc")

    # --- Mock: unittest.mock を使う ---
    from unittest.mock import MagicMock
    mock_gw = MagicMock()
    mock_gw.charge.return_value = {"status": "success"}
    service.process_order(mock_gw)
    mock_gw.charge.assert_called_once_with(500, "tok_abc")

    # --- Fake: インメモリDB ---
    class FakeDatabase:
        def __init__(self):
            self.data = {}
        def save(self, key, value):
            self.data[key] = value
        def find(self, key):
            return self.data.get(key)
    """)

    p("""
    unittest.mock の実践的な使い方:

    from unittest.mock import patch, MagicMock, PropertyMock

    # --- patch: モジュールレベルのオブジェクトを差し替え ---

    # 1. デコレータとして
    @patch('myapp.services.requests.get')
    def test_fetch_data(mock_get):
        mock_get.return_value.json.return_value = {"name": "Alice"}
        result = fetch_user(1)
        assert result["name"] == "Alice"
        mock_get.assert_called_once_with("https://api.example.com/users/1")

    # 2. コンテキストマネージャとして
    def test_send_email():
        with patch('myapp.services.smtp_client') as mock_smtp:
            send_welcome_email("bob@example.com")
            mock_smtp.send.assert_called_once()
            # 引数の検証
            args, kwargs = mock_smtp.send.call_args
            assert "Welcome" in args[1]

    # 3. side_effect で例外やシーケンスを設定
    mock_db = MagicMock()
    mock_db.query.side_effect = [
        [{"id": 1}],          # 1回目の呼び出し
        [],                    # 2回目の呼び出し
        ConnectionError("DB down"),  # 3回目は例外
    ]

    # 4. spec で型安全にする
    mock_repo = MagicMock(spec=UserRepository)
    # mock_repo.non_existent_method()  → AttributeError!
    # spec を使うと存在しないメソッドの呼び出しを検出できる

    注意: Mockの過剰使用はテストを実装に密結合させる。
    「何が返るか (state verification)」 のテストを優先し、
    「何が呼ばれたか (behavior verification)」 は副作用の検証に限定する。
    """)

    misconception(
        "MockとStubは同じもの",
        "Stubは「入力の制御」（何を返すか）、Mockは「出力の検証」（何が呼ばれたか）。"
        "Stubはテスト対象に値を注入し、Mockはテスト対象の振る舞いを検証する。目的が違う"
    )

    interview("""
    Q: テストダブルの5種類を説明してください。
    A: Dummy（引数埋め、中身なし）、Stub（固定値を返す、入力制御）、
       Spy（Stub+呼び出し記録、後から検証）、
       Mock（期待値を事前設定し自動検証）、
       Fake（簡易実装、InMemoryDB等）の5種類です。
       Mockの多用はテストが実装に密結合するリスクがあるため、
       状態の検証（Stubで値を返して結果を確認）を優先し、
       Mockは副作用（メール送信、ログ記録等）の検証に限定するのがベストプラクティスです。
    """)


# ======================================================================
#  第2章: テスト技法 — 上級テクニック
# ======================================================================

def chapter_2_test_techniques():
    title("第2章: テスト技法 — Property-based Testing から Contract Testing まで")

    # --- Property-based Testing ---
    heading("2-1. Property-based Testing (性質ベーステスト)")

    p("""
    先に結論: 「2-1. Property-based Testing (性質ベーステスト)」は実装と設計判断に直結する。背景とトレードオフを押さえる。
    従来のテストは「具体的な入力と期待出力」を書く:
      assert sort([3, 1, 2]) == [1, 2, 3]

    しかしこれでは「テストに書いたケース」しか検証できない。
    [3, 1, 2] でうまくいっても、[-5, 0, 0, 100] では壊れるかもしれない。

    Property-based Testing は発想を逆転させる。
    「具体的な入出力」ではなく「常に成り立つべき性質（プロパティ）」を書く:

      プロパティ1: sort(sort(xs)) == sort(xs)   # 冪等性
      プロパティ2: len(sort(xs)) == len(xs)      # 長さ保存
      プロパティ3: sort(xs) の全要素が xs に含まれる  # 要素保存
      プロパティ4: sort(xs)[i] <= sort(xs)[i+1]  # 順序性

    そしてテストフレームワーク（Hypothesis など）がランダムな入力を大量に生成し、
    プロパティが破られるケースを探す。

    ランダムで壊れるケースが見つかったら「Shrinking」が始まる。
    Shrinkingとは、反例（プロパティを破る入力）をできるだけ小さくする処理だ。
    [47, -82, 3, 0, 15, -23, 8] で壊れたとしても、
    最小の反例は [-1] かもしれない。小さい方がバグの原因を特定しやすい。
    """)

    p("""
    Property-based Testing が特に有効な場面:
    1. シリアライズ/デシリアライズ: decode(encode(x)) == x
    2. データ変換: 逆変換で元に戻る（暗号化、圧縮、エンコーディング）
    3. 数学的性質: 結合法則、交換法則、単位元
    4. パーサー: 有効な入力を生成して、パースが成功することを確認
    5. ステートマシン: ランダムな操作列でも不変条件が維持される

    ツール:
    - Python: Hypothesis（業界標準）
    - Java: jqwik
    - Haskell: QuickCheck（元祖）
    - JavaScript: fast-check
    """)

    misconception(
        "ランダムテストはテストの信頼性を下げる",
        "Property-based Testing はランダムだが、シードを固定して再現可能にできる。"
        "さらにShrinkingにより最小反例が得られるため、バグの特定は手動テストより速い"
    )

    # --- Mutation Testing ---
    heading("2-2. Mutation Testing (ミューテーションテスト)")

    p("""
    この節の狙い: 「2-2. Mutation Testing (ミューテーションテスト)」を単語暗記ではなく、なぜ必要かまでつながる形で理解する。
    「テストが通ったからOK」は本当か？
    Line Coverage 100% でもバグを見逃すことがある。

    例:
      def is_adult(age):
          return age >= 18

      # このテストスイートはLine Coverage 100%
      assert is_adult(20) == True
      assert is_adult(10) == False

    しかし、もし実装が age > 18 に変わったら？（>= ではなく >）
    18歳が「未成年」扱いになるバグが入るが、
    上のテストスイートではこのバグを検出できない。
    なぜなら 18歳をテストしていないからだ。

    Mutation Testing は「テストの品質」を測定する手法だ。

    手順:
    1. ソースコードに小さな変更（ミューテーション）を加える
       例: >= を > に変える、+ を - に変える、return True を return False に変える
    2. 変更したコード（ミュータント）に対してテストスイートを実行する
    3. テストが失敗する → ミュータントは「殺された (killed)」 → テストは有効
       テストが通る → ミュータントは「生き残った (survived)」→ テストが不足

    Mutation Score = 殺されたミュータント数 / 全ミュータント数

    Mutation Score 80%以上が一般的な目標。
    Line Coverage が 100% でも Mutation Score が 60% なら、テストが甘い証拠だ。
    """)

    p("""
    主なミューテーション演算子:
    - 比較演算子: >= → >, <= → <, == → !=
    - 算術演算子: + → -, * → /, % → *
    - 論理演算子: and → or, not の除去
    - 定数変更: 0 → 1, True → False
    - 文の削除: return 文を削除、if分岐を削除
    - 境界値: n+1 → n, n-1 → n

    ツール:
    - Python: mutmut, cosmic-ray
    - Java: PITest
    - JavaScript: Stryker
    """)

    interview("""
    Q: テストカバレッジ100%は十分ですか？
    A: Line Coverageは「コードが実行されたか」を測るだけで、
       「正しい動作を検証しているか」は測れません。
       Mutation Testingを使うと、テストが実際にバグを検出する能力を測定できます。
       Coverage 100% でも Mutation Score が低ければ、テストは表面的です。
       理想は Branch Coverage 90%以上 + Mutation Score 80%以上です。
    """)

    # --- Fuzzing ---
    heading("2-3. Fuzzing (ファジング)")

    p("""
    先に結論: 「2-3. Fuzzing (ファジング)」は実装と設計判断に直結する。背景とトレードオフを押さえる。
    Fuzzingは「意図的に異常な入力をプログラムに与えて、
    クラッシュやセキュリティ脆弱性を見つける」手法だ。

    Property-based Testing との違い:
    - Property-based Testing: 「性質が成り立つか」を検証。入力は型に合ったもの
    - Fuzzing: 「壊れるか」を検証。入力はバイト列レベルのでたらめなデータ

    Fuzzingの種類:
    1. ダムファジング (Dumb Fuzzing): 完全にランダムなバイト列を投げる
    2. スマートファジング (Smart Fuzzing): 入力フォーマットを理解して変異させる
    3. カバレッジガイドファジング: コードカバレッジをフィードバックに使い、
       新しいコードパスを通る入力を優先的に生成する

    ツール:
    - AFL (American Fuzzy Lop): カバレッジガイドの元祖
    - libFuzzer (LLVM): Googleが開発、Chrome/OpenSSL等で使用
    - OSS-Fuzz: Googleが運営する自動Fuzzingサービス
    - Atheris: Python向けカバレッジガイドファザー

    成果例: Heartbleed (OpenSSL) はFuzzingで発見可能だった脆弱性。
    Googleは OSS-Fuzz で 850以上のOSSプロジェクトから 10,000以上のバグを発見している。
    """)

    # --- Snapshot Testing ---
    heading("2-4. Snapshot Testing (スナップショットテスト)")

    p("""
    まず全体像: この節では「2-4. Snapshot Testing (スナップショットテスト)」を、定義 -> 仕組み -> 実務上の判断の順で整理する。
    Snapshot Testing は「出力の全体像を記録し、変更を検出する」手法だ。

    通常のテスト: assert output == "期待値"
    スナップショットテスト: output を __snapshots__/test.snap に保存。
    次回実行時に保存された値と比較。一致すればOK、異なれば差分を表示。

    用途:
    - UIコンポーネントのHTML出力（React の react-test-renderer）
    - API レスポンスの構造
    - 設定ファイルの生成結果
    - コンパイラの出力

    利点:
    - 期待値を手で書かなくていい（初回は自動保存）
    - 大きな出力構造の回帰テストに強い

    欠点:
    - 意図的な変更でもスナップショットを更新する手間がかかる
    - 「スナップショットを何も考えずに更新する」習慣がつくと無意味になる
    - 出力が大きいと差分レビューが困難

    ベストプラクティス:
    - スナップショットは小さく保つ
    - レビューで「なぜ変わったか」を必ず確認する
    - 非決定的な値（タイムスタンプ、ID）はマスクする
    """)

    # --- Contract Testing ---
    heading("2-5. Contract Testing (契約テスト)")

    p("""
    先に結論: 「2-5. Contract Testing (契約テスト)」は実装と設計判断に直結する。背景とトレードオフを押さえる。
    マイクロサービスが増えると、サービス間のAPI仕様が重要になる。
    UserService が返す JSON のフィールドを変更したら、
    OrderService が壊れるかもしれない。

    Contract Testing は「APIの契約（インターフェース仕様）を
    消費者（Consumer）と提供者（Provider）の間で共有し、
    互換性を自動検証する」手法だ。

    Consumer-Driven Contract (CDC):
    1. Consumer が「私はこのフィールドをこの型で使います」という契約を書く
    2. Provider がその契約を満たしているか自動テストで検証する
    3. Provider は契約を壊す変更をデプロイできない

    アナロジー:
    レストラン（Provider）とお客（Consumer）の関係。
    メニュー（Contract）に「カレーライス 800円」と書いてあるのに、
    「今日からカレーは1500円です」と勝手に変えたらお客は怒る。
    メニューの変更はお客と合意してから行う。

    後方互換性のルール:
    ✅ OK: オプショナルフィールドの追加
    ✅ OK: 新しいAPIエンドポイントの追加
    ❌ NG: フィールドの削除
    ❌ NG: フィールドの型変更
    ❌ NG: 必須フィールドの追加

    ツール:
    - Pact: Consumer-Driven Contract Testing のデファクト
    - Spring Cloud Contract: Java/Spring向け
    - Prism: OpenAPI仕様からモックサーバーを自動生成
    """)

    interview("""
    Q: マイクロサービス間のAPI互換性をどう保証しますか？
    A: Consumer-Driven Contract Testing を使います。
       ConsumerがPactファイル（期待するレスポンス構造）を定義し、
       ProviderのCIパイプラインでそのPactを検証します。
       Providerは全Consumerの契約を満たさない限りデプロイできません。
       これにより「APIの変更で他のサービスが壊れる」問題を防げます。
       後方互換性を維持するため、フィールド追加はオプショナルに限定し、
       破壊的変更はAPIバージョニング（/v2/users）で対応します。
    """)


# ======================================================================
#  第3章: パフォーマンスエンジニアリング
# ======================================================================

def chapter_3_performance():
    title("第3章: パフォーマンスエンジニアリング — 計測、分析、最適化")

    heading("3-1. Big-O 分析 — 計算量を見積もる")

    p("""
    先に結論: 「3-1. Big-O 分析 — 計算量を見積もる」は実装と設計判断に直結する。背景とトレードオフを押さえる。
    Big-O記法は「入力サイズが大きくなったとき、処理時間がどう増えるか」を表す。
    正確には「漸近的な上界」だが、実務では「最悪ケースの成長率」と理解すれば十分。

    アナロジー:
    本棚から本を探すとする。
    - O(1): 本の場所を知っている → 直接取る（辞書のインデックス）
    - O(log n): 本がアルファベット順 → 二分探索
    - O(n): 本が無秩序 → 端から順に探す
    - O(n log n): 本を一旦並べ替えてから探す
    - O(n²): 全ての本と全ての本を比較する（バブルソート）
    - O(2^n): 本の全ての組み合わせを試す（部分集合問題）

    主要なデータ構造の計算量:

    | 操作        | 配列(list) | 連結リスト | dict/set | ソート済配列 |
    |-------------|-----------|-----------|---------|-------------|
    | アクセス    | O(1)      | O(n)      | -       | O(1)        |
    | 検索        | O(n)      | O(n)      | O(1)*   | O(log n)    |
    | 挿入(先頭)  | O(n)      | O(1)      | O(1)*   | O(n)        |
    | 挿入(末尾)  | O(1)*     | O(1)      | O(1)*   | O(n)        |
    | 削除        | O(n)      | O(1)      | O(1)*   | O(n)        |

    * は「平均」。最悪ケースでは異なる場合がある。
    dict の最悪は O(n)（ハッシュ衝突時）だが、実用上は O(1)。

    「O(n) と O(n²) の違い」が実際にどれだけ効くか:
    n = 1,000    → O(n)=1,000,     O(n²)=1,000,000       (1000倍)
    n = 1,000,000 → O(n)=1,000,000, O(n²)=1,000,000,000,000 (100万倍!)

    O(n²) のアルゴリズムが n=100 で動くからといって、
    n=100,000 でも動くとは限らない。これがBig-Oの実務的な重要性だ。
    """)

    misconception(
        "O(1) は O(n) より常に速い",
        "Big-Oは成長率であり、定数倍を無視する。O(1)でも定数が巨大なら、"
        "小さいnではO(n)の方が速い。例: ハッシュテーブルの検索(O(1))は"
        "要素3個の配列の線形探索(O(n))より遅いことがある"
    )

    p("""
    計算量改善の実例:

    問題: リストの中から2つの数の和がtargetになるペアを見つける (Two Sum)

    # O(n²) ブルートフォース
    def two_sum_brute(nums, target):
        for i in range(len(nums)):
            for j in range(i+1, len(nums)):
                if nums[i] + nums[j] == target:
                    return [i, j]
        return []

    # O(n) ハッシュマップ
    def two_sum_hash(nums, target):
        seen = {}
        for i, num in enumerate(nums):
            complement = target - num
            if complement in seen:
                return [seen[complement], i]
            seen[num] = i
        return []

    n=10,000 の場合:
    - O(n²): 10,000 × 10,000 = 100,000,000 回のループ → 数秒
    - O(n):  10,000 回のループ + dict検索 → 数ミリ秒

    アルゴリズム改善 > 定数倍改善
    O(n²) をどれだけチューニングしても O(n) には勝てない。
    最適化の第一歩は「アルゴリズムの計算量を下げること」だ。

    よくある計算量改善パターン:
    - 線形探索 → ハッシュテーブル: O(n) → O(1)
    - ソートして二分探索: O(n) → O(log n) (ソートは O(n log n) 前払い)
    - 再帰 → メモ化 (Dynamic Programming): O(2^n) → O(n)
    - ネストループ → Two Pointers: O(n²) → O(n)
    """)

    heading("3-2. プロファイリング — 推測するな、計測せよ")

    p("""
    先に結論: 「3-2. プロファイリング — 推測するな、計測せよ」は実装と設計判断に直結する。背景とトレードオフを押さえる。
    「推測するな、計測せよ」(Measure, don't guess) — Rob Pike

    パフォーマンス最適化の最大の過ちは「遅いと思う場所」を最適化すること。
    実際にボトルネックになっている場所は、直感と違うことが多い。

    Pythonのプロファイリングツール:

    1. cProfile (CPU時間の計測):
       python -m cProfile -s cumulative my_script.py

       出力例:
         ncalls  tottime  percall  cumtime  percall filename:lineno(function)
         10000   0.500    0.000    0.500    0.000   engine.py:25(calculate)
         1       0.001    0.001    0.501    0.501   main.py:10(run)

       - ncalls: 呼び出し回数
       - tottime: その関数自体の実行時間（子関数を含まない）
       - cumtime: その関数+子関数の合計時間

    2. line_profiler (行単位の計測):
       @profile デコレータをつけて kernprof -lv my_script.py

    3. tracemalloc (メモリ使用量):
       import tracemalloc
       tracemalloc.start()
       # ... 処理 ...
       snapshot = tracemalloc.take_snapshot()
       top_stats = snapshot.statistics('lineno')
       for stat in top_stats[:10]:
           print(stat)

    4. perf (Linux): syscall レベルのプロファイリング
       perf record python my_script.py
       perf report

    プロファイリングの手順:
    1. まず再現可能なベンチマーク環境を用意する
    2. プロファイラで計測し、ボトルネックを特定する
    3. ボトルネック以外は触らない（Amdahlの法則）
    4. 最適化後に再計測して効果を確認する
    """)

    p("""
    Amdahl の法則 (アムダールの法則):
    全体のうちP%が最適化可能なら、その部分をS倍速くしたとき、
    全体の高速化率 = 1 / ((1-P) + P/S)

    例: 処理全体の20%がボトルネック（P=0.2）で、それを10倍速くする（S=10）
    全体の高速化 = 1 / (0.8 + 0.02) = 1.22倍 (たった22%!)

    つまり、ボトルネックが全体の20%しか占めないなら、
    そこを100倍速くしても全体は1.25倍にしかならない。
    ボトルネックの占める割合が小さいなら、最適化する価値がない。
    逆に、全体の80%を占めるボトルネックを2倍速くすれば全体は1.67倍になる。
    """)

    heading("3-3. メモリリーク検出")

    p("""
    この節の狙い: 「3-3. メモリリーク検出」を単語暗記ではなく、なぜ必要かまでつながる形で理解する。
    メモリリークとは「使い終わったメモリが解放されず、消費量が増え続ける」問題だ。

    Pythonは参照カウント + GC（ガベージコレクション）で自動メモリ管理するが、
    以下のケースでメモリリークが起きる:

    1. 循環参照 + __del__ メソッド:
       class A:
           def __init__(self):
               self.b = None
           def __del__(self):
               print("deleted")
       class B:
           def __init__(self):
               self.a = None
       a = A(); b = B()
       a.b = b; b.a = a  # 循環参照
       del a; del b  # GCが回収できない（__del__がある場合）

    2. グローバル変数にキャッシュし続ける:
       cache = {}
       def process(key, data):
           cache[key] = data  # 永遠にcacheが成長する
       → 対策: maxsize付きの @lru_cache や TTL付きキャッシュを使う

    3. クロージャが外側の変数を保持:
       def create_handlers():
           handlers = []
           for i in range(10000):
               big_data = [0] * 1000000  # 巨大なリスト
               handlers.append(lambda: big_data)  # big_data が保持される
           return handlers

    4. C拡張モジュールのメモリリーク:
       ctypes や cffi 経由で確保したメモリを解放し忘れる

    検出方法:
    - tracemalloc: Pythonレベルのメモリアロケーションを追跡
    - objgraph: オブジェクトの参照グラフを可視化
    - gc.get_objects(): GC管理下のオブジェクト一覧
    - weakref: 弱参照を使って循環参照を避ける
    - Valgrind (C拡張): ネイティブレベルのメモリリーク検出
    """)

    heading("3-4. キャッシュ戦略 (LRU / LFU)")

    p("""
    まず全体像: この節では「3-4. キャッシュ戦略 (LRU / LFU)」を、定義 -> 仕組み -> 実務上の判断の順で整理する。
    キャッシュは「遅い処理の結果を保存して、2回目以降を高速化する」仕組みだ。
    CPUキャッシュ、ブラウザキャッシュ、CDN、Redis — 至る所にキャッシュがある。

    キャッシュの効果:
    L1キャッシュ:  ~1ns (4 CPUサイクル)
    RAM:          ~100ns (400 CPUサイクル) → キャッシュで100倍速い
    SSD:          ~100μs (400,000 CPUサイクル) → キャッシュで100,000倍速い
    ネットワーク:  ~100ms → キャッシュで100,000,000倍速い

    問題は「キャッシュが満杯になったとき、何を追い出すか」だ。
    これがキャッシュ置換アルゴリズム。

    LRU (Least Recently Used):
    「最も最近使われていないものを追い出す」
    - 実装: OrderedDict（アクセスしたら末尾に移動、先頭を追い出す）
    - 時間計算量: O(1)（dictとdoubly-linked listの組み合わせ）
    - 用途: 汎用的。WebサーバーのレスポンスキャッシュやDBのクエリキャッシュ
    - Python: functools.lru_cache がこれ

    LFU (Least Frequently Used):
    「最もアクセス頻度が低いものを追い出す」
    - 実装: 頻度ごとのリスト + dict
    - 時間計算量: O(1)（工夫が必要）
    - 用途: アクセスパターンに偏りがある場合（ホットキー問題）
    - 問題点: 過去の頻度に引きずられる（一時的に人気だったキーが残り続ける）

    LRU vs LFU の使い分け:
    - アクセスパターンが時間的局所性を持つ → LRU
      （最近使われたものは再び使われやすい）
    - アクセスパターンに頻度の偏りがある → LFU
      （人気アイテムは常にアクセスされる）
    - 迷ったら LRU（シンプルで十分効果的）
    """)

    p("""
    キャッシュ戦略パターン:

    Cache-Aside (Lazy Loading):
      1. アプリがキャッシュに問い合わせ
      2. なければDBから読み、キャッシュに保存
      3. 次回はキャッシュから返す
      → 最も一般的。キャッシュミスのコストはDB読み取り

    Read-Through:
      1. アプリはキャッシュだけに問い合わせ
      2. キャッシュが自動的にDBから読み込む
      → アプリがDB接続を知らなくていい

    Write-Through:
      1. アプリがキャッシュに書き込み
      2. キャッシュが同時にDBにも書き込み
      → データの整合性が高い。書き込みは遅い

    Write-Behind (Write-Back):
      1. アプリがキャッシュに書き込み
      2. キャッシュが非同期でDBに書き込み
      → 書き込みが速い。キャッシュが落ちるとデータが消える

    Cache Stampede（Thundering Herd）問題:
    人気キーのTTLが切れた瞬間、大量のリクエストが同時にDBに殺到する。
    対策:
    1. Probabilistic Early Expiration: TTL切れの前にランダムに更新
    2. Lock: 1リクエストだけDBに問い合わせ、他は待機
    3. Stale-while-revalidate: 古い値を返しつつバックグラウンドで更新
    """)

    interview("""
    Q: キャッシュ戦略について説明してください。
    A: 読み取りにはCache-Aside（キャッシュミス時にDBから読んでキャッシュ保存）が最も一般的です。
       書き込みにはWrite-Through（即座にDB同期、整合性重視）か
       Write-Behind（非同期DB書き込み、速度重視）を使い分けます。
       置換アルゴリズムはLRU（最近未使用を追い出す）が汎用的で、
       アクセス頻度に偏りがあればLFUを検討します。
       Cache Stampede対策として、TTL前のランダム更新やLock機構を組み合わせます。
    """)

    heading("3-5. 接続プール (Connection Pool)")

    p("""
    先に結論: 「3-5. 接続プール (Connection Pool)」は実装と設計判断に直結する。背景とトレードオフを押さえる。
    接続プールとは「DBやHTTPの接続を使い回す仕組み」だ。

    なぜ必要か？ TCP接続の確立には3-wayハンドシェイクが必要で、
    さらにTLS接続なら追加のラウンドトリップが発生する。
    リクエストのたびに接続を作ると:
    - 接続確立: ~1ms (ローカル) ~ 100ms (リモート)
    - TLS: 追加 ~50-100ms
    - 毎秒1000リクエストなら、接続だけで100秒/秒のオーバーヘッド

    接続プールは事前に接続を確立し、リクエスト間で使い回す。

    サイジング（適切なプールサイズ）:

    Little's Law: L = λ × W
    - L: 同時に必要な接続数（プールサイズ）
    - λ: リクエストレート（req/sec）
    - W: 平均レスポンスタイム（sec）

    例:
    - 100 req/sec, 平均 50ms → L = 100 × 0.05 = 5 接続
    - 1000 req/sec, 平均 200ms → L = 1000 × 0.2 = 200 接続

    HikariCP (Java) の推奨公式:
    pool_size = CPU_cores × 2 + disk_spindles
    → 4コア + SSD(1) = 9 接続（意外と小さい!）

    プールが大きすぎると:
    - DB側のメモリ消費増大
    - コンテキストスイッチ増加
    - Lock contention 増加
    「大きければ良い」は間違い。計測して最適値を見つける。
    """)

    misconception(
        "接続プールのサイズは大きいほど良い",
        "プールサイズを大きくすると、DBサーバーのリソース消費が増え、"
        "かえって全体のスループットが下がる。Little's Law で必要最小限を計算し、"
        "負荷テストで検証するのが正しいアプローチ"
    )


# ======================================================================
#  第4章: Python高度 — メタクラス、デスクリプタ、GIL、asyncio、型ヒント
# ======================================================================

def chapter_4_python_advanced():
    title("第4章: Python高度 — 言語の内部構造を理解する")

    heading("4-1. メタクラス (Metaclass)")

    p("""
    まず全体像: この節では「4-1. メタクラス (Metaclass)」を、定義 -> 仕組み -> 実務上の判断の順で整理する。
    Pythonでは「全てがオブジェクト」だ。関数もクラスもオブジェクト。
    では「クラスは何のインスタンスか？」→ メタクラスのインスタンスだ。

    通常のインスタンス生成:
      obj = MyClass()  → MyClass.__call__() が呼ばれる

    クラス自体の生成:
      class MyClass: ... → type.__call__() が呼ばれる

    つまり:
      obj のクラス = MyClass
      MyClass のクラス = type（デフォルトのメタクラス）
      type のクラス = type（自分自身）

    >>> type(42)        # <class 'int'>
    >>> type(int)       # <class 'type'>
    >>> type(type)      # <class 'type'>

    メタクラスを使うと「クラスの生成過程をカスタマイズ」できる。

    例: 全てのメソッドに自動ログを追加するメタクラス

    class LoggingMeta(type):
        def __new__(mcs, name, bases, namespace):
            for key, value in namespace.items():
                if callable(value) and not key.startswith('_'):
                    namespace[key] = mcs._add_logging(value)
            return super().__new__(mcs, name, bases, namespace)

        @staticmethod
        def _add_logging(func):
            def wrapper(*args, **kwargs):
                print(f"Calling {func.__name__}")
                return func(*args, **kwargs)
            return wrapper

    class MyService(metaclass=LoggingMeta):
        def process(self):
            return "done"

    # MyService().process() → "Calling process" が自動出力される

    メタクラスの典型的な用途:
    1. Singleton パターン（インスタンスを1つに制限）
    2. ORM（Django Model のように、クラス定義からDB操作を自動生成）
    3. API登録（クラスを定義するだけで自動登録）
    4. バリデーション（クラス定義時にフィールドの制約を検証）
    """)

    p("""
    メタクラスの生成フロー:

    class Foo(metaclass=Meta):
        x = 1
        def method(self): pass

    裏側で起きること:
    1. Python が class 文を実行
    2. namespace = Meta.__prepare__('Foo', ())  ← 名前空間の準備
    3. class body を namespace に exec
    4. Foo = Meta.__new__(Meta, 'Foo', (), namespace)  ← クラス生成
    5. Meta.__init__(Foo, 'Foo', (), namespace)  ← 初期化

    __prepare__ は Python 3 で追加された。
    OrderedDict を返すことで、定義順序を保存できる（Django Model のフィールド順序）。
    """)

    misconception(
        "メタクラスは高度なテクニックなので積極的に使うべき",
        "Tim Peters（Zen of Python の著者）の言葉: "
        "「メタクラスが必要かどうか迷うなら、必要ない」。"
        "99%のケースはクラスデコレータ、__init_subclass__、"
        "デスクリプタで解決できる。メタクラスはフレームワーク作成者向け"
    )

    p("""
    __init_subclass__ (Python 3.6+): メタクラスの軽量代替

    class Plugin:
        _registry = {}

        def __init_subclass__(cls, plugin_name=None, **kwargs):
            super().__init_subclass__(**kwargs)
            name = plugin_name or cls.__name__.lower()
            Plugin._registry[name] = cls

        @classmethod
        def get(cls, name):
            return cls._registry[name]()

    class PDFExporter(Plugin, plugin_name="pdf"):
        def export(self): return "Exporting PDF"

    class CSVExporter(Plugin, plugin_name="csv"):
        def export(self): return "Exporting CSV"

    exporter = Plugin.get("pdf")  # PDFExporter のインスタンス

    これはメタクラスを使わずに「クラス定義時のフック」を実現できる。
    99%のケースではメタクラスより __init_subclass__ の方がシンプルで適切だ。
    """)

    heading("4-2. デスクリプタ (Descriptor)")

    p("""
    まず全体像: この節では「4-2. デスクリプタ (Descriptor)」を、定義 -> 仕組み -> 実務上の判断の順で整理する。
    デスクリプタは「属性アクセスをカスタマイズする仕組み」だ。
    property, classmethod, staticmethod は全てデスクリプタで実装されている。

    デスクリプタプロトコル:
    - __get__(self, obj, objtype=None): 属性を読み取るとき
    - __set__(self, obj, value): 属性に書き込むとき
    - __delete__(self, obj): 属性を削除するとき

    データデスクリプタ: __get__ と __set__ (or __delete__) を持つ
    非データデスクリプタ: __get__ のみ持つ

    優先順位:
    データデスクリプタ > インスタンス辞書 > 非データデスクリプタ

    実用例: 型バリデーション付きフィールド

    class Typed:
        def __init__(self, name, expected_type):
            self.name = name
            self.expected_type = expected_type

        def __set_name__(self, owner, name):
            self.name = name  # Python 3.6+: 自動で属性名を取得

        def __get__(self, obj, objtype=None):
            if obj is None:
                return self
            return obj.__dict__.get(self.name)

        def __set__(self, obj, value):
            if not isinstance(value, self.expected_type):
                raise TypeError(
                    f"{self.name} must be {self.expected_type.__name__}, "
                    f"got {type(value).__name__}"
                )
            obj.__dict__[self.name] = value

    class User:
        name = Typed('name', str)
        age = Typed('age', int)

        def __init__(self, name, age):
            self.name = name  # Typed.__set__ が呼ばれる
            self.age = age

    user = User("Alice", 30)   # OK
    user.age = "thirty"        # TypeError!

    property はデスクリプタの糖衣構文:
    @property
    def name(self):
        return self._name

    # 上は以下と等価:
    name = property(fget=lambda self: self._name)
    """)

    p("""
    property が デスクリプタ で実装されていることの証明:

    class Temperature:
        def __init__(self, celsius):
            self._celsius = celsius

        @property
        def fahrenheit(self):
            return self._celsius * 9 / 5 + 32

        @fahrenheit.setter
        def fahrenheit(self, value):
            self._celsius = (value - 32) * 5 / 9

    # 上のコードの裏側:
    # fahrenheit は property オブジェクト（デスクリプタ）
    # Temperature.fahrenheit は property(fget=..., fset=...) と等価
    # t.fahrenheit にアクセスすると property.__get__() が呼ばれる
    # t.fahrenheit = 100 とすると property.__set__() が呼ばれる

    >>> type(Temperature.__dict__['fahrenheit'])
    <class 'property'>
    >>> hasattr(Temperature.__dict__['fahrenheit'], '__get__')
    True
    >>> hasattr(Temperature.__dict__['fahrenheit'], '__set__')
    True

    デスクリプタの属性検索順序（MRO と合わせて）:
    1. データデスクリプタ（__get__ + __set__/__delete__ を持つ） ← 最優先
    2. インスタンスの __dict__
    3. 非データデスクリプタ（__get__ のみ）
    4. クラスの __dict__
    5. 親クラスの __dict__（MRO順）
    6. __getattr__（存在すれば）

    この順序があるから property（データデスクリプタ）は
    インスタンス辞書より優先される。
    classmethod や staticmethod は非データデスクリプタだ。
    """)

    heading("4-3. GIL (Global Interpreter Lock) の内部")

    p("""
    この節の狙い: 「4-3. GIL (Global Interpreter Lock) の内部」を単語暗記ではなく、なぜ必要かまでつながる形で理解する。
    GIL（Global Interpreter Lock）は CPython の実装詳細で、
    「同時に1つのスレッドだけがPythonバイトコードを実行できる」ロックだ。

    なぜGILが存在するか？
    CPythonのメモリ管理は「参照カウント」に基づいている。
    各オブジェクトが「何個の変数から参照されているか」を保持し、
    カウントが0になったら即座に解放する。

    マルチスレッドで参照カウントを安全に更新するには:
    方法A: 全オブジェクトに個別ロック → オーバーヘッド膨大
    方法B: グローバルロック1つ → シンプルだが同時実行不可

    CPythonは方法Bを選んだ。これがGILだ。

    GILの影響:
    - CPUバウンド処理: マルチスレッドでも並列にならない（1コアしか使えない）
    - I/Oバウンド処理: GILは I/O待ちの間に解放される → マルチスレッドが有効

    GILの切り替えタイミング:
    Python 3.2+: 5ms ごとにGILを解放して他のスレッドに渡す
    (以前は100バイトコード命令ごとだったが、不公平だった)

    GILの回避方法:
    1. multiprocessing: プロセスごとに独立したGIL
    2. C拡張: GILを解放してネイティブコードを実行（NumPy等）
    3. asyncio: シングルスレッドで I/O並行処理（GIL関係なし）
    4. Python 3.13+: --disable-gil オプション（実験的）

    重要: GIL は CPython の実装詳細であり、Python言語仕様ではない。
    Jython (Java), IronPython (.NET), PyPy (一部) にはGILがない。
    """)

    misconception(
        "GILがあるからPythonでマルチスレッドは無意味",
        "I/OバウンドなタスクではGILは問題にならない。"
        "Webスクレイピング、API呼び出し、ファイルI/Oなどは"
        "マルチスレッドで十分に高速化できる。"
        "CPUバウンドにはmultiprocessingやC拡張を使う"
    )

    heading("4-4. asyncio の内部構造")

    p("""
    まず全体像: この節では「4-4. asyncio の内部構造」を、定義 -> 仕組み -> 実務上の判断の順で整理する。
    asyncio は「シングルスレッドで I/O並行処理を行う」フレームワークだ。
    マルチスレッドと違い、ロックが不要で、メモリ使用量も少ない。

    asyncio の構成要素:

    1. イベントループ (Event Loop):
       「待機中のI/Oがないか監視し、完了したタスクを再開する」制御構造。
       内部的には select/poll/epoll/kqueue を使ってOSのI/O完了通知を受け取る。

       while True:
           ready_callbacks = selector.select(timeout)
           for callback in ready_callbacks:
               callback()  # タスクを再開

    2. コルーチン (Coroutine):
       async def で定義された関数。await で中断・再開できる。
       中断時にイベントループに制御を返し、他のコルーチンが実行される。

    3. Task:
       コルーチンをイベントループにスケジュールしたもの。
       asyncio.create_task(coro) で作成。

    4. Future:
       「まだ完了していない非同期操作の結果」を表すオブジェクト。
       TaskはFutureのサブクラス。

    実行フロー:
      async def fetch(url):
          response = await http_client.get(url)  # ← ここで中断
          return response.json()

    1. fetch() を呼ぶと、コルーチンオブジェクトが返る（まだ実行されない）
    2. await http_client.get(url) で I/O開始 → コルーチン中断
    3. イベントループが他の待機中タスクを実行
    4. I/O完了 → イベントループが fetch を再開
    5. response.json() を計算して返す

    gather vs create_task:
    - asyncio.gather(coro1, coro2): 全完了を待つ。例外は即座に伝搬
    - asyncio.create_task(coro): スケジュールだけして制御を返す。後でawait
    - TaskGroup (3.11+): 構造化並行性。エラー処理がgatherより安全

    async for / async with:
    - async for: 非同期イテレータ（DBカーソル、WebSocket等）
    - async with: 非同期コンテキストマネージャ（接続の確立と解放）
    """)

    interview("""
    Q: asyncio はなぜ GIL の制約を受けないのですか？
    A: GILは「CPUバウンドの処理」を1スレッドに制限するものです。
       asyncioはI/O待ちの間に他のタスクを実行する「協調的マルチタスク」で、
       CPUを並列に使うわけではありません。
       シングルスレッドで動くので、そもそもGILの競合が発生しません。
       CPUバウンドの処理を asyncio で並列化することはできませんが、
       run_in_executor で別プロセスに委譲することは可能です。
    """)

    heading("4-5. 型ヒント高度 (Protocol / TypeVar / ParamSpec)")

    p("""
    先に結論: 「4-5. 型ヒント高度 (Protocol / TypeVar / ParamSpec)」は実装と設計判断に直結する。背景とトレードオフを押さえる。
    Pythonの型ヒントはランタイムでは何もしない。では何のためにあるか？

    1. 静的型チェッカー (mypy, pyright) がバグを事前に検出する
    2. IDEの補完と推論が劇的に改善する
    3. ドキュメントとしてコードの意図を伝える

    基本の型ヒントは知っていると仮定し、高度なものを解説する。

    --- TypeVar: ジェネリック型を定義する ---

    T = TypeVar('T')

    def first(items: list[T]) -> T:
        return items[0]

    # first([1, 2, 3]) → int と推論される
    # first(["a", "b"]) → str と推論される
    # 型が一致しない場合: first([1, "a"]) → int | str

    TypeVar に制約をつける:
    Num = TypeVar('Num', int, float)
    def add(a: Num, b: Num) -> Num: ...
    # add(1, 2.0) → OK
    # add("a", "b") → mypyエラー

    TypeVar に上限をつける:
    Comparable = TypeVar('Comparable', bound='SupportsLessThan')
    # Comparable は SupportsLessThan のサブクラスのみ受け付ける

    --- Protocol: 構造的部分型 (Structural Subtyping) ---

    from typing import Protocol

    class Drawable(Protocol):
        def draw(self) -> None: ...

    class Circle:
        def draw(self) -> None:
            print("○")

    def render(shape: Drawable) -> None:
        shape.draw()

    render(Circle())  # OK! Circle は Drawable を明示的に継承していないが、
                      # draw() メソッドを持っているので型チェックが通る

    Protocol vs ABC:
    - ABC (Abstract Base Class): 名目的型付け。明示的に継承が必要
    - Protocol: 構造的型付け。メソッドのシグネチャが合えばOK

    Protocolは「Goのインターフェース」に近い。
    「このメソッドを持っていればOK」というダックタイピングを
    型チェッカーで検証可能にしたもの。

    --- ParamSpec: 関数シグネチャの型パラメータ (Python 3.10+) ---

    from typing import ParamSpec, Callable, TypeVar

    P = ParamSpec('P')
    R = TypeVar('R')

    def retry(func: Callable[P, R], *args: P.args, **kwargs: P.kwargs) -> R:
        for _ in range(3):
            try:
                return func(*args, **kwargs)
            except Exception:
                continue
        raise RuntimeError("All retries failed")

    # retryは元の関数と同じシグネチャを保持する
    # → IDEの補完がretry経由でも正しく動く

    ParamSpec がない場合:
    def retry(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        # 引数と返り値の型情報が完全に失われる
        ...
    """)

    p("""
    --- TypeGuard: 型の絞り込み (Python 3.10+) ---

    from typing import TypeGuard

    def is_string_list(val: list[object]) -> TypeGuard[list[str]]:
        return all(isinstance(x, str) for x in val)

    def process(items: list[object]):
        if is_string_list(items):
            # ここでは items は list[str] と推論される!
            for s in items:
                print(s.upper())  # str のメソッドが使える

    TypeGuard がない場合、isinstance チェック後も型が絞り込まれない。
    TypeGuard は「この関数が True を返したら、引数の型はXだ」と型チェッカーに教える。

    --- Literal 型: 値を型として扱う ---

    from typing import Literal

    def set_mode(mode: Literal["read", "write", "append"]) -> None:
        ...

    set_mode("read")    # OK
    set_mode("delete")  # mypyエラー! "delete" は許可されていない

    --- overload: 引数の型に応じた返り値の型 ---

    from typing import overload

    @overload
    def parse(data: str) -> dict: ...
    @overload
    def parse(data: bytes) -> list: ...

    def parse(data):
        if isinstance(data, str):
            return json.loads(data)
        return list(data)

    # parse("{}") → dict と推論
    # parse(b"abc") → list と推論
    # 引数の型によって返り値の型が変わることを表現できる
    """)

    misconception(
        "型ヒントを書くとPythonの実行速度が遅くなる",
        "型ヒントはランタイムでは無視される（from __future__ import annotations で文字列化される）。"
        "実行速度への影響はゼロ。むしろ型チェッカーによるバグの早期発見で開発速度が上がる"
    )


# ======================================================================
#  第5章: デザインパターン — GoF 23パターン
# ======================================================================

def chapter_5_design_patterns():
    title("第5章: デザインパターン — GoF 23パターン完全ガイド")

    p("""
    デザインパターンは「よくある設計問題への、検証済みの解決策」だ。
    Gang of Four (GoF) の4人が1994年に23個のパターンを体系化した。

    パターンを暗記するのではなく、「どんな問題を解決するか」を理解することが重要。
    パターンは3カテゴリに分かれる:
    - 生成 (Creational): オブジェクトの作り方に関する問題
    - 構造 (Structural): オブジェクトの組み合わせ方に関する問題
    - 振舞い (Behavioral): オブジェクト間の責任分担に関する問題
    """)

    heading("5-1. 生成パターン (Creational Patterns) — 5個")

    p("""
    この節の狙い: 「5-1. 生成パターン (Creational Patterns) — 5個」を単語暗記ではなく、なぜ必要かまでつながる形で理解する。
    【Singleton — インスタンスを1つだけにする】
    いつ使う: 設定、ログ、接続プールなど、1つだけ存在すべきリソース
    なぜ使う: グローバル変数の代わりに、制御されたアクセスを提供する
    Python的実装: モジュールレベル変数が事実上のSingleton。
                   またはメタクラスや__new__で制御する

    class Singleton(type):
        _instances = {}
        def __call__(cls, *args, **kwargs):
            if cls not in cls._instances:
                cls._instances[cls] = super().__call__(*args, **kwargs)
            return cls._instances[cls]

    注意: テストが困難になるため、DI（依存性注入）で代替できないか先に検討する。

    【Factory Method — サブクラスに生成を委ねる】
    いつ使う: 生成するオブジェクトの型を実行時に決定したいとき
    なぜ使う: 呼び出し側が具象クラスを知らなくても済む（疎結合）
    Python的実装: 辞書 + callable で十分なことが多い

    # Java風
    class DocumentFactory(ABC):
        @abstractmethod
        def create(self, content) -> Document: ...

    # Python風 (シンプル)
    factories = {
        "pdf": PDFDocument,
        "html": HTMLDocument,
    }
    doc = factories[format_type](content)

    【Abstract Factory — 関連オブジェクト群の生成】
    いつ使う: 一貫した外観のUI部品を作りたい（ダークテーマ/ライトテーマ）
    なぜ使う: 関連するオブジェクトの整合性を保証する

    【Builder — 複雑なオブジェクトを段階的に構築】
    いつ使う: コンストラクタの引数が多い（5個以上）とき
    なぜ使う: テレスコーピングコンストラクタ（引数だらけの__init__）を避ける
    Python的実装: dataclass + メソッドチェーン

    @dataclass
    class QueryBuilder:
        _table: str = ""
        _conditions: list = field(default_factory=list)
        _limit: int = 100

        def table(self, name): self._table = name; return self
        def where(self, cond): self._conditions.append(cond); return self
        def limit(self, n): self._limit = n; return self

        def build(self) -> str:
            sql = f"SELECT * FROM {self._table}"
            if self._conditions:
                sql += " WHERE " + " AND ".join(self._conditions)
            sql += f" LIMIT {self._limit}"
            return sql

    query = QueryBuilder().table("users").where("age > 18").limit(10).build()

    【Prototype — 既存オブジェクトをコピーして新しいオブジェクトを作る】
    いつ使う: オブジェクトの生成が高コスト（DBから読み取り等）のとき
    なぜ使う: コピーの方が生成より速い場合がある
    Python的実装: copy.deepcopy() がそのまま使える
    """)

    heading("5-2. 構造パターン (Structural Patterns) — 7個")

    p("""
    この節の狙い: 「5-2. 構造パターン (Structural Patterns) — 7個」を単語暗記ではなく、なぜ必要かまでつながる形で理解する。
    【Adapter — インターフェースの変換】
    いつ使う: 既存クラスのインターフェースが合わないとき
    なぜ使う: 既存コードを変更せずに、別のインターフェースで使えるようにする
    アナロジー: 海外旅行の電源変換プラグ

    class OldPrinter:
        def print_document(self, text): ...

    class NewPrinterAdapter:
        def __init__(self, old_printer):
            self.old = old_printer
        def render(self, text):  # 新しいインターフェース
            self.old.print_document(text)  # 古いメソッドに委譲

    【Bridge — 抽象と実装を分離】
    いつ使う: 2つの独立した次元（形状 × 色、デバイス × リモコン）の組み合わせ
    なぜ使う: 継承の爆発を防ぐ（M × N のサブクラスを作らなくて済む）

    【Composite — ツリー構造で再帰的に扱う】
    いつ使う: ファイルシステム、組織図、UIコンポーネントなどのツリー構造
    なぜ使う: 個別のオブジェクトとグループを同じインターフェースで扱える

    class FileSystemItem(ABC):
        @abstractmethod
        def size(self) -> int: ...

    class File(FileSystemItem):
        def __init__(self, name, size): self._size = size
        def size(self): return self._size

    class Directory(FileSystemItem):
        def __init__(self):
            self.children = []
        def add(self, item): self.children.append(item)
        def size(self): return sum(c.size() for c in self.children)

    【Decorator — 機能を動的に追加】
    いつ使う: 既存オブジェクトに機能を追加したいが、サブクラスは作りたくないとき
    なぜ使う: 組み合わせの自由度が高い（ログ+キャッシュ+認証 等）
    Python的実装: @decorator がまさにこのパターン

    def retry(max_retries=3):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except Exception:
                        if attempt == max_retries - 1:
                            raise
            return wrapper
        return decorator

    【Facade — 複雑なサブシステムに単純なインターフェースを提供】
    いつ使う: 複数のクラスの操作を「1つのメソッド」にまとめたいとき
    なぜ使う: クライアントがサブシステムの内部構造を知らなくて済む
    アナロジー: ホテルのフロントデスク（レストラン予約、タクシー手配、etc.を一箇所で）

    【Flyweight — 大量の類似オブジェクトのメモリを節約】
    いつ使う: 何千ものオブジェクトが共通のデータを持つとき
    なぜ使う: 共有できる部分（intrinsic state）を使い回してメモリ削減
    Python的実装: __slots__、intern()、enum が活用される

    【Proxy — オブジェクトへのアクセスを制御】
    いつ使う: アクセス制御、遅延初期化、キャッシュ、ログ
    なぜ使う: 本体を変更せずに前後の処理を追加できる
    種類: Virtual Proxy（遅延初期化）、Protection Proxy（権限チェック）、
          Remote Proxy（リモートオブジェクトのローカル代理）
    """)

    heading("5-3. 振舞いパターン (Behavioral Patterns) — 11個")

    p("""
    先に結論: 「5-3. 振舞いパターン (Behavioral Patterns) — 11個」は実装と設計判断に直結する。背景とトレードオフを押さえる。
    【Observer — 状態変化を通知する】
    いつ使う: あるオブジェクトの変化を、複数のオブジェクトに通知したいとき
    なぜ使う: 疎結合で通知できる（Subject が Observer の詳細を知らない）
    アナロジー: YouTubeのチャンネル登録。新動画が出たら登録者全員に通知

    class EventEmitter:
        def __init__(self):
            self._listeners = defaultdict(list)
        def on(self, event, callback):
            self._listeners[event].append(callback)
        def emit(self, event, data=None):
            for callback in self._listeners[event]:
                callback(data)

    【Strategy — アルゴリズムを差し替え可能にする】
    いつ使う: 同じ処理で複数のアルゴリズムを使い分けたいとき
    なぜ使う: if-elif の連鎖を避けて、開放閉鎖原則に従う
    Python的実装: 関数を渡すだけ（Strategyパターンの最もPython的な実装）

    def sort_data(data, strategy=sorted):
        return strategy(data)
    # strategy=sorted, strategy=lambda x: list(reversed(sorted(x)))

    【Command — 操作をオブジェクトとしてカプセル化】
    いつ使う: Undo/Redo、マクロ記録、キューイング
    なぜ使う: 操作の実行と操作の指示を分離できる

    【Template Method — 処理の骨格を定義し、詳細をサブクラスに委ねる】
    いつ使う: アルゴリズムの大枠は同じだが、一部のステップが異なるとき
    なぜ使う: 共通処理の重複を排除する

    【Iterator — コレクションの要素に順番にアクセス】
    いつ使う: コレクションの内部構造を隠蔽して走査したいとき
    Python的実装: __iter__ と __next__ がまさにこれ。for文で自動使用

    【State — 状態に応じてオブジェクトの振る舞いを変える】
    いつ使う: if-elif で状態を判定している箇所が複雑になったとき
    なぜ使う: 状態ごとのクラスに分離することで、単一責任原則に従う

    【Chain of Responsibility — 処理を連鎖させる】
    いつ使う: ミドルウェア（認証→ログ→バリデーション→ビジネスロジック）
    なぜ使う: 各ハンドラが独立し、順序の変更や追加が容易

    【Mediator — オブジェクト間の通信を仲介】
    いつ使う: 多対多の通信が複雑になったとき
    なぜ使う: 各オブジェクトが直接通信せず、仲介者を通すことで疎結合になる
    アナロジー: 空港の管制塔。飛行機同士が直接通信したら混乱する

    【Memento — オブジェクトの状態を保存・復元】
    いつ使う: Undo機能、セーブ/ロード
    なぜ使う: カプセル化を破壊せずに内部状態を保存できる

    【Visitor — データ構造と処理を分離】
    いつ使う: データ構造は固定だが、処理を追加したいとき
    なぜ使う: 既存クラスを変更せずに新しい操作を追加できる
    Python的実装: @singledispatch がVisitorパターンを簡潔に実現

    from functools import singledispatch

    @singledispatch
    def serialize(obj):
        raise TypeError(f"Unknown type: {type(obj)}")

    @serialize.register(int)
    def _(obj): return str(obj)

    @serialize.register(str)
    def _(obj): return f'"{obj}"'

    【Interpreter — 文法を定義し、解釈する】
    いつ使う: DSL（ドメイン固有言語）、設定ファイルパーサー
    なぜ使う: 文法ルールをクラス階層で表現し、拡張可能にする
    """)

    interview("""
    Q: 実務でよく使うデザインパターンを3つ挙げてください。
    A: 1) Observer: イベント駆動の通知。UIフレームワーク、メッセージング、
          Pub/Sub全般に使われる。PythonではEventEmitterやsignalで実現。
       2) Strategy: アルゴリズムの差し替え。認証方式、ソート方式、
          価格計算ロジックの切り替え。Pythonでは関数を渡すだけで実現。
       3) Decorator: 機能の動的追加。ログ、キャッシュ、認証、リトライ。
          Pythonの@decoratorが最もクリーンな実装。
       選ぶ基準は「問題の種類」。生成の問題→Factory/Builder、
       組み合わせの問題→Composite/Decorator、通知の問題→Observerです。
    """)


# ======================================================================
#  第6章: SOLID原則
# ======================================================================

def chapter_6_solid():
    title("第6章: SOLID原則 — 変更に強い設計の5原則")

    p("""
    SOLID原則は Robert C. Martin (Uncle Bob) が提唱した5つの設計原則だ。
    これらは「変更に強く、拡張しやすく、テストしやすいコード」を作るための指針。

    なぜSOLIDが重要か？
    ソフトウェアの本質は「変更」だ。要件は変わる。技術は変わる。
    変更のたびにコード全体を書き直していたら、開発は破綻する。
    SOLIDは「変更の影響範囲を最小化する」ための設計原則だ。
    """)

    heading("6-1. S — Single Responsibility Principle (単一責任原則)")

    p("""
    この節の狙い: 「6-1. S — Single Responsibility Principle (単一責任原則)」を単語暗記ではなく、なぜ必要かまでつながる形で理解する。
    定義: クラスを変更する理由は1つだけであるべき

    「1つの責任」とは「変更理由が1つ」という意味だ。

    ❌ 違反例:
    class UserService:
        def create_user(self, data):
            # ユーザーの作成（ビジネスロジック）
            user = User(**data)
            # DBへの保存（永続化）
            self.db.save(user)
            # メール送信（通知）
            self.email.send(user.email, "Welcome!")
            # ログ出力（運用）
            self.logger.info(f"User created: {user.id}")

    このクラスは4つの変更理由を持つ:
    1. ビジネスロジックの変更 → create_user を変更
    2. DB構造の変更 → create_user を変更
    3. メールテンプレートの変更 → create_user を変更
    4. ログ形式の変更 → create_user を変更

    ✅ 修正例:
    class UserService:
        def __init__(self, repo, notifier):
            self.repo = repo
            self.notifier = notifier

        def create_user(self, data):
            user = User(**data)
            self.repo.save(user)
            self.notifier.welcome(user)

    # 永続化、通知、ログはそれぞれ別クラスの責任
    """)

    heading("6-2. O — Open/Closed Principle (開放閉鎖原則)")

    p("""
    まず全体像: この節では「6-2. O — Open/Closed Principle (開放閉鎖原則)」を、定義 -> 仕組み -> 実務上の判断の順で整理する。
    定義: 拡張に対して開いていて、修正に対して閉じているべき

    新しい機能を追加するとき、既存のコードを変更せずに拡張できるべき。

    ❌ 違反例:
    def calculate_area(shape):
        if shape.type == "circle":
            return 3.14 * shape.radius ** 2
        elif shape.type == "rectangle":
            return shape.width * shape.height
        elif shape.type == "triangle":
            # 新しい図形を追加するたびに、この関数を変更する!
            return 0.5 * shape.base * shape.height

    ✅ 修正例:
    class Shape(ABC):
        @abstractmethod
        def area(self) -> float: ...

    class Circle(Shape):
        def __init__(self, radius): self.radius = radius
        def area(self): return 3.14 * self.radius ** 2

    class Rectangle(Shape):
        def __init__(self, w, h): self.width = w; self.height = h
        def area(self): return self.width * self.height

    # 新しい図形を追加するときは、新しいクラスを追加するだけ
    # 既存のコードは一切変更しない
    """)

    heading("6-3. L — Liskov Substitution Principle (リスコフの置換原則)")

    p("""
    先に結論: 「6-3. L — Liskov Substitution Principle (リスコフの置換原則)」は実装と設計判断に直結する。背景とトレードオフを押さえる。
    定義: 基底クラスを使っている箇所で、派生クラスに置き換えても正しく動くべき

    アナロジー: 「鳥」を受け取る関数に「ペンギン」を渡しても壊れないべき。
    しかし「fly()」メソッドがある場合、ペンギンは飛べないので壊れる。

    ❌ 違反例:
    class Bird:
        def fly(self): return "flying"

    class Penguin(Bird):
        def fly(self): raise Exception("Can't fly!")  # LSP違反!

    def make_bird_fly(bird: Bird):
        bird.fly()  # Penguinを渡すと例外が飛ぶ

    ✅ 修正例:
    class Bird:
        def move(self): ...

    class FlyingBird(Bird):
        def fly(self): return "flying"
        def move(self): return self.fly()

    class Penguin(Bird):
        def swim(self): return "swimming"
        def move(self): return self.swim()

    ルール:
    - 派生クラスは基底クラスの事前条件を強化してはいけない
    - 派生クラスは基底クラスの事後条件を弱化してはいけない
    - 基底クラスの不変条件は派生クラスでも維持されるべき
    """)

    heading("6-4. I — Interface Segregation Principle (インターフェース分離原則)")

    p("""
    この節の狙い: 「6-4. I — Interface Segregation Principle (インターフェース分離原則)」を単語暗記ではなく、なぜ必要かまでつながる形で理解する。
    定義: クライアントが使わないメソッドに依存すべきでない

    大きなインターフェースを小さく分割して、必要なものだけ実装する。

    ❌ 違反例:
    class Worker(ABC):
        @abstractmethod
        def work(self): ...
        @abstractmethod
        def eat(self): ...
        @abstractmethod
        def sleep(self): ...

    class Robot(Worker):
        def work(self): return "working"
        def eat(self): raise NotImplementedError()  # ロボットは食べない!
        def sleep(self): raise NotImplementedError()  # ロボットは寝ない!

    ✅ 修正例:
    class Workable(Protocol):
        def work(self) -> str: ...

    class Eatable(Protocol):
        def eat(self) -> str: ...

    class Human:  # Workable かつ Eatable
        def work(self): return "working"
        def eat(self): return "eating"

    class Robot:  # Workable のみ
        def work(self): return "working"
    """)

    heading("6-5. D — Dependency Inversion Principle (依存性逆転原則)")

    p("""
    先に結論: 「6-5. D — Dependency Inversion Principle (依存性逆転原則)」は実装と設計判断に直結する。背景とトレードオフを押さえる。
    定義: 上位モジュールは下位モジュールに依存すべきでない。
          両方とも抽象に依存すべき。

    アナロジー: コンセントのプラグ。
    家電は「コンセント」という抽象に依存し、電力会社も「コンセント」に依存する。
    家電が「東京電力の特定の発電機」に直接依存していたら、引っ越しできない。

    ❌ 違反例:
    class OrderService:
        def __init__(self):
            self.db = PostgresDatabase()  # 具象クラスに直接依存

    ✅ 修正例:
    class Repository(Protocol):
        def save(self, entity: dict) -> None: ...
        def find(self, id: int) -> dict: ...

    class OrderService:
        def __init__(self, repo: Repository):  # 抽象に依存
            self.repo = repo

    # テスト時: OrderService(FakeRepository())
    # 本番時: OrderService(PostgresRepository())
    # 変更時: PostgresからMongoに変えても、OrderServiceは変更不要
    """)

    interview("""
    Q: SOLID原則で最も重要なのはどれですか？
    A: 実務で最もインパクトが大きいのは D（依存性逆転原則）です。
       これを実践すると、テスタビリティが劇的に改善し、
       コンポーネントの差し替えが容易になります。
       具体的にはコンストラクタインジェクション（依存をコンストラクタで受け取る）
       を徹底することで、Mockによるテストが容易になり、
       DBの変更やクラウドサービスの移行もビジネスロジックに影響しません。
       ただし全原則は相互に補完しあうため、バランスよく適用することが重要です。
    """)


# ======================================================================
#  第7章: クリーンコード
# ======================================================================

def chapter_7_clean_code():
    title("第7章: クリーンコード — 読みやすく、変更しやすいコード")

    heading("7-1. リファクタリング (Refactoring)")

    p("""
    この節の狙い: 「7-1. リファクタリング (Refactoring)」を単語暗記ではなく、なぜ必要かまでつながる形で理解する。
    リファクタリングとは「外部からの振る舞いを変えずに、コードの内部構造を改善する」ことだ。
    Martin Fowler が体系化した。

    リファクタリングの前提条件:
    1. テストがある（振る舞いが変わっていないことを確認できる）
    2. 小さなステップで行う（大きな変更は壊れやすい）
    3. バージョン管理を使う（戻れるようにする）

    よく使うリファクタリングパターン:

    Extract Method (メソッドの抽出):
    長い関数の一部を意味のある名前の別関数に切り出す

    ❌ Before:
    def process_order(order):
        # 価格計算 (10行)
        subtotal = sum(item.price * item.qty for item in order.items)
        tax = subtotal * 0.1
        shipping = 500 if subtotal < 5000 else 0
        total = subtotal + tax + shipping
        # メール送信 (10行)
        subject = f"Order #{order.id}"
        body = f"Total: {total}"
        send_email(order.user.email, subject, body)

    ✅ After:
    def process_order(order):
        total = calculate_total(order)
        send_order_confirmation(order, total)

    def calculate_total(order):
        subtotal = sum(item.price * item.qty for item in order.items)
        tax = subtotal * 0.1
        shipping = 500 if subtotal < 5000 else 0
        return subtotal + tax + shipping

    def send_order_confirmation(order, total):
        subject = f"Order #{order.id}"
        body = f"Total: {total}"
        send_email(order.user.email, subject, body)

    Replace Conditional with Polymorphism (条件分岐をポリモーフィズムで置換):
    if-elif の連鎖を、クラス階層に変換する

    Introduce Parameter Object (パラメータオブジェクトの導入):
    def create_user(name, email, age, role, active) → def create_user(user_data: UserData)

    他の重要なリファクタリング:
    - Rename (名前変更): 意図が伝わる名前に
    - Move Method: メソッドを適切なクラスに移動
    - Extract Interface: 共通インターフェースを抽出
    - Replace Magic Number with Named Constant: 定数に名前をつける
    """)

    p("""
    コードの臭い (Code Smell) — リファクタリングが必要なサイン:

    1. Long Method (長いメソッド):
       20行以上のメソッドは分割を検討する。
       「このメソッドは何をしているか」を1文で説明できないなら長すぎる。

    2. God Class (神クラス):
       1つのクラスが多くの責任を持ちすぎている。
       1000行を超えるクラスは分割が必要。

    3. Feature Envy (機能の横恋慕):
       あるクラスのメソッドが、自分のクラスより他のクラスのデータを多く使う。
       → そのメソッドは使っているデータのクラスに移動すべき。

    4. Primitive Obsession (プリミティブの偏執):
       文字列やintで全てを表現する。
       email = "alice@example.com"  # ただの str
       → Email型を定義して、バリデーションをカプセル化する

    5. Shotgun Surgery (散弾銃手術):
       1つの変更で多くのクラスを修正する必要がある。
       → 関連するロジックが散らばっている証拠。1箇所にまとめる

    6. Dead Code (使われていないコード):
       呼ばれていない関数、到達不可能な分岐、コメントアウトされたコード。
       → 削除する。バージョン管理があるのだから、いつでも戻せる

    7. Magic Number (マジックナンバー):
       if age >= 18:  # 18 は何？
       → ADULT_AGE = 18; if age >= ADULT_AGE:

    8. Duplicate Code (重複コード):
       同じロジックが2箇所以上にある。
       → 関数に抽出する (Extract Method)

    DRY (Don't Repeat Yourself) vs WET (Write Everything Twice):
    DRYの過度な適用は「間違った抽象化」を生む。
    2回までの重複は許容し、3回目で初めて抽象化するルールが実践的。
    """)

    heading("7-2. コードレビュー (Code Review)")

    p("""
    この節の狙い: 「7-2. コードレビュー (Code Review)」を単語暗記ではなく、なぜ必要かまでつながる形で理解する。
    コードレビューは「他の開発者がコードの変更を検査する」プロセスだ。

    コードレビューの目的（優先順位順）:
    1. バグの発見: 動作しないコードを本番に出さない
    2. 設計の改善: より良い構造、パターンの適用
    3. 知識の共有: チーム全体がコードベースを理解する
    4. コーディング標準の維持: 一貫性のあるコードベース

    効果的なレビューのコツ:

    レビュアー側:
    - 「なぜ？」を聞く（Why did you choose X over Y?）
    - 具体的な改善案を示す（「ここは〇〇にした方がいい」）
    - 批判ではなく提案する（「must」ではなく「nit:」「consider:」）
    - 小さなPRをレビューする（200行以下が理想）
    - チェックリストを使う: エッジケース、エラーハンドリング、テスト

    著者側:
    - PRの説明をしっかり書く（なぜこの変更が必要か）
    - 自分でまずセルフレビューする
    - テストを含める
    - PRを小さく保つ（1つのPRは1つの目的）

    Google のコードレビュー基準:
    - 全てのコード変更は誰かのレビューを通す（例外なし）
    - レビューは24時間以内に返す
    - 「作業日1日以上の遅延はチームの速度を落とす」
    """)

    heading("7-3. 技術的負債 (Technical Debt)")

    p("""
    まず全体像: この節では「7-3. 技術的負債 (Technical Debt)」を、定義 -> 仕組み -> 実務上の判断の順で整理する。
    技術的負債とは「短期的な利益のために取った近道が、
    将来の開発速度を落とすコスト」だ。
    Ward Cunningham が金融の「借金」のアナロジーで名付けた。

    借金と同じく、技術的負債には「利息」がかかる:
    - 新機能の追加に時間がかかる（レガシーコードの理解コスト）
    - バグが増える（複雑なコードは壊れやすい）
    - 開発者のモチベーションが下がる（汚いコードで作業する苦痛）
    - 採用が困難になる（技術的に魅力のないコードベース）

    技術的負債の4象限（Martin Fowler）:

                    意図的               無自覚
    無謀    │ 「リファクタリングする │ 「レイヤリング？     │
            │ 時間はない」          │ 何それ？」          │
    ────────┼──────────────────────┼──────────────────────┤
    慎重    │ 「今はリリースを優先し │ 「もっといい方法が   │
            │ 後で直す」            │ あったとわかった」   │

    対処法:
    1. 可視化: 技術的負債をチケットとして管理する（バックログに入れる）
    2. 計測: 変更にかかる時間の増加、バグ率の上昇を追跡する
    3. 返済: 各スプリントで20%の時間を技術的負債の返済に充てる
    4. 予防: コードレビュー、CIでの品質チェック、リファクタリングの習慣化

    Boy Scout Rule (ボーイスカウトルール):
    「来た時よりも美しく」— 触ったコードは少しでも良くして離れる
    """)

    interview("""
    Q: 技術的負債をどう管理しますか？
    A: まず可視化します。技術的負債をJIRAチケットとして登録し、
       影響範囲と修正コストを見積もります。
       各スプリントで開発時間の20%を技術的負債の返済に充て、
       Boy Scout Rule（触ったコードは少し良くして離れる）を実践します。
       計測としては、変更リードタイム（コード変更からデプロイまでの時間）と
       変更失敗率を追跡し、技術的負債が開発速度に与える影響を定量化します。
       重要なのは「負債ゼロ」を目指すのではなく、
       「コントロール下に置く」ことです。
    """)

    misconception(
        "技術的負債は悪いものだから一切許すべきでない",
        "技術的負債は「意図的な借金」として戦略的に活用できる。"
        "市場投入のスピードが最重要な場面では、意図的に負債を取り、"
        "後で返済する計画を立てるのが合理的。問題は「無自覚な負債」と「返済しない負債」"
    )


# ======================================================================
#  第8章: Go / TypeScript との比較
# ======================================================================

def chapter_8_polyglot():
    title("第8章: Go / TypeScript 比較 — 型、エラー、非同期")

    p("""
    なぜ複数の言語を知るべきか？
    「Pythonで全部できる」は技術的に正しい。しかし「できる」と「適している」は違う。
    包丁で木を切ることは「できる」が、大工はノコギリを使う。効率が桁違いだからだ。

    FAANG のシステムデザイン面接では必ず聞かれる:
    「このコンポーネントにはどの言語を選びますか？ なぜですか？」
    """)

    heading("8-1. 型システムの比較")

    p("""
    まず全体像: この節では「8-1. 型システムの比較」を、定義 -> 仕組み -> 実務上の判断の順で整理する。
    | 特徴             | Python          | Go              | TypeScript      |
    |-----------------|-----------------|-----------------|-----------------|
    | 型付け方式       | 動的型付け       | 静的型付け       | 静的型付け       |
    | 型推論           | mypyが推論      | 部分的推論       | 強力な推論       |
    | ジェネリクス     | TypeVar         | Go 1.18+        | <T>             |
    | Null安全        | Optional (mypy) | nil (安全でない) | strictNullChecks|
    | 構造的型付け     | Protocol        | interface       | デフォルト       |
    | ユニオン型       | Union[A, B]     | なし             | A | B           |

    Python:
    - 型ヒントはオプション。書かなくても動く。mypy で検証する
    - 最大の利点: 柔軟性。プロトタイプや探索的プログラミングに最適
    - 最大の弱点: 大規模コードベースで型エラーが実行時まで潜む

    Go:
    - 型は必須。コンパイル時に全てチェックされる
    - interface は構造的型付け (メソッドを持っていればOK)
    - ジェネリクスは1.18で追加されたばかりで、まだ機能が限定的
    - 特徴: シンプルさを重視。継承なし、例外なし、型階層は浅い

    TypeScript:
    - JavaScriptの上に型システムを載せた言語
    - 型推論が非常に強力（書かなくてもかなり推論してくれる）
    - ユニオン型、リテラル型、条件型など、型の表現力が最も高い
    - 型レベルプログラミング（型でロジックを表現）が可能

    # Python
    def greet(name: str | None) -> str:
        if name is None:
            return "Hello, stranger"
        return f"Hello, {name}"

    // Go
    func greet(name *string) string {
        if name == nil {
            return "Hello, stranger"
        }
        return "Hello, " + *name
    }

    // TypeScript
    function greet(name: string | null): string {
        if (name === null) {
            return "Hello, stranger";
        }
        return `Hello, ${name}`;
    }
    """)

    heading("8-2. エラーハンドリングの比較")

    p("""
    この節の狙い: 「8-2. エラーハンドリングの比較」を単語暗記ではなく、なぜ必要かまでつながる形で理解する。
    3つの言語は「エラーをどう扱うか」の哲学が根本的に異なる。

    Python: 例外 (Exception)
    - try/except で捕捉。例外は型階層を持つ
    - EAFP (Easier to Ask Forgiveness than Permission):
      「やってみて、ダメなら例外を捕まえる」
    - 利点: コードがすっきり。正常系に集中できる
    - 欠点: どの関数がどの例外を投げるか不明瞭

    # Python
    try:
        user = find_user(user_id)
        order = create_order(user, items)
    except UserNotFoundError:
        return "User not found"
    except InsufficientStockError as e:
        return f"Stock issue: {e}"

    Go: 戻り値によるエラー返却
    - 関数が (値, error) のタプルを返す
    - エラーは常に明示的にチェックする
    - 利点: エラーの見落としが起きにくい
    - 欠点: if err != nil が大量に発生する（ボイラープレート）

    // Go
    user, err := findUser(userID)
    if err != nil {
        return fmt.Errorf("user lookup failed: %w", err)
    }
    order, err := createOrder(user, items)
    if err != nil {
        return fmt.Errorf("order creation failed: %w", err)
    }

    TypeScript: 例外 + Result型（ライブラリ依存）
    - JavaScriptの例外機構を継承
    - 近年は Result<T, E> パターン（neverthrow等）が普及
    - 型で「この関数はエラーを返す可能性がある」と表現できる

    // TypeScript
    try {
        const user = await findUser(userId);
        const order = await createOrder(user, items);
    } catch (error) {
        if (error instanceof UserNotFoundError) { ... }
    }

    どれが最善か？
    - 答えはない。トレードオフが異なる
    - Go のスタイルは「エラーの見落としが少ない」が「冗長」
    - Python のスタイルは「簡潔」だが「エラーが暗黙的」
    - TypeScript は両方使えるが、チーム内で統一が必要
    """)

    heading("8-3. 非同期モデルの比較")

    p("""
    まず全体像: この節では「8-3. 非同期モデルの比較」を、定義 -> 仕組み -> 実務上の判断の順で整理する。
    | 特徴             | Python            | Go                | TypeScript        |
    |-----------------|-------------------|-------------------|-------------------|
    | 基本モデル       | asyncio           | goroutine         | Promise/async     |
    | 並行性の単位     | コルーチン         | goroutine          | Promise           |
    | スケジューラ     | イベントループ     | Go runtime         | V8イベントループ   |
    | スレッド数       | 1 (シングルスレッド)| M:N マッピング     | 1 (シングルスレッド)|
    | CPU並列         | 不可 (GILあり)     | 可能               | 不可 (Worker除く) |
    | 通信方式         | Queue, Event      | channel            | Promise, Observable|

    Python asyncio:
    - シングルスレッドの協調的マルチタスク
    - await で明示的に制御を返す（プリエンプティブでない）
    - I/Oバウンドに特化。CPUバウンドは別プロセスに委譲
    - 利点: ロック不要、デバッグしやすい
    - 欠点: async/await が伝搬する（関数カラーリング問題）

    # Python
    async def fetch_all():
        async with aiohttp.ClientSession() as session:
            tasks = [fetch(session, url) for url in urls]
            return await asyncio.gather(*tasks)

    Go goroutine:
    - 軽量スレッド（goroutine）を M:N でOSスレッドにマッピング
    - go キーワードで即座に並行実行
    - channel で goroutine 間通信
    - 利点: CPUバウンドも並列実行可能、構文がシンプル
    - 欠点: データ競合のリスク（ロックやchannelで対処）

    // Go
    func fetchAll(urls []string) []Response {
        ch := make(chan Response, len(urls))
        for _, url := range urls {
            go func(u string) {
                ch <- fetch(u)
            }(url)
        }
        results := make([]Response, len(urls))
        for i := range urls {
            results[i] = <-ch
        }
        return results
    }

    TypeScript (Node.js):
    - V8のイベントループ上で動作
    - Promise + async/await
    - シングルスレッド（Worker Threads で並列化は可能）
    - 利点: ブラウザとサーバーで同じモデル
    - 欠点: CPUバウンドはメインスレッドをブロックする

    // TypeScript
    async function fetchAll(urls: string[]): Promise<Response[]> {
        return Promise.all(urls.map(url => fetch(url)));
    }

    言語選定の指針:
    - I/Oバウンドの高並行: Go >= Python (asyncio) >= Node.js
    - CPUバウンドの並列: Go >> Python (multiprocessing) >> Node.js
    - データ分析/ML: Python 一択
    - Web Frontend: TypeScript 一択
    - CLI/インフラツール: Go が得意
    - API/マイクロサービス: Go or TypeScript (Node.js)
    """)

    heading("8-4. パッケージ管理・ビルドシステムの比較")

    p("""
    この節の狙い: 「8-4. パッケージ管理・ビルドシステムの比較」を単語暗記ではなく、なぜ必要かまでつながる形で理解する。
    | 特徴             | Python            | Go                | TypeScript        |
    |-----------------|-------------------|-------------------|-------------------|
    | パッケージ管理   | pip/poetry/uv     | go mod             | npm/yarn/pnpm     |
    | ビルド           | 不要(インタプリタ) | go build            | tsc/esbuild/swc   |
    | 依存解決         | pip: 遅い         | 高速               | npm: node_modules |
    |                  | uv: 高速          |                    | pnpm: 効率的      |
    | モノレポ         | 困難              | go workspace        | turborepo/nx      |
    | バイナリ配布     | PyInstaller等     | 静的バイナリ1つ     | Node.js必要       |

    Go の強み: go build で単一バイナリが生成される。
    依存もバイナリに含まれるので、Dockerイメージが極小になる:
    - Python: ベースイメージ + pip install → 500MB～1GB
    - Go: scratch + バイナリ → 10～20MB
    - Node.js: node + node_modules → 200MB～500MB

    これが「CLIツールやインフラツールはGoで書かれることが多い」理由だ。
    Docker, Kubernetes, Terraform, Hugo — 全てGoで書かれている。
    """)

    heading("8-5. 並行処理の安全性比較")

    p("""
    この節の狙い: 「8-5. 並行処理の安全性比較」を単語暗記ではなく、なぜ必要かまでつながる形で理解する。
    データ競合（Data Race）: 複数のスレッドが同じメモリに同時アクセスし、
    少なくとも1つが書き込みの場合に発生する。

    Python:
    - GILがあるため、CPythonではデータ競合が起きにくい（完全に安全ではない）
    - I/O操作中にGILが解放されるため、共有データの操作は要注意
    - threading.Lock で保護する

    import threading
    lock = threading.Lock()
    counter = 0
    def increment():
        global counter
        with lock:  # ロックで保護
            counter += 1

    Go:
    - goroutine 間の共有データはデータ競合のリスクがある
    - go run -race でデータ競合を検出できる（Race Detector）
    - 推奨: channel を使って通信する（共有メモリではなくメッセージパッシング）

    // Go: "Don't communicate by sharing memory; share memory by communicating."
    ch := make(chan int)
    go func() { ch <- 42 }()
    value := <-ch  // channel経由でデータを受け取る

    // NG: 共有変数を直接操作
    var counter int
    go func() { counter++ }()  // データ競合!

    TypeScript (Node.js):
    - シングルスレッドなので、通常はデータ競合が起きない
    - Worker Threads を使う場合は SharedArrayBuffer + Atomics で安全に操作
    - ほとんどのケースでは Worker Threads は不要（I/Oはイベントループで十分）
    """)

    misconception(
        "Goのgoroutineは軽量だから数百万個起動しても問題ない",
        "goroutine は確かに軽量（~2-8KB）だが、大量に起動すると"
        "スケジューラのオーバーヘッドやメモリ消費が問題になる。"
        "ワーカープール（semaphore パターン）で同時実行数を制御するのが実践的"
    )

    interview("""
    Q: 新しいマイクロサービスの言語をどう選定しますか？
    A: 4つの軸で評価します:
       1. パフォーマンス要件: レイテンシ制約が厳しいなら Go、ML推論なら Python
       2. チームのスキル: 学習コストとエコシステムの成熟度
       3. エコシステム: 必要なライブラリ・フレームワークの充実度
       4. 運用コスト: ビルド、デプロイ、監視の容易さ
       例えば「高スループットのAPIサーバー」なら Go を第一候補とし、
       「データパイプライン」なら Python を選びます。
       大事なのは「好み」ではなく「根拠のある判断」をすることです。
    """)


# ======================================================================
#  メイン関数
# ======================================================================

def main():
    print(SEP)
    print("  Programming Practices - 深掘り解説")
    print("  テスト戦略、パフォーマンス、Python高度、デザインパターン、")
    print("  SOLID原則、クリーンコード、多言語比較")
    print(SEP)

    chapter_1_test_strategy()
    chapter_2_test_techniques()
    chapter_3_performance()
    chapter_4_python_advanced()
    chapter_5_design_patterns()
    chapter_6_solid()
    chapter_7_clean_code()
    chapter_8_polyglot()

    title("付録: よくある面接質問と模範回答")

    heading("面接質問集")

    interview("""
    Q: テストを書く時間がない場合、どうしますか？
    A: テストを書く時間がないのではなく、テストを書かない時間のコストが見えていないのです。
       テストなしのコードは手動テストとバグ修正に時間が取られます。
       時間が限られているなら、最もリスクの高いビジネスロジックの単体テストだけ書きます。
       80/20の法則で、20%のコード（決済、認証、データ変換）に集中します。
    """)

    interview("""
    Q: あなたのアプリケーションが遅いです。どう調査しますか？
    A: 5段階で調査します:
       1. メトリクス確認: P50, P95, P99 のどれが遅いか？ 全体か特定エンドポイントか？
       2. APM/分散トレース: どのスパンが支配的か？ (DB? 外部API? 計算?)
       3. DBクエリ分析: slow query log, EXPLAIN ANALYZE でN+1やフルスキャンを検出
       4. プロファイリング: cProfile(CPU), tracemalloc(メモリ) でホットスポット特定
       5. 仮説検証: ボトルネックを特定したら修正し、改善効果を計測する
       推測に基づく最適化はしません。必ず計測結果に基づいて判断します。
    """)

    interview("""
    Q: マイクロサービスでのデータ整合性をどう保証しますか？
    A: 分散トランザクションは避け、Sagaパターンを使います。
       各サービスがローカルトランザクションを実行し、
       失敗した場合は補償トランザクション（逆操作）で取り消します。
       Outbox パターンでイベントの確実な発行を保証し、
       べき等性（同じ操作を複数回実行しても結果が変わらない）を全APIに実装します。
       Contract Testing で API の互換性を継続的に検証します。
    """)

    interview("""
    Q: デザインパターンを使いすぎてしまうことはありますか？
    A: はい、Over-Engineering（過剰設計）は深刻な問題です。
       パターンは「問題が存在するとき」に適用するもので、
       「将来使うかもしれない」で適用するとコードが不必要に複雑になります。
       YAGNI (You Ain't Gonna Need It) の原則に従い、
       現在の要件に対して最もシンプルな解決策を選びます。
       リファクタリングの際にパターンを適用する方が、最初から適用するより安全です。
    """)

    title("総まとめ — 優先度順学習ガイド")

    p("""
    先に結論: 「面接質問集」は実装と設計判断に直結する。背景とトレードオフを押さえる。
    【Tier 1: 最優先 — 面接・実務で即必要】
    ・テストピラミッド (Unit 70% / Integration 20% / E2E 10%)
    ・テストダブル 5種 (Dummy, Stub, Spy, Mock, Fake)
    ・TDD Red-Green-Refactor サイクル
    ・SOLID原則（特にD: 依存性逆転原則）
    ・Big-O分析（主要データ構造の計算量）
    ・リファクタリングの基本テクニック

    【Tier 2: 重要 — 3ヶ月以内に習得】
    ・Property-based Testing (Hypothesis)
    ・Mutation Testing (テスト品質の計測)
    ・キャッシュ戦略 (LRU, Cache-Aside, Write-Through)
    ・接続プール (Little's Law)
    ・デザインパターン (Observer, Strategy, Decorator, Factory)
    ・プロファイリング (cProfile, tracemalloc)
    ・Go / TypeScript の基本文法と違い

    【Tier 3: 上級 — 6ヶ月以内に習得】
    ・GoF 23パターンの全体像と使い分け
    ・Contract Testing (Consumer-Driven Contract)
    ・メタクラス、デスクリプタの内部動作
    ・GIL の内部構造と回避方法
    ・asyncio の Event Loop 内部
    ・型ヒント高度 (Protocol, TypeVar, ParamSpec)
    ・技術的負債の管理戦略

    【Tier 4: 専門 — 1年以内に習得】
    ・Fuzzing (AFL, OSS-Fuzz)
    ・Snapshot Testing のベストプラクティス
    ・Amdahl の法則とTail Latency
    ・メモリリーク検出と対策
    ・コードレビューのプロセス設計
    ・言語選定フレームワーク
    """)

    interview("""
    Q: プログラミングプラクティスで最も大事なことは何ですか？
    A: 3つに絞ると:
       1. テストを書く習慣: テストなしのコードは「負債」。
          特に単体テストのROIが最も高い。
       2. 依存性を逆転させる: 具象ではなく抽象に依存することで、
          テスタビリティと変更容易性が劇的に改善する。
       3. 計測してから最適化する: 推測に基づく最適化は時間の無駄。
          プロファイラで実際のボトルネックを特定してから手を入れる。
       これら3つは言語やフレームワークに依存しない普遍的なスキルです。
    """)

    heading("おすすめ書籍")
    p("""
    ■ 『リファクタリング 第2版』 Martin Fowler
      コードの品質改善の決定版。Chapter 7 (クリーンコード) の
      リファクタリングパターンをカタログ的に網羅。
      具体的なコード変換例が豊富で、即実務に使える。
      第2版は JavaScript で書き直されており読みやすい。

    ■ 『テスト駆動開発』 Kent Beck (オーム社)
      TDD の生みの親による原典。Red-Green-Refactor の
      思想と実践を最も正確に理解できる。
      Chapter 1-2 (テスト戦略・技法) の根幹思想がここにある。
      薄い本なので1日で読める。

    ■ 『Head First デザインパターン 第2版』
      Eric Freeman, Elisabeth Robson (O'Reilly)
      GoF 23パターンをストーリー形式で分かりやすく解説。
      Chapter 5 (デザインパターン) を初めて学ぶならこの本がベスト。
      GoF 原典は難解なので、こちらから入ることを推奨。

    ■ 『Fluent Python 第2版』 Luciano Ramalho (O'Reilly)
      Python の深い仕組み (デスクリプタ、メタクラス、asyncio内部、
      型ヒント) を解説。Chapter 4 (Python Advanced) の全てをカバー。
      Python 中級→上級のブレイクスルーに最適な1冊。
    """)

    print(f"\n{SEP}")
    print("  以上で Programming Practices 深掘り解説を終わります。")
    print(f"{SEP}")


if __name__ == "__main__":
    main()
