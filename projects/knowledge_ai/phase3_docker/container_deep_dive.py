#!/usr/bin/env python3
"""
Container / Docker / Kubernetes ディープダイブ
============================================
FAANG面接レベルのコンテナ技術を体系的に学ぶ。
標準ライブラリのみで実行可能。

実行: python3 container_deep_dive.py
"""

import json
import textwrap
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

SEP = "━" * 60


def section(title: str) -> None:
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)


def subsection(title: str) -> None:
    print(f"\n  ── {title} ──")


def question(q: str) -> None:
    print(f"\n  [考えてほしい疑問] {q}")


def task(desc: str) -> None:
    print(f"\n  [実装してみよう] {desc}")


# ============================================================
# 1. コンテナの仕組み - What a container really is
# ============================================================
def container_internals() -> None:
    section("1. コンテナの仕組み ─ Linux Namespaces, cgroups, UnionFS")

    print("""
    コンテナは「軽量VM」ではない。
    コンテナとは、Linux カーネルの機能を組み合わせた「プロセス隔離」の仕組みである。

    ┌─────────────────────────────────────────────────────┐
    │  VM vs Container                                    │
    ├─────────────────────────┬───────────────────────────┤
    │       VM                │      Container            │
    │  ┌──────────────┐       │  ┌──────────────┐         │
    │  │  App          │      │  │  App          │         │
    │  │  Guest OS     │      │  │  (bins/libs)  │         │
    │  │  Hypervisor   │      │  │  Container    │         │
    │  │  Host OS      │      │  │  Runtime      │         │
    │  │  Hardware     │      │  │  Host OS      │         │
    │  └──────────────┘       │  │  Hardware     │         │
    │                         │  └──────────────┘         │
    │  起動: 分単位           │  起動: ミリ秒単位         │
    │  サイズ: GB単位         │  サイズ: MB単位           │
    │  隔離: ハードウェアレベル│  隔離: カーネルレベル     │
    └─────────────────────────┴───────────────────────────┘
    """)

    subsection("Linux Namespaces ─ リソースの見え方を隔離")

    # Namespace の種類をデータで表現
    namespaces = [
        ("PID",    "プロセスID空間の隔離。コンテナ内ではPID 1から始まる"),
        ("NET",    "ネットワークスタックの隔離。独自のIPアドレス・ルーティングテーブル"),
        ("MNT",    "マウントポイントの隔離。独自のファイルシステムビュー"),
        ("UTS",    "ホスト名・ドメイン名の隔離"),
        ("IPC",    "プロセス間通信の隔離（共有メモリ、セマフォ等）"),
        ("USER",   "UID/GIDのマッピング。rootless containerの基盤"),
        ("CGROUP", "cgroupビューの隔離（Linux 4.6+）"),
    ]

    print("\n    Namespace 一覧:")
    print(f"    {'種類':<10} {'説明'}")
    print("    " + "─" * 55)
    for ns_type, desc in namespaces:
        print(f"    {ns_type:<10} {desc}")

    print("""
    # PID Namespace の実例（概念コード）
    # unshare(CLONE_NEWPID) を呼ぶと新しいPID空間が作られる
    #
    # Host側:  PID 1 (systemd) → PID 1234 (container runtime) → PID 1235 (app)
    # Container側: PID 1 (app)  ← コンテナ内からはPID 1に見える
    """)

    subsection("cgroups ─ リソース使用量の制限")

    print("""
    cgroups (Control Groups) はリソースの「量」を制御する仕組み。

    ┌─────────────────────────────────────────────┐
    │  cgroup で制御できるリソース                │
    ├──────────────┬──────────────────────────────┤
    │  cpu         │ CPU使用時間の割り当て        │
    │  memory      │ メモリ上限（OOM Killerと連携）│
    │  blkio       │ ブロックI/Oの帯域制限        │
    │  cpuset      │ 使用可能なCPUコアを指定      │
    │  devices     │ デバイスアクセスの制御        │
    │  pids        │ 生成可能なプロセス数の制限    │
    └──────────────┴──────────────────────────────┘

    docker run --memory=512m --cpus=1.5 nginx
    → memory cgroup: 512MB上限, cpu cgroup: 1.5コア分のCPU時間
    """)

    subsection("UnionFS (OverlayFS) ─ レイヤー構造")

    print("""
    コンテナイメージはレイヤーの積み重ね（Copy-on-Write）。

    ┌────────────────────────────┐  ← Container Layer (Read/Write)
    ├────────────────────────────┤
    │  Layer 4: COPY app.py     │  ← アプリケーションコード
    ├────────────────────────────┤
    │  Layer 3: RUN pip install  │  ← 依存パッケージ
    ├────────────────────────────┤
    │  Layer 2: RUN apt-get     │  ← システムパッケージ
    ├────────────────────────────┤
    │  Layer 1: Ubuntu base     │  ← ベースイメージ
    └────────────────────────────┘

    ポイント:
    - 各レイヤーは不変（immutable）。変更は新レイヤーに記録される
    - 同じベースレイヤーは複数コンテナで共有 → ディスク節約
    - docker history <image> でレイヤー構成を確認可能
    """)

    question("コンテナ内でPID 1のプロセスが死んだらどうなる？VMとの違いは？")
    question("cgroups v1 と v2 の違いは何か？なぜ v2 への移行が進んでいるか？")

    task("unshare コマンドで PID namespace を分離し、隔離されたシェルを体験せよ:\n"
         "    unshare --pid --fork --mount-proc /bin/bash && ps aux")


