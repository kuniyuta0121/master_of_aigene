#!/usr/bin/env python3
"""
lang_comparison_pydantic.py
  Python (Pydantic) を起点に Go / Java / Rust で書くとどうなるか

題材: ユーザー管理 API の典型的なパターン
  1. データモデル定義 (Pydantic BaseModel → 各言語の等価物)
  2. バリデーション
  3. シリアライズ / デシリアライズ (JSON)
  4. 設定読み込み (pydantic-settings → 各言語)
  5. REST API エンドポイント定義
  6. エラーハンドリング

実行方法:
    python lang_comparison_pydantic.py

標準ライブラリのみ使用。
"""

import textwrap

# ============================================================
# ユーティリティ
# ============================================================

def section(title: str) -> None:
    print()
    print("=" * 76)
    print(f"  {title}")
    print("=" * 76)
    print()


def subsection(title: str) -> None:
    print()
    print(f"  ── {title} ──")
    print()


def note(text: str) -> None:
    for line in textwrap.dedent(text).strip().split("\n"):
        print(f"  {line}")
    print()


def point(text: str) -> None:
    print(f"    ✔ {text}")


def warn(text: str) -> None:
    print(f"    ! {text}")


def lang_block(lang: str, code: str) -> None:
    """言語ラベル付きコードブロック"""
    width = 72
    bar = "-" * width
    print(f"  +-- {lang} {'-' * (width - len(lang) - 5)}+")
    for line in code.rstrip().split("\n"):
        print(f"  | {line}")
    print(f"  +{bar}+")
    print()


def compare(python_code: str, go_code: str, java_code: str, rust_code: str) -> None:
    """Python → Go → Java → Rust の順で並べて表示"""
    lang_block("Python", python_code)
    lang_block("Go    ", go_code)
    lang_block("Java  ", java_code)
    lang_block("Rust  ", rust_code)


def table(headers: list, rows: list) -> None:
    widths = [max(len(str(r[i])) for r in [headers] + rows)
              for i in range(len(headers))]
    fmt = "  | " + " | ".join(f"{{:<{w}}}" for w in widths) + " |"
    sep = "  +-" + "-+-".join("-" * w for w in widths) + "-+"
    print(sep)
    print(fmt.format(*headers))
    print(sep)
    for row in rows:
        print(fmt.format(*row))
    print(sep)
    print()


# ============================================================
# 1. データモデル定義
# ============================================================

def chapter1_model_definition():
    section("1. データモデル定義 ── Pydantic BaseModel vs 各言語")

    note("""\
    Python/Pydantic のモデルはフィールド宣言だけで
    型チェック・JSON変換・スキーマ生成を全部やってくれる。
    他言語では「何が自動で、何を手書きするか」が異なる。
    """)

    compare(
        python_code="""\
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class User(BaseModel):
    id: int
    name: str = Field(..., min_length=1, max_length=100)
    email: str
    age: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)

# 使い方
user = User(id=1, name="Alice", email="alice@example.com")
print(user.model_dump())        # dict に変換
print(user.model_dump_json())   # JSON 文字列に変換
user2 = User.model_validate({"id": 2, "name": "Bob", "email": "b@b.com"})
""",

        go_code="""\
// Go: 構造体 + json タグ + 手動バリデーション
// (or go-playground/validator ライブラリ)

package main

import (
    "encoding/json"
    "time"
)

type User struct {
    ID        int       `json:"id"`
    Name      string    `json:"name"      validate:"required,min=1,max=100"`
    Email     string    `json:"email"     validate:"required,email"`
    Age       *int      `json:"age,omitempty"`   // Optional = ポインタ
    CreatedAt time.Time `json:"created_at"`
}

// 使い方
func main() {
    u := User{ID: 1, Name: "Alice", Email: "alice@example.com"}

    // JSON に変換
    b, _ := json.Marshal(u)
    println(string(b))

    // JSON から変換
    var u2 User
    json.Unmarshal([]byte(`{"id":2,"name":"Bob","email":"b@b.com"}`), &u2)
}
""",

        java_code="""\
// Java: record + Bean Validation (Jakarta) + Jackson
// Spring Boot が全部を自動でつなぐ

import jakarta.validation.constraints.*;
import java.time.LocalDateTime;
import java.util.Optional;

public record User(
    @NotNull
    Integer id,

    @NotBlank @Size(min = 1, max = 100)
    String name,

    @NotBlank @Email
    String email,

    Optional<Integer> age,      // Optional で nullable を表現

    LocalDateTime createdAt     // @JsonFormat でフォーマット指定
) {
    // コンパクトコンストラクタ (バリデーションはフレームワークが呼ぶ)
    public User {
        if (createdAt == null) createdAt = LocalDateTime.now();
    }
}

// 使い方 (Jackson ObjectMapper)
ObjectMapper mapper = new ObjectMapper();
String json = mapper.writeValueAsString(user);   // → JSON
User user2  = mapper.readValue(json, User.class); // JSON →
""",

        rust_code="""\
// Rust: serde + validator クレート
// Cargo.toml: serde = { features = ["derive"] }, validator = { features = ["derive"] }

use serde::{Deserialize, Serialize};
use validator::Validate;
use chrono::{DateTime, Utc};

#[derive(Debug, Serialize, Deserialize, Validate, Clone)]
pub struct User {
    pub id: u32,

    #[validate(length(min = 1, max = 100))]
    pub name: String,

    #[validate(email)]
    pub email: String,

    pub age: Option<u32>,       // Option<T> = nullable

    pub created_at: DateTime<Utc>,
}

// 使い方
fn main() {
    let user = User {
        id: 1,
        name: "Alice".to_string(),
        email: "alice@example.com".to_string(),
        age: None,
        created_at: Utc::now(),
    };

    // JSON に変換 (serde_json)
    let json = serde_json::to_string(&user).unwrap();
    println!("{}", json);

    // JSON から変換
    let user2: User = serde_json::from_str(&json).unwrap();

    // バリデーション実行 (明示的に呼ぶ)
    user.validate().expect("validation failed");
}
""")

    subsection("バリデーションのタイミング比較")
    table(
        ["言語", "バリデーションのタイミング", "手動 or 自動"],
        [
            ["Python/Pydantic", "インスタンス生成時に自動",      "自動 (コンストラクタ内)"],
            ["Go + validator",  "明示的に validate.Struct() 呼ぶ","手動"],
            ["Java + Bean Val", "フレームワーク(Spring)が自動",  "自動 (@Valid アノテーション)"],
            ["Rust + validator","明示的に .validate() 呼ぶ",     "手動"],
        ]
    )

    point("Python が最も自動化されている (生成時にバリデーション + エラーメッセージも自動)")
    point("Go / Rust はバリデーションを明示的に呼ぶ設計 — 「驚き最小の原則」")
    point("Java は @Valid を付けるとフレームワークが呼んでくれる (Spring MVC)")
    warn("Rust は derive マクロで宣言的に書けるが、実行は手動。unwrap() は本番では ? に変える")


# ============================================================
# 2. ネストモデル / バリデーション
# ============================================================

