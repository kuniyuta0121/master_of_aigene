#!/usr/bin/env python3
"""
TechCorp Simulator - メインシミュレーター
==========================================
あなたはスタートアップのテックリード兼PMに就任した。
本番環境には複数の問題が存在する。発見・修正・判断せよ。

実行方法:
  pip install httpx rich
  docker compose up --build -d    # 先にサービスを起動
  python sim_runner.py
"""

import subprocess
import sys
import time

try:
    import httpx
    from rich import box
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Confirm, Prompt
    from rich.table import Table
    from rich.text import Text
except ImportError:
    print("依存ライブラリをインストールしてください:")
    print("  pip install httpx rich")
    sys.exit(1)

console = Console()

SERVICES = {
    "api_gateway":        "http://localhost:8000",
    "note_service":       "http://localhost:8001",
    "search_service":     "http://localhost:8002",
    "analytics_service":  "http://localhost:8003",
    "prometheus":         "http://localhost:9090",
    "grafana":            "http://localhost:3001",
}

SCENARIOS = []  # 動的に読み込む


# ─── ユーティリティ ───────────────────────────────────────

def check_services() -> dict[str, bool]:
    """全サービスの稼働状況を確認する"""
    results = {}
    for name, url in SERVICES.items():
        try:
            r = httpx.get(f"{url}/health", timeout=3.0)
            results[name] = r.status_code == 200
        except Exception:
            results[name] = False
    return results


def show_service_status():
    table = Table(title="サービス稼働状況", box=box.ROUNDED)
    table.add_column("サービス", style="cyan")
    table.add_column("URL")
    table.add_column("状態")

    status = check_services()
    for name, url in SERVICES.items():
        ok = status.get(name, False)
        state = "[green]✓ RUNNING[/green]" if ok else "[red]✗ DOWN[/red]"
        table.add_row(name, url, state)

    console.print(table)
    return status


def wait_for_services(timeout: int = 120):
    """サービスが全て起動するまで待機する"""
    console.print("\n[yellow]サービスの起動を待機中...[/yellow]")
    start = time.time()
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
        task = progress.add_task("起動確認中", total=None)
        while time.time() - start < timeout:
            status = check_services()
            core_services = ["api_gateway", "note_service", "search_service", "analytics_service"]
            ready = all(status.get(s, False) for s in core_services)
            progress.update(task, description=f"起動済: {sum(status.values())}/{len(SERVICES)}")
            if ready:
                console.print("[green]✓ 全コアサービスが起動しました[/green]")
                return True
            time.sleep(3)
    return False


# ─── スコアシステム ───────────────────────────────────────

class SimulationState:
    def __init__(self):
        self.score = 0
        self.max_score = 0
        self.completed_scenarios: list[str] = []
        self.discovered_bugs: list[str] = []
        self.decisions: dict[str, str] = {}

    def add_score(self, points: int, reason: str):
        self.score += points
        console.print(f"[green bold]+{points}点[/green bold] {reason}")

    def lose_score(self, points: int, reason: str):
        self.score = max(0, self.score - points)
        console.print(f"[red bold]-{points}点[/red bold] {reason}")

    def show_scoreboard(self):
        panel = Panel(
            f"[bold yellow]現在のスコア: {self.score} / {self.max_score}[/bold yellow]\n"
            f"完了シナリオ: {len(self.completed_scenarios)}\n"
            f"発見バグ: {len(self.discovered_bugs)}\n"
            f"意思決定: {len(self.decisions)}件",
            title="スコアボード",
            border_style="yellow",
        )
        console.print(panel)


state = SimulationState()


# ─── シナリオ定義 ─────────────────────────────────────────

