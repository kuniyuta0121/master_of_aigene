#!/usr/bin/env python3
"""
DevOps / Infrastructure ハンズオン学習モジュール
================================================
Docker, Kubernetes, Terraform, CI/CD, FinOps, Cloud Security を
体系的に学ぶ。標準ライブラリのみで実行可能。

実行: python3 devops_hands_on.py
"""

import json
import math
import random
import textwrap
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple

SEP = "━" * 60


def section(title: str) -> None:
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)


def subsection(title: str) -> None:
    print(f"\n  ── {title} ──")


def show_yaml(label: str, content: str) -> None:
    print(f"\n  [{label}]")
    for line in textwrap.dedent(content).strip().splitlines():
        print(f"    {line}")
    print()


def show_config(label: str, content: str) -> None:
    print(f"\n  [{label}]")
    for line in textwrap.dedent(content).strip().splitlines():
        print(f"    {line}")
    print()


def quiz(q: str, choices: List[str], answer_idx: int, explanation: str) -> None:
    print(f"\n  [Quiz] {q}")
    for i, c in enumerate(choices):
        print(f"    {chr(65 + i)}. {c}")
    ans = chr(65 + answer_idx)
    print(f"  --> 正解: {ans}. {choices[answer_idx]}")
    print(f"      解説: {explanation}")