# ============================================================
# 2. Docker イメージ最適化
# ============================================================
def docker_image_optimization() -> None:
    section("2. Docker イメージ最適化 ─ Layer Caching & Multi-stage Builds")

    subsection("レイヤーキャッシュ戦略")

    print("""
    Dockerfile の命令順序がビルド速度を決定する。
    変更頻度の低いものを上に、高いものを下に配置する。

    # BAD: ソースコード変更のたびに全レイヤー再ビルド
    COPY . /app
    RUN pip install -r requirements.txt

    # GOOD: 依存関係のキャッシュを活用
    COPY requirements.txt /app/
    RUN pip install -r requirements.txt
    COPY . /app

    原則: 「変更頻度の低い命令 → 高い命令」の順に記述
    """)

    subsection("Multi-stage Build ─ 本番イメージの最小化")

    print("""
    # ── Stage 1: ビルド環境 ──
    FROM golang:1.22 AS builder
    WORKDIR /app
    COPY go.mod go.sum ./
    RUN go mod download
    COPY . .
    RUN CGO_ENABLED=0 go build -o server .

    # ── Stage 2: 実行環境（最小イメージ）──
    FROM gcr.io/distroless/static:nonroot
    COPY --from=builder /app/server /server
    USER nonroot:nonroot
    ENTRYPOINT ["/server"]
    """)

    subsection("イメージサイズ比較テーブル")

    # ベースイメージサイズの比較
    images = [
        ("ubuntu:22.04",              "77MB",   "フル機能、デバッグ容易"),
        ("python:3.12",               "1.01GB", "全パッケージ込み、開発向け"),
        ("python:3.12-slim",          "155MB",  "最小限のDebian、本番推奨"),
        ("python:3.12-alpine",        "51MB",   "musl libc、互換性注意"),
        ("node:20",                   "1.1GB",  "フル機能"),
        ("node:20-alpine",            "135MB",  "軽量だがnative addon注意"),
        ("golang:1.22",               "814MB",  "ビルド用"),
        ("gcr.io/distroless/static",  "2.5MB",  "シェルなし、最小攻撃面"),
        ("scratch",                   "0MB",    "空イメージ、静的バイナリ専用"),
    ]

    print(f"\n    {'ベースイメージ':<35} {'サイズ':<10} {'備考'}")
    print("    " + "─" * 65)
    for name, size, note in images:
        print(f"    {name:<35} {size:<10} {note}")

    subsection(".dockerignore の重要性")

    print("""
    .dockerignore がないと COPY . でビルドコンテキストに不要ファイルが含まれる。

    # .dockerignore の例
    .git
    .github
    __pycache__
    *.pyc
    .env
    node_modules
    .vscode
    *.md
    tests/
    docker-compose*.yml

    効果: ビルド時間短縮 + 秘密情報の混入防止 + イメージサイズ削減
    """)

    question("Alpine Linux ベースのイメージで Python パッケージが動かないケースがある。なぜか？")
    question("distroless イメージにシェルがない場合、デバッグはどうする？")

    task("既存プロジェクトの Dockerfile を multi-stage build に書き換え、\n"
         "    サイズ削減率を docker images で確認せよ")


# ============================================================
# 3. Docker Compose 設計パターン
# ============================================================
def docker_compose_patterns() -> None:
    section("3. Docker Compose 設計パターン ─ Service Discovery & Volume")

    subsection("Service Discovery")

    print("""
    Compose はデフォルトでサービス名をDNS名として解決する。

    services:
      web:
        image: nginx
        depends_on:
          db:
            condition: service_healthy
      db:
        image: postgres:16
        healthcheck:
          test: ["CMD-SHELL", "pg_isready -U postgres"]
          interval: 5s
          timeout: 3s
          retries: 5

    web コンテナから db:5432 でアクセス可能（内部DNS解決）。
    depends_on だけでは「起動順序」のみ保証。
    condition: service_healthy で「準備完了」まで待てる。
    """)

    subsection("Volume の種類と使い分け")

    volumes = [
        ("Bind Mount",  "-v ./src:/app",        "開発時のホットリロード。ホストのパスに依存"),
        ("Named Volume", "-v db_data:/var/lib",  "データ永続化。Docker管理。本番推奨"),
        ("tmpfs",        "--tmpfs /tmp",         "メモリ上の一時領域。機密データの一時保存"),
        ("Anonymous",    "-v /data",             "コンテナ削除で消える。テスト用"),
    ]

    print(f"\n    {'種類':<16} {'例':<28} {'用途'}")
    print("    " + "─" * 65)
    for vtype, example, usage in volumes:
        print(f"    {vtype:<16} {example:<28} {usage}")

    subsection("Network Isolation パターン")

    print("""
    # フロントエンド・バックエンド・DBの3層分離

    services:
      frontend:
        networks: [frontend]
      backend:
        networks: [frontend, backend]   # 両方に接続
      db:
        networks: [backend]             # バックエンドからのみアクセス可

    networks:
      frontend:
        driver: bridge
      backend:
        driver: bridge
        internal: true                  # 外部アクセス不可

    → DB はインターネットから到達不可能。最小権限の原則。
    """)

    question("depends_on の condition に service_started / service_healthy /\n"
             "    service_completed_successfully がある。それぞれどう使い分けるか？")

    task("Web + API + DB + Redis の4サービス構成で、\n"
         "    ネットワーク分離と healthcheck を設計せよ")