def scenario_01_performance():
    """シナリオ1: 本番パフォーマンス障害"""
    state.max_score += 300

    console.print(Panel(
        "[bold red]🚨 ALERT: P1 INCIDENT[/bold red]\n\n"
        "[white]alert: note_service_request_duration_seconds > 5\n"
        "severity: critical\n"
        "message: /notes endpoint が5秒以上かかっています\n"
        "affected_users: 全ユーザー（推定 2,400人）\n"
        "business_impact: ページが表示されず、ユーザーが離脱しています[/white]",
        title="📟 PagerDuty Alert",
        border_style="red",
    ))

    console.print("\n[cyan]あなたはオンコール担当です。今すぐ対応してください。[/cyan]\n")
    time.sleep(1)

    # Step 1: 問題の特定
    console.print("[bold]Step 1: 問題を特定する[/bold]")
    console.print("以下のコマンドで実際にAPIのレスポンス時間を計測してください:")
    console.print("[dim]  time curl http://localhost:8001/notes?limit=20[/dim]")
    console.print("[dim]  または: http://localhost:9090 でPrometheusのメトリクスを確認[/dim]")

    answer = Prompt.ask(
        "\n原因として最も可能性が高いものは？",
        choices=["1", "2", "3", "4"],
        default="1",
    )
    console.print("""
  1. DBのインデックスが不足している
  2. N+1クエリ問題（ループの中で個別クエリを発行）
  3. サーバーのCPUが不足している
  4. ネットワーク遅延
""")

    answer = Prompt.ask("番号を選択", choices=["1", "2", "3", "4"])

    if answer == "2":
        state.add_score(50, "正解！ N+1クエリ問題を特定")
    else:
        console.print("[yellow]hint: note_service/main.py の list_notes 関数を確認してください[/yellow]")

    # Step 2: コードの確認
    console.print("\n[bold]Step 2: バグコードを確認する[/bold]")
    console.print("note_service/main.py の list_notes 関数を開いてください。")
    console.print("[dim]  cat services/note_service/main.py | grep -A 20 'for note in notes'[/dim]")

    confirmed = Confirm.ask("N+1問題を発見しましたか？")
    if confirmed:
        state.add_score(50, "N+1問題を発見")
        state.discovered_bugs.append("BUG-01: N+1クエリ")

    # Step 3: 修正の実装
    console.print("\n[bold]Step 3: 修正を実装する[/bold]")
    console.print("[yellow]以下のSQLにnote_service/main.pyのlist_notesを修正してください:[/yellow]")
    console.print("""
[dim]  # 修正後のSQL（JOINで1クエリに）:
  SELECT n.*, u.email
  FROM notes n
  LEFT JOIN users u ON n.user_id = u.id
  ORDER BY n.created_at DESC
  LIMIT :limit OFFSET :offset[/dim]
""")

    console.print("修正したら、サービスを再起動してください:")
    console.print("[dim]  docker compose restart note_service[/dim]")
    console.print("[dim]  time curl http://localhost:8001/notes?limit=20[/dim]")

    fixed = Confirm.ask("修正・再起動・速度改善を確認しましたか？")
    if fixed:
        state.add_score(100, "N+1問題を修正・デプロイ完了")

    # Step 4: 追加対策（インデックス）
    console.print("\n[bold]Step 4: 根本対策 - DBインデックスの追加[/bold]")
    console.print("infra/postgres/init.sql にインデックスが不足しています。")
    console.print("[dim]  CREATE INDEX idx_notes_created_at ON notes(created_at DESC);[/dim]")

    added_index = Confirm.ask("インデックスを追加しましたか？")
    if added_index:
        state.add_score(100, "パフォーマンス根本対策（インデックス追加）")

    # PM視点の問いかけ
    console.print(Panel(
        "[bold]PM視点の問い:[/bold]\n"
        "1. この障害の影響を受けたユーザー数をどう計算するか？\n"
        "2. 次回同様の障害を防ぐためのSLO/SLIをどう定義するか？\n"
        "3. ステークホルダーへの障害報告（ポストモーテム）を書いてください",
        title="🎯 PM課題",
        border_style="blue",
    ))

    state.completed_scenarios.append("scenario_01_performance")
    console.print(f"\n[green]シナリオ1完了！[/green]")


