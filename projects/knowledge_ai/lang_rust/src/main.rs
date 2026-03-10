// =============================================================================
// Rust Key-Value Store CLI
// Rust の所有権・型システム・トレイト・パターンマッチングを体系的に学ぶ
// =============================================================================

use std::collections::{BTreeMap, HashMap};
use std::fmt;

// =============================================================================
// モジュール: カスタムエラー型
// - mod で単一ファイル内にモジュールを定義できる
// - pub で外部に公開
// =============================================================================
mod error {
    use std::fmt;

    // --- derive マクロ: コンパイラが自動実装を生成 ---
    // Debug: {:?} でデバッグ出力
    // Clone: .clone() で複製
    // PartialEq: == で比較
    #[derive(Debug, Clone, PartialEq)]
    pub enum KvError {
        // --- Enum with data: 各バリアントがデータを持てる ---
        KeyNotFound(String),
        EmptyKey,
        InvalidCommand(String),
        ParseError(String),
    }

    // --- Display トレイト: ユーザー向けの表示を実装 ---
    // fmt::Display を実装すると .to_string() も自動で使える
    impl fmt::Display for KvError {
        fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
            // --- パターンマッチング: 全バリアントを網羅 ---
            // Rust は match が網羅的でないとコンパイルエラー（安全性の保証）
            match self {
                KvError::KeyNotFound(key) => write!(f, "キーが見つかりません: '{}'", key),
                KvError::EmptyKey => write!(f, "キーが空です"),
                KvError::InvalidCommand(cmd) => write!(f, "無効なコマンド: '{}'", cmd),
                KvError::ParseError(msg) => write!(f, "パースエラー: {}", msg),
            }
        }
    }

    // --- From トレイト: 型変換を定義 ---
    // これにより ? 演算子で自動変換ができる
    impl From<std::num::ParseIntError> for KvError {
        fn from(e: std::num::ParseIntError) -> Self {
            KvError::ParseError(e.to_string())
        }
    }

    impl From<std::num::ParseFloatError> for KvError {
        fn from(e: std::num::ParseFloatError) -> Self {
            KvError::ParseError(e.to_string())
        }
    }
}

// モジュールから型をインポート
use error::KvError;

// 型エイリアス: Result の E を固定して簡潔に書ける
type KvResult<T> = Result<T, KvError>;

// =============================================================================
// 値の型: Enum with data
// - Rust の enum は代数的データ型（Tagged Union）
// - null は存在しない。代わりに Option<T> を使う
// =============================================================================
#[derive(Debug, Clone, PartialEq)]
enum Value {
    Text(String),
    Integer(i64),
    Float(f64),
    Bool(bool),
}

// --- impl ブロック: 型にメソッドを定義 ---
impl Value {
    // --- 関連関数 (associated function): Self を取らない ---
    // Python の classmethod / Java の static method に相当
    // Value::parse("42") のように :: で呼ぶ
    fn parse(input: &str) -> Self {
        // --- if let: 一つのパターンだけ試す簡潔な構文 ---
        if let Ok(n) = input.parse::<i64>() {
            return Value::Integer(n);
        }
        if let Ok(f) = input.parse::<f64>() {
            return Value::Float(f);
        }
        match input.to_lowercase().as_str() {
            "true" => Value::Bool(true),
            "false" => Value::Bool(false),
            _ => Value::Text(input.to_string()),
        }
    }

    // --- &self: 不変借用（読み取り専用） ---
    // 所有権を移動せずに値を参照する
    fn type_name(&self) -> &str {
        // --- &str を返す: 静的な文字列スライス ---
        // String は所有権のあるヒープ文字列
        // &str は借用された文字列スライス（ポインタ＋長さ）
        match self {
            Value::Text(_) => "Text",
            Value::Integer(_) => "Integer",
            Value::Float(_) => "Float",
            Value::Bool(_) => "Bool",
        }
    }
}

// --- Display トレイト実装 ---
impl fmt::Display for Value {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Value::Text(s) => write!(f, "\"{}\"", s),
            Value::Integer(n) => write!(f, "{}", n),
            Value::Float(v) => write!(f, "{:.2}", v),
            Value::Bool(b) => write!(f, "{}", b),
        }
    }
}