# ============================================================
# 4. コンテナセキュリティ
# ============================================================
def container_security() -> None:
    section("4. コンテナセキュリティ ─ 多層防御")

    subsection("Non-root 実行")

    print("""
    デフォルトでは root で実行されるが、これは危険。

    # Dockerfile でユーザーを作成
    RUN groupadd -r appuser && useradd -r -g appuser appuser
    USER appuser

    # docker run でも指定可能
    docker run --user 1000:1000 myapp

    rootless Docker/Podman を使えばデーモン自体が非root。
    """)

    subsection("Read-only ファイルシステム")

    print("""
    docker run --read-only --tmpfs /tmp myapp

    書き込みが必要な場所だけ tmpfs でマウント。
    マルウェアがバイナリを書き込むのを防ぐ。
    """)

    subsection("Seccomp & Capabilities")

    print("""
    Linux Capabilities の制御:
    docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE myapp
    → 全権限を剥奪し、必要最小限（ポート80/443バインド）だけ付与

    Seccomp プロファイル:
    docker run --security-opt seccomp=custom.json myapp
    → システムコールレベルで制限（デフォルトでも44個のsyscallをブロック）

    --security-opt=no-new-privileges:true
    → 子プロセスが権限昇格するのを防ぐ（setuid ビットを無効化）
    """)

    subsection("イメージスキャン & サプライチェーン")

    print("""
    スキャンツール比較:
    ┌──────────────┬──────────────────────────────────────┐
    │  Trivy       │ OSS、高速、CI/CDに統合しやすい       │
    │  Snyk        │ 商用、開発者UX重視、修正提案あり     │
    │  Grype       │ OSS（Anchore）、SBOMと連携           │
    │  docker scout│ Docker公式、docker CLI統合           │
    └──────────────┴──────────────────────────────────────┘

    SBOM (Software Bill of Materials):
    - コンテナ内の全ソフトウェア部品を一覧化
    - syft <image> で SBOM 生成 → grype で脆弱性スキャン
    - 米国大統領令(EO 14028)でSBOMが義務化の流れ

    CI/CD での実装:
    trivy image --severity HIGH,CRITICAL --exit-code 1 myapp:latest
    → HIGH以上の脆弱性があればパイプライン失敗
    """)

    # セキュリティチェックリストをシミュレーション
    checklist = [
        ("Non-root ユーザーで実行",       True),
        ("Read-only ファイルシステム",     True),
        ("不要な Capability を DROP",      True),
        ("no-new-privileges 設定",         True),
        ("イメージスキャン（CI/CD統合）",  True),
        ("ベースイメージの定期更新",       True),
        (".dockerignore で機密ファイル除外", True),
        ("SBOM の生成と管理",              False),
    ]

    print("\n    セキュリティチェックリスト:")
    for item, done in checklist:
        mark = "✓" if done else "□"
        print(f"      [{mark}] {item}")

    question("コンテナブレイクアウト（コンテナからホストへの脱出）の\n"
             "    攻撃ベクトルを3つ挙げ、それぞれの対策を述べよ")

    task("Trivy をインストールし、自分のプロジェクトのイメージをスキャンせよ:\n"
         "    trivy image <your-image>")


# ============================================================
# 5. Kubernetes アーキテクチャ
# ============================================================
def k8s_architecture() -> None:
    section("5. Kubernetes アーキテクチャ ─ Control Plane & Data Plane")

    print("""
    ┌───────────────────────────────────────────────────────────────────┐
    │                      Control Plane (Master)                      │
    │                                                                   │
    │  ┌─────────────┐  ┌──────────┐  ┌────────────┐  ┌────────────┐  │
    │  │ API Server   │  │  etcd    │  │ Scheduler  │  │ Controller │  │
    │  │             │  │ (分散KVS)│  │            │  │  Manager   │  │
    │  │ 全通信の     │  │ 全状態を │  │ Podの配置  │  │ 望ましい   │  │
    │  │ ゲートウェイ │  │ 永続化   │  │ 先を決定   │  │ 状態を維持 │  │
    │  └──────┬──────┘  └──────────┘  └────────────┘  └────────────┘  │
    │         │                                                         │
    └─────────┼─────────────────────────────────────────────────────────┘
              │  kubelet が API Server を Watch
    ┌─────────┼─────────────────────────────────────────────────────────┐
    │         ▼         Data Plane (Worker Nodes)                      │
    │                                                                   │
    │  Node 1                      Node 2                              │
    │  ┌────────────────────┐     ┌────────────────────────┐           │
    │  │ kubelet             │    │ kubelet                 │           │
    │  │  └─ Pod [container] │    │  └─ Pod [container]     │           │
    │  │  └─ Pod [container] │    │  └─ Pod [container]     │           │
    │  │ kube-proxy          │    │ kube-proxy              │           │
    │  │ Container Runtime   │    │ Container Runtime       │           │
    │  └────────────────────┘    └────────────────────────┘            │
    └───────────────────────────────────────────────────────────────────┘
    """)

    subsection("各コンポーネントの役割")

    components = {
        "API Server": (
            "全ての操作の入口。kubectl, kubelet, 他コンポーネント全てがここを経由。\n"
            "         認証(AuthN) → 認可(AuthZ/RBAC) → Admission Control → etcd書き込み"
        ),
        "etcd": (
            "分散キーバリューストア（Raft合意アルゴリズム）。\n"
            "         クラスタの全状態を保持。バックアップが最重要運用タスク"
        ),
        "Scheduler": (
            "未割り当てPodを検知し、最適なNodeを選択。\n"
            "         Filtering（条件に合わないNodeを除外）→ Scoring（スコアリング）"
        ),
        "Controller Manager": (
            "各種Controllerの集合体。Reconciliation Loop で\n"
            "         「現在の状態」を「望ましい状態(desired state)」に近づけ続ける"
        ),
        "kubelet": (
            "各Nodeで動作するエージェント。Pod仕様に基づきコンテナを管理。\n"
            "         Liveness/Readiness/Startup Probe を実行"
        ),
        "kube-proxy": (
            "Serviceの仮想IPへのトラフィックを実際のPodに転送。\n"
            "         iptables / IPVS / eBPF モードがある"
        ),
    }

    for name, desc in components.items():
        print(f"\n    {name}:")
        print(f"      {desc}")

    subsection("Pod ライフサイクル")

    print("""
    Pending → Running → Succeeded/Failed
       │                    │
       └── ContainerCreating ─ CrashLoopBackOff (再起動ループ)

    重要な Probe:
    ┌──────────────┬───────────────────────────────────────────┐
    │ Liveness     │ 失敗 → コンテナ再起動。デッドロック検知用 │
    │ Readiness    │ 失敗 → Service から除外。起動待ち用       │
    │ Startup      │ 起動が遅いアプリ用。成功まで他Probeを停止 │
    └──────────────┴───────────────────────────────────────────┘
    """)

    question("etcd が全滅したらクラスタはどうなるか？復旧手順は？")
    question("API Server が 1台しかない場合のリスクと対策は？")