# ============================================================
# Chapter 1: Docker Patterns
# ============================================================
def chapter1_docker_patterns() -> None:
    section("Chapter 1: Docker Patterns")

    # --- Multi-stage Build ---
    subsection("1.1 Multi-stage Build パターン")

    print("""
    Multi-stage build は最終イメージサイズを劇的に削減する手法。
    ビルド環境と実行環境を分離し、実行に必要なアーティファクトだけをコピーする。

    ┌─────────────── Build Stage ───────────────┐
    │  FROM golang:1.21 AS builder               │
    │  - ソースコード                              │
    │  - コンパイラ / ビルドツール                   │
    │  - 依存パッケージ                             │
    │  - 最終バイナリ ← これだけ次へ                 │
    └──────────────────┬────────────────────────┘
                       │ COPY --from=builder
    ┌──────────────────▼────────────────────────┐
    │  FROM gcr.io/distroless/static-debian12   │
    │  - バイナリのみ (数MB)                      │
    │  - シェルなし・パッケージマネージャなし         │
    │  - 攻撃対象面 (Attack Surface) を最小化       │
    └───────────────────────────────────────────┘
    """)

    show_yaml("Go アプリの Multi-stage Dockerfile", """
        # ---- Stage 1: Build ----
        FROM golang:1.21-alpine AS builder
        WORKDIR /app
        COPY go.mod go.sum ./
        RUN go mod download          # 依存だけ先にDL (レイヤーキャッシュ活用)
        COPY . .
        RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /app/server .

        # ---- Stage 2: Runtime ----
        FROM gcr.io/distroless/static-debian12:nonroot
        COPY --from=builder /app/server /server
        USER nonroot:nonroot
        EXPOSE 8080
        ENTRYPOINT ["/server"]
    """)

    show_yaml("Python アプリの Multi-stage Dockerfile", """
        # ---- Stage 1: Build ----
        FROM python:3.11-slim AS builder
        WORKDIR /app
        RUN python -m venv /opt/venv
        ENV PATH="/opt/venv/bin:$PATH"
        COPY requirements.txt .
        RUN pip install --no-cache-dir -r requirements.txt

        # ---- Stage 2: Runtime ----
        FROM python:3.11-slim
        COPY --from=builder /opt/venv /opt/venv
        ENV PATH="/opt/venv/bin:$PATH"
        WORKDIR /app
        COPY . .
        RUN useradd --create-home appuser
        USER appuser
        EXPOSE 8000
        CMD ["gunicorn", "app:create_app()", "-b", "0.0.0.0:8000"]
    """)

    # --- Image size simulation ---
    subsection("1.2 イメージサイズ比較シミュレーション")

    images = [
        ("ubuntu:22.04 + build tools + app", 850),
        ("python:3.11 (full)",               920),
        ("python:3.11-slim",                 150),
        ("python:3.11-alpine",                55),
        ("golang:1.21 (full)",              800),
        ("distroless/static (Go binary)",      5),
        ("scratch (Go binary)",                3),
    ]
    print("\n    ベースイメージ別サイズ比較:")
    print(f"    {'イメージ':<42} {'サイズ':>8}")
    print(f"    {'─' * 42} {'─' * 8}")
    for name, size in images:
        bar = "█" * (size // 20)
        print(f"    {name:<42} {size:>6} MB  {bar}")

    # --- Docker Compose ---
    subsection("1.3 Docker Compose オーケストレーション")

    show_yaml("本番レベルの docker-compose.yml", """
        version: "3.9"
        services:
          app:
            build:
              context: .
              dockerfile: Dockerfile
              target: runtime            # multi-stage の特定ステージ指定
            ports:
              - "8080:8080"
            environment:
              - DATABASE_URL=postgres://db:5432/mydb
              - REDIS_URL=redis://cache:6379
            depends_on:
              db:
                condition: service_healthy
              cache:
                condition: service_started
            deploy:
              resources:
                limits:
                  cpus: "1.0"
                  memory: 512M
                reservations:
                  cpus: "0.25"
                  memory: 128M
            healthcheck:
              test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
              interval: 30s
              timeout: 10s
              retries: 3
              start_period: 40s
            restart: unless-stopped

          db:
            image: postgres:16-alpine
            volumes:
              - pgdata:/var/lib/postgresql/data
            environment:
              POSTGRES_DB: mydb
              POSTGRES_PASSWORD_FILE: /run/secrets/db_password
            secrets:
              - db_password
            healthcheck:
              test: ["CMD-SHELL", "pg_isready -U postgres"]
              interval: 10s
              timeout: 5s
              retries: 5

          cache:
            image: redis:7-alpine
            command: redis-server --maxmemory 128mb --maxmemory-policy allkeys-lru

        volumes:
          pgdata:
            driver: local

        secrets:
          db_password:
            file: ./secrets/db_password.txt
    """)

    # --- Container Networking ---
    subsection("1.4 コンテナネットワーキング")

    print("""
    Docker のネットワークドライバ:

    ┌─────────────────────────────────────────────────────────────┐
    │ Driver      │ 用途              │ 特徴                       │
    ├─────────────┼───────────────────┼────────────────────────────┤
    │ bridge      │ 単一ホスト内通信    │ デフォルト。NAT経由で外部接続  │
    │ host        │ パフォーマンス重視   │ ホストのネットワークスタック共有│
    │ overlay     │ マルチホスト(Swarm) │ VXLAN で L2 ネットワーク構築  │
    │ macvlan     │ 物理NW直接接続      │ コンテナに固有MACアドレス付与  │
    │ none        │ 完全隔離           │ ネットワークなし              │
    └─────────────┴───────────────────┴────────────────────────────┘

    bridge ネットワークの通信フロー:
    ┌─────────┐     ┌──────────┐     ┌─────────────┐
    │ ContainerA│───▶│ docker0  │───▶ │ ContainerB  │
    │ 172.17.0.2│    │ (bridge) │     │ 172.17.0.3  │
    └─────────┘     └────┬─────┘     └─────────────┘
                         │ iptables NAT
                    ┌────▼─────┐
                    │ eth0     │
                    │ (host)   │
                    └──────────┘
    """)

    # --- Volume Strategies ---
    subsection("1.5 ボリューム戦略")

    volume_types = [
        ("Named Volume",  "docker volume create mydata",
         "データの永続化。DBデータなど。Docker が管理。"),
        ("Bind Mount",    "-v /host/path:/container/path",
         "開発時のソースコード共有。ホストとコンテナで双方向同期。"),
        ("tmpfs Mount",   "--tmpfs /tmp",
         "メモリ上の一時領域。秘密情報の一時保持に最適。"),
        ("Volume Driver",  "driver: local / nfs / s3fs",
         "NFS, EFS, S3 などリモートストレージをマウント。"),
    ]

    print("\n    ボリュームタイプ比較:")
    for vtype, cmd, desc in volume_types:
        print(f"\n    [{vtype}]")
        print(f"      コマンド例: {cmd}")
        print(f"      用途: {desc}")

    # --- Security ---
    subsection("1.6 Docker セキュリティベストプラクティス")

    show_yaml("セキュアな Dockerfile テンプレート", """
        FROM python:3.11-slim

        # 1. non-root ユーザー作成
        RUN groupadd -r appgroup && useradd -r -g appgroup -d /home/appuser appuser

        # 2. 必要最小限のパッケージのみインストール
        RUN apt-get update && \\
            apt-get install -y --no-install-recommends curl && \\
            rm -rf /var/lib/apt/lists/*

        WORKDIR /app
        COPY --chown=appuser:appgroup . .

        # 3. non-root ユーザーで実行
        USER appuser

        # 4. セキュリティオプション
        # docker run --read-only --no-new-privileges --security-opt=no-new-privileges ...
    """)

    security_checks = [
        ("non-root 実行",       "USER 命令で root 以外を指定"),
        ("read-only FS",       "--read-only フラグで書き込み防止"),
        ("no-new-privileges",  "権限昇格を防止"),
        ("capabilities 制限",   "--cap-drop ALL --cap-add NET_BIND_SERVICE"),
        ("イメージスキャン",     "trivy / grype でCVEスキャン"),
        ("署名検証",            "Docker Content Trust (DCT) で署名"),
        (".dockerignore",      ".git, .env, node_modules を除外"),
        ("COPY vs ADD",        "ADDは自動展開するため COPY を優先"),
    ]

    print("    セキュリティチェックリスト:")
    for item, desc in security_checks:
        print(f"      [{'x'}] {item:<24} -- {desc}")

    # --- Layer Caching ---
    subsection("1.7 レイヤーキャッシュ最適化")

    print("""
    Dockerfile の命令順序がキャッシュ効率を決定する。
    変更頻度が低い → 高い の順に並べる。

    ❌ 悪い例 (毎回全レイヤー再ビルド):
      COPY . .                    # ソース変更 → 以降すべて無効
      RUN pip install -r req.txt

    ✅ 良い例 (依存はキャッシュ済み):
      COPY requirements.txt .     # 依存ファイルだけ先にコピー
      RUN pip install -r req.txt  # 依存が変わらない限りキャッシュ
      COPY . .                    # ソースのみ再コピー

    キャッシュ無効化の条件:
      - RUN 命令の文字列が変わった
      - COPY/ADD のファイル内容が変わった
      - 上位レイヤーが無効化された → 以降すべて無効
    """)

    quiz(
        "Docker multi-stage build の主な目的は?",
        [
            "ビルド速度を上げるため",
            "最終イメージサイズを削減するため",
            "マルチアーキテクチャに対応するため",
            "Docker Compose と連携するため",
        ],
        1,
        "ビルドツールを最終イメージに含めず、実行に必要なアーティファクトだけをコピーすることで"
        "イメージサイズを大幅に削減できる。"
    )


# ============================================================
# Chapter 2: Kubernetes Day-2 Operations
# ============================================================
def chapter2_kubernetes_day2() -> None:
    section("Chapter 2: Kubernetes Day-2 Operations")

    # --- Pod Lifecycle ---
    subsection("2.1 Pod ライフサイクル")

    print("""
    Pod のフェーズ遷移:

    Pending ──▶ Running ──▶ Succeeded
                  │              │
                  ▼              │
               Failed ◀─────────┘

    Pod 内のコンテナ構成パターン:

    ┌──────────── Pod ─────────────────────────┐
    │  ┌────────────┐  ┌──────────┐            │
    │  │ Init       │  │ Init     │  (順次実行) │
    │  │ Container 1│─▶│ Container2│            │
    │  └────────────┘  └────┬─────┘            │
    │                       ▼                  │
    │  ┌────────────┐  ┌──────────┐            │
    │  │ Main App   │  │ Sidecar  │  (並行実行) │
    │  │ Container  │  │ (log等)  │            │
    │  └────────────┘  └──────────┘            │
    └──────────────────────────────────────────┘
    """)

    show_yaml("Pod with Init Container & Probes", """
        apiVersion: v1
        kind: Pod
        metadata:
          name: app-pod
        spec:
          initContainers:
            - name: wait-for-db
              image: busybox:1.36
              command: ['sh', '-c', 'until nc -z db-svc 5432; do sleep 2; done']

          containers:
            - name: app
              image: myapp:1.0
              ports:
                - containerPort: 8080

              # Startup Probe: 起動完了を検知 (起動が遅いアプリ向け)
              startupProbe:
                httpGet:
                  path: /healthz
                  port: 8080
                failureThreshold: 30    # 30 * 10s = 最大5分待つ
                periodSeconds: 10

              # Liveness Probe: デッドロック検知 → コンテナ再起動
              livenessProbe:
                httpGet:
                  path: /healthz
                  port: 8080
                initialDelaySeconds: 0
                periodSeconds: 15
                failureThreshold: 3

              # Readiness Probe: トラフィック受入れ可否 → Service から除外
              readinessProbe:
                httpGet:
                  path: /ready
                  port: 8080
                periodSeconds: 5
                failureThreshold: 3

              resources:
                requests:
                  cpu: "250m"
                  memory: "256Mi"
                limits:
                  cpu: "1000m"
                  memory: "512Mi"

            - name: log-shipper         # Sidecar パターン
              image: fluent-bit:2.1
              volumeMounts:
                - name: log-vol
                  mountPath: /var/log/app

          volumes:
            - name: log-vol
              emptyDir: {}
    """)

    # --- Deployment Strategies ---
    subsection("2.2 デプロイメント戦略")

    strategies = [
        ("Rolling Update", "段階的に旧→新へ置換",
         "ダウンタイムなし", "ロールバックに時間がかかる場合がある"),
        ("Blue-Green",     "新旧環境を並行運用し一括切替",
         "即座にロールバック可能", "リソースが2倍必要"),
        ("Canary",         "一部トラフィックのみ新バージョンへ",
         "リスクを限定できる", "トラフィック制御の仕組みが必要"),
        ("Recreate",       "全Pod停止 → 新Pod起動",
         "シンプル", "ダウンタイムが発生"),
    ]

    print("\n    デプロイメント戦略の比較:")
    print(f"    {'戦略':<16} {'メリット':<24} {'デメリット'}")
    print(f"    {'─' * 16} {'─' * 24} {'─' * 28}")
    for name, desc, pros, cons in strategies:
        print(f"    {name:<16} {pros:<24} {cons}")
        print(f"    {'':16} ({desc})")

    # --- Rolling Update Simulation ---
    subsection("2.3 Rolling Update シミュレーション")

    @dataclass
    class PodState:
        name: str
        version: str
        status: str = "Running"

    def simulate_rolling_update(
        replicas: int = 4,
        max_surge: int = 1,
        max_unavailable: int = 1,
    ) -> None:
        print(f"\n    設定: replicas={replicas}, maxSurge={max_surge}, "
              f"maxUnavailable={max_unavailable}")
        pods = [PodState(f"pod-{i}", "v1") for i in range(replicas)]

        step = 0
        updated = 0
        while updated < replicas:
            step += 1
            # Terminate old pod
            for p in pods:
                if p.version == "v1" and p.status == "Running":
                    p.status = "Terminating"
                    break
            # Create new pod
            pods.append(PodState(f"pod-{replicas + updated}", "v2", "Running"))
            updated += 1

            running = [p for p in pods if p.status == "Running"]
            status_line = " ".join(
                f"[{p.name}:{p.version}]" for p in running
            )
            print(f"    Step {step}: {status_line}")

            # Remove terminated
            pods = [p for p in pods if p.status != "Terminating"]

        print(f"    完了: 全 {replicas} Pod が v2 に更新されました")

    simulate_rolling_update()

    show_yaml("Rolling Update Deployment 設定", """
        apiVersion: apps/v1
        kind: Deployment
        metadata:
          name: app
        spec:
          replicas: 4
          strategy:
            type: RollingUpdate
            rollingUpdate:
              maxSurge: 1           # 最大で replicas + 1 Pod まで
              maxUnavailable: 1     # 最低 replicas - 1 Pod は Running
          selector:
            matchLabels:
              app: myapp
          template:
            metadata:
              labels:
                app: myapp
            spec:
              containers:
                - name: app
                  image: myapp:v2
    """)

    # --- Resource Management ---
    subsection("2.4 リソース管理 & QoS クラス")

    print("""
    QoS クラスの決定ルール:

    ┌───────────────────────────────────────────────────────────┐
    │ QoS Class     │ 条件                   │ 退去優先度      │
    ├───────────────┼────────────────────────┼─────────────────┤
    │ Guaranteed    │ requests == limits      │ 最後 (最も安全) │
    │               │ (全コンテナ・CPU/Mem)   │                 │
    ├───────────────┼────────────────────────┼─────────────────┤
    │ Burstable     │ requests < limits       │ 中間            │
    │               │ (一部でも設定あり)       │                 │
    ├───────────────┼────────────────────────┼─────────────────┤
    │ BestEffort    │ 設定なし               │ 最初に退去       │
    └───────────────┴────────────────────────┴─────────────────┘

    ノードのメモリ不足時、BestEffort → Burstable → Guaranteed の順に Pod が退去される。
    本番ワークロードは Guaranteed または Burstable(requests設定)を推奨。
    """)

    show_yaml("HPA (Horizontal Pod Autoscaler) 設定", """
        apiVersion: autoscaling/v2
        kind: HorizontalPodAutoscaler
        metadata:
          name: app-hpa
        spec:
          scaleTargetRef:
            apiVersion: apps/v1
            kind: Deployment
            name: app
          minReplicas: 2
          maxReplicas: 20
          metrics:
            - type: Resource
              resource:
                name: cpu
                target:
                  type: Utilization
                  averageUtilization: 70
            - type: Resource
              resource:
                name: memory
                target:
                  type: Utilization
                  averageUtilization: 80
          behavior:
            scaleUp:
              stabilizationWindowSeconds: 60
              policies:
                - type: Percent
                  value: 100           # 最大2倍まで一気にスケール
                  periodSeconds: 60
            scaleDown:
              stabilizationWindowSeconds: 300  # 5分間安定してから縮小
              policies:
                - type: Percent
                  value: 10
                  periodSeconds: 60
    """)

    # --- ConfigMap / Secret ---
    subsection("2.5 ConfigMap / Secret 管理")

    show_yaml("ConfigMap と Secret の使い分け", """
        # ConfigMap: 平文の設定値
        apiVersion: v1
        kind: ConfigMap
        metadata:
          name: app-config
        data:
          LOG_LEVEL: "info"
          DB_HOST: "db-service.default.svc.cluster.local"
          config.yaml: |
            server:
              port: 8080
              read_timeout: 30s

        ---
        # Secret: Base64 エンコード (暗号化ではない!)
        apiVersion: v1
        kind: Secret
        metadata:
          name: app-secrets
        type: Opaque
        data:
          DB_PASSWORD: cGFzc3dvcmQxMjM=    # echo -n "password123" | base64
          API_KEY: c2VjcmV0LWtleQ==

        # 本番では外部シークレットマネージャを使う:
        #   - AWS Secrets Manager + External Secrets Operator
        #   - HashiCorp Vault + CSI Driver
        #   - GCP Secret Manager
    """)

    # --- RBAC ---
    subsection("2.6 RBAC モデル")

    print("""
    Kubernetes RBAC の構成要素:

    ┌───────────────┐     ┌──────────────┐     ┌────────────────┐
    │ Subject       │     │ RoleBinding   │     │ Role           │
    │ (User/SA/     │◀────│              │────▶│ (Namespace内)  │
    │  Group)       │     │              │     │ rules:         │
    └───────────────┘     └──────────────┘     │  - resources   │
                                               │  - verbs       │
                                               └────────────────┘

    ClusterRole / ClusterRoleBinding: クラスタ全体に適用
    """)

    show_yaml("最小権限の RBAC 設定例", """
        # ServiceAccount
        apiVersion: v1
        kind: ServiceAccount
        metadata:
          name: app-sa
          namespace: production

        ---
        # Role: namespace 内の Pod を読み取り専用
        apiVersion: rbac.authorization.k8s.io/v1
        kind: Role
        metadata:
          name: pod-reader
          namespace: production
        rules:
          - apiGroups: [""]
            resources: ["pods", "pods/log"]
            verbs: ["get", "list", "watch"]

        ---
        # RoleBinding: SA に Role を紐付け
        apiVersion: rbac.authorization.k8s.io/v1
        kind: RoleBinding
        metadata:
          name: app-pod-reader
          namespace: production
        subjects:
          - kind: ServiceAccount
            name: app-sa
            namespace: production
        roleRef:
          kind: Role
          name: pod-reader
          apiGroup: rbac.authorization.k8s.io
    """)

    # --- Network Policies ---
    subsection("2.7 Network Policies")

    show_yaml("マイクロサービス間通信を制限する NetworkPolicy", """
        apiVersion: networking.k8s.io/v1
        kind: NetworkPolicy
        metadata:
          name: api-netpol
          namespace: production
        spec:
          podSelector:
            matchLabels:
              app: api-server
          policyTypes:
            - Ingress
            - Egress
          ingress:
            - from:
                - podSelector:
                    matchLabels:
                      app: frontend       # frontend からのみ受信
              ports:
                - protocol: TCP
                  port: 8080
          egress:
            - to:
                - podSelector:
                    matchLabels:
                      app: database       # database へのみ送信
              ports:
                - protocol: TCP
                  port: 5432
            - to:                         # DNS は許可
                - namespaceSelector: {}
              ports:
                - protocol: UDP
                  port: 53
    """)

    # --- Helm ---
    subsection("2.8 Helm チャート構造")

    print("""
    Helm チャートのディレクトリ構造:

    mychart/
    ├── Chart.yaml           # チャートのメタデータ (name, version, appVersion)
    ├── values.yaml          # デフォルト値 (helm install -f custom.yaml で上書き)
    ├── templates/
    │   ├── _helpers.tpl     # テンプレートヘルパー関数
    │   ├── deployment.yaml  # {{ .Values.replicaCount }} で値を参照
    │   ├── service.yaml
    │   ├── ingress.yaml
    │   ├── hpa.yaml
    │   ├── configmap.yaml
    │   └── NOTES.txt        # インストール後の案内文
    ├── charts/              # サブチャート (依存関係)
    └── .helmignore

    よく使う Helm コマンド:
      helm install myrelease ./mychart -f prod-values.yaml
      helm upgrade myrelease ./mychart --set image.tag=v2.0
      helm rollback myrelease 1    # リビジョン1にロールバック
      helm template ./mychart      # テンプレートレンダリング確認
      helm diff upgrade ...        # 差分プレビュー (plugin)
    """)

    # --- Troubleshooting ---
    subsection("2.9 Kubernetes トラブルシューティング")

    issues = [
        ("CrashLoopBackOff",
         "コンテナが起動直後にクラッシュし、再起動を繰り返す",
         ["kubectl logs <pod> --previous   # 前回のログ確認",
          "kubectl describe pod <pod>      # Events 確認",
          "原因: アプリのバグ, 設定ミス, ヘルスチェック失敗"]),
        ("OOMKilled",
         "メモリ上限 (limits.memory) を超過して強制終了",
         ["kubectl describe pod <pod> | grep -A5 'Last State'",
          "対策: limits.memory を増やす or アプリのメモリリーク修正",
          "JVM: -Xmx をコンテナ limits の 75% 程度に設定"]),
        ("ImagePullBackOff",
         "コンテナイメージの取得に失敗",
         ["kubectl describe pod <pod> | grep -A3 Events",
          "原因: イメージ名 typo, プライベートレジストリの認証失敗",
          "対策: imagePullSecrets を設定, イメージ名を確認"]),
        ("Pending",
         "Pod がスケジュールされない",
         ["kubectl describe pod <pod> | grep Events",
          "原因: リソース不足, nodeSelector/affinity 不一致, PVC 未バインド",
          "kubectl get nodes -o wide  # ノードのリソース状況確認"]),
    ]

    for issue_name, desc, cmds in issues:
        print(f"\n    [{issue_name}]")
        print(f"      症状: {desc}")
        print(f"      対処法:")
        for cmd in cmds:
            print(f"        $ {cmd}")

    quiz(
        "Kubernetes で Pod がノードのメモリ不足で退去される順番は?",
        [
            "Guaranteed -> Burstable -> BestEffort",
            "BestEffort -> Burstable -> Guaranteed",
            "ランダム",
            "作成時間が古い順",
        ],
        1,
        "BestEffort (requests/limits 未設定) が最初に退去され、"
        "Guaranteed (requests == limits) が最後に退去される。"
    )


# ============================================================
# Chapter 3: Infrastructure as Code - Terraform
# ============================================================
def chapter3_terraform() -> None:
    section("Chapter 3: Infrastructure as Code - Terraform")

    # --- HCL Basics ---
    subsection("3.1 HCL (HashiCorp Configuration Language) 基本構文")

    print("""
    Terraform の主要ブロック:

    ┌──────────────────────────────────────────────────────────┐
    │ Block        │ 役割                                      │
    ├──────────────┼───────────────────────────────────────────┤
    │ terraform    │ バージョン制約, backend設定                 │
    │ provider     │ クラウドプロバイダの設定 (AWS, GCP等)        │
    │ resource     │ インフラリソースの定義 (作成/更新/削除)       │
    │ data         │ 既存リソースの参照 (読み取り専用)            │
    │ variable     │ 入力変数                                   │
    │ output       │ 出力値                                     │
    │ locals       │ ローカル変数 (計算結果の再利用)              │
    │ module       │ 再利用可能なリソースグループ                 │
    └──────────────┴───────────────────────────────────────────┘
    """)

    show_config("基本的な Terraform 構成 (main.tf)", """
        terraform {
          required_version = ">= 1.5"
          required_providers {
            aws = {
              source  = "hashicorp/aws"
              version = "~> 5.0"
            }
          }

          backend "s3" {
            bucket         = "my-terraform-state"
            key            = "prod/terraform.tfstate"
            region         = "ap-northeast-1"
            dynamodb_table = "terraform-locks"   # State Locking
            encrypt        = true
          }
        }

        provider "aws" {
          region = var.region
          default_tags {
            tags = {
              Environment = var.environment
              ManagedBy   = "terraform"
              Project     = var.project_name
            }
          }
        }
    """)

    show_config("variables.tf", """
        variable "region" {
          description = "AWS region"
          type        = string
          default     = "ap-northeast-1"
        }

        variable "environment" {
          description = "Environment name"
          type        = string
          validation {
            condition     = contains(["dev", "staging", "prod"], var.environment)
            error_message = "Environment must be dev, staging, or prod."
          }
        }

        variable "instance_config" {
          description = "EC2 instance configuration"
          type = object({
            instance_type = string
            ami_id        = string
            volume_size   = number
          })
          default = {
            instance_type = "t3.micro"
            ami_id        = "ami-0abcdef1234567890"
            volume_size   = 20
          }
        }

        locals {
          name_prefix = "${var.project_name}-${var.environment}"
          common_tags = {
            Environment = var.environment
            Terraform   = "true"
          }
        }
    """)

    # --- State Management ---
    subsection("3.2 State 管理")

    print("""
    Terraform State の重要性:

    terraform.tfstate はインフラの「真実の源泉」。
    コードとクラウドの実態をマッピングする JSON ファイル。

    ┌──────────────┐     ┌───────────────┐     ┌──────────────┐
    │ .tf コード    │     │  State File   │     │  Cloud       │
    │ (desired)    │────▶│  (recorded)   │────▶│  (actual)    │
    └──────────────┘     └───────────────┘     └──────────────┘

    plan 時: コード vs State → 差分を計算
    apply 時: 差分をクラウドに反映 → State を更新

    State 管理のベストプラクティス:
    1. Remote Backend (S3 + DynamoDB / GCS) で共有
    2. State Locking で並行 apply を防止
    3. State は Git にコミットしない (機密情報を含む)
    4. Workspace でステート分離 (dev / staging / prod)

    よく使う State 操作:
      terraform state list                    # リソース一覧
      terraform state show aws_instance.web   # 詳細表示
      terraform state mv old.name new.name    # リソース名変更
      terraform state rm aws_instance.web     # State から除去 (リソースは残る)
      terraform import aws_instance.web i-xxx # 既存リソースをインポート
    """)

    # --- Module Patterns ---
    subsection("3.3 モジュールパターン")

    print("""
    モジュール構成の推奨ディレクトリ構造:

    infrastructure/
    ├── modules/                    # 再利用可能モジュール
    │   ├── vpc/
    │   │   ├── main.tf
    │   │   ├── variables.tf
    │   │   ├── outputs.tf
    │   │   └── README.md
    │   ├── ecs-service/
    │   └── rds/
    │
    ├── environments/
    │   ├── dev/
    │   │   ├── main.tf            # module "vpc" { source = "../../modules/vpc" }
    │   │   ├── terraform.tfvars
    │   │   └── backend.tf
    │   ├── staging/
    │   └── prod/
    │
    └── global/                    # 全環境共通 (IAM, Route53等)
        ├── iam/
        └── dns/
    """)

    show_config("モジュール呼び出し (environments/prod/main.tf)", """
        module "vpc" {
          source = "../../modules/vpc"

          cidr_block       = "10.0.0.0/16"
          azs              = ["ap-northeast-1a", "ap-northeast-1c"]
          private_subnets  = ["10.0.1.0/24", "10.0.2.0/24"]
          public_subnets   = ["10.0.101.0/24", "10.0.102.0/24"]
          environment      = "prod"
        }

        module "ecs_service" {
          source = "../../modules/ecs-service"

          cluster_id   = module.ecs_cluster.id
          vpc_id       = module.vpc.vpc_id
          subnet_ids   = module.vpc.private_subnet_ids
          service_name = "api"
          image        = "123456789.dkr.ecr.ap-northeast-1.amazonaws.com/api:v1.0"
          cpu          = 256
          memory       = 512
          desired_count = 3
        }
    """)

    # --- Lifecycle Rules ---
    subsection("3.4 Lifecycle ルール")

    show_config("Lifecycle 設定の活用例", """
        resource "aws_instance" "web" {
          ami           = var.ami_id
          instance_type = var.instance_type

          lifecycle {
            # リソースを先に作成してから古いものを削除 (ダウンタイム防止)
            create_before_destroy = true

            # 誤削除防止 (terraform destroy でもエラー)
            prevent_destroy = true

            # 外部変更を無視 (手動変更との競合回避)
            ignore_changes = [
              tags["LastModifiedBy"],
              user_data,
            ]
          }
        }

        # Terraform import の使い方:
        # 1. resource ブロックを .tf に書く
        # 2. terraform import aws_instance.web i-0abcd1234efgh5678
        # 3. terraform plan で差分がないことを確認
        # 4. 必要に応じて .tf を調整

        # Terraform 1.5+ の import ブロック:
        import {
          to = aws_instance.web
          id = "i-0abcd1234efgh5678"
        }
    """)

    # --- Terraform workflow simulation ---
    subsection("3.5 Terraform ワークフロー シミュレーション")

    def simulate_terraform_plan() -> None:
        resources = [
            ("aws_vpc.main",              "create", "+"),
            ("aws_subnet.public[0]",      "create", "+"),
            ("aws_subnet.public[1]",      "create", "+"),
            ("aws_subnet.private[0]",     "create", "+"),
            ("aws_security_group.web",    "create", "+"),
            ("aws_instance.web",          "create", "+"),
            ("aws_lb.main",              "create", "+"),
            ("aws_rds_instance.db",       "create", "+"),
        ]

        print("\n    terraform plan 出力シミュレーション:")
        print("    " + "─" * 50)
        for name, action, symbol in resources:
            color_action = f"{symbol} {name}"
            print(f"      {color_action}")
        print(f"\n    Plan: {len(resources)} to add, 0 to change, 0 to destroy.")

        # Simulate apply
        print("\n    terraform apply 実行中...")
        for i, (name, _, _) in enumerate(resources):
            progress = (i + 1) / len(resources) * 100
            bar = "█" * int(progress // 5) + "░" * (20 - int(progress // 5))
            print(f"    [{bar}] {progress:5.1f}% - Creating {name}...")
        print("\n    Apply complete! Resources: "
              f"{len(resources)} added, 0 changed, 0 destroyed.")

    simulate_terraform_plan()

    quiz(
        "Terraform で prevent_destroy = true を設定したリソースを削除するには?",
        [
            "terraform destroy -force を使う",
            "先に lifecycle ブロックを削除してから destroy する",
            "terraform state rm で State から除去する",
            "A と C の両方",
        ],
        1,
        "prevent_destroy はコード上の安全装置。"
        "まず .tf から prevent_destroy を削除し、apply 後に destroy する。"
    )


# ============================================================
# Chapter 4: CI/CD Pipeline Patterns
# ============================================================
def chapter4_cicd_patterns() -> None:
    section("Chapter 4: CI/CD Pipeline Patterns")

    # --- GitHub Actions Structure ---
    subsection("4.1 GitHub Actions ワークフロー構造")

    print("""
    GitHub Actions の階層構造:

    Workflow (.github/workflows/*.yml)
    └── Event (push, pull_request, schedule, workflow_dispatch)
        └── Job (runs-on: ubuntu-latest)
            └── Step
                ├── uses: actions/checkout@v4    # 再利用可能アクション
                └── run: npm test                # シェルコマンド

    Job 間の依存関係:
    ┌─────┐   ┌──────┐   ┌─────────┐   ┌──────────┐
    │ lint │──▶│ test │──▶│ build   │──▶│ deploy   │
    └─────┘   └──────┘   └─────────┘   └──────────┘
                │
                └──▶ ┌────────────┐
                     │ e2e-test   │
                     └────────────┘
    """)

    show_yaml("本番レベルの CI/CD ワークフロー (.github/workflows/ci.yml)", """
        name: CI/CD Pipeline
        on:
          push:
            branches: [main]
          pull_request:
            branches: [main]

        env:
          REGISTRY: ghcr.io
          IMAGE_NAME: ${{ github.repository }}

        jobs:
          lint:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v4
              - uses: actions/setup-python@v5
                with:
                  python-version: "3.11"
              - run: pip install ruff
              - run: ruff check .

          test:
            runs-on: ubuntu-latest
            needs: [lint]
            strategy:
              matrix:
                python-version: ["3.10", "3.11", "3.12"]
            services:
              postgres:
                image: postgres:16
                env:
                  POSTGRES_PASSWORD: test
                ports:
                  - 5432:5432
                options: >-
                  --health-cmd pg_isready
                  --health-interval 10s
                  --health-timeout 5s
                  --health-retries 5
            steps:
              - uses: actions/checkout@v4
              - uses: actions/setup-python@v5
                with:
                  python-version: ${{ matrix.python-version }}
              - name: Cache pip
                uses: actions/cache@v4
                with:
                  path: ~/.cache/pip
                  key: pip-${{ runner.os }}-${{ hashFiles('requirements*.txt') }}
                  restore-keys: pip-${{ runner.os }}-
              - run: pip install -r requirements.txt -r requirements-dev.txt
              - run: pytest --cov=app --cov-report=xml -v
              - uses: codecov/codecov-action@v4
                if: matrix.python-version == '3.11'

          build:
            runs-on: ubuntu-latest
            needs: [test]
            if: github.ref == 'refs/heads/main'
            permissions:
              contents: read
              packages: write
            steps:
              - uses: actions/checkout@v4
              - uses: docker/setup-buildx-action@v3
              - uses: docker/login-action@v3
                with:
                  registry: ${{ env.REGISTRY }}
                  username: ${{ github.actor }}
                  password: ${{ secrets.GITHUB_TOKEN }}
              - uses: docker/build-push-action@v5
                with:
                  push: true
                  tags: |
                    ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
                    ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
                  cache-from: type=gha
                  cache-to: type=gha,mode=max

          deploy-staging:
            runs-on: ubuntu-latest
            needs: [build]
            environment: staging
            steps:
              - uses: actions/checkout@v4
              - name: Deploy to staging
                run: |
                  echo "Deploying ${{ github.sha }} to staging..."
                  # kubectl set image deployment/app app=$IMAGE:$TAG

          deploy-production:
            runs-on: ubuntu-latest
            needs: [deploy-staging]
            environment:
              name: production
              url: https://myapp.example.com
            steps:
              - uses: actions/checkout@v4
              - name: Deploy to production
                run: |
                  echo "Deploying ${{ github.sha }} to production..."
    """)

    # --- Pipeline Patterns ---
    subsection("4.2 パイプラインパターン")

    # Simulate pipeline execution
    def simulate_pipeline() -> None:
        stages = [
            ("Lint",           ["ruff check", "eslint"], 8),
            ("Unit Test",      ["pytest (py3.10)", "pytest (py3.11)", "pytest (py3.12)"], 45),
            ("Build Image",    ["docker build", "docker push"], 120),
            ("Deploy Staging", ["kubectl apply", "smoke test"], 60),
            ("E2E Test",       ["playwright run"], 180),
            ("Deploy Prod",    ["canary 10%", "canary 50%", "canary 100%"], 300),
        ]

        print("\n    パイプライン実行シミュレーション:")
        print("    " + "─" * 55)
        total_time = 0
        for stage_name, tasks, duration in stages:
            total_time += duration
            status = "PASS"
            mins, secs = divmod(duration, 60)
            time_str = f"{mins}m{secs:02d}s" if mins else f"{secs}s"
            task_list = ", ".join(tasks)
            print(f"    [{status}] {stage_name:<20} ({time_str:>6}) [{task_list}]")

        total_mins, total_secs = divmod(total_time, 60)
        print(f"\n    Total Pipeline Time: {total_mins}m{total_secs:02d}s")

    simulate_pipeline()

    # --- Caching Strategies ---
    subsection("4.3 キャッシュ戦略")

    print("""
    CI/CD でのキャッシュ戦略:

    1. 依存関係キャッシュ:
       - pip: ~/.cache/pip (key: requirements.txt のハッシュ)
       - npm: ~/.npm (key: package-lock.json のハッシュ)
       - Go:  ~/go/pkg/mod (key: go.sum のハッシュ)

    2. Docker レイヤーキャッシュ:
       - GitHub Actions: cache-from/to: type=gha
       - BuildKit inline cache: --build-arg BUILDKIT_INLINE_CACHE=1
       - レジストリキャッシュ: cache-from: type=registry

    3. ビルドアーティファクトキャッシュ:
       - actions/cache で中間成果物を保存
       - actions/upload-artifact / download-artifact でジョブ間共有

    キャッシュキーの設計:
      key:          pip-${{ runner.os }}-${{ hashFiles('requirements.txt') }}
      restore-keys: pip-${{ runner.os }}-
      # 完全一致 → 部分一致のフォールバックでヒット率向上
    """)

    # --- Secret Management ---
    subsection("4.4 CI/CD シークレット管理")

    print("""
    シークレット管理の階層:

    ┌─────────────────────────────────────────────────────────┐
    │ レベル         │ スコープ              │ 例             │
    ├────────────────┼───────────────────────┼────────────────┤
    │ Repository     │ 単一リポジトリ         │ API_KEY        │
    │ Environment    │ staging / production  │ DB_PASSWORD    │
    │ Organization   │ 全リポジトリ共有       │ NPM_TOKEN      │
    └────────────────┴───────────────────────┴────────────────┘

    ベストプラクティス:
    1. Environment secrets で本番/ステージングを分離
    2. OIDC 認証 (secrets 不要で AWS/GCP に認証)
    3. 短寿命トークンの利用 (GITHUB_TOKEN は自動失効)
    4. シークレットのローテーション自動化
    5. PRからのシークレットアクセスを制限

    OIDC フェデレーション (推奨):
      GitHub Actions → OIDC Token → AWS STS AssumeRole
      パスワードレスで一時的な認証情報を取得
    """)

    # --- GitOps ---
    subsection("4.5 GitOps with ArgoCD")

    print("""
    GitOps の原則:
    1. Git がインフラの唯一の真実の源泉 (Single Source of Truth)
    2. 宣言的な構成 (Declarative)
    3. 自動同期 (Automated Reconciliation)
    4. Git の変更履歴 = デプロイ履歴

    ArgoCD のアーキテクチャ:

    Developer ─── git push ──▶ Git Repository
                                     │
                              ArgoCD watches
                                     │
                                     ▼
                             ┌──────────────┐
                             │   ArgoCD     │
                             │  Controller  │
                             └──────┬───────┘
                                    │ kubectl apply
                                    ▼
                             ┌──────────────┐
                             │  Kubernetes  │
                             │   Cluster    │
                             └──────────────┘

    Sync Status:
      - Synced:    Git の状態 == クラスタの状態
      - OutOfSync: Git の状態 != クラスタの状態 → 自動/手動で同期
    """)

    show_yaml("ArgoCD Application マニフェスト", """
        apiVersion: argoproj.io/v1alpha1
        kind: Application
        metadata:
          name: myapp
          namespace: argocd
        spec:
          project: default
          source:
            repoURL: https://github.com/myorg/myapp-k8s.git
            targetRevision: main
            path: overlays/production     # Kustomize overlay
          destination:
            server: https://kubernetes.default.svc
            namespace: production
          syncPolicy:
            automated:
              prune: true                 # Git から削除 → k8s からも削除
              selfHeal: true              # 手動変更を自動修復
            syncOptions:
              - CreateNamespace=true
            retry:
              limit: 5
              backoff:
                duration: 5s
                factor: 2
                maxDuration: 3m
    """)

    # --- Pipeline Optimization ---
    subsection("4.6 パイプライン最適化")

    print("""
    最適化テクニック:

    1. 並列実行:
       - matrix strategy で複数バージョン/OS を並列テスト
       - 独立したジョブ (lint, test, security-scan) を並列化

    2. 条件付き実行:
       - paths フィルタ: docs/ 変更時はテスト不要
       - if: github.ref == 'refs/heads/main' でデプロイ制御

    3. 早期失敗:
       - fail-fast: true で最初のテスト失敗で全マトリクス停止
       - lint を最初に実行 (高速 & フィードバック早い)

    4. Self-hosted runner:
       - 大規模プロジェクトでコスト削減
       - GPU テスト、特殊環境が必要な場合

    5. Reusable Workflows:
       - .github/workflows/reusable-deploy.yml を作成
       - workflow_call で他ワークフローから呼び出し
    """)

    quiz(
        "GitOps において Git リポジトリが果たす役割は?",
        [
            "ソースコードの保存場所",
            "インフラの唯一の真実の源泉 (Single Source of Truth)",
            "CI/CD ログの保存場所",
            "シークレットの管理場所",
        ],
        1,
        "GitOps ではインフラの望ましい状態 (desired state) を Git で管理し、"
        "クラスタを自動的に Git の状態に収束させる。"
    )


# ============================================================
# Chapter 5: FinOps & Cost Optimization
# ============================================================
def chapter5_finops() -> None:
    section("Chapter 5: FinOps & Cost Optimization")

    # --- Cloud Cost Models ---
    subsection("5.1 クラウドコストモデル")

    print("""
    主要な料金モデル:

    ┌───────────────────────────────────────────────────────────────┐
    │ モデル            │ 割引率    │ コミットメント  │ ユースケース  │
    ├───────────────────┼──────────┼────────────────┼──────────────┤
    │ On-Demand         │ 0%       │ なし           │ 開発/テスト   │
    │ Reserved (1yr)    │ ~30-40%  │ 1年           │ 安定ワークロード│
    │ Reserved (3yr)    │ ~50-60%  │ 3年           │ 長期安定      │
    │ Savings Plans     │ ~30-60%  │ $/hr で契約    │ 柔軟なコミット│
    │ Spot/Preemptible  │ ~60-90%  │ なし(中断あり)  │ バッチ処理    │
    └───────────────────┴──────────┴────────────────┴──────────────┘
    """)

    # --- Cost Calculator Simulation ---
    subsection("5.2 コスト比較シミュレーション")

    @dataclass
    class Instance:
        name: str
        vcpu: int
        memory_gb: float
        on_demand_hourly: float

    instances = [
        Instance("t3.micro",    2,  1.0, 0.0104),
        Instance("t3.medium",   2,  4.0, 0.0416),
        Instance("m5.large",    2,  8.0, 0.096),
        Instance("m5.xlarge",   4, 16.0, 0.192),
        Instance("c5.2xlarge",  8, 16.0, 0.340),
        Instance("r5.xlarge",   4, 32.0, 0.252),
    ]

    hours_per_month = 730

    print(f"\n    {'インスタンス':<16} {'vCPU':>5} {'Mem(GB)':>8} "
          f"{'On-Demand/月':>13} {'1yr RI/月':>11} {'Spot/月':>10} {'節約額/月':>10}")
    print(f"    {'─' * 16} {'─' * 5} {'─' * 8} {'─' * 13} {'─' * 11} {'─' * 10} {'─' * 10}")

    for inst in instances:
        on_demand = inst.on_demand_hourly * hours_per_month
        reserved = on_demand * 0.65  # ~35% off
        spot = on_demand * 0.30      # ~70% off
        savings = on_demand - spot
        print(f"    {inst.name:<16} {inst.vcpu:>5} {inst.memory_gb:>8.1f} "
              f"${on_demand:>11.2f} ${reserved:>9.2f} ${spot:>8.2f} ${savings:>8.2f}")

    # --- Right-sizing ---
    subsection("5.3 ライトサイジング戦略")

    def simulate_rightsizing() -> None:
        workloads = [
            {"name": "API Server",       "current": "m5.xlarge",
             "cpu_avg": 15, "mem_avg": 25, "recommended": "m5.large",     "savings_pct": 50},
            {"name": "Worker",           "current": "c5.2xlarge",
             "cpu_avg": 65, "mem_avg": 40, "recommended": "c5.xlarge",    "savings_pct": 50},
            {"name": "Database (RDS)",   "current": "r5.2xlarge",
             "cpu_avg": 30, "mem_avg": 70, "recommended": "r5.xlarge",    "savings_pct": 50},
            {"name": "Batch Processor",  "current": "m5.2xlarge",
             "cpu_avg": 80, "mem_avg": 60, "recommended": "m5.2xlarge",   "savings_pct": 0},
        ]

        print("\n    ライトサイジング分析結果:")
        print(f"    {'ワークロード':<20} {'現在':>14} {'CPU平均':>8} {'Mem平均':>8} "
              f"{'推奨':>14} {'削減':>6}")
        print(f"    {'─' * 20} {'─' * 14} {'─' * 8} {'─' * 8} {'─' * 14} {'─' * 6}")
        for w in workloads:
            indicator = "<--" if w["savings_pct"] > 0 else ""
            print(f"    {w['name']:<20} {w['current']:>14} {w['cpu_avg']:>7}% "
                  f"{w['mem_avg']:>7}% {w['recommended']:>14} {w['savings_pct']:>5}% {indicator}")

    simulate_rightsizing()

    # --- Cost Allocation ---
    subsection("5.4 コスト配分 (タグ戦略)")

    print("""
    必須タグの設計:

    ┌─────────────────────────────────────────────────────────┐
    │ タグキー       │ 例                │ 目的              │
    ├────────────────┼───────────────────┼───────────────────┤
    │ Environment    │ prod / staging    │ 環境別コスト把握   │
    │ Team           │ platform / ml     │ チーム別配分      │
    │ Service        │ api / worker      │ サービス別コスト   │
    │ CostCenter     │ CC-1234           │ 部門への請求      │
    │ Owner          │ alice@example.com │ 責任者            │
    │ ManagedBy      │ terraform         │ 管理方法          │
    └────────────────┴───────────────────┴───────────────────┘

    AWS: Tag Policy + SCP で必須タグ強制
    GCP: Labels + Organization Policy
    """)

    # --- FinOps Framework ---
    subsection("5.5 FinOps フレームワーク")

    print("""
    FinOps のライフサイクル:

    ┌─────────────────────────────────────────────────────────────┐
    │                                                             │
    │   ┌─────────┐    ┌──────────┐    ┌─────────┐              │
    │   │ INFORM  │───▶│ OPTIMIZE │───▶│ OPERATE │──┐           │
    │   └─────────┘    └──────────┘    └─────────┘  │           │
    │       ▲                                        │           │
    │       └────────────────────────────────────────┘           │
    │                                                             │
    │   Inform:   可視化、レポート、アラート                        │
    │   Optimize: RI/SP購入、ライトサイジング、Spot活用             │
    │   Operate:  ガバナンス、予算管理、自動化                      │
    └─────────────────────────────────────────────────────────────┘

    成熟度モデル:
      Crawl: 基本的なコスト可視化、タグ付け開始
      Walk:  チーム別配分、RI/SP購入、アラート設定
      Run:   自動最適化、Unit Economics、予測分析
    """)

    # --- Unit Economics ---
    subsection("5.6 Unit Economics シミュレーション")

    def simulate_unit_economics() -> None:
        monthly_cost = 15000  # $15,000/month
        monthly_requests = 50_000_000  # 50M requests
        monthly_users = 100_000

        cost_per_request = monthly_cost / monthly_requests
        cost_per_user = monthly_cost / monthly_users

        print(f"\n    月間クラウドコスト:     ${monthly_cost:,.0f}")
        print(f"    月間リクエスト数:       {monthly_requests:,.0f}")
        print(f"    月間アクティブユーザー:  {monthly_users:,.0f}")
        print(f"    ")
        print(f"    コスト / リクエスト:    ${cost_per_request:.6f}")
        print(f"    コスト / ユーザー:      ${cost_per_user:.2f}")

        # Trend simulation
        print("\n    月次トレンド:")
        print(f"    {'月':>4} {'コスト':>10} {'リクエスト':>14} {'$/req':>12} {'$/user':>10}")
        print(f"    {'─' * 4} {'─' * 10} {'─' * 14} {'─' * 12} {'─' * 10}")
        for m in range(1, 7):
            cost = monthly_cost * (1 + 0.05 * m)   # 5% monthly growth
            reqs = monthly_requests * (1 + 0.10 * m)  # 10% req growth
            users = monthly_users * (1 + 0.08 * m)
            cpr = cost / reqs
            cpu = cost / users
            print(f"    {m:>4} ${cost:>9,.0f} {reqs:>13,.0f} ${cpr:>11.6f} ${cpu:>8.2f}")

        print("\n    ポイント: コストが増えても、Unit Economics が改善していれば健全。")
        print("    リクエスト成長率 > コスト成長率 = スケールメリットが効いている。")

    simulate_unit_economics()

    # --- Cost Anomaly Detection ---
    subsection("5.7 コスト異常検知アプローチ")

    def simulate_anomaly_detection() -> None:
        random.seed(42)
        # Generate daily costs with a spike
        daily_costs = [500 + random.gauss(0, 30) for _ in range(30)]
        daily_costs[22] = 1200  # Spike!
        daily_costs[23] = 950   # Elevated

        mean_cost = sum(daily_costs[:20]) / 20
        std_cost = (sum((c - mean_cost) ** 2 for c in daily_costs[:20]) / 20) ** 0.5
        threshold = mean_cost + 2 * std_cost

        print(f"\n    過去20日の平均: ${mean_cost:.0f}/day")
        print(f"    標準偏差:       ${std_cost:.0f}")
        print(f"    異常検知閾値:   ${threshold:.0f} (平均 + 2σ)")
        print()
        print(f"    {'Day':>6} {'Cost':>8} {'Status'}")
        print(f"    {'─' * 6} {'─' * 8} {'─' * 16}")
        for i, cost in enumerate(daily_costs[18:], start=19):
            status = "ANOMALY!" if cost > threshold else "normal"
            bar = "█" * int(cost / 50)
            print(f"    Day {i:>2}: ${cost:>7.0f}  {bar}  {status}")

    simulate_anomaly_detection()

    quiz(
        "Spot / Preemptible インスタンスに最適なワークロードは?",
        [
            "データベースサーバー",
            "バッチ処理 / データパイプライン",
            "リアルタイム決済システム",
            "DNS サーバー",
        ],
        1,
        "Spot インスタンスは中断の可能性があるため、中断耐性があり"
        "再実行可能なバッチ処理やデータパイプラインに最適。"
    )


# ============================================================
# Chapter 6: Cloud Security Fundamentals
# ============================================================
def chapter6_cloud_security() -> None:
    section("Chapter 6: Cloud Security Fundamentals")

    # --- Shared Responsibility Model ---
    subsection("6.1 責任共有モデル (Shared Responsibility Model)")

    print("""
    AWS 責任共有モデル:

    ┌──────────────────────────────────────────────────────────────┐
    │                   顧客の責任                                 │
    │              "Security IN the Cloud"                         │
    │                                                              │
    │   ┌──────────────────────────────────────────────────────┐   │
    │   │  データの暗号化・分類                                  │   │
    │   │  IAM (アクセス管理)                                   │   │
    │   │  OS / ネットワーク / ファイアウォール設定               │   │
    │   │  アプリケーションセキュリティ                           │   │
    │   │  データ保護 (暗号化, バックアップ)                     │   │
    │   └──────────────────────────────────────────────────────┘   │
    ├──────────────────────────────────────────────────────────────┤
    │                   AWS の責任                                 │
    │              "Security OF the Cloud"                         │
    │                                                              │
    │   ┌──────────────────────────────────────────────────────┐   │
    │   │  物理セキュリティ (データセンター)                      │   │
    │   │  ハードウェア / ネットワークインフラ                     │   │
    │   │  仮想化レイヤー                                       │   │
    │   │  マネージドサービスの基盤部分                           │   │
    │   └──────────────────────────────────────────────────────┘   │
    └──────────────────────────────────────────────────────────────┘

    サービスモデル別の責任範囲:
      IaaS (EC2):  OS以上は顧客責任
      PaaS (ECS):  アプリ & データは顧客責任
      SaaS (S3):   データ & アクセス管理は顧客責任
    """)

    # --- IAM Best Practices ---
    subsection("6.2 IAM ベストプラクティス")

    iam_practices = [
        ("最小権限の原則",
         "必要最小限の権限のみ付与。Action と Resource を具体的に指定"),
        ("MFA 必須化",
         "全 IAM ユーザーに MFA を強制。特に管理者アカウント"),
        ("ルートアカウント不使用",
         "日常業務にルートアカウントを使わない。MFA + アクセスキー無効化"),
        ("サービスアカウント分離",
         "アプリごとに専用の IAM Role / Service Account を作成"),
        ("一時認証情報の利用",
         "長期アクセスキーの代わりに IAM Role + STS を使用"),
        ("定期的な棚卸し",
         "未使用の IAM ユーザー/ロール/ポリシーを定期的に削除"),
        ("SCPによるガードレール",
         "Organization SCP で禁止操作を組織全体に適用"),
    ]

    print("\n    IAM セキュリティチェックリスト:")
    for name, desc in iam_practices:
        print(f"      [ ] {name}")
        print(f"          {desc}")

    show_config("最小権限 IAM ポリシー例", """
        {
          "Version": "2012-10-17",
          "Statement": [
            {
              "Sid": "AllowS3ReadSpecificBucket",
              "Effect": "Allow",
              "Action": [
                "s3:GetObject",
                "s3:ListBucket"
              ],
              "Resource": [
                "arn:aws:s3:::my-app-data",
                "arn:aws:s3:::my-app-data/*"
              ],
              "Condition": {
                "StringEquals": {
                  "aws:RequestedRegion": "ap-northeast-1"
                }
              }
            },
            {
              "Sid": "DenyUnencryptedUploads",
              "Effect": "Deny",
              "Action": "s3:PutObject",
              "Resource": "arn:aws:s3:::my-app-data/*",
              "Condition": {
                "StringNotEquals": {
                  "s3:x-amz-server-side-encryption": "aws:kms"
                }
              }
            }
          ]
        }
    """)

    # --- Network Security ---
    subsection("6.3 ネットワークセキュリティ")

    print("""
    VPC ネットワーク層の防御:

    ┌─── Internet ─────────────────────────────────────────────┐
    │                                                          │
    │   ┌─── WAF (Layer 7) ──────────────────────────────┐     │
    │   │  SQL Injection, XSS, Bot Protection             │     │
    │   └──────────────┬──────────────────────────────────┘     │
    │                  ▼                                       │
    │   ┌─── ALB/NLB ────────────────────────────────────┐     │
    │   │  TLS終端, リクエストルーティング                  │     │
    │   └──────────────┬──────────────────────────────────┘     │
    │                  ▼                                       │
    │   ┌─── VPC ────────────────────────────────────────┐     │
    │   │                                                │     │
    │   │  ┌─ Public Subnet ──────────────────────────┐  │     │
    │   │  │  NACL: ステートレス (IN/OUT 両方設定)      │  │     │
    │   │  │  ┌─────────────────────────────────┐      │  │     │
    │   │  │  │ Security Group: ステートフル      │      │  │     │
    │   │  │  │ (IN 許可 → OUT 自動許可)         │      │  │     │
    │   │  │  │  ┌─────────┐ ┌──────────┐       │      │  │     │
    │   │  │  │  │ NAT GW  │ │ Bastion  │       │      │  │     │
    │   │  │  │  └─────────┘ └──────────┘       │      │  │     │
    │   │  │  └─────────────────────────────────┘      │  │     │
    │   │  └──────────────────────────────────────────┘  │     │
    │   │                                                │     │
    │   │  ┌─ Private Subnet ─────────────────────────┐  │     │
    │   │  │  App Servers, Databases                   │  │     │
    │   │  │  インターネット直接アクセス不可              │  │     │
    │   │  └──────────────────────────────────────────┘  │     │
    │   └────────────────────────────────────────────────┘     │
    └──────────────────────────────────────────────────────────┘

    Security Group vs NACL:
    ┌──────────────────┬──────────────────┬──────────────────┐
    │                  │ Security Group   │ NACL             │
    ├──────────────────┼──────────────────┼──────────────────┤
    │ 状態管理         │ ステートフル      │ ステートレス      │
    │ 適用対象         │ ENI (インスタンス)│ サブネット        │
    │ ルール           │ 許可のみ         │ 許可 + 拒否      │
    │ 評価順           │ 全ルール評価     │ 番号順に評価      │
    │ デフォルト       │ OUT全許可        │ ALL DENY         │
    └──────────────────┴──────────────────┴──────────────────┘
    """)

    # --- Data Encryption ---
    subsection("6.4 データ暗号化")

    print("""
    暗号化の3層:

    1. 保存時暗号化 (At-Rest):
       - S3: SSE-S3 / SSE-KMS / SSE-C
       - EBS: AES-256 暗号化
       - RDS: TDE (Transparent Data Encryption)
       - DynamoDB: AWS managed key / CMK

    2. 転送時暗号化 (In-Transit):
       - TLS 1.2+ (ALB/NLB で TLS 終端)
       - VPC 内通信も暗号化推奨 (Service Mesh / mTLS)
       - S3: aws:SecureTransport 条件で HTTP を拒否

    3. 鍵管理 (KMS):
       - AWS KMS: CMK (Customer Managed Key) を作成
       - Key Rotation: 自動ローテーション (年1回)
       - Key Policy: 誰が鍵を使えるかを制御
       - Envelope Encryption: CMK → Data Key → データ暗号化

    ┌─────────────────────────────────────────────────────┐
    │  Envelope Encryption:                               │
    │                                                     │
    │  CMK (KMS) ──encrypt──▶ Data Key (暗号化済み)       │
    │                                                     │
    │  Data Key (平文) ──encrypt──▶ データ (暗号化済み)    │
    │                                                     │
    │  保存するもの: 暗号化済みData Key + 暗号化済みデータ  │
    │  平文のData Key はメモリ上でのみ使用し即座に破棄      │
    └─────────────────────────────────────────────────────┘
    """)

    # --- Compliance Frameworks ---
    subsection("6.5 コンプライアンスフレームワーク概要")

    frameworks = [
        ("SOC 2",    "Type I: ある時点の設計評価 / Type II: 期間中の運用評価",
         "SaaS企業のほぼ必須。Trust Services Criteria (セキュリティ、可用性、機密性等)"),
        ("HIPAA",    "医療情報 (PHI) の保護",
         "BAA (Business Associate Agreement) の締結が必要。暗号化・監査ログ必須"),
        ("PCI-DSS",  "クレジットカード情報の保護",
         "4レベルのコンプライアンス。Level 1 は年次監査必須。トークナイゼーション推奨"),
        ("GDPR",     "EU 個人データ保護",
         "データ主体の権利 (削除権、ポータビリティ)。DPO任命。違反時は売上4%の罰金"),
        ("ISO 27001", "情報セキュリティマネジメントシステム (ISMS)",
         "リスクベースアプローチ。PDCA サイクル。認証取得で信頼性向上"),
    ]

    print("\n    主要コンプライアンスフレームワーク:")
    for name, scope, notes in frameworks:
        print(f"\n    [{name}]")
        print(f"      対象: {scope}")
        print(f"      要点: {notes}")

    # --- Security Monitoring ---
    subsection("6.6 セキュリティモニタリング (AWS)")

    print("""
    AWS セキュリティサービスマップ:

    ┌───────────────────────────────────────────────────────────┐
    │ カテゴリ      │ サービス           │ 用途                 │
    ├───────────────┼───────────────────┼──────────────────────┤
    │ 監査ログ      │ CloudTrail        │ API コール記録       │
    │ 脅威検知      │ GuardDuty         │ 異常検知 (ML ベース) │
    │ 統合ダッシュ   │ Security Hub      │ セキュリティ状態一覧  │
    │ 構成監査      │ AWS Config        │ リソース変更追跡     │
    │ 脆弱性スキャン │ Inspector         │ EC2/ECR 脆弱性検査  │
    │ DDoS 防御    │ Shield / WAF      │ L3-L7 攻撃防御     │
    │ シークレット   │ Secrets Manager   │ 認証情報の管理       │
    │ 鍵管理       │ KMS               │ 暗号鍵の管理        │
    │ アクセス分析   │ IAM Access Analyzer│ 外部アクセス検出     │
    └───────────────┴───────────────────┴──────────────────────┘

    推奨構成:
      CloudTrail → S3 (ログ保存) + CloudWatch Logs (リアルタイム監視)
      GuardDuty → SNS → Lambda → Slack/PagerDuty (アラート通知)
      Security Hub → 全サービスの Findings を集約
    """)

    # --- Incident Response ---
    subsection("6.7 インシデントレスポンス基本")

    print("""
    インシデントレスポンスの6フェーズ (NIST SP 800-61):

    ┌────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
    │ 1.準備 │─▶│ 2.検知   │─▶│ 3.分析   │─▶│ 4.封じ込め│
    └────────┘  └──────────┘  └──────────┘  └────┬─────┘
                                                  │
    ┌────────┐  ┌──────────┐                      │
    │ 6.教訓 │◀─│ 5.復旧   │◀─────────────────────┘
    └────────┘  └──────────┘

    フェーズ別アクション:

    1. 準備 (Preparation):
       - Runbook / Playbook の整備
       - インシデント対応チームの定義
       - 連絡先リスト、エスカレーションパス

    2. 検知 (Detection):
       - GuardDuty, CloudTrail, IDS/IPS
       - アラートの優先度分類 (P0-P3)

    3. 分析 (Analysis):
       - 影響範囲の特定
       - 攻撃経路の調査 (IOC: Indicators of Compromise)
       - タイムラインの作成

    4. 封じ込め (Containment):
       - 短期: Security Group で通信遮断
       - 長期: 感染リソースの隔離、認証情報ローテーション
       - フォレンジック用にスナップショット取得

    5. 復旧 (Recovery):
       - クリーンなイメージから再構築
       - パッチ適用、脆弱性修正
       - 段階的にトラフィック復旧

    6. 教訓 (Lessons Learned):
       - Post-Incident Review (PIR) / Blameless Postmortem
       - 改善アクションアイテムの作成
       - Runbook の更新
    """)

    # --- Security simulation ---
    subsection("6.8 セキュリティ監査シミュレーション")

    def simulate_security_audit() -> None:
        checks = [
            ("IAM",     "Root account MFA enabled",            True),
            ("IAM",     "No access keys for root account",     True),
            ("IAM",     "MFA enabled for all IAM users",       False),
            ("IAM",     "No unused IAM credentials (90 days)", False),
            ("S3",      "No public buckets",                   True),
            ("S3",      "Default encryption enabled",          True),
            ("S3",      "Access logging enabled",              False),
            ("EC2",     "No unrestricted SSH (0.0.0.0/0:22)",  False),
            ("EC2",     "EBS volumes encrypted",               True),
            ("RDS",     "Multi-AZ enabled",                    True),
            ("RDS",     "Automated backups enabled",           True),
            ("RDS",     "Public accessibility disabled",       True),
            ("CloudTrail", "Enabled in all regions",           True),
            ("GuardDuty",  "Enabled",                          False),
            ("VPC",     "Flow Logs enabled",                   False),
            ("KMS",     "Key rotation enabled",                True),
        ]

        passed = sum(1 for _, _, ok in checks if ok)
        total = len(checks)
        score = passed / total * 100

        print(f"\n    セキュリティ監査レポート")
        print(f"    スコア: {passed}/{total} ({score:.0f}%)")
        print(f"    {'─' * 55}")
        print(f"    {'Service':<14} {'Check':<42} {'Status':>8}")
        print(f"    {'─' * 14} {'─' * 42} {'─' * 8}")
        for svc, check, ok in checks:
            status = "PASS" if ok else "FAIL"
            print(f"    {svc:<14} {check:<42} {status:>8}")

        failed = [(s, c) for s, c, ok in checks if not ok]
        if failed:
            print(f"\n    要対応項目 ({len(failed)}件):")
            for i, (svc, check) in enumerate(failed, 1):
                print(f"      {i}. [{svc}] {check}")

    simulate_security_audit()

    quiz(
        "AWS の責任共有モデルにおいて、顧客が責任を持つのは?",
        [
            "データセンターの物理セキュリティ",
            "ハイパーバイザーの管理",
            "IAM ポリシーとデータの暗号化",
            "グローバルネットワークインフラ",
        ],
        2,
        "顧客は 'Security IN the Cloud' の責任を持つ。"
        "IAM設定、データの暗号化、アプリケーションセキュリティ等が含まれる。"
    )


# ============================================================
# Main
# ============================================================
def main() -> None:
    print("=" * 60)
    print("  DevOps / Infrastructure ハンズオン学習モジュール")
    print("  Docker | K8s | Terraform | CI/CD | FinOps | Security")
    print("=" * 60)

    chapter1_docker_patterns()
    chapter2_kubernetes_day2()
    chapter3_terraform()
    chapter4_cicd_patterns()
    chapter5_finops()
    chapter6_cloud_security()

    print(f"\n{SEP}")
    print("  全チャプター完了!")
    print("  次のステップ:")
    print("    1. Docker: multi-stage build で自分のアプリをコンテナ化")
    print("    2. K8s: minikube でローカル Deployment を作成")
    print("    3. Terraform: LocalStack で AWS リソースを IaC 化")
    print("    4. CI/CD: GitHub Actions で自動テスト + ビルドを構築")
    print("    5. FinOps: AWS Cost Explorer でコスト可視化を実践")
    print("    6. Security: IAM Access Analyzer で権限を棚卸し")
    print(SEP)


if __name__ == "__main__":
    main()