// =============================================================================
// トレイト: Storage（インタフェースに相当）
// - Java の interface / Python の ABC に近い
// - ジェネリクス: <V> で値の型をパラメータ化
// =============================================================================
trait Storage<V> {
    fn store(&mut self, key: String, value: V) -> Option<V>;
    fn retrieve(&self, key: &str) -> Option<&V>;
    fn remove(&mut self, key: &str) -> Option<V>;
    fn keys(&self) -> Vec<&str>;
    fn len(&self) -> usize;
    fn is_empty(&self) -> bool {
        // --- デフォルト実装: トレイトにデフォルトメソッドを持てる ---
        self.len() == 0
    }
}

// =============================================================================
// KVStore 構造体
// - HashMap: O(1) のキー検索（順序なし）
// - BTreeMap: O(log n) のキー検索（キーがソート済み）
// =============================================================================
#[derive(Debug)]
struct KvStore {
    // --- HashMap<String, Value>: キーが String, 値が Value ---
    // String を使う = KvStore がキーの所有権を持つ
    data: HashMap<String, Value>,
    // --- BTreeMap: 操作ログをソート順で保持 ---
    history: BTreeMap<u64, String>,
    op_count: u64,
}

impl KvStore {
    // --- 関連関数 ::new(): コンストラクタの慣習 ---
    fn new() -> Self {
        Self {
            data: HashMap::new(),
            history: BTreeMap::new(),
            op_count: 0,
        }
    }

    // --- &mut self: 可変借用（読み書き可能） ---
    // Rust のルール: 可変借用は同時に1つだけ（データ競合を防止）
    fn record(&mut self, operation: String) {
        self.op_count += 1;
        self.history.insert(self.op_count, operation);
    }
}

// --- Storage トレイトを KvStore に実装 ---
impl Storage<Value> for KvStore {
    // --- 所有権の移動 (move): key と value の所有権が KvStore に移る ---
    // 呼び出し元は key, value を使えなくなる（use-after-free を防止）
    fn store(&mut self, key: String, value: Value) -> Option<Value> {
        // HashMap::insert は既存の値を Option<V> で返す
        let old = self.data.insert(key.clone(), value);
        self.record(format!("SET {}", key));
        old
    }

    // --- &self で不変借用、Option<&V> で値への参照を返す ---
    // 値の所有権は KvStore が保持したまま。呼び出し元は読むだけ
    fn retrieve(&self, key: &str) -> Option<&Value> {
        self.data.get(key)
    }

    // --- remove: 所有権を呼び出し元に返す ---
    fn remove(&mut self, key: &str) -> Option<Value> {
        let removed = self.data.remove(key);
        self.record(format!("DEL {}", key));
        removed
    }

    // --- イテレータ: map + collect で変換 ---
    fn keys(&self) -> Vec<&str> {
        // .keys() -> イテレータ
        // .map(|k| k.as_str()) -> String を &str に変換するクロージャ
        // .collect() -> イテレータから Vec を構築
        self.data.keys().map(|k| k.as_str()).collect()
    }

    fn len(&self) -> usize {
        self.data.len()
    }
}

// =============================================================================
// ライフタイム注釈
// - 参照が有効な期間をコンパイラに伝える
// - 'a は「この構造体は 'a の間だけ生きる」という意味
// =============================================================================
#[derive(Debug)]
struct StoreView<'a> {
    // --- &'a KvStore: KvStore への参照。KvStore が 'a の間有効であることを保証 ---
    store: &'a KvStore,
    label: &'a str,
}

impl<'a> StoreView<'a> {
    fn new(store: &'a KvStore, label: &'a str) -> Self {
        Self { store, label }
    }

    // --- 戻り値のライフタイムが self と同じ 'a ---
    // StoreView が生きている間だけ有効な参照を返せる
    fn summary(&self) -> String {
        format!(
            "[{}] エントリ数: {}, 操作数: {}",
            self.label,
            self.store.data.len(),
            self.store.op_count
        )
    }
}

impl<'a> fmt::Display for StoreView<'a> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.summary())
    }
}

// =============================================================================
// ジェネリック関数
// - <T: fmt::Display> は「Display トレイトを実装している任意の型 T」
// - トレイト境界 (trait bound) でジェネリクスの能力を制約
// =============================================================================
fn print_items<T: fmt::Display>(items: &[T], header: &str) {
    println!("--- {} ---", header);
    if items.is_empty() {
        println!("  (なし)");
        return;
    }
    for (i, item) in items.iter().enumerate() {
        println!("  [{}] {}", i + 1, item);
    }
}

// --- 複数のトレイト境界: where 句で読みやすく書ける ---
fn find_matching<T>(items: &[T], predicate: &dyn Fn(&T) -> bool) -> Vec<&T>
where
    T: fmt::Debug,
{
    // --- イテレータチェーン: filter + collect ---
    items.iter().filter(|item| predicate(item)).collect()
}