# ============================================================
# 6. K8s リソース設計 ─ Workload の使い分け
# ============================================================
def k8s_resource_design() -> None:
    section("6. K8s リソース設計 ─ Deployment / StatefulSet / DaemonSet / Job")

    print("""
    ワークロードの決定木 (Decision Tree):

    アプリケーションの性質は？
    │
    ├─ ステートレス（Webサーバ、API等）
    │   └─ → Deployment + HPA
    │
    ├─ ステートフル（DB、Kafka、ZooKeeper等）
    │   └─ → StatefulSet
    │       ・安定したネットワークID（pod-0, pod-1, ...）
    │       ・永続ボリュームとの1:1マッピング
    │       ・順序付き起動/停止
    │
    ├─ 全Nodeで1つずつ（ログ収集、モニタリング等）
    │   └─ → DaemonSet
    │       ・fluentd, datadog-agent, node-exporter等
    │
    ├─ 一回限りの処理（バッチ、データ移行等）
    │   └─ → Job
    │       ・completions: 完了が必要なPod数
    │       ・parallelism: 並列実行数
    │       ・backoffLimit: リトライ上限
    │
    └─ 定期実行（集計、レポート等）
        └─ → CronJob
            ・schedule: "0 */6 * * *"
            ・concurrencyPolicy: Forbid/Replace/Allow
    """)

    subsection("Deployment の更新戦略")

    strategies = [
        ("RollingUpdate", "デフォルト。maxSurge/maxUnavailable で速度制御",
         "一般的なWebアプリ"),
        ("Recreate",      "全Pod停止 → 全Pod起動。ダウンタイムあり",
         "DBスキーマ変更等"),
        ("Blue/Green",    "新旧環境を並行稼働しService切替（K8s外で実装）",
         "ゼロダウンタイム"),
        ("Canary",        "少量トラフィックを新バージョンに流す（Istio等）",
         "リスク最小化"),
    ]

    print(f"\n    {'戦略':<16} {'説明':<48} {'ユースケース'}")
    print("    " + "─" * 78)
    for name, desc, use in strategies:
        print(f"    {name:<16} {desc:<48} {use}")

    subsection("Resource Requests / Limits")

    print("""
    resources:
      requests:           # スケジューリングに使用（保証値）
        cpu: "250m"       # 0.25 CPU core
        memory: "256Mi"
      limits:             # 超過時の制限（上限値）
        cpu: "500m"       # スロットリング
        memory: "512Mi"   # OOM Kill

    QoS クラス:
    ┌──────────────┬───────────────────────────────────────┐
    │ Guaranteed   │ requests == limits（全リソース指定）   │
    │ Burstable    │ requests < limits（部分指定）          │
    │ BestEffort   │ requests/limits なし（最初にevict）    │
    └──────────────┴───────────────────────────────────────┘

    ベストプラクティス:
    - 本番では必ず requests を設定（スケジューリング精度）
    - CPU limits は設定しない派閥もある（スロットリングの害）
    - Memory limits は必ず設定（OOM Kill の方がハングより良い）
    """)

    question("StatefulSet の Pod が順序通りに起動する必要があるのはなぜか？\n"
             "    podManagementPolicy: Parallel にするとどうなる？")

    task("Deployment の maxSurge=1, maxUnavailable=0 と\n"
         "    maxSurge=0, maxUnavailable=1 の動作の違いを図で説明せよ")