def scenario_02_security():
    """シナリオ2: セキュリティ脆弱性の発見と対応"""
    state.max_score += 400

    console.print(Panel(
        "[bold red]🔒 SECURITY ALERT[/bold red]\n\n"
        "外部のペネトレーションテスト会社から報告が届きました:\n\n"
        "[white]1. Critical: SQLインジェクション脆弱性を発見\n"
        "   エンドポイント: GET /api/notes/search?q=\n"
        "   影響: 全DBデータの漏洩、認証情報の取得が可能\n\n"
        "2. High: JWTシークレットがデフォルト値のまま\n"
        "   影響: 任意のJWTトークンを偽造可能\n\n"
        "3. Medium: 未認証エンドポイントの存在\n"
        "   エンドポイント: GET /api/notes/search\n"
        "   影響: 認証なしでコンテンツにアクセス可能[/white]",
        title="🔍 ペネトレーションテスト報告書",
        border_style="red",
    ))

    # Step 1: SQLインジェクションの実証
    console.print("\n[bold]Step 1: 脆弱性を実際に確認する[/bold]")
    console.print("以下のコマンドでSQLインジェクションを試してください（自分のシステムなので合法）:")
    console.print("[dim]  curl \"http://localhost:8001/notes/search?q=' OR '1'='1\"[/dim]")
    console.print("[yellow]全件のデータが返ってきたらSQLインジェクション成功（脆弱性確認）[/yellow]")

    confirmed = Confirm.ask("SQLインジェクション脆弱性を確認しましたか？")
    if confirmed:
        state.add_score(50, "SQLインジェクション脆弱性を確認")
        state.discovered_bugs.append("BUG-02: SQLインジェクション")

    # Step 2: 修正
    console.print("\n[bold]Step 2: パラメータ化クエリに修正する[/bold]")
    console.print("[yellow]note_service/main.py の search_notes を修正してください:[/yellow]")
    console.print("""
[dim]  # 修正前（脆弱）:
  unsafe_sql = f"SELECT ... WHERE title ILIKE '%{q}%'"

  # 修正後（安全なパラメータ化クエリ）:
  safe_sql = text("SELECT id, title, content FROM notes WHERE title ILIKE :q OR content ILIKE :q LIMIT 20")
  results = db.execute(safe_sql, {"q": f"%{q}%"}).fetchall()[/dim]
""")

    fixed_sqli = Confirm.ask("パラメータ化クエリに修正しましたか？")
    if fixed_sqli:
        state.add_score(100, "SQLインジェクション修正完了")

    # Step 3: JWT シークレット
    console.print("\n[bold]Step 3: JWTシークレットをSecretsManagerに移行する[/bold]")
    console.print("services/api_gateway/main.py を確認してください。")
    console.print("[dim]  JWT_SECRET = os.environ.get(\"JWT_SECRET\", \"super-secret-do-not-use-in-prod\")[/dim]")
    console.print("[yellow]問題: デフォルト値がハードコード → 環境変数が設定されない場合でも動いてしまう[/yellow]")
    console.print("\n修正方法:")
    console.print("[dim]  import secrets  # 起動時にシークレットがなければ例外を投げる\n"
                  "  JWT_SECRET = os.environ[\"JWT_SECRET\"]  # KeyError で起動失敗させる[/dim]")

    fixed_jwt = Confirm.ask("JWTシークレットの修正とdocker-compose.ymlの環境変数設定を完了しましたか？")
    if fixed_jwt:
        state.add_score(100, "JWT設定セキュア化")
        state.discovered_bugs.append("BUG-05: JWTデフォルトシークレット")

    # Step 4: 認証追加
    console.print("\n[bold]Step 4: /api/notes/search に認証を追加する[/bold]")
    console.print("api_gateway/main.py の search_notes エンドポイントに認証チェックを追加してください")

    fixed_auth = Confirm.ask("認証チェックを追加しましたか？")
    if fixed_auth:
        state.add_score(100, "認証エンドポイント保護")
        state.discovered_bugs.append("BUG-06: 未認証エンドポイント")

    # 脅威モデリングの問いかけ
    console.print(Panel(
        "[bold]セキュリティ演習:[/bold]\n"
        "1. このシステムのDFD（データフロー図）を描いてみてください\n"
        "2. STRIDEモデルで残りの脅威を洗い出してください\n"
        "3. セキュリティインシデントが発生した場合の対応手順書を書いてください\n"
        "4. 今回の修正をPRとしてどうレビューするか？",
        title="🎯 テックリード課題",
        border_style="red",
    ))

    state.completed_scenarios.append("scenario_02_security")
    console.print("[green]シナリオ2完了！[/green]")