def chapter2_nested_models():
    section("2. ネストモデル / バリデ���ション")

    note("""\
    住所を持つユーザー。ネストしたモデルのバリデーションと
    カスタムバリデーターの書き方を比較する。
    """)

    compare(
        python_code="""\
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Literal

class Address(BaseModel):
    street: str
    city: str
    country: str = "JP"
    zip_code: str = Field(pattern=r"^\\d{3}-\\d{4}$")  # 正規表現

class UserWithAddress(BaseModel):
    name: str
    email: str
    address: Address       # ネストは自動でバリデーション

    @field_validator("email")
    @classmethod
    def email_must_have_domain(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("email must contain @")
        return v.lower()   # 正規化も同時にできる

    @model_validator(mode="after")
    def check_jp_zip(self) -> "UserWithAddress":
        if self.address.country == "JP" and not self.address.zip_code:
            raise ValueError("JP address requires zip_code")
        return self

# 使い方
user = UserWithAddress(
    name="Alice",
    email="Alice@Example.com",   # → "alice@example.com" に正規化される
    address=Address(street="渋谷1-1", city="東京", zip_code="150-0001")
)
""",

        go_code="""\
type Address struct {
    Street  string `json:"street"   validate:"required"`
    City    string `json:"city"     validate:"required"`
    Country string `json:"country"`
    ZipCode string `json:"zip_code" validate:"required,len=8"`
}

type UserWithAddress struct {
    Name    string  `json:"name"    validate:"required"`
    Email   string  `json:"email"   validate:"required,email"`
    Address Address `json:"address" validate:"required"` // ネストも validate が再帰的に検証
}

// カスタムバリデーター登録
var validate = validator.New()

func init() {
    validate.RegisterValidation("jp_zip", func(fl validator.FieldLevel) bool {
        matched, _ := regexp.MatchString(`^\\d{3}-\\d{4}$`, fl.Field().String())
        return matched
    })
}

func CreateUser(u UserWithAddress) error {
    // メール正規化 (Go は変換を手動でやる)
    u.Email = strings.ToLower(u.Email)
    return validate.Struct(u)   // バリデーション実行
}
""",

        java_code="""\
public record Address(
    @NotBlank String street,
    @NotBlank String city,
    String country,
    @Pattern(regexp = "\\\\d{3}-\\\\d{4}") String zipCode
) {}

public record UserWithAddress(
    @NotBlank String name,
    @NotBlank @Email String email,
    @Valid @NotNull Address address  // @Valid でネストバリデーション
) {
    // カスタム正規化 (コンパクトコンストラクタ)
    public UserWithAddress {
        email = email.toLowerCase();
    }
}

// Spring MVC では @Valid を付けるだけ
@PostMapping("/users")
public ResponseEntity<UserWithAddress> create(
        @Valid @RequestBody UserWithAddress user) {  // 自動バリデーション
    return ResponseEntity.ok(userService.save(user));
}
""",

        rust_code="""\
#[derive(Debug, Serialize, Deserialize, Validate)]
pub struct Address {
    #[validate(length(min = 1))]
    pub street: String,
    pub city: String,
    pub country: String,
    #[validate(regex(path = "ZIP_REGEX"))]
    pub zip_code: String,
}

static ZIP_REGEX: once_cell::sync::Lazy<regex::Regex> =
    once_cell::sync::Lazy::new(|| regex::Regex::new(r"^\\d{3}-\\d{4}$").unwrap());

#[derive(Debug, Serialize, Deserialize, Validate)]
pub struct UserWithAddress {
    pub name: String,
    #[validate(email)]
    pub email: String,
    #[validate(nested)]   // validator 0.18+ でネストバリデーション
    pub address: Address,
}

impl UserWithAddress {
    pub fn new(name: String, email: String, address: Address)
        -> Result<Self, validator::ValidationErrors>
    {
        let mut u = Self {
            name,
            email: email.to_lowercase(),   // 正規化
            address,
        };
        u.validate()?;   // バリデーション
        Ok(u)
    }
}
""")

    point("Python: @field_validator で変換と検証を1か所に書ける (宣言的)")
    point("Go: カスタムバリデーターは init() で登録する (グローバル)")
    point("Java: @Valid をネストに伝播させるだけ (フレームワークが再帰検証)")
    point("Rust: new() コンストラクタでバリデーションを強制 → 型レベルで「不正な値は存在しない」")


# ============================================================
# 3. 設定読み込み (pydantic-settings)
# ============================================================

def chapter3_config():
    section("3. 設定読み込み ── pydantic-settings vs 各言語")

    note("""\
    環境変数 / .env ファイルから設定を読む。
    Python は pydantic-settings が最もシンプル。
    他言語の等価物を比較する。
    """)

    compare(
        python_code="""\
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="APP_",       # 環境変数は APP_ プレフィックス
    )

    # 型を書くだけで環境変数から自動読み込み・型変換
    database_url: str
    secret_key: str
    debug: bool = False
    max_connections: int = Field(default=10, ge=1, le=100)
    allowed_hosts: list[str] = ["localhost"]

# .env ファイル:
# APP_DATABASE_URL=postgresql://localhost/mydb
# APP_SECRET_KEY=supersecret
# APP_DEBUG=true

settings = Settings()   # 起動時に1回だけ生成
print(settings.database_url)
print(settings.debug)   # str "true" → bool True に自動変換
""",

        go_code="""\
// Go: 標準は os.Getenv + strconv。
// ライブラリ: viper (ファイル対応) or caarlos0/env

package config

import (
    "github.com/caarlos0/env/v11"
    "log"
)

type Config struct {
    DatabaseURL    string   `env:"APP_DATABASE_URL,required"`
    SecretKey      string   `env:"APP_SECRET_KEY,required"`
    Debug          bool     `env:"APP_DEBUG"          envDefault:"false"`
    MaxConnections int      `env:"APP_MAX_CONNECTIONS" envDefault:"10"`
    AllowedHosts   []string `env:"APP_ALLOWED_HOSTS"   envSeparator:","`
}

func Load() *Config {
    cfg := &Config{}
    if err := env.Parse(cfg); err != nil {
        log.Fatalf("config error: %v", err)
    }
    return cfg
}

// main.go
// cfg := config.Load()
// fmt.Println(cfg.DatabaseURL)
""",

        java_code="""\
// Java: Spring Boot は application.yml + @ConfigurationProperties
// または @Value で個別注入

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.bind.DefaultValue;
import jakarta.validation.constraints.*;

@ConfigurationProperties(prefix = "app")  // application.yml の app: 以下を読む
public record AppConfig(
    @NotBlank String databaseUrl,
    @NotBlank String secretKey,
    @DefaultValue("false") boolean debug,
    @DefaultValue("10") @Min(1) @Max(100) int maxConnections,
    @DefaultValue("localhost") List<String> allowedHosts
) {}

// application.yml:
// app:
//   database-url: postgresql://localhost/mydb
//   secret-key: supersecret
//   debug: true

// Spring Boot が起動時に自動バインド + バリデーション実行
// @SpringBootApplication クラスに @EnableConfigurationProperties(AppConfig.class) を追加
""",

        rust_code="""\
// Rust: config クレート + serde + dotenvy (.env 読み込み)
// Cargo.toml: config = "0.14", serde = { features = ["derive"] }, dotenvy = "0.15"

use serde::Deserialize;
use config::{Config, Environment, File};

#[derive(Debug, Deserialize)]
pub struct Settings {
    pub database_url: String,
    pub secret_key: String,
    #[serde(default)]
    pub debug: bool,
    #[serde(default = "default_max_connections")]
    pub max_connections: u32,
    #[serde(default = "default_hosts")]
    pub allowed_hosts: Vec<String>,
}

fn default_max_connections() -> u32 { 10 }
fn default_hosts() -> Vec<String> { vec!["localhost".to_string()] }

impl Settings {
    pub fn load() -> Result<Self, config::ConfigError> {
        dotenvy::dotenv().ok();   // .env ファイルを環境変数に展開
        Config::builder()
            .add_source(File::with_name("config/default").required(false))
            .add_source(Environment::with_prefix("APP").separator("_"))
            .build()?
            .try_deserialize()
    }
}

// main.rs
// let settings = Settings::load().expect("config error");
// println!("{}", settings.database_url);
""")

    subsection("設定管理の比較")
    table(
        ["言語", "主要ライブラリ", ".env対応", "型変換", "バリデーション"],
        [
            ["Python", "pydantic-settings", "組み込み",    "自動",   "自動"],
            ["Go",     "caarlos0/env",       "別途dotenvy","自動",   "required タグ"],
            ["Java",   "@ConfigurationProperties","application.yml","自動","@Valid 連携"],
            ["Rust",   "config + dotenvy",   "dotenvy",    "serde",  "起動時にパニック"],
        ]
    )
    point("Python/pydantic-settings が最も設定量が少ない")
    point("Java の application.yml は環境別プロファイル (dev/prod) と相性が良い")
    point("Rust は型が合わなければコンパイルエラー → 実行前に設定ミスを検出")