# ============================================================
# 7. K8s ネットワーク
# ============================================================
def k8s_networking() -> None:
    section("7. K8s ネットワーク ─ Service Types & Ingress & Service Mesh")

    print("""
    外部トラフィックの到達経路:

    Internet
       │
       ▼
    ┌──────────────┐
    │  Ingress     │  L7 (HTTP/HTTPS) ルーティング
    │  Controller  │  パスベース・ホストベース振り分け
    └──────┬───────┘
           │
    ┌──────▼───────┐
    │  Service     │  L4 ロードバランシング
    │  (ClusterIP) │  仮想IP → Pod群へ分散
    └──────┬───────┘
           │
    ┌──────▼───────┐
    │  Pod         │  実際のワークロード
    │  (Endpoint)  │
    └──────────────┘
    """)

    subsection("Service Types 比較")

    service_types = [
        ("ClusterIP",    "クラスタ内部のみ",     "マイクロサービス間通信"),
        ("NodePort",     "Node IP:30000-32767",   "開発・テスト用"),
        ("LoadBalancer", "クラウドLBを自動作成",  "外部公開（費用注意）"),
        ("ExternalName", "CNAMEレコード",         "外部サービスへのエイリアス"),
        ("Headless",     "ClusterIP: None",       "StatefulSet, DNS直接解決"),
    ]

    print(f"\n    {'Type':<16} {'アクセス範囲':<24} {'ユースケース'}")
    print("    " + "─" * 60)
    for stype, scope, use in service_types:
        print(f"    {stype:<16} {scope:<24} {use}")

    subsection("Ingress パターン")

    print("""
    # パスベースルーティング
    apiVersion: networking.k8s.io/v1
    kind: Ingress
    spec:
      rules:
      - host: api.example.com
        http:
          paths:
          - path: /users    → users-service:8080
          - path: /orders   → orders-service:8080
          - path: /payments → payments-service:8080

    Ingress Controller の選択肢:
    ┌──────────────────┬──────────────────────────────────┐
    │ NGINX Ingress    │ 最も普及。設定の柔軟性が高い     │
    │ Traefik          │ 自動SSL、ミドルウェアチェーン    │
    │ AWS ALB Ingress  │ AWS ALBをネイティブに利用        │
    │ Istio Gateway    │ Service Mesh統合                 │
    │ Envoy Gateway    │ Gateway API 対応、次世代標準     │
    └──────────────────┴──────────────────────────────────┘
    """)

    subsection("Service Mesh ─ Istio / Linkerd")

    print("""
    Service Mesh はサイドカーパターンでトラフィックを制御する。

    ┌──────────────────────────────┐
    │  Pod                         │
    │  ┌────────┐  ┌────────────┐ │
    │  │  App   │──│ Envoy      │ │  ← サイドカープロキシ
    │  │        │  │ (Sidecar)  │ │
    │  └────────┘  └─────┬──────┘ │
    └────────────────────┼────────┘
                         │ mTLS で暗号化
    ┌────────────────────┼────────┐
    │  Pod               ▼        │
    │  ┌────────┐  ┌────────────┐ │
    │  │  App   │──│ Envoy      │ │
    │  │        │  │ (Sidecar)  │ │
    │  └────────┘  └────────────┘ │
    └──────────────────────────────┘

    Service Mesh が提供する機能:
    - mTLS（サービス間の自動暗号化）
    - トラフィック分割（Canary, A/B テスト）
    - サーキットブレーカー、リトライ、タイムアウト
    - 分散トレーシング（Jaeger/Zipkin連携）
    - アクセスポリシー（AuthorizationPolicy）

    Ambient Mesh (Istio): サイドカーなしの新アーキテクチャ（ztunnel + waypoint）
    """)

    question("Service Mesh のサイドカーがPodに与えるオーバーヘッドは？\n"
             "    それを回避する Ambient Mesh の仕組みを説明せよ")

    task("minikube 上で NGINX Ingress Controller を有効化し、\n"
         "    パスベースルーティングを設定せよ")