def scenario_03_data_pipeline():
    """シナリオ3: データパイプライン障害とPM意思決定"""
    state.max_score += 350

    console.print(Panel(
        "[bold yellow]📊 データ品質アラート[/bold yellow]\n\n"
        "プロダクトマネージャーから Slack メッセージ:\n\n"
        "[white]「分析ダッシュボードのデータが3日間更新されていません。\n"
        " 投資家向けのデモが明日あるのに、古いデータを見せることになります。\n"
        " 緊急対応をお願いします！」[/white]\n\n"
        "analytics_service の /pipeline/run を叩いても応答がない...",
        title="💬 Slack - #engineering-alerts",
        border_style="yellow",
    ))

    # Step 1: 問題の診断
    console.print("\n[bold]Step 1: パイプラインの状態を診断する[/bold]")
    console.print("以下のコマンドで状態を確認してください:")
    console.print("[dim]  curl -X POST http://localhost:8003/pipeline/run\n"
                  "  curl http://localhost:8003/stats/summary\n"
                  "  docker logs techcorp_sim-analytics_service-1[/dim]")
    console.print("[yellow]pipelineを実行しても何も返ってこない（サイレント失敗）[/yellow]")

    found = Confirm.ask("サイレント失敗を発見しましたか？ (analytics_service/main.py の except: pass を確認)")
    if found:
        state.add_score(50, "サイレント失敗バグを発見")
        state.discovered_bugs.append("BUG-09: サイレント例外握りつぶし")

    # Step 2: 修正
    console.print("\n[bold]Step 2: エラーハンドリングを修正する[/bold]")
    console.print("[yellow]analytics_service/main.py の except 節を修正してください:[/yellow]")
    console.print("""
[dim]  # 修正後:
  except Exception as e:
      import logging
      logging.error(f"Pipeline failed: {e}", exc_info=True)
      PIPELINE_RUNS.labels("failure").inc()
      return {"status": "failed", "error": str(e)}[/dim]
""")

    fixed = Confirm.ask("エラーハンドリングを修正しましたか？")
    if fixed:
        state.add_score(100, "パイプラインのエラーハンドリング修正")

    # Step 3: 定期実行の設定
    console.print("\n[bold]Step 3: パイプラインを自動化する（APScheduler）[/bold]")
    console.print("現状: 手動でAPIを叩かないと集計されない")
    console.print("[yellow]analytics_service/main.py に定期実行を追加してください:[/yellow]")
    console.print("""
[dim]  from apscheduler.schedulers.background import BackgroundScheduler

  scheduler = BackgroundScheduler()
  scheduler.add_job(run_pipeline_internal, 'cron', hour=1, minute=0)
  scheduler.start()[/dim]
""")

    automated = Confirm.ask("定期実行を設定しましたか？")
    if automated:
        state.add_score(100, "パイプライン自動化（定期実行）")

    # PM意思決定
    console.print(Panel(
        "[bold]PM判断が必要です:[/bold]\n\n"
        "状況: データが3日分欠損している。\n"
        "選択肢:\n"
        "  A) 欠損期間を手動で補完してから投資家デモ（3時間かかる）\n"
        "  B) 欠損を投資家に正直に説明してデモ（信頼性リスク）\n"
        "  C) デモを1日延期して正確なデータで臨む（スケジュールリスク）\n"
        "  D) 欠損部分を除いたデータでデモ（部分的なデータを見せる）",
        title="🎯 PM判断",
        border_style="blue",
    ))

    decision = Prompt.ask("あなたの判断は？（A/B/C/D）", choices=["A", "B", "C", "D"])
    state.decisions["data_pipeline_incident"] = decision

    reasoning = {
        "A": "技術的解決を優先。ただし3時間の工数コストと品質リスクを考慮したか？",
        "B": "透明性を優先。投資家との信頼構築に良いが、準備不足の印象を与えるリスク",
        "C": "品質を最優先。スケジュール変更のコストを上回るメリットを説明できるか？",
        "D": "現実的な妥協案。透明性を保ちながらデモを進められる",
    }
    console.print(f"\n[cyan]あなたの選択 ({decision}):[/cyan] {reasoning[decision]}")
    console.print("[yellow]正解はありません。判断の根拠を言語化できることが重要です。[/yellow]")
    state.add_score(100, f"PM判断を実施（選択: {decision}）")

    state.completed_scenarios.append("scenario_03_data_pipeline")
    console.print("[green]シナリオ3完了！[/green]")