# ============================================================
# 4. REST API エンドポイント
# ============================================================

def chapter4_api_endpoint():
    section("4. REST API エンドポイント ── FastAPI vs 各言語")

    note("""\
    POST /users でユーザーを作成するエンドポイント。
    リクエストボディの受け取り・バリデーション・レスポンス返却。
    """)

    compare(
        python_code="""\
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, EmailStr

app = FastAPI()

class CreateUserRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    age: int | None = None

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

@app.post("/users", response_model=UserResponse, status_code=201)
async def create_user(body: CreateUserRequest) -> UserResponse:
    # body は自動でバリデーション済み
    # バリデーション失敗時は FastAPI が 422 を自動返却
    user = await user_service.create(body)
    return UserResponse(id=user.id, name=user.name, email=user.email)

# エラーハンドリング
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    raise HTTPException(status_code=400, detail=str(exc))
""",

        go_code="""\
// Go: net/http 標準 + chi router (軽量)
// or Gin / Echo でより FastAPI に近い書き方

package handler

import (
    "encoding/json"
    "net/http"
    "github.com/go-playground/validator/v10"
)

type CreateUserRequest struct {
    Name  string `json:"name"  validate:"required,min=1,max=100"`
    Email string `json:"email" validate:"required,email"`
    Age   *int   `json:"age"`
}

type UserResponse struct {
    ID    int    `json:"id"`
    Name  string `json:"name"`
    Email string `json:"email"`
}

var validate = validator.New()

func CreateUser(w http.ResponseWriter, r *http.Request) {
    var req CreateUserRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    if err := validate.Struct(req); err != nil {
        http.Error(w, err.Error(), http.StatusUnprocessableEntity)
        return
    }
    user, err := userService.Create(r.Context(), req)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(http.StatusCreated)
    json.NewEncoder(w).Encode(UserResponse{ID: user.ID, Name: user.Name, Email: user.Email})
}
""",

        java_code="""\
// Java: Spring Boot + Spring MVC
// 宣言的でコードが最も短い

import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;

@RestController
@RequestMapping("/users")
public class UserController {

    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    record CreateUserRequest(
        @NotBlank @Size(min = 1, max = 100) String name,
        @NotBlank @Email                    String email,
        Integer age  // null 許容
    ) {}

    record UserResponse(int id, String name, String email) {}

    @PostMapping
    public ResponseEntity<UserResponse> createUser(
            @Valid @RequestBody CreateUserRequest body) {
        // @Valid でバリデーション失敗時は 400 を自動返却
        var user = userService.create(body);
        return ResponseEntity.status(201)
            .body(new UserResponse(user.id(), user.name(), user.email()));
    }
}
""",

        rust_code="""\
// Rust: Axum (モダンな非同期 Web フレームワーク)
// Cargo.toml: axum, serde, validator, tokio

use axum::{extract::Json, http::StatusCode, response::IntoResponse, Router};
use serde::{Deserialize, Serialize};
use validator::Validate;

#[derive(Debug, Deserialize, Validate)]
pub struct CreateUserRequest {
    #[validate(length(min = 1, max = 100))]
    pub name: String,
    #[validate(email)]
    pub email: String,
    pub age: Option<u32>,
}

#[derive(Debug, Serialize)]
pub struct UserResponse {
    pub id: u32,
    pub name: String,
    pub email: String,
}

// Axum ハンドラー
pub async fn create_user(
    Json(body): Json<CreateUserRequest>,  // JSON デシリアライズ自動
) -> impl IntoResponse {
    // バリデーションは手動 (or カスタム Extractor で自動化可)
    if let Err(e) = body.validate() {
        return (StatusCode::UNPROCESSABLE_ENTITY, e.to_string()).into_response();
    }
    let user = user_service::create(body).await.unwrap();
    (StatusCode::CREATED, Json(UserResponse {
        id: user.id, name: user.name, email: user.email,
    })).into_response()
}

pub fn router() -> Router {
    Router::new().route("/users", axum::routing::post(create_user))
}
""")

    subsection("エンドポイント定義の比較")
    table(
        ["言語", "バリデーション", "JSON変換", "エラー自動化", "行数(概算)"],
        [
            ["Python/FastAPI",  "自動",    "自動",   "◎ (422自動)",     "~20行"],
            ["Go/chi",          "手動呼び", "手動呼び","△ (手書き必要)", "~35行"],
            ["Java/Spring",     "自動(@Valid)","自動","◎ (400自動)",   "~25行"],
            ["Rust/Axum",       "手動呼び", "自動",   "○ (自動化可能)", "~30行"],
        ]
    )
    point("FastAPI が最も少ないコードでエンドポイントを定義できる")
    point("Spring MVC は Java にしてはかなり簡潔 (record + @Valid の組み合わせ)")
    point("Axum はカスタム Extractor を作れば FastAPI に近いバリデーショ���自動化が可能")


# ============================================================
# 5. エラーハンドリング
# ============================================================

