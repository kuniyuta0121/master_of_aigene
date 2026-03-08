# Phase 5: Terraform によるAWSインフラ定義
# ==========================================
# 学習ポイント:
#   - インフラをコードで表現することで「再現性」「レビュー可能性」「変更追跡」を得る
#   - VPC設計（パブリック/プライベートサブネットの役割）を理解する
#   - マネージドサービス（RDS/ElastiCache）とセルフホストの使い分け
#
# 考えてほしい疑問:
#   Q1. なぜ RDS を private subnet に置くのか？public subnet ではダメか？
#   Q2. terraform.tfstate とは何か？なぜ S3 に置くのか？（ローカルに置いてはダメか？）
#   Q3. terraform plan と terraform apply の違いは？なぜ plan を先に確認するのか？
#   Q4. このIaCファイル自体のセキュリティレビューで何を見るべきか？
#
# 実行方法:
#   terraform init
#   terraform plan
#   terraform apply

terraform {
  required_version = ">= 1.9"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # stateファイルをS3に保存（チームでの共有・ロック管理のため）
  # [考える] ローカルに state を置くとどんな問題が起きるか？（チーム開発で）
  backend "s3" {
    bucket         = "knowledge-ai-terraform-state"   # 事前に作成が必要
    key            = "prod/terraform.tfstate"
    region         = "ap-northeast-1"
    encrypt        = true   # stateはDBの接続情報などを含むため必ず暗号化
    dynamodb_table = "knowledge-ai-terraform-lock"   # 同時実行ロック
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "KnowledgeAI"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# --- ネットワーク（VPC設計） ---

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.project_name}-${var.environment}"
  cidr = "10.0.0.0/16"

  # 東京リージョンの3AZ（高可用性のため複数AZに分散）
  azs             = ["ap-northeast-1a", "ap-northeast-1c", "ap-northeast-1d"]
  public_subnets  = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  private_subnets = ["10.0.11.0/24", "10.0.12.0/24", "10.0.13.0/24"]

  # [考える] NAT Gatewayはなぜ必要か？なぜ高い（$0.045/時間）のか？
  enable_nat_gateway = true
  single_nat_gateway = var.environment != "prod"  # 本番は冗長化
}

# --- ECS Fargate（コンテナ実行環境） ---
# [考える] ECS Fargate と EC2 の使い分けは？ Serverlessとの違いは？

resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"  # CloudWatchによるコンテナ監視
  }
}

resource "aws_ecs_task_definition" "api" {
  family                   = "${var.project_name}-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 512    # 0.5 vCPU
  memory                   = 1024   # 1 GB
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name  = "api"
    image = "${aws_ecr_repository.api.repository_url}:latest"
    portMappings = [{
      containerPort = 8000
      protocol      = "tcp"
    }]
    environment = [
      { name = "DATABASE_URL", value = "postgresql://${var.db_username}:${random_password.db.result}@${aws_db_instance.main.endpoint}/${var.db_name}" }
    ]
    secrets = [
      { name = "ANTHROPIC_API_KEY", valueFrom = aws_secretsmanager_secret.anthropic_key.arn }
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.api.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "api"
      }
    }
    healthCheck = {
      command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 60
    }
  }])
}

# --- RDS PostgreSQL（マネージドDB） ---

resource "random_password" "db" {
  length  = 32
  special = false
}

resource "aws_secretsmanager_secret" "db_password" {
  name = "${var.project_name}/${var.environment}/db-password"
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = random_password.db.result
}

resource "aws_db_instance" "main" {
  identifier = "${var.project_name}-${var.environment}"

  engine         = "postgres"
  engine_version = "16"
  instance_class = var.db_instance_class

  allocated_storage     = 20
  max_allocated_storage = 100  # ストレージオートスケーリング

  db_name  = var.db_name
  username = var.db_username
  password = random_password.db.result

  # プライベートサブネットに配置（外部からの直接アクセス禁止）
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.db.id]
  publicly_accessible    = false

  # 本番必須設定
  backup_retention_period = 7      # 7日間バックアップ保持
  deletion_protection     = true   # 誤削除防止
  skip_final_snapshot     = false  # 削除時にスナップショット

  tags = { Name = "${var.project_name}-db" }
}

# Secrets Manager に API キーを保存
resource "aws_secretsmanager_secret" "anthropic_key" {
  name = "${var.project_name}/${var.environment}/anthropic-api-key"
  # [実装してみよう] recovery_window_in_days を設定して即時削除を防ぐ
}

# CloudWatch Logs
resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/${var.project_name}-${var.environment}/api"
  retention_in_days = 30
}