// =============================================================================
// コマンドパーサー
// =============================================================================
#[derive(Debug)]
enum Command {
    Set(String, String),
    Get(String),
    Delete(String),
    List,
    Filter(String),
    Stats,
    Help,
    Quit,
}

// --- &str からのパース: String vs &str の違いを活用 ---
// &str: 借用。パース中だけ参照すればよい
// String: 所有。コマンドに格納するときは所有権が必要
fn parse_command(input: &str) -> KvResult<Command> {
    // --- trim() は &str を返す（新しい String を作らない、ゼロコスト） ---
    let input = input.trim();
    if input.is_empty() {
        return Err(KvError::InvalidCommand("空のコマンド".into()));
    }

    // --- splitn: 最大 n 個に分割 ---
    let parts: Vec<&str> = input.splitn(3, ' ').collect();

    match parts[0].to_uppercase().as_str() {
        "SET" => {
            if parts.len() < 3 {
                Err(KvError::InvalidCommand("使い方: SET <key> <value>".into()))
            } else {
                // --- .to_string(): &str -> String に変換（所有権を作る） ---
                Ok(Command::Set(parts[1].to_string(), parts[2].to_string()))
            }
        }
        "GET" => {
            if parts.len() < 2 {
                Err(KvError::InvalidCommand("使い方: GET <key>".into()))
            } else {
                Ok(Command::Get(parts[1].to_string()))
            }
        }
        "DEL" | "DELETE" => {
            if parts.len() < 2 {
                Err(KvError::InvalidCommand("使い方: DEL <key>".into()))
            } else {
                Ok(Command::Delete(parts[1].to_string()))
            }
        }
        "LIST" | "LS" => Ok(Command::List),
        "FILTER" => {
            if parts.len() < 2 {
                Err(KvError::InvalidCommand("使い方: FILTER <type>".into()))
            } else {
                Ok(Command::Filter(parts[1].to_string()))
            }
        }
        "STATS" => Ok(Command::Stats),
        "HELP" | "?" => Ok(Command::Help),
        "QUIT" | "EXIT" | "Q" => Ok(Command::Quit),
        other => Err(KvError::InvalidCommand(other.to_string())),
    }
}