def chapter5_error_handling():
    section("5. エラーハンドリング ── Python 例外 vs Go error vs Java 例外 vs Rust Result")

    note("""\
    「ユーザーが見つからない場合」と「DB エラー」の2種類のエラーを
    どう表現・伝播するかを比較する。
    """)

    compare(
        python_code="""\
from typing import Optional

# カスタム例外の定義
class AppError(Exception):
    \"\"\"アプリケーション基底例外\"\"\"
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class NotFoundError(AppError):
    def __init__(self, resource: str, id: int):
        super().__init__(f"{resource} (id={id}) not found", status_code=404)

class DatabaseError(AppError):
    def __init__(self, detail: str):
        super().__init__(f"Database error: {detail}", status_code=500)

# サービス層
async def get_user(user_id: int) -> User:
    try:
        user = await db.find_user(user_id)
    except DBException as e:
        raise DatabaseError(str(e))   # DB例外をアプリ例外に変換

    if user is None:
        raise NotFoundError("User", user_id)
    return user

# FastAPI で自動的に HTTP レスポンスに変換
@app.exception_handler(AppError)
async def app_error_handler(request, exc: AppError):
    return JSONResponse({"error": exc.message}, status_code=exc.status_code)
""",

        go_code="""\
// Go: error インターフェースを実装したカスタムエラー型
// errors.As() / errors.Is() でエラー種別を判定

package domain

import "fmt"

// カスタムエラー型
type NotFoundError struct {
    Resource string
    ID       int
}
func (e *NotFoundError) Error() string {
    return fmt.Sprintf("%s (id=%d) not found", e.Resource, e.ID)
}

type DatabaseError struct{ Cause error }
func (e *DatabaseError) Error() string { return "database error: " + e.Cause.Error() }
func (e *DatabaseError) Unwrap() error { return e.Cause }  // errors.Is() 対応

// サービス層
func (s *UserService) GetUser(ctx context.Context, id int) (*User, error) {
    user, err := s.repo.FindByID(ctx, id)
    if err != nil {
        return nil, &DatabaseError{Cause: err}  // エラー変換
    }
    if user == nil {
        return nil, &NotFoundError{Resource: "User", ID: id}
    }
    return user, nil
}

// ハンドラーでの判定
func (h *Handler) GetUser(w http.ResponseWriter, r *http.Request) {
    user, err := h.service.GetUser(r.Context(), id)
    if err != nil {
        var nfe *NotFoundError
        if errors.As(err, &nfe) {
            http.Error(w, nfe.Error(), http.StatusNotFound)
        } else {
            http.Error(w, err.Error(), http.StatusInternalServerError)
        }
        return
    }
    json.NewEncoder(w).Encode(user)
}
""",

        java_code="""\
// Java: checked exception vs unchecked exception
// Spring 推奨: RuntimeException を継承した unchecked 例外

// カスタム例外
public class AppException extends RuntimeException {
    private final int statusCode;

    public AppException(String message, int statusCode) {
        super(message);
        this.statusCode = statusCode;
    }
    public int getStatusCode() { return statusCode; }
}

public class NotFoundException extends AppException {
    public NotFoundException(String resource, int id) {
        super(resource + " (id=" + id + ") not found", 404);
    }
}

// サービス層
public User getUser(int userId) {
    return userRepository.findById(userId)
        .orElseThrow(() -> new NotFoundException("User", userId));
}

// グローバルエラーハンドラー (1か所に集約)
@RestControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(AppException.class)
    public ResponseEntity<Map<String, String>> handle(AppException e) {
        return ResponseEntity.status(e.getStatusCode())
            .body(Map.of("error", e.getMessage()));
    }
}
""",

        rust_code="""\
// Rust: Result<T, E> + thiserror クレートでカスタムエラー
// ? 演算子でエラー伝播 (Python の raise と同等)

use thiserror::Error;

// カスタムエラー型 (enum が基本)
#[derive(Debug, Error)]
pub enum AppError {
    #[error("{resource} (id={id}) not found")]
    NotFound { resource: String, id: u32 },

    #[error("database error: {0}")]
    Database(#[from] sqlx::Error),   // sqlx::Error からの自動変換

    #[error("internal error: {0}")]
    Internal(String),
}

// Axum との連携 (IntoResponse を実装)
impl axum::response::IntoResponse for AppError {
    fn into_response(self) -> axum::response::Response {
        let (status, message) = match &self {
            AppError::NotFound { .. } => (StatusCode::NOT_FOUND, self.to_string()),
            AppError::Database(_)     => (StatusCode::INTERNAL_SERVER_ERROR, self.to_string()),
            AppError::Internal(_)     => (StatusCode::INTERNAL_SERVER_ERROR, self.to_string()),
        };
        (status, Json(serde_json::json!({"error": message}))).into_response()
    }
}

// サービス層
pub async fn get_user(id: u32) -> Result<User, AppError> {
    let user = db::find_user(id).await?;   // ? = DB エラーを AppError::Database に自動変換
    user.ok_or(AppError::NotFound { resource: "User".into(), id })
}

// ハンドラー (AppError が IntoResponse を実装しているので return するだけ)
pub async fn get_user_handler(Path(id): Path<u32>) -> Result<Json<User>, AppError> {
    let user = get_user(id).await?;   // ? でエラー伝播
    Ok(Json(user))
}
""")

    subsection("エラーハンドリングの哲学比較")
    table(
        ["言語", "エラー表現", "伝播方法", "型安全性", "見逃しやすさ"],
        [
            ["Python",  "例外クラス",        "raise / 自動伝播",    "△ (実行時)", "大 (try忘れ)"],
            ["Go",      "error インターフェース","return err (明示)", "△ (無視可能)","中 (if err != nil)"],
            ["Java",    "例外クラス",         "throw / 自動伝播",   "△ (実行時)", "小 (unchecked)"],
            ["Rust",    "Result<T,E> enum",  "? 演算子",           "◎ (コンパイル時)","最小 (無視不可)"],
        ]
    )
    point("Rust は Result を無視するとコンパイルエラー → エラー見逃しが構造的に不可能")
    point("Go は 'if err != nil' を書かないとエラーを無視できてしまう (linter で検出可)")
    point("Python / Java は try を書かなくても動く → 大規模チームでは規律が必要")


# ============================================================
# 6. シリアライズ高度編 (カスタム変換)
# ============================================================