def scenario_04_scaling():
    """シナリオ4: トラフィックスパイクとスケーリング"""
    state.max_score += 350

    console.print(Panel(
        "[bold red]⚡ CRITICAL: トラフィックスパイク検知[/bold red]\n\n"
        "[white]Grafana Alert:\n"
        "  api_gateway: CPU 95%, Memory 88%\n"
        "  note_service: Response time P99 = 12秒\n"
        "  エラー率: 23% (5xx)\n\n"
        "原因: TechCrunchに記事が掲載され、通常の50倍のトラフィック\n"
        "推定影響: $50,000/時間の機会損失[/white]",
        title="🔥 Grafana Critical Alert",
        border_style="red",
    ))

    # Step 1: 即時対応
    console.print("\n[bold]Step 1: 即時対応（5分以内）[/bold]")
    console.print("Docker Composeでスケールアウト:")
    console.print("[dim]  docker compose up --scale note_service=3 -d\n"
                  "  docker compose up --scale api_gateway=2 -d[/dim]")
    console.print("\n[yellow]注意: 現在のapi_gatewayはステートフル（セッション情報をメモリに持つ）\n"
                  "複数インスタンスにするとセッションが失われる。なぜか？[/yellow]")

    scaled = Confirm.ask("スケールアウトを実施しましたか？")
    if scaled:
        state.add_score(80, "緊急スケールアウト実施")

    # Step 2: 根本解決
    console.print("\n[bold]Step 2: ステートレス化（根本解決）[/bold]")
    console.print("セッションをRedisに移行することでステートレス化できます")
    console.print("[yellow]api_gateway/main.py に Redis セッション管理を実装してください:[/yellow]")
    console.print("""
[dim]  import redis
  r = redis.from_url(os.environ["REDIS_URL"])

  # セッションをRedisに保存
  r.setex(f"session:{token}", 3600, json.dumps(session_data))

  # セッションをRedisから取得
  data = r.get(f"session:{token}")[/dim]
""")

    stateless = Confirm.ask("Redisセッション管理を実装しましたか？")
    if stateless:
        state.add_score(100, "ステートレス化（Redis）完了")

    # Step 3: レート制限
    console.print("\n[bold]Step 3: レート制限の実装（再発防止）[/bold]")
    console.print("api_gateway/main.py の rate_limit 関数を実装してください:")
    console.print("""
[dim]  # Redisを使ったスライディングウィンドウ方式
  async def rate_limit(request: Request, redis_client):
      key = f"rate:{request.client.host}"
      pipe = redis_client.pipeline()
      now = time.time()
      window_start = now - 60  # 1分間のウィンドウ

      pipe.zremrangebyscore(key, 0, window_start)
      pipe.zadd(key, {str(now): now})
      pipe.zcard(key)
      pipe.expire(key, 60)
      _, _, count, _ = await pipe.execute()

      if count > 100:
          raise HTTPException(status_code=429)[/dim]
""")

    rate_limited = Confirm.ask("レート制限を実装しましたか？")
    if rate_limited:
        state.add_score(100, "レート制限実装完了")

    # アーキテクチャ設計の問い
    console.print(Panel(
        "[bold]アーキテクチャ設計の問い:[/bold]\n\n"
        "長期的にこのスケーリング問題を解決するには？\n\n"
        "  1. Kubernetes (HPA) による自動スケーリング\n"
        "  2. CDN (CloudFront) による静的コンテンツのオフロード\n"
        "  3. キャッシュ層 (Redis) の追加\n"
        "  4. 読み取り/書き込みDBの分離 (Read Replica)\n"
        "  5. CQRS パターンの採用\n\n"
        "これらを組み合わせた場合のコスト試算と優先順位を考えてください",
        title="🏗️ アーキテクチャ課題",
        border_style="magenta",
    ))

    state.add_score(70, "スケーリング設計を検討")
    state.completed_scenarios.append("scenario_04_scaling")
    console.print("[green]シナリオ4完了！[/green]")