// =============================================================================
// コマンド実行
// - Result + ? 演算子でエラー伝播
// =============================================================================
fn execute(store: &mut KvStore, cmd: Command) -> KvResult<String> {
    match cmd {
        // --- 所有権の移動: key, val_str は Command から move される ---
        Command::Set(key, val_str) => {
            if key.is_empty() {
                return Err(KvError::EmptyKey);
            }
            let value = Value::parse(&val_str);
            let msg = match store.store(key.clone(), value.clone()) {
                Some(old) => format!("更新: {} = {} (旧値: {})", key, value, old),
                None => format!("追加: {} = {}", key, value),
            };
            Ok(msg)
        }

        Command::Get(key) => {
            // --- Option を match: null チェックの代わり ---
            // Rust に null は存在しない。Option::None が「値なし」を表現
            match store.retrieve(&key) {
                Some(value) => Ok(format!("{} = {} ({})", key, value, value.type_name())),
                None => Err(KvError::KeyNotFound(key)),
            }
        }

        Command::Delete(key) => match store.remove(&key) {
            Some(value) => Ok(format!("削除: {} (値: {})", key, value)),
            None => Err(KvError::KeyNotFound(key)),
        },

        Command::List => {
            let mut keys = store.keys();
            keys.sort();
            if keys.is_empty() {
                return Ok("ストアは空です".to_string());
            }
            let mut output = format!("全 {} 件:\n", keys.len());
            for key in &keys {
                // --- .unwrap(): Option を強制展開 ---
                // キーが存在することが保証されているので安全
                let val = store.retrieve(key).unwrap();
                output.push_str(&format!("  {} = {} [{}]\n", key, val, val.type_name()));
            }
            Ok(output.trim_end().to_string())
        }

        // --- クロージャ: |v| はクロージャ（無名関数） ---
        // Fn: 環境を不変借用するクロージャ
        // FnMut: 環境を可変借用するクロージャ
        // FnOnce: 環境を消費するクロージャ（一度だけ呼べる）
        Command::Filter(type_name) => {
            // --- filter + map + collect: イテレータパイプライン ---
            let filtered: Vec<String> = store
                .data
                .iter()
                .filter(|(_, v)| {
                    // --- クロージャが環境から type_name を不変借用 (Fn) ---
                    v.type_name().to_lowercase() == type_name.to_lowercase()
                })
                .map(|(k, v)| format!("  {} = {}", k, v))
                .collect();

            if filtered.is_empty() {
                Ok(format!("型 '{}' のエントリはありません", type_name))
            } else {
                Ok(format!(
                    "型 '{}' のエントリ ({} 件):\n{}",
                    type_name,
                    filtered.len(),
                    filtered.join("\n")
                ))
            }
        }

        Command::Stats => {
            // --- fold: イテレータを畳み込み（reduce） ---
            // (text数, int数, float数, bool数) のタプルに集約
            let (texts, ints, floats, bools) = store.data.values().fold(
                (0u32, 0u32, 0u32, 0u32),
                |(t, i, f, b), val| match val {
                    Value::Text(_) => (t + 1, i, f, b),
                    Value::Integer(_) => (t, i + 1, f, b),
                    Value::Float(_) => (t, i, f + 1, b),
                    Value::Bool(_) => (t, i, f, b + 1),
                },
            );

            // --- 整数の合計を Option で安全に計算 ---
            let int_sum: Option<i64> = {
                let ints_vec: Vec<i64> = store
                    .data
                    .values()
                    .filter_map(|v| match v {
                        // --- filter_map: filter + map を一度に ---
                        Value::Integer(n) => Some(*n),
                        _ => None,
                    })
                    .collect();
                if ints_vec.is_empty() {
                    None
                } else {
                    Some(ints_vec.iter().sum())
                }
            };

            let mut output = format!(
                "統計:\n  合計エントリ: {}\n  Text: {}, Integer: {}, Float: {}, Bool: {}\n  操作回数: {}",
                store.len(), texts, ints, floats, bools, store.op_count
            );

            // --- if let: Option のパターンマッチ（Some の時だけ処理） ---
            if let Some(sum) = int_sum {
                output.push_str(&format!("\n  整数合計: {}", sum));
            }

            // --- while let の例（履歴の末尾3件を取得） ---
            let recent: Vec<&String> = store.history.values().rev().take(3).collect();
            if !recent.is_empty() {
                output.push_str("\n  最近の操作:");
                // while let は iter.next() のパターンに使える
                let mut iter = recent.iter();
                while let Some(op) = iter.next() {
                    output.push_str(&format!("\n    - {}", op));
                }
            }

            Ok(output)
        }

        Command::Help => Ok(
            "コマンド一覧:\n  SET <key> <value>  - 値を設定\n  GET <key>          - 値を取得\n  DEL <key>          - 値を削除\n  LIST               - 全エントリ表示\n  FILTER <type>      - 型でフィルタ (Text/Integer/Float/Bool)\n  STATS              - 統計情報\n  HELP               - このヘルプ\n  QUIT               - 終了"
                .to_string(),
        ),

        Command::Quit => Ok("終了します".to_string()),
    }
}