def chapter6_serialization():
    section("6. シリアライズ高度編 ── フィールド名変換・discriminated union・exclude")

    note("""\
    実際の API では「DB の snake_case」と「API の camelCase」の変換、
    型の継承(polymorphism)、レスポンスからの秘密情報除外などが必要になる。
    """)

    compare(
        python_code="""\
from pydantic import BaseModel, Field, model_serializer
from typing import Literal, Annotated, Union

# snake_case → camelCase 自動変換
class CamelModel(BaseModel):
    model_config = {"alias_generator": lambda s: ''.join(
        w.capitalize() if i else w for i, w in enumerate(s.split('_'))
    ), "populate_by_name": True}

class UserResponse(CamelModel):
    user_id: int           # JSON では "userId"
    full_name: str         # JSON では "fullName"
    password_hash: str = Field(exclude=True)   # レスポンスから除外

# Discriminated Union (型判別)
class Cat(BaseModel):
    type: Literal["cat"]
    meow_volume: int

class Dog(BaseModel):
    type: Literal["dog"]
    bark_loudness: int

Animal = Annotated[Union[Cat, Dog], Field(discriminator="type")]

class Zoo(BaseModel):
    animals: list[Animal]

zoo = Zoo(animals=[
    {"type": "cat", "meow_volume": 7},
    {"type": "dog", "bark_loudness": 9},
])
# zoo.animals[0] は Cat インスタンス (型が解決される)
print(type(zoo.animals[0]))  # <class 'Cat'>
""",

        go_code="""\
// Go: JSON タグで名前変換、カスタム MarshalJSON でフィールド除外

type UserResponse struct {
    UserID       int    `json:"userId"`    // camelCase 指定
    FullName     string `json:"fullName"`
    PasswordHash string `json:"-"`         // json:"-" で除外
}

// Discriminated Union → interface + type switch
type Animal interface {
    AnimalType() string
}

type Cat struct {
    Type        string `json:"type"`
    MeowVolume  int    `json:"meow_volume"`
}
func (c Cat) AnimalType() string { return "cat" }

type Dog struct {
    Type          string `json:"type"`
    BarkLoudness  int    `json:"bark_loudness"`
}
func (d Dog) AnimalType() string { return "dog" }

// JSON デシリアライズ時に型を判別 (手動実装が必要)
func UnmarshalAnimal(data []byte) (Animal, error) {
    var raw struct{ Type string `json:"type"` }
    json.Unmarshal(data, &raw)
    switch raw.Type {
    case "cat":
        var c Cat; json.Unmarshal(data, &c); return c, nil
    case "dog":
        var d Dog; json.Unmarshal(data, &d); return d, nil
    }
    return nil, fmt.Errorf("unknown type: %s", raw.Type)
}
""",

        java_code="""\
// Java: Jackson アノテーション

// snake_case → camelCase (Jackson のデフォルト動作)
@JsonNaming(PropertyNamingStrategies.LowerCamelCaseStrategy.class)
public record UserResponse(
    int userId,
    String fullName,
    @JsonIgnore String passwordHash   // レスポンスから除外
) {}

// Discriminated Union → Jackson @JsonTypeInfo
@JsonTypeInfo(use = JsonTypeInfo.Id.NAME, property = "type")
@JsonSubTypes({
    @JsonSubTypes.Type(value = Cat.class, name = "cat"),
    @JsonSubTypes.Type(value = Dog.class, name = "dog"),
})
public interface Animal {}

public record Cat(String type, int meowVolume)  implements Animal {}
public record Dog(String type, int barkLoudness) implements Animal {}

// デシリアライズ時に Jackson が自動で型を判別
// objectMapper.readValue(json, Animal.class) → Cat or Dog
""",

        rust_code="""\
// Rust: serde のフィールドアトリビュート

#[derive(Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]   // 全フィールドを camelCase に変換
pub struct UserResponse {
    pub user_id: u32,       // JSON では "userId"
    pub full_name: String,  // JSON では "fullName"
    #[serde(skip_serializing)]   // シリアライズ時のみ除外
    pub password_hash: String,
}

// Discriminated Union → serde の tagged enum
#[derive(Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum Animal {
    Cat { meow_volume: u32 },
    Dog { bark_loudness: u32 },
}

// JSON: {"type": "cat", "meow_volume": 7}
// デシリアライズ時に serde が自動で型を判別
let animal: Animal = serde_json::from_str(r#"{"type":"cat","meow_volume":7}"#).unwrap();
match animal {
    Animal::Cat { meow_volume } => println!("Cat: {}", meow_volume),
    Animal::Dog { bark_loudness } => println!("Dog: {}", bark_loudness),
}
""")

    subsection("Discriminated Union の比較まとめ")
    table(
        ["言語", "実装方法", "型安全", "コード量"],
        [
            ["Python/Pydantic", "Annotated + discriminator",  "◎ (実行時解決)", "少"],
            ["Go",              "interface + 手動 switch",     "○ (型assertionが必要)", "多"],
            ["Java/Jackson",    "@JsonTypeInfo アノテーション", "◎ (フレームワーク)", "中"],
            ["Rust/serde",      "#[serde(tag)] enum",         "◎ (コンパイル時)", "少"],
        ]
    )
    point("Rust の enum は Discriminated Union をネイティブに表現できる最も自然な言語")
    point("Python の Pydantic も Union + discriminator で同等の機能を提供")
    point("Go は型システムの制約から手動実装が必要 — ジェネリクス追加後も完全解決はしていない")


# ============================================================
# 7. インポート / モジュールシステム
# ============================================================