# ============================================================
# 8. スケーリング戦略
# ============================================================
def scaling_strategies() -> None:
    section("8. スケーリング戦略 ─ HPA / VPA / Cluster Autoscaler / KEDA")

    subsection("Horizontal Pod Autoscaler (HPA)")

    print("""
    Pod数を自動的に増減させる。

    apiVersion: autoscaling/v2
    kind: HorizontalPodAutoscaler
    spec:
      scaleTargetRef:
        kind: Deployment
        name: web-app
      minReplicas: 2
      maxReplicas: 20
      metrics:
      - type: Resource
        resource:
          name: cpu
          target:
            type: Utilization
            averageUtilization: 70    # CPU使用率70%を維持
      - type: Pods
        pods:
          metric:
            name: requests_per_second  # カスタムメトリクス
          target:
            type: AverageValue
            averageValue: "1000"

    スケーリングの計算式:
    desiredReplicas = ceil(currentReplicas × (currentMetric / desiredMetric))

    例: 現在3Pod, CPU 90%, 目標70%
    → ceil(3 × (90/70)) = ceil(3.86) = 4 Pod
    """)

    subsection("Vertical Pod Autoscaler (VPA)")

    print("""
    Pod のリソース requests/limits を自動調整する。

    注意点:
    - HPAとの併用は基本NG（CPU/Memory メトリクスが衝突）
    - updateMode:
      ・"Off"      → 推奨値の表示のみ（安全）
      ・"Initial"  → Pod作成時のみ適用
      ・"Auto"     → 既存Podも再作成して適用（ダウンタイムあり）
    """)

    subsection("Cluster Autoscaler")

    print("""
    Node数を自動的に増減させる。

    スケールアウト: Pending Pod を検知 → 新Node追加
    スケールイン:  Node利用率が低い → Pod退避 → Node削除

    ┌──────────────────────────────────────────────┐
    │  HPA: Pod数を調整（水平スケーリング）        │
    │   ↕ 連動                                     │
    │  Cluster Autoscaler: Node数を調整            │
    │   ↕ 連動                                     │
    │  VPA: Pod のリソースサイズを調整（垂直）      │
    └──────────────────────────────────────────────┘
    """)

    subsection("KEDA ─ イベント駆動スケーリング")

    print("""
    KEDA (Kubernetes Event-Driven Autoscaling):
    - 外部イベントソースに基づいてスケーリング
    - 0 Pod → N Pod のスケール（HPAは1以上が必要）

    対応スケーラー例:
    ┌────────────────────┬──────────────────────────────┐
    │  AWS SQS           │ キューの深さに応じてスケール │
    │  Kafka             │ Consumer Lag に応じて         │
    │  Prometheus        │ カスタムメトリクスに応じて    │
    │  Cron              │ 時間ベーススケジュール        │
    │  PostgreSQL        │ クエリ結果に応じて            │
    └────────────────────┴──────────────────────────────┘

    ユースケース: 夜間はPod 0、メッセージが来たら即座にスケールアウト
    → コスト最適化に非常に効果的
    """)

    question("HPA の stabilizationWindowSeconds はなぜ必要か？\n"
             "    スケールアップとスケールダウンで異なる値を設定すべき理由は？")

    task("metrics-server をインストールし、HPAを設定して\n"
         "    kubectl run で負荷をかけてスケーリングを確認せよ:\n"
         "    kubectl run load -- /bin/sh -c 'while true; do wget -q -O- http://web; done'")


# ============================================================
# 9. Helm & GitOps
# ============================================================
def helm_and_gitops() -> None:
    section("9. Helm & GitOps ─ Helm Charts, ArgoCD, Flux")

    subsection("Helm Chart 構造")

    print("""
    mychart/
    ├── Chart.yaml          # チャートのメタデータ（name, version, dependencies）
    ├── values.yaml         # デフォルトの設定値
    ├── values-prod.yaml    # 環境別オーバーライド
    ├── templates/
    │   ├── deployment.yaml # Go template でパラメータ化
    │   ├── service.yaml
    │   ├── ingress.yaml
    │   ├── hpa.yaml
    │   ├── _helpers.tpl    # 共通テンプレート関数
    │   └── NOTES.txt       # インストール後に表示されるメッセージ
    └── charts/             # 依存チャート

    # テンプレートの例
    replicas: {{ .Values.replicaCount }}
    image: {{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}

    # 便利なコマンド
    helm template mychart ./mychart -f values-prod.yaml  # ドライラン
    helm install mychart ./mychart --namespace prod
    helm upgrade mychart ./mychart --set image.tag=v2.0
    helm rollback mychart 1                               # リビジョン1に戻す
    """)

    subsection("GitOps の原則")

    print("""
    GitOps の4原則:
    1. 宣言的 ─ システムの望ましい状態をYAMLで宣言
    2. バージョン管理 ─ Gitが唯一の信頼源(Single Source of Truth)
    3. 自動適用 ─ 承認された変更が自動的にクラスタに反映
    4. 継続的監視 ─ 実際の状態と望ましい状態の乖離を検知・修復

    Push型 (CI/CD)              Pull型 (GitOps)
    ┌──────┐                    ┌──────┐
    │  Dev │── git push ──→    │  Dev │── git push ──→
    └──┬───┘                    └──────┘
       │                            │
       ▼                            ▼
    ┌──────┐    kubectl apply    ┌──────┐
    │  CI  │────────────────→   │  Git │ ← Single Source of Truth
    └──────┘                    └──┬───┘
                                   │ Watch (Pull)
                                ┌──▼───────┐
                                │  ArgoCD  │── sync ──→ K8s Cluster
                                │  / Flux  │
                                └──────────┘
    """)

    subsection("ArgoCD vs Flux")

    comparison = [
        ("UI",           "リッチなWeb UI",         "CLI中心、Grafana連携"),
        ("マルチクラスタ", "ネイティブサポート",    "Kustomization で対応"),
        ("Helm対応",      "Helmテンプレート直接",   "HelmRelease CRD"),
        ("同期戦略",      "自動/手動選択可",        "常に自動同期"),
        ("学習コスト",    "中（UIで直感的）",       "やや高い"),
        ("CNCF",          "Graduated",              "Graduated"),
    ]

    print(f"\n    {'観点':<16} {'ArgoCD':<24} {'Flux'}")
    print("    " + "─" * 60)
    for aspect, argo, flux in comparison:
        print(f"    {aspect:<16} {argo:<24} {flux}")

    question("GitOps で「秘密情報（Secret）」をGitに入れるわけにはいかない。\n"
             "    Sealed Secrets / SOPS / External Secrets Operator の違いは？")

    task("ArgoCD をminikubeにインストールし、GitHub リポジトリと\n"
         "    同期して自動デプロイを体験せよ")