// =============================================================================
// デモシーケンス
// - 全機能を一通り実行して Rust の概念を実演
// =============================================================================
fn run_demo() -> KvResult<()> {
    println!("========================================");
    println!(" Rust Key-Value Store デモ");
    println!("========================================\n");

    let mut store = KvStore::new();

    // --- 1. 所有権と移動 ---
    println!("[1] 所有権と移動 (Ownership & Move)");
    println!("----");
    let key = String::from("name");
    let val = String::from("Rust");
    // key, val の所有権が execute に移る
    let cmd = Command::Set(key, val);
    // ここで key, val はもう使えない（コンパイルエラーになる）
    // println!("{}", key); // <- これはコンパイルエラー！
    let result = execute(&mut store, cmd)?; // ? でエラー伝播
    println!("  {}\n", result);

    // --- 2. 借用 ---
    println!("[2] 借用 (Borrowing)");
    println!("----");
    // &store: 不変借用。store の中身を読めるが変更できない
    let view = StoreView::new(&store, "デモビュー");
    println!("  {}", view); // Display トレイトで表示
    // store はまだ使える（借用しただけで所有権は移動していない）
    println!("  store.len() = {}\n", store.len());

    // --- 3. 複数の SET ---
    println!("[3] データ投入");
    println!("----");
    let entries = vec![
        ("age", "30"),
        ("score", "95.5"),
        ("active", "true"),
        ("city", "Tokyo"),
        ("level", "42"),
        ("rate", "3.14"),
    ];
    for (k, v) in &entries {
        let cmd = Command::Set(k.to_string(), v.to_string());
        let result = execute(&mut store, cmd)?;
        println!("  {}", result);
    }
    println!();

    // --- 4. パターンマッチング ---
    println!("[4] パターンマッチング (Pattern Matching)");
    println!("----");
    let test_keys = vec!["name", "unknown", "age"];
    for key in test_keys {
        let cmd = Command::Get(key.to_string());
        // --- match on Result: Ok/Err の両方を処理 ---
        match execute(&mut store, cmd) {
            Ok(msg) => println!("  OK: {}", msg),
            Err(e) => println!("  Err: {}", e),
        }
    }
    println!();

    // --- 5. イテレータとクロージャ ---
    println!("[5] イテレータとクロージャ (Iterator & Closure)");
    println!("----");
    let cmd = Command::Filter("Integer".to_string());
    println!("  {}", execute(&mut store, cmd)?);
    println!();

    let cmd = Command::Filter("Text".to_string());
    println!("  {}", execute(&mut store, cmd)?);
    println!();

    // --- 6. ジェネリック関数 ---
    println!("[6] ジェネリック関数 (Generics)");
    println!("----");
    let numbers = vec![10, 20, 30, 40, 50];
    print_items(&numbers, "数値リスト");

    let words = vec!["Rust", "は", "安全"];
    print_items(&words, "文字列リスト");

    // --- find_matching: ジェネリクス + クロージャ ---
    let big: Vec<&&i32> = find_matching(&numbers, &|n| **n > 25);
    println!("  25 より大きい値: {:?}", big);
    println!();

    // --- 7. 統計（fold, filter_map） ---
    println!("[7] 統計 (fold / filter_map)");
    println!("----");
    let cmd = Command::Stats;
    println!("  {}", execute(&mut store, cmd)?);
    println!();

    // --- 8. 削除と Option ---
    println!("[8] 削除と Option");
    println!("----");
    let cmd = Command::Delete("city".to_string());
    println!("  {}", execute(&mut store, cmd)?);
    // 存在しないキーの削除
    let cmd = Command::Delete("ghost".to_string());
    match execute(&mut store, cmd) {
        Ok(msg) => println!("  {}", msg),
        Err(e) => println!("  期待通りのエラー: {}", e),
    }
    println!();

    // --- 9. リスト表示 ---
    println!("[9] 全エントリ一覧 (LIST)");
    println!("----");
    let cmd = Command::List;
    println!("  {}", execute(&mut store, cmd)?);
    println!();

    // --- 10. ライフタイムの実演 ---
    println!("[10] ライフタイム (Lifetimes)");
    println!("----");
    {
        // view は store への参照を保持
        // store が先にドロップされると view は無効になる
        // Rust はこれをコンパイル時に検出する
        let view = StoreView::new(&store, "最終ビュー");
        println!("  {}", view.summary());
    }
    // view はスコープを抜けてドロップ済み。store はまだ有効
    println!("  store は有効: {} エントリ\n", store.len());

    // --- 11. String vs &str ---
    println!("[11] String vs &str");
    println!("----");
    let owned: String = String::from("所有された文字列"); // ヒープ上、可変、所有権あり
    let borrowed: &str = "借用された文字列"; // スタック上のポインタ、不変
    let slice: &str = &owned[..6]; // String のスライス（部分参照）
    println!("  String (所有): {}", owned);
    println!("  &str (借用):   {}", borrowed);
    println!("  スライス:      {}", slice);
    println!();

    // --- 12. エラーハンドリングまとめ ---
    println!("[12] エラーハンドリング (? operator / From trait)");
    println!("----");
    let bad_commands = vec!["", "UNKNOWN", "SET", "GET"];
    for input in bad_commands {
        match parse_command(input) {
            Ok(cmd) => println!("  パース成功: {:?}", cmd),
            Err(e) => println!("  エラー捕捉: {}", e),
        }
    }
    println!();

    println!("========================================");
    println!(" デモ完了！");
    println!(" Rust はコンパイル時に以下を防ぎます:");
    println!("   - null参照 (Option<T> で安全に処理)");
    println!("   - データ競合 (所有権 + 借用ルール)");
    println!("   - use-after-free (ライフタイム検査)");
    println!("   - パターンの漏れ (網羅性チェック)");
    println!("========================================");

    Ok(())
}

// =============================================================================
// メイン関数
// - Result を返すことで ? 演算子が使える
// =============================================================================
fn main() {
    if let Err(e) = run_demo() {
        eprintln!("エラー: {}", e);
        std::process::exit(1);
    }
}