def chapter7_imports():
    section("7. インポート / モジュールシステム ── from X import Y の各言語版")

    note("""\
    Python の `from module import SomeClass` に相当する書き方を各言語で比較する。
    「どこに置いたファイルが、どんな名前でインポートできるか」のルールが
    言語ごとに大きく異なる。
    """)

    # ------------------------------------------------------------------
    # 7-1. 同じプロジェクト内の自分で書いたファイルをインポート
    # ------------------------------------------------------------------
    subsection("7-1. 自分で書いたファイル（同プロジェクト内）のインポート")

    compare(
        python_code="""\
# ファイル構成:
# my_app/
# ├── models/
# │   ├── __init__.py
# │   └── user.py       ← class User, class Address を定義
# ├── services/
# │   └── user_service.py
# └── main.py

# --- user.py ---
class User:
    def __init__(self, name: str):
        self.name = name

class Address:
    def __init__(self, city: str):
        self.city = city

# --- user_service.py ---
from my_app.models.user import User          # 特定クラスだけ
from my_app.models.user import User, Address # 複数
from my_app.models import user               # モジュールごと → user.User で使う
from my_app.models.user import *             # 全部 (非推奨)

# 相対インポート (同パッケージ内)
from ..models.user import User   # 1つ上のディレクトリから
from .helper import some_func    # 同じディレクトリから
""",

        go_code="""\
// ファイル構成:
// my-app/
// ├── go.mod              (module my-app)
// ├── internal/
// │   ├── model/
// │   │   └── user.go    ← type User struct, type Address struct
// │   └── service/
// │       └── user_service.go
// └── cmd/api/main.go

// --- model/user.go ---
package model   // ディレクトリ名 = パッケージ名 (慣習)

type User struct {
    Name string
}

type Address struct {
    City string
}

// --- service/user_service.go ---
package service

import (
    "my-app/internal/model"   // go.mod のモジュール名 + ディレクトリパス
)

func DoSomething() {
    u := model.User{Name: "Alice"}   // パッケージ名.型名 で使う
    _ = u
}

// ポイント:
// - Go に "from X import Y" はない。必ずパッケージ名でアクセス
// - import "my-app/internal/model" → model.User, model.Address
// - 別名をつける: import m "my-app/internal/model" → m.User
// - 使わない import はコンパイルエラー (自動削除ツール: goimports)
""",

        java_code="""\
// ファイル構成:
// src/main/java/com/example/myapp/
// ├── model/
// │   ├── User.java      ← public class User
// │   └── Address.java   ← public class Address
// ├── service/
// │   └── UserService.java
// └── MyAppApplication.java

// --- model/User.java ---
package com.example.myapp.model;   // ファイルの場所と一致させる (必須)

public class User {
    private String name;
    // ...
}

// --- service/UserService.java ---
package com.example.myapp.service;

import com.example.myapp.model.User;          // 特定クラスだけ
import com.example.myapp.model.Address;       // 追加で別クラス
import com.example.myapp.model.*;             // model パッケージ全部 (非推奨)

public class UserService {
    public void doSomething() {
        User u = new User();   // インポート済みなのでそのまま使える
    }
}

// ポイント:
// - 同じ package 内ならインポート不要
// - java.lang.* (String, Integer など) は自動インポート済み
// - IDE が自動で import を追加/削除してくれる
""",

        rust_code="""\
// ファイル構成:
// src/
// ├── main.rs
// ├── model/
// │   ├── mod.rs         ← モジュール定義 (必須)
// │   ├── user.rs        ← pub struct User, pub struct Address
// │   └── address.rs
// └── service/
//     ├── mod.rs
//     └── user_service.rs

// --- model/user.rs ---
pub struct User {
    pub name: String,
}

pub struct Address {
    pub city: String,
}

// --- model/mod.rs --- (ディレクトリをモジュールとして公開)
pub mod user;    // user.rs を公開
pub mod address; // address.rs を公開

// 再エクスポート (Python の __init__.py と同じ感覚)
pub use user::User;       // model::User で直接アクセス可能にする
pub use address::Address;

// --- service/user_service.rs ---
use crate::model::User;          // クレートルートから絶対パス
use crate::model::{User, Address}; // 複数まとめて
use crate::model::user::User;    // ファイルを指定して
use super::model::User;          // 相対パス (1つ上から)

fn do_something() {
    let u = User { name: "Alice".to_string() };
    let _ = u;
}

// --- main.rs --- (モジュール宣言が必要)
mod model;    // model/mod.rs を読み込む
mod service;
""")

    point("Python: ディレクトリ + __init__.py があれば自動的にパッケージ化")
    point("Go: ディレクトリ = パッケージ。import パスはモジュール名+ディレクトリパス")
    point("Java: package 宣言とディレクトリ構造を一致させる必要がある")
    point("Rust: mod 宣言が必須。使わないと存在しないも同然")
    print()

    # ------------------------------------------------------------------
    # 7-2. 外部ライブラリのインポート
    # ------------------------------------------------------------------
    subsection("7-2. 外部ライブラリ（pip install したもの）のインポート")

    compare(
        python_code="""\
# インストール:
#   pip install pydantic fastapi

# インポート:
from pydantic import BaseModel, Field
from pydantic import BaseModel as BM          # 別名
import pydantic                               # モジュールごと → pydantic.BaseModel
from fastapi import FastAPI, HTTPException

# インストール情報: pyproject.toml / requirements.txt
# dependencies = ["pydantic>=2.0", "fastapi>=0.100"]
""",

        go_code="""\
// インストール:
//   go get github.com/go-playground/validator/v10
//   → go.mod と go.sum に自動追記

// インポート:
import (
    "github.com/go-playground/validator/v10"  // 外部ライブラリ
    "encoding/json"                            // 標準ライブラリ (パスが短い)
    "fmt"

    v "github.com/go-playground/validator/v10" // 別名 v をつける
)

// 使う:
validate := validator.New()
// または別名あり:
validate := v.New()

// インストール情報: go.mod
// require (
//     github.com/go-playground/validator/v10 v10.22.0
// )
""",

        java_code="""\
// インストール: pom.xml (Maven) に追記 → mvn install で自動ダウンロード

// pom.xml:
// <dependency>
//     <groupId>org.springframework.boot</groupId>
//     <artifactId>spring-boot-starter-web</artifactId>
//     <version>3.2.0</version>
// </dependency>

// インポート:
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.http.ResponseEntity;

// 同パッケージは自動 (import 不要)
// static インポート (定数・メソッドを直接使う)
import static org.assertj.core.api.Assertions.assertThat;  // テストでよく使う

// ワイルドカード (IDE が管理するので手書きは非推奨)
import org.springframework.web.bind.annotation.*;
""",

        rust_code="""\
// インストール: Cargo.toml の [dependencies] に追記 → cargo build で自動ダウンロード

// Cargo.toml:
// [dependencies]
// serde = { version = "1", features = ["derive"] }
// serde_json = "1"
// validator = { version = "0.18", features = ["derive"] }

// インポート:
use serde::{Deserialize, Serialize};          // 複数まとめて
use serde::Serialize;                          // 1つだけ
use serde_json;                                // クレートごと → serde_json::to_string()
use validator::Validate;

// 別名:
use std::collections::HashMap as Map;

// ネストした use (まとめて書く):
use std::{
    collections::HashMap,
    fmt::Display,
    io::{self, Read},   // io 自体と io::Read を同時に
};
""")

    # ------------------------------------------------------------------
    # 7-3. よくあるパターン早見表
    # ------------------------------------------------------------------
    subsection("7-3. よくあるパターン早見表")

    table(
        ["やりたいこと", "Python", "Go", "Java", "Rust"],
        [
            ["特定クラスをインポート",
             "from x.y import Foo",
             "import \"mod/x/y\"  → y.Foo",
             "import x.y.Foo",
             "use crate::x::y::Foo"],
            ["複数まとめてインポート",
             "from x import A, B",
             "import \"mod/x\" → x.A, x.B",
             "import x.A; import x.B",
             "use crate::x::{A, B}"],
            ["モジュールごとインポート",
             "import x.y as xy",
             "import xy \"mod/x/y\"",
             "(Javaはクラス単位)",
             "use crate::x::y; (or mod)"],
            ["全部インポート (glob)",
             "from x import *",
             "(存在しない)",
             "import x.*",
             "use crate::x::*"],
            ["別名をつける",
             "import numpy as np",
             "import np \"mod/numpy\"",
             "(型エイリアスのみ)",
             "use numpy as np"],
            ["標準ライブラリ",
             "import os, sys",
             "import \"os\", \"fmt\"",
             "import java.util.List",
             "use std::collections::HashMap"],
            ["同ディレクトリ/パッケージ",
             "from . import helper",
             "(同 package なら自動)",
             "(同 package なら自動)",
             "use super::helper"],
        ]
    )

    # ------------------------------------------------------------------
    # 7-4. 循環インポートとその解決
    # ------------------------------------------------------------------
    subsection("7-4. 循環インポートとその解決")

    note("""\
    A が B をインポートして、B が A をインポートする「循環」は
    どの言語でも問題になる。解決策も似ている。
    """)

    lang_block("Python ── 循環インポートの例と解決策",
    """\
# 問題: user.py と order.py が互いにインポート
# user.py: from order import Order   ← NG
# order.py: from user import User    ← NG

# 解決策1: 型ヒントだけなら TYPE_CHECKING フラグを使う
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from order import Order   # 実行時はインポートしない (型チェックのみ)

class User:
    def get_orders(self) -> list["Order"]:  # 文字列で前方参照
        ...

# 解決策2: インポートを関数の中に移動 (遅延インポート)
def get_orders(self):
    from order import Order   # 呼び出し時に初めてインポート
    ...

# 解決策3: 共通の基底モジュールに型定義を移す (最善)
# base.py に UserBase, OrderBase を定義 → user.py と order.py が base.py だけを参照
""")

    lang_block("Go ── 循環インポートはコンパイルエラー",
    """\
// Go はパッケージ間の循環インポートをコンパイラが禁止する
// → 設計の問題として強制的に気づかせてくれる

// 解決策: インターフェースで依存を逆転 (DIP)
// domain パッケージにインターフェースを定義
package domain

type OrderRepository interface {   // ← インターフェースだけ domain に置く
    FindByUserID(userID int) ([]Order, error)
}

// infra パッケージが実装
package infra

import "my-app/domain"

type PostgresOrderRepo struct{}

func (r *PostgresOrderRepo) FindByUserID(id int) ([]domain.Order, error) {
    // ...
}
// → domain は infra を知らず、infra が domain を知る (一方向)
""")

    lang_block("Java ── 循環は実行時エラー or 設計の警告",
    """\
// Java はコンパイルは通るが、Spring の DI が循環依存を検出してエラーにする
// (Spring Boot 2.6+ からデフォルトで禁止)

// 解決策: @Lazy で遅延初期化
@Service
public class UserService {
    @Lazy   // 循環を解消する応急処置 (根本解決ではない)
    private final OrderService orderService;
}

// 根本解決: ApplicationEventPublisher でイベント経由にする
// または共通インターフェースで依存を分離する
""")

    lang_block("Rust ── モジュール内の循環は許可される",
    """\
// Rust は同じクレート内のモジュール間循環は OK
// クレート間の循環は Cargo がコンパイルエラーにする

// 同クレート内: user.rs と order.rs が互いを use しても問題なし
// → Rust コンパイラがうまく解決する

// ただし型の前方参照は Box<T> や Arc<T> でポインタにする必要あり
pub struct User {
    pub orders: Vec<Order>,   // Order は別モジュールでも OK
}

pub struct Order {
    pub user: Box<User>,      // 再帰的な参照は Box が必要 (サイズ確定のため)
}
""")

    point("Python: `if TYPE_CHECKING:` パターンが実用的で最も多く使われる")
    point("Go: コンパイラが循環を禁止する → 設計を直すしかない (良いこと)")
    point("Java: @Lazy は応急処置。根本はインターフェース分離で解決")
    point("Rust: 同クレート内は OK。クレート間はコンパイルエラーで気づける")