def scenario_05_pm_decision():
    """シナリオ5: PM総合判断 - 技術的負債 vs 新機能"""
    state.max_score += 300

    console.print(Panel(
        "[bold blue]📋 四半期計画会議[/bold blue]\n\n"
        "経営陣からの要請:\n\n"
        "[white]・CEOから: 競合が新機能をリリース。2週間以内に同等機能が必要\n"
        "・CFOから: インフラコストが先月比40%増。削減が必要\n"
        "・CTOから: 技術的負債がたまっており、このまま開発速度が低下する\n"
        "・開発チームから: バグ修正に80%の時間を取られている\n\n"
        "あなたの役割: テックリード兼PM として最適な判断を下せ[/white]",
        title="🏢 Q3 Planning Meeting",
        border_style="blue",
    ))

    # 優先度判断
    items = [
        ("A", "競合対抗の新機能開発（2週間）",         "高収益", "技術的負債がさらに増加"),
        ("B", "技術的負債の解消（4週間）",               "開発速度回復", "短期売上なし"),
        ("C", "インフラコスト削減（1週間）",             "コスト削減", "一時的な機能停止リスク"),
        ("D", "A+Cを並行（2週間、チームを2分割）",    "速度と削減を同時に", "各チームの負荷増大"),
    ]

    table = Table(title="優先度判断", box=box.ROUNDED)
    table.add_column("選択肢")
    table.add_column("内容")
    table.add_column("メリット")
    table.add_column("デメリット")
    for row in items:
        table.add_row(*row)
    console.print(table)

    console.print("\n[cyan]判断前に確認すべきデータ:[/cyan]")
    console.print("  curl http://localhost:8003/stats/summary  # ユーザー数・閲覧数")
    console.print("  curl http://localhost:8003/stats/trending  # 人気コンテンツ")

    decision = Prompt.ask("\nあなたの判断（A/B/C/D）", choices=["A", "B", "C", "D"])
    reasoning = Prompt.ask("判断の根拠（OKR・エラーバジェット・ROIの観点から）")

    state.decisions["q3_planning"] = {"decision": decision, "reasoning": reasoning}
    state.add_score(100, "Q3計画の意思決定完了")

    # OKR設計
    console.print("\n[bold]OKRを設計してください[/bold]")
    console.print("""
例:
  Objective: エンジニアリング品質を改善して持続的な開発速度を実現する
  KR1: エラー率を現在の23%から2%以下に削減する（6週間）
  KR2: デプロイ頻度を週1回から毎日に改善する
  KR3: P99レイテンシを12秒から1秒以下に改善する
""")

    okr_set = Confirm.ask("OKRを設計しましたか？")
    if okr_set:
        state.add_score(100, "OKR設計完了")

    # ステークホルダーコミュニケーション
    console.print("\n[bold]ステークホルダーへの報告書を作成してください[/bold]")
    console.print("[dim]  内容: 判断根拠・リスク・期待効果・タイムライン[/dim]")

    reported = Confirm.ask("報告書（Notion/Confluence）を作成しましたか？")
    if reported:
        state.add_score(100, "ステークホルダーレポート作成")

    state.completed_scenarios.append("scenario_05_pm_decision")
    console.print("[green]シナリオ5完了！[/green]")


# ─── メインループ ─────────────────────────────────────────