# ============================================================
# 10. GPU ワークロード on K8s
# ============================================================
def gpu_workloads() -> None:
    section("10. GPU ワークロード ─ ML Inference on Kubernetes")

    subsection("NVIDIA Device Plugin")

    print("""
    K8s で GPU を使うための構成:

    ┌─────────────────────────────────────────────────┐
    │  Node                                            │
    │  ┌─────────────────────────────────────────────┐ │
    │  │  NVIDIA Driver                               │ │
    │  │  NVIDIA Container Toolkit (nvidia-docker2)   │ │
    │  │  Container Runtime (containerd + nvidia hook) │ │
    │  └─────────────────────────────────────────────┘ │
    │                                                   │
    │  ┌─────────────────────────────────────────────┐ │
    │  │  NVIDIA Device Plugin (DaemonSet)            │ │
    │  │  → GPU をK8sリソースとして公開               │ │
    │  │  → nvidia.com/gpu: 1 で要求可能に            │ │
    │  └─────────────────────────────────────────────┘ │
    └─────────────────────────────────────────────────┘

    # Pod で GPU を要求
    resources:
      limits:
        nvidia.com/gpu: 1    # GPU 1枚を占有

    制約: GPU は整数単位でしか割り当てられない（デフォルト）
    """)

    subsection("GPU Sharing ─ コスト最適化")

    print("""
    GPU は高価。1Pod=1GPU だと使用率が低くなりがち。

    共有方式:
    ┌────────────────────┬────────────────────────────────────┐
    │  Time-slicing      │ 時分割で複数Podが1GPUを共有        │
    │                    │ NVIDIA GPU Operator で設定          │
    │                    │ メモリ保護なし（OOMリスク）         │
    ├────────────────────┼────────────────────────────────────┤
    │  MIG               │ A100/H100をハードウェア分割        │
    │  (Multi-Instance   │ 最大7インスタンス                  │
    │   GPU)             │ メモリ・演算の完全分離             │
    ├────────────────────┼────────────────────────────────────┤
    │  MPS               │ CUDA レベルの空間共有              │
    │  (Multi-Process    │ 推論ワークロード向き               │
    │   Service)         │                                    │
    ├────────────────────┼────────────────────────────────────┤
    │  vGPU              │ VMware/NVIDIA仮想化                │
    │                    │ ライセンス費用が必要               │
    └────────────────────┴────────────────────────────────────┘
    """)

    subsection("ML Inference on K8s ─ 実践パターン")

    print("""
    推論サービスの構成例:

    ┌─────────┐    ┌──────────────┐    ┌──────────────┐
    │ Client  │───→│  Ingress     │───→│  Triton /    │
    │         │    │  (gRPC/HTTP) │    │  TorchServe  │
    └─────────┘    └──────────────┘    │  vLLM        │
                                       └──────┬───────┘
                                              │
                                       ┌──────▼───────┐
                                       │  Model Store │
                                       │  (S3 / PVC)  │
                                       └──────────────┘

    推論フレームワーク:
    - NVIDIA Triton: マルチフレームワーク対応、動的バッチング
    - vLLM: LLM特化、PagedAttention、高スループット
    - TorchServe: PyTorch公式、TorchScript対応
    - KServe: K8sネイティブ推論プラットフォーム

    スケーリング戦略:
    - GPU使用率ベースのHPA（DCGM Exporterでメトリクス取得）
    - リクエストキュー長ベースのKEDA
    - Knative で0→Nスケーリング（コールドスタート注意）
    """)

    question("GPU ノードのコストを最小化しつつ、推論レイテンシのSLAを\n"
             "    守るにはどのようなスケーリング戦略が最適か？")

    task("minikube で NVIDIA Device Plugin を有効化し（--gpus=all）、\n"
         "    GPU Pod をデプロイして nvidia-smi の出力を確認せよ")