# ============================================================
# 8. パッケージ管理 ── pip / PyPI の各言語版
# ============================================================

def chapter8_package_management():
    section("8. パッケージ管理 ── pip install / PyPI の各言語版")

    note("""\
    Python の「pip install ライブラリ名」と「PyPI (pypi.org)」に相当するものが
    各言語に存在する。ツール名・設定ファイル・コマンドを一気に比較する。
    """)

    # ------------------------------------------------------------------
    # 8-1. ツールとリポジトリの全体像
    # ------------------------------------------------------------------
    subsection("8-1. ツールとリポジトリの全体像")

    table(
        ["", "Python", "Go", "Java (Maven)", "Rust"],
        [
            ["パッケージ管理ツール", "pip / uv / poetry",   "go (組み込み)",      "mvn / gradle",        "cargo (組み込み)"],
            ["パッケージリポジトリ", "PyPI (pypi.org)",      "pkg.go.dev (検索)",  "Maven Central",       "crates.io"],
            ["設定ファイル",         "pyproject.toml",       "go.mod",             "pom.xml / build.gradle","Cargo.toml"],
            ["ロックファイル",       "uv.lock / poetry.lock","go.sum",             "pom.xml (バージョン固定)","Cargo.lock"],
            ["インストール先",       "venv / site-packages","$GOPATH/pkg/mod",    "~/.m2/repository",    "~/.cargo/registry"],
        ]
    )

    note("""\
    Go と Rust はツールが言語に組み込まれている。
    Python や Java は「どのツールを使うか」を自分で選ぶ必要がある。
    """)

    # ------------------------------------------------------------------
    # 8-2. よく使うコマンド対応表
    # ------------------------------------------------------------------
    subsection("8-2. よく使うコマンド対応表")

    table(
        ["やりたいこと", "Python (pip/uv)", "Go", "Java (Maven)", "Rust (cargo)"],
        [
            ["パッケージをインストール",
             "pip install requests\nuv add requests",
             "go get github.com/xxx/yyy",
             "pom.xml に追記\n→ mvn install",
             "cargo add serde"],
            ["requirements.txt から一括インストール",
             "pip install -r requirements.txt\nuv sync",
             "go mod download",
             "mvn dependency:resolve",
             "cargo build (自動)"],
            ["パッケージを削除",
             "pip uninstall requests",
             "go mod tidy (未使用を削除)",
             "pom.xml から削除\n→ mvn install",
             "cargo remove serde"],
            ["インストール済み一覧",
             "pip list",
             "go list -m all",
             "mvn dependency:tree",
             "cargo tree"],
            ["パッケージを検索",
             "pip search (廃止→pypi.org)",
             "pkg.go.dev で検索",
             "search.maven.org",
             "cargo search serde"],
            ["バージョンを上げる",
             "pip install -U requests",
             "go get xxx@latest",
             "versions-maven-plugin",
             "cargo update serde"],
            ["未使用の依存を削除",
             "(手動)",
             "go mod tidy",
             "(手動)",
             "cargo machete (外部)"],
            ["仮想環境を作る",
             "python -m venv .venv\nuv venv",
             "(不要: モジュール単位で分離)",
             "(不要: ~/.m2 で共有)",
             "(不要: プロジェクト単位)"],
        ]
    )

    # ------------------------------------------------------------------
    # 8-3. 設定ファイルの書き方比較
    # ------------------------------------------------------------------
    subsection("8-3. 設定ファイルの書き方比較")

    compare(
        python_code="""\
# pyproject.toml (現代的な Python プロジェクトの標準)

[project]
name = "my-app"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.110",
    "pydantic>=2.6",
    "sqlalchemy>=2.0",
    "psycopg2-binary>=2.9",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "mypy>=1.9",
    "ruff>=0.3",
]

# インストール:
#   uv sync            # 全依存をインストール (lockfile 使用)
#   uv sync --dev      # dev 依存も含む
#   pip install -e .   # 開発モード (editable install)
""",

        go_code="""\
// go.mod ── go get / go mod tidy で自動管理

module my-app    // モジュール名 (GitHub URL が慣習)

go 1.22          // 最小 Go バージョン

require (
    github.com/gin-gonic/gin       v1.9.1
    github.com/go-playground/validator/v10 v10.22.0
    github.com/jmoiron/sqlx        v1.3.5
    github.com/lib/pq              v1.10.9   // PostgreSQL ドライバー
)

// 間接依存 (直接使っていないが必要なもの)
require (
    github.com/bytedance/sonic v1.11.3 // indirect
)

// コマンド:
//   go get github.com/gin-gonic/gin   → require に追記 + go.sum 更新
//   go mod tidy                       → 未使用削除 + go.sum 整合
//   go mod download                   → ローカルキャッシュにダウンロード
""",

        java_code="""\
<!-- pom.xml (Maven) -->
<project>
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.example</groupId>
  <artifactId>my-app</artifactId>
  <version>0.0.1-SNAPSHOT</version>

  <parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.2.4</version>  <!-- バージョン管理を親に委譲 -->
  </parent>

  <dependencies>
    <!-- Web + REST -->
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-web</artifactId>
      <!-- version 省略可 → 親 POM が管理 -->
    </dependency>

    <!-- DB -->
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-data-jpa</artifactId>
    </dependency>

    <!-- テスト (scope=test → 本番ビルドに含まれない) -->
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-test</artifactId>
      <scope>test</scope>
    </dependency>
  </dependencies>
</project>

<!-- コマンド:
     mvn install          → 依存ダウンロード + ビルド + テスト
     mvn dependency:tree  → 依存ツリー表示
     mvn versions:display-dependency-updates  → 更新可能なバージョン確認 -->
""",

        rust_code="""\
# Cargo.toml

[package]
name = "my-app"
version = "0.1.0"
edition = "2021"   # Rust エディション (2015/2018/2021)

[dependencies]
axum       = "0.7"
serde      = { version = "1", features = ["derive"] }  # feature フラグで機能選択
serde_json = "1"
sqlx       = { version = "0.7", features = ["postgres", "runtime-tokio"] }
tokio      = { version = "1",   features = ["full"] }
validator  = { version = "0.18", features = ["derive"] }

[dev-dependencies]    # テスト時のみ (Python の optional-dependencies dev と同じ)
tokio-test = "0.4"

[build-dependencies]  # ビルドスクリプト用 (Python にはない概念)
build = "0.1"

# コマンド:
#   cargo add serde --features derive    → Cargo.toml に追記
#   cargo build                          → 依存ダウンロード + ビルド
#   cargo update                         → Cargo.lock を最新に更新
#   cargo tree                           → 依存ツリー表示
""")

    # ------------------------------------------------------------------
    # 8-4. バージョン指定の書き方
    # ------------------------------------------------------------------
    subsection("8-4. バージョン指定の書き方 (Semantic Versioning)")

    note("""\
    バージョン番号は「メジャー.マイナー.パッチ」(例: 2.6.1) の SemVer が標準。
    各言語のバージョン指定記法を比較する。
    """)

    table(
        ["意味", "Python (PEP 440)", "Go", "Java (Maven)", "Rust (Cargo)"],
        [
            ["完全一致",          "==2.6.1",    "v2.6.1 (タグ固定)",    "<version>2.6.1</version>","= \"2.6.1\""],
            ["以上",              ">=2.6",      "v2.6.0 以降は go get", "未対応(範囲指定は別)",    ">= \"2.6\""],
            ["メジャー固定",      "~=2.6 (>=2.6,<3)","(慣習で管理)",   "2.6.x (範囲指定)",       "\"2\" (^2.0.0)"],
            ["マイナー固定",      "~=2.6.1 (>=2.6.1,<2.7)","(go.sum固定)","[2.6.1,2.7)",         "~\"2.6\" (~2.6.0)"],
            ["キャレット (互換)", "(相当なし)",  "-",                    "-",                       "\"2.6\" (^2.6.0)"],
            ["最新を取得",        "pip install X (指定なし)","go get X@latest","LATEST (非推奨)",  "\"*\" (非推奨)"],
        ]
    )

    note("""\
    Rust の Cargo は ^ (キャレット) がデフォルト:
      "1.2.3"  →  ^1.2.3  →  >=1.2.3, <2.0.0  (メジャーバージョンは変えない)
      "0.2.3"  →  ^0.2.3  →  >=0.2.3, <0.3.0  (0.x は マイナーも変えない)
    Go の go.sum はチェックサムを記録して改ざん検知 → Python の hash オプションに相当
    """)

    # ------------------------------------------------------------------
    # 8-5. パッケージリポジトリ詳細
    # ------------------------------------------------------------------
    subsection("8-5. パッケージリポジトリ詳細")

    table(
        ["項目", "PyPI", "pkg.go.dev / GitHub", "Maven Central", "crates.io"],
        [
            ["URL",          "pypi.org",         "pkg.go.dev",          "central.sonatype.com","crates.io"],
            ["登録方法",     "twine upload",     "GitHub に push するだけ","Sonatype OSSRH",   "cargo publish"],
            ["認証",         "APIトークン",      "不要 (GitHub URL = ID)","GPG署名 + 審査",    "APIトークン"],
            ["プライベート", "PyPI 有料 or 自前","GitHub Private Repo",   "Artifactory等",     "Cloudsmith等"],
            ["ミラー",       "devpi (社内)",     "(go env GOPROXY)",      "Nexus/Artifactory",  "(vendoring)"],
            ["検索",         "pypi.org/search",  "pkg.go.dev",            "search.maven.org",  "crates.io/search"],
            ["DL数表示",     "○",                "△ (GitHub stars)",     "○",                  "○"],
            ["メンテ状況",   "○ (更新日)",       "○ (GitHub commits)",   "○",                  "○"],
        ]
    )

    note("""\
    Go が特殊: パッケージリポジトリが存在せず、GitHub (や GitLab) が直接ソース。
      - go get github.com/gin-gonic/gin  → GitHub から直接取得
      - pkg.go.dev は「ドキュメント表示サービス」であって配布元ではない
      - GOPROXY=https://proxy.golang.org がキャッシュ・配信を担う (デフォルト)
    """)

    # ------------------------------------------------------------------
    # 8-6. 社内/オフライン環境での使い方
    # ------------------------------------------------------------------
    subsection("8-6. 社内 / オフライン環境での依存管理")

    table(
        ["手法", "Python", "Go", "Java", "Rust"],
        [
            ["オフラインキャッシュ",
             "pip download → ローカルdir",
             "go mod vendor",
             "mvn dependency:go-offline",
             "cargo vendor"],
            ["社内プロキシ/ミラー",
             "pip --index-url http://内部サーバー",
             "GOPROXY=http://内部サーバー",
             "settings.xml にミラー設定",
             ".cargo/config.toml に [source]"],
            ["ベンダリング (依存をコミット)",
             "vendor/ に copy",
             "go mod vendor → vendor/",
             "(通常しない)",
             "cargo vendor → vendor/"],
        ]
    )

    point("Go の `go mod vendor` はオフライン・セキュリティ審査環境でよく使われる")
    point("Rust の `cargo vendor` も同様。CI で外部通信を禁止する場合に有効")
    point("Java は ~/.m2 をまるごと共有ストレージに置けるのでオフライン対応が容易")
    point("Python は uv の --offline モードや devpi サーバーでオフライン対応できる")