def show_final_results():
    total_bugs = len(state.discovered_bugs)
    total_decisions = len(state.decisions)
    pct = (state.score / state.max_score * 100) if state.max_score > 0 else 0

    grade = "S" if pct >= 90 else "A" if pct >= 75 else "B" if pct >= 60 else "C"

    console.print(Panel(
        f"[bold]最終スコア: {state.score} / {state.max_score} ({pct:.1f}%)[/bold]\n"
        f"グレード: [bold yellow]{grade}[/bold yellow]\n\n"
        f"✓ 発見したバグ: {total_bugs}件\n"
        f"  {chr(10).join(state.discovered_bugs)}\n\n"
        f"✓ 意思決定: {total_decisions}件\n"
        f"  {chr(10).join(f'{k}: {v}' for k,v in state.decisions.items())}\n\n"
        "[dim]このシミュレーションで使ったスキル一覧:\n"
        "  観測性(Prometheus/Grafana) | SQL最適化 | Goの並行処理\n"
        "  セキュリティ(OWASP/JWT) | データパイプライン | スケーリング\n"
        "  PM判断 | OKR設計 | ステークホルダー管理[/dim]",
        title="🏆 シミュレーション完了",
        border_style="gold1",
    ))


def main():
    console.print(Panel(
        "[bold cyan]TechCorp Simulator[/bold cyan]\n\n"
        "あなたはスタートアップ「TechCorp」のテックリード兼PMに就任しました。\n"
        "本番環境には複数の問題が潜んでいます。\n\n"
        "[yellow]全スキルを駆使して乗り越えてください。[/yellow]\n\n"
        "サービス構成:\n"
        "  - API Gateway (Python/FastAPI) :8000\n"
        "  - Note Service  (Python/FastAPI) :8001  ← バグあり\n"
        "  - Search Service (Go)            :8002  ← バグあり\n"
        "  - Analytics Service (Python)     :8003  ← バグあり\n"
        "  - Prometheus                     :9090\n"
        "  - Grafana                        :3001",
        title="🎮 ようこそ、TechCorp Simulator へ",
        border_style="cyan",
    ))

    # サービスの起動確認
    status = show_service_status()
    core = ["api_gateway", "note_service", "search_service", "analytics_service"]
    if not all(status.get(s, False) for s in core):
        console.print("\n[red]コアサービスが起動していません。[/red]")
        console.print("以下のコマンドでサービスを起動してください:")
        console.print("  [bold]docker compose up --build -d[/bold]")
        if not Confirm.ask("起動を試みますか？"):
            sys.exit(0)
        subprocess.run(["docker", "compose", "up", "--build", "-d"], check=False)
        wait_for_services()

    # シナリオ選択
    scenarios = [
        ("1", "🔴 シナリオ1: 本番パフォーマンス障害  (SQL・観測性・DevOps)", scenario_01_performance),
        ("2", "🔴 シナリオ2: セキュリティ脆弱性対応  (OWASP・JWT・認証)", scenario_02_security),
        ("3", "🟡 シナリオ3: データパイプライン障害  (データ工学・PM判断)", scenario_03_data_pipeline),
        ("4", "🔴 シナリオ4: トラフィックスパイク    (スケーリング・Redis・レート制限)", scenario_04_scaling),
        ("5", "🔵 シナリオ5: 四半期計画・PM意思決定  (OKR・ステークホルダー・戦略)", scenario_05_pm_decision),
        ("all", "📋 全シナリオを順番に実行", None),
        ("q", "終了", None),
    ]

    while True:
        console.print("\n[bold]--- シナリオ選択 ---[/bold]")
        state.show_scoreboard()
        for key, label, _ in scenarios:
            done = "✓ " if any(f"scenario_0{key}" in s for s in state.completed_scenarios) else "  "
            console.print(f"  {done}[bold]{key}[/bold]. {label}")

        choice = Prompt.ask("\n選択", choices=[s[0] for s in scenarios])

        if choice == "q":
            show_final_results()
            break
        elif choice == "all":
            for key, _, fn in scenarios[:-2]:
                console.print(f"\n{'='*60}")
                fn()
        else:
            fn = next((s[2] for s in scenarios if s[0] == choice), None)
            if fn:
                console.print(f"\n{'='*60}")
                fn()


if __name__ == "__main__":
    main()