# ============================================================
# 面接での質問例 (Interview Questions)
# ============================================================
def interview_questions() -> None:
    section("面接での質問例 ─ FAANG Container/K8s Interview Questions")

    questions = [
        # (難易度, カテゴリ, 質問, ヒント)
        ("基礎", "Container",
         "コンテナとVMの違いを、カーネルの観点から説明してください",
         "Namespace, cgroups, ハイパーバイザーの違い"),
        ("基礎", "Docker",
         "Dockerfile の COPY と ADD の違いは？",
         "ADDはURL取得とtar自動展開。COPYの方が推奨"),
        ("基礎", "Docker",
         "ENTRYPOINT と CMD の違いと使い分けは？",
         "ENTRYPOINTは固定コマンド、CMDはデフォルト引数"),
        ("中級", "Docker",
         "マルチステージビルドはなぜ必要か？具体例を挙げて説明せよ",
         "ビルドツール（gcc等）が本番イメージに含まれないようにする"),
        ("中級", "K8s",
         "Pod が CrashLoopBackOff になっている。トラブルシュートの手順は？",
         "kubectl logs, describe, events, リソース不足, probe設定"),
        ("中級", "K8s",
         "Deployment と StatefulSet の違いを、具体的なユースケースで説明せよ",
         "Pod名の安定性, PVCの1:1マッピング, 起動順序"),
        ("上級", "K8s",
         "1000 Pod のサービスで Rolling Update を安全に行うには？",
         "PDB, maxSurge/maxUnavailable, readiness gate, preStop hook"),
        ("上級", "K8s",
         "マルチテナントK8sクラスタの設計で考慮すべきことは？",
         "Namespace分離, NetworkPolicy, ResourceQuota, RBAC, PodSecurityStandard"),
        ("上級", "Networking",
         "Service Mesh を導入するか判断する基準は？メリットとオーバーヘッドは？",
         "サービス数, mTLS必要性, 可観測性要件, サイドカーのCPU/メモリコスト"),
        ("上級", "Architecture",
         "大規模K8sクラスタ（5000 Node）で直面する課題と対策は？",
         "etcdパフォーマンス, API Serverスケーリング, ネットワークCIDR設計"),
        ("上級", "GPU/ML",
         "GPU推論サービスのコストを50%削減する方法を3つ挙げよ",
         "MIG/Time-slicing, spot instance, モデル量子化, バッチング最適化"),
        ("応用", "GitOps",
         "GitOps で秘密情報を管理する方法を比較説明せよ",
         "Sealed Secrets, SOPS, External Secrets Operator, Vault"),
    ]

    for level, category, q, hint in questions:
        print(f"\n    [{level}][{category}]")
        print(f"    Q: {q}")
        print(f"    Hint: {hint}")

    subsection("システム設計問題の例")

    print("""
    Q: 「1日1億リクエストを処理するAPIサービスをK8s上に設計せよ」

    考慮すべきポイント:
    1. トラフィック計算: 1億/86400 ≒ 1157 RPS (ピーク時は3-5倍)
    2. Pod設計: 1 Pod あたりの処理能力を計測 → 必要Pod数算出
    3. HPA設定: CPU + カスタムメトリクス (RPS) で自動スケール
    4. Ingress: NGINX Ingress + rate limiting
    5. データストア: Redis (キャッシュ) + PostgreSQL (永続化)
    6. 可観測性: Prometheus + Grafana + Jaeger
    7. 耐障害性: PDB, Pod Anti-Affinity, Multi-AZ
    8. コスト: Spot Instance + Cluster Autoscaler + Resource Requests最適化
    """)


# ============================================================
# まとめ ─ 学習ロードマップ
# ============================================================
def learning_roadmap() -> None:
    section("学習ロードマップ ─ コンテナ技術の習得順序")

    print("""
    Phase 1: Docker 基礎（1-2週間）
    ├─ Dockerfile の書き方（multi-stage build含む）
    ├─ docker-compose でローカル開発環境構築
    └─ イメージ最適化とセキュリティ基礎

    Phase 2: Kubernetes 基礎（2-4週間）
    ├─ minikube / kind でローカルクラスタ構築
    ├─ Pod, Deployment, Service, Ingress
    ├─ ConfigMap, Secret, PersistentVolume
    └─ kubectl を使いこなす

    Phase 3: Kubernetes 運用（2-4週間）
    ├─ HPA, VPA, Cluster Autoscaler
    ├─ RBAC, NetworkPolicy, PodSecurityStandard
    ├─ Helm Chart の作成
    └─ モニタリング（Prometheus + Grafana）

    Phase 4: 本番レベル（4-8週間）
    ├─ GitOps (ArgoCD / Flux)
    ├─ Service Mesh (Istio / Linkerd)
    ├─ マルチクラスタ・マルチテナント
    └─ GPU ワークロード・MLOps

    推奨資格:
    - CKA  (Certified Kubernetes Administrator)
    - CKAD (Certified Kubernetes Application Developer)
    - CKS  (Certified Kubernetes Security Specialist)
    """)


# ============================================================
# メイン実行
# ============================================================
def main() -> None:
    print(SEP)
    print("  Container / Docker / Kubernetes ディープダイブ")
    print("  FAANG面接レベルのコンテナ技術を体系的に学ぶ")
    print(SEP)

    # 1. コンテナの仕組み
    container_internals()

    # 2. Docker イメージ最適化
    docker_image_optimization()

    # 3. Docker Compose 設計パターン
    docker_compose_patterns()

    # 4. コンテナセキュリティ
    container_security()

    # 5. Kubernetes アーキテクチャ
    k8s_architecture()

    # 6. K8s リソース設計
    k8s_resource_design()

    # 7. K8s ネットワーク
    k8s_networking()

    # 8. スケーリング戦略
    scaling_strategies()

    # 9. Helm & GitOps
    helm_and_gitops()

    # 10. GPU ワークロード
    gpu_workloads()

    # 面接問題集
    interview_questions()

    # 学習ロードマップ
    learning_roadmap()

    print("""
  ★ 優先度順まとめ (この順で覚える):

  【Tier 1: 最優先 — 面接・実務で即必要】
    - Dockerfile書き方
    - docker build/run/logs/exec
    - docker compose基礎

  【Tier 2: 重要 — 実務で頻出】
    - マルチステージビルド
    - ネットワーク設計
    - ボリューム管理
    - ヘルスチェック

  【Tier 3: 上級 — シニア以上で差がつく】
    - namespaces/cgroups理解
    - K8sアーキテクチャ
    - Pod設計
    - HPA

  【Tier 4: 専門 — Staff+/特定ドメインで必要】
    - CNI, CSI, CRI
    - カスタムコントローラー
    - Operator パターン
""")

    print(f"\n{SEP}")
    print("  学習完了！次のステップ:")
    print("  1. minikube install → ローカルクラスタで実践")
    print("  2. 自分のアプリをコンテナ化して K8s にデプロイ")
    print("  3. CKA/CKAD 資格取得を目指す")
    print(SEP)


if __name__ == "__main__":
    main()