# ============================================================
# 9. 全体まとめ対応表
# ============================================================

def chapter9_summary():
    section("7. 全体まとめ ── Pydantic エコシステム対応表")

    note("""\
    Pydantic が提供する機能を他言語のライブラリと対応させた早見表。
    """)

    table(
        ["Pydantic の機能", "Go", "Java (Spring)", "Rust"],
        [
            ["BaseModel (型定義)",      "struct + json タグ",        "record / class",          "struct + serde"],
            ["バリデーション",           "go-playground/validator",   "Bean Validation (@Valid)", "validator クレート"],
            ["JSON シリアライズ",        "encoding/json",             "Jackson",                 "serde_json"],
            ["フィールド名変換",         "json タグ手書き",            "@JsonNaming",             "#[serde(rename_all)]"],
            ["フィールド除外",           'json:"-"',                  "@JsonIgnore",             "#[serde(skip)]"],
            ["Optional フィールド",     "ポインタ (*T)",              "Optional<T>",             "Option<T>"],
            ["Discriminated Union",     "interface + switch (手動)",  "@JsonTypeInfo",           "enum + #[serde(tag)]"],
            ["pydantic-settings (設定)","caarlos0/env or viper",     "@ConfigurationProperties","config + dotenvy"],
            ["model_dump() → dict",     "json.Marshal → map",        "ObjectMapper.convertValue","serde_json::to_value"],
            ["カスタムバリデーター",     "RegisterValidation()",      "@Constraint カスタム実装","fn validate_xxx()"],
        ]
    )

    note("""\
    どの言語でも「データモデル」「バリデーション」「シリアライズ」の3つは
    必ず必要になる。Python/Pydantic はこの3つを1つのライブラリで担う。
    他言語は専用ライブラリを組み合わせる設計になっている。
    """)

    point("Python/Pydantic: 最も少ない記述量・最速のプロトタイピング")
    point("Go: シンプルだが verbosity が高い。大規模チームでは読みやすさが武器")
    point("Java/Spring: アノテーション駆動で宣言的。エンタープライズで実績多数")
    point("Rust: 型システムが最も強力。バリデーション漏れをコンパイル時に検出可能")


# ============================================================
# メイン
# ============================================================

def main():
    print()
    print("=" * 76)
    print("  lang_comparison_pydantic.py")
    print("  Python (Pydantic) を起点に Go / Java / Rust を対比する")
    print("=" * 76)
    print()
    print("  題材: ユーザー管理 API の典型パターン")
    print("  構成: Python コード → Go → Java → Rust の順で並べて比較")
    print()

    chapter1_model_definition()
    chapter2_nested_models()
    chapter3_config()
    chapter4_api_endpoint()
    chapter5_error_handling()
    chapter6_serialization()
    chapter7_imports()
    chapter8_package_management()
    chapter9_summary()

    print()
    print("=" * 76)
    print("  完了! 各言語の公式ドキュメント:")
    print("    Python : https://docs.pydantic.dev/")
    print("    Go     : https://pkg.go.dev/encoding/json")
    print("    Java   : https://jakarta.ee/specifications/bean-validation/")
    print("    Rust   : https://serde.rs/")
    print("=" * 76)
    print()


if __name__ == "__main__":
    main()
