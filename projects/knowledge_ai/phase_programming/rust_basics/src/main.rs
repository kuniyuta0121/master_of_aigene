// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Rust 基礎学習 - Pythonエンジニアのための Rust 入門
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//
// Rust を学ぶ最大の理由:
//   1. メモリ安全性をコンパイル時に保証 (GCなしで!)
//   2. C/C++ 並の速度で Python の 10〜100 倍速い
//   3. WebAssembly, CLI, サーバー, 組み込みなど用途が広い
//   4. 所有権という概念を理解するとプログラミング全般の理解が深まる
//
// 実行方法: cargo run
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

use std::collections::HashMap;
use std::io::{BufRead, BufReader, Write};
use std::net::TcpListener;
use std::sync::{mpsc, Arc, Mutex};
use std::thread;
use std::time::Instant;

fn main() {
    println!("========================================");
    println!("  Rust 基礎学習デモ");
    println!("========================================\n");

    // 各セクションのデモを順番に実行
    demo_ownership();
    demo_pattern_matching();
    demo_traits();
    demo_concurrency();
    demo_performance();

    // HTTPサーバーは最後に起動（Ctrl+C で停止）
    println!("\n========================================");
    println!("  HTTP サーバーを起動しますか？");
    println!("  起動する場合は cargo run -- server");
    println!("========================================");

    let args: Vec<String> = std::env::args().collect();
    if args.len() > 1 && args[1] == "server" {
        demo_http_server();
    }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// セクション A: 所有権 (Ownership) - Rust 最重要概念
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//
// Python との決定的な違い:
//   Python: すべてが参照カウントで管理。GC がメモリを回収。
//   Rust:   各値には「所有者」が1つだけ。所有者がスコープを抜けると自動解放。
//
// なぜこれが重要か:
//   - GC なし = 予測可能なパフォーマンス (リアルタイム処理に最適)
//   - コンパイル時にメモリバグを検出 = 実行時エラーが激減
//   - データ競合をコンパイル時に防止 = 安全な並行処理
//
// [考えてほしい疑問] Python で大量のオブジェクトを作成するとGCが走り、
// 一時的にプログラムが止まることがある。Rust ではなぜこの問題がないのか？

fn demo_ownership() {
    println!("--- セクション A: 所有権 (Ownership) ---\n");

    // ■ 基本: 所有権の移動 (Move)
    // Python では代入は参照のコピー。Rust では所有権が「移動」する。
    //
    // Python の場合:
    //   a = [1, 2, 3]
    //   b = a        # a も b も同じリストを指す
    //   print(a)     # 問題なく動く
    //
    // Rust の場合:
    let a = String::from("hello");
    let b = a; // 所有権が a から b に移動 (move)
    // ここで println!("{}", a); とするとコンパイルエラー！
    // a はもう使えない。これが Rust の安全性の根幹。
    println!("  move後の b: {}", b);

    // ■ なぜ move が必要か？
    // もし a と b が同じメモリを指していたら、どちらかが解放した後に
    // もう一方がアクセスすると「use-after-free」バグが発生する。
    // Rust は所有者を1つに限定することでこれを防ぐ。

    // ■ Clone: 明示的なコピー
    // 本当にコピーしたい場合は clone() を使う。
    let c = String::from("world");
    let d = c.clone(); // ヒープデータの深いコピー
    println!("  clone: c={}, d={}", c, d);

    // ■ Copy トレイト: スタック上のデータは自動コピー
    // i32, f64, bool などプリミティブ型は Copy トレイトを持つ。
    // これらは move ではなくコピーされる。
    let x = 42;
    let y = x; // コピーされる (move ではない)
    println!("  Copy型: x={}, y={}", x, y);

    // ■ 借用 (Borrowing): 所有権を移さずにデータにアクセス
    //
    // Python では関数に渡しても参照が共有されるだけ。
    // Rust では関数に渡すと所有権が移動してしまう。
    // 「借りる」仕組みが borrowing。
    let s = String::from("Rust");

    // 不変の借用 (&T): 読み取り専用。何個でも同時に存在可能。
    let len = calculate_length(&s);
    println!("  借用: '{}'の長さ = {}", s, len); // s はまだ使える！

    // 可変の借用 (&mut T): 書き換え可能。ただし同時に1つだけ。
    let mut greeting = String::from("Hello");
    append_world(&mut greeting);
    println!("  可変借用: {}", greeting);

    // ■ 借用のルール (コンパイラが強制):
    //   1. 不変参照 (&T) はいくつでも同時に存在可能
    //   2. 可変参照 (&mut T) は同時に1つだけ
    //   3. 不変参照と可変参照は同時に存在できない
    //
    // [考えてほしい疑問] なぜ可変参照を1つに制限するのか？
    // ヒント: 2つのスレッドが同時に同じデータを書き換えたら何が起きる？

    // ■ ライフタイム (Lifetime) の基礎
    // 参照が有効な期間をコンパイラが追跡する仕組み。
    // 多くの場合は推論されるが、明示が必要な場合もある。
    let result;
    {
        let string1 = String::from("long string");
        let string2 = "xyz";
        result = longest(string1.as_str(), string2);
        println!("  ライフタイム: 最長文字列 = {}", result);
    }
    // result は string1 と同じスコープ内で使ったので安全。

    println!();
}

// 不変借用を受け取る関数。所有権は移動しない。
fn calculate_length(s: &str) -> usize {
    s.len()
    // s はここでスコープを抜けるが、所有権を持っていないので何も起きない
}

// 可変借用を受け取る関数。元のデータを変更できる。
fn append_world(s: &mut String) {
    s.push_str(", World!");
}

// ■ ライフタイム注釈 ('a)
// 「返り値の参照は、引数と同じ期間だけ有効」ということをコンパイラに伝える。
// Python にはこの概念がない。Python は GC があるので参照の有効期間を気にしなくていい。
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() {
        x
    } else {
        y
    }
}

// [実装してみよう]
// 1. 構造体に String フィールドを持たせ、所有権の移動を体験してみよう
// 2. 関数が &self と &mut self を受け取るメソッドを書いてみよう
// 3. ダングリング参照（無効な参照）を作ろうとしてコンパイルエラーを体験しよう

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// セクション B: パターンマッチング - Python の match より遥かに強力
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//
// Rust の enum は「代数的データ型 (Algebraic Data Type)」。
// Python の Enum とは全くの別物。各バリアントがデータを持てる。
//
// [考えてほしい疑問] Python で None チェックを忘れて NoneType エラーが出た経験は？
// Rust では Option<T> によりこの問題がコンパイル時に解決される。

// ■ enum: データを持てる列挙型
#[derive(Debug)]
enum Shape {
    Circle(f64),                    // 半径を持つ
    Rectangle(f64, f64),            // 幅と高さを持つ
    Triangle { base: f64, height: f64 }, // 名前付きフィールドも可
}

// ■ Option<T>: null を型レベルで排除
// Python: value = get_user(id)  # None かもしれない。チェックを忘れるとバグ。
// Rust:   Option<T> = Some(値) | None  # 使う前にマッチが必須。
fn find_user(id: u32) -> Option<String> {
    match id {
        1 => Some(String::from("Alice")),
        2 => Some(String::from("Bob")),
        _ => None,
    }
}

// ■ Result<T, E>: 例外を使わないエラー処理
// Python: try/except で実行時にエラーを捕捉
// Rust:   Result<T, E> で戻り値としてエラーを返す。処理を強制される。
//
// Python の try/except の問題点:
//   - except Exception: で雑にキャッチしがち
//   - どの関数がどんな例外を投げるか型情報がない
//   - エラーハンドリングを忘れても コンパイルは通る
//
// Rust の Result の利点:
//   - エラーの可能性が型に表現される
//   - 処理しないとコンパイラが警告
//   - ? 演算子で簡潔にエラーを伝播
#[derive(Debug)]
enum ParseError {
    InvalidFormat,
    OutOfRange,
}

fn parse_age(input: &str) -> Result<u8, ParseError> {
    match input.parse::<u8>() {
        Ok(age) if age <= 150 => Ok(age),
        Ok(_) => Err(ParseError::OutOfRange),
        Err(_) => Err(ParseError::InvalidFormat),
    }
}

fn demo_pattern_matching() {
    println!("--- セクション B: パターンマッチング ---\n");

    // ■ enum + match
    let shapes = vec![
        Shape::Circle(5.0),
        Shape::Rectangle(4.0, 6.0),
        Shape::Triangle { base: 3.0, height: 8.0 },
    ];

    for shape in &shapes {
        let area = match shape {
            Shape::Circle(r) => std::f64::consts::PI * r * r,
            Shape::Rectangle(w, h) => w * h,
            Shape::Triangle { base, height } => base * height / 2.0,
            // match は全パターンを網羅しなければコンパイルエラー！
            // Python の match にはこの保証がない。
        };
        println!("  {:?} の面積 = {:.2}", shape, area);
    }

    // ■ Option<T> の使い方
    // Python: if user is not None: ...
    // Rust:   match / if let / unwrap_or
    println!();
    for id in 1..=3 {
        match find_user(id) {
            Some(name) => println!("  ユーザーID {}: {}", id, name),
            None => println!("  ユーザーID {}: 見つかりません", id),
        }
    }

    // if let: 1つのパターンだけ処理したい場合の簡潔な書き方
    if let Some(name) = find_user(1) {
        println!("  if let: {} を発見", name);
    }

    // unwrap_or: デフォルト値を指定
    let name = find_user(99).unwrap_or(String::from("ゲスト"));
    println!("  unwrap_or: {}", name);

    // ■ Result<T, E> の使い方
    println!();
    let test_inputs = vec!["25", "abc", "200"];
    for input in test_inputs {
        match parse_age(input) {
            Ok(age) => println!("  parse_age(\"{}\"): 年齢 = {}", input, age),
            Err(ParseError::InvalidFormat) => {
                println!("  parse_age(\"{}\"): 形式エラー", input)
            }
            Err(ParseError::OutOfRange) => {
                println!("  parse_age(\"{}\"): 範囲外", input)
            }
        }
    }

    // ■ ? 演算子: エラーを簡潔に伝播
    // Python: 例外は自動的に上位に伝播する
    // Rust:   ? を付けると Err の場合に即座に return Err(...) する
    fn process_input(input: &str) -> Result<String, ParseError> {
        let age = parse_age(input)?; // エラーなら即 return
        Ok(format!("{}歳のユーザーを処理しました", age))
    }

    println!("  ? 演算子: {:?}", process_input("30"));
    println!("  ? 演算子: {:?}", process_input("abc"));

    println!();
}

// [実装してみよう]
// 1. 独自の enum を作って match で網羅的にハンドリングしてみよう
// 2. Result を返す関数を3つチェーンして ? 演算子で繋いでみよう
// 3. Option の map, and_then, filter メソッドを試してみよう

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// セクション C: 型システム - トレイト (Trait)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//
// Python との比較:
//   Python: Protocol / ABC (抽象基底クラス) で型のインターフェースを定義
//   Rust:   trait で型が持つべき振る舞いを定義
//
// 決定的な違い:
//   Python の Protocol/ABC は実行時チェック（型ヒントは任意）
//   Rust の trait はコンパイル時にチェック（違反は絶対にコンパイルが通らない）
//
// [考えてほしい疑問] Python で duck typing に頼りすぎて、
// 予期しないメソッド呼び出しでクラッシュした経験は？

// ■ trait の定義と実装
trait Summary {
    // 必須メソッド: 実装側が必ず定義する
    fn summarize(&self) -> String;

    // デフォルト実装: オーバーライド可能
    fn preview(&self) -> String {
        format!("{}...", &self.summarize()[..20.min(self.summarize().len())])
    }
}

// ■ 構造体に trait を実装
#[derive(Debug)]
struct Article {
    title: String,
    author: String,
    content: String,
}

impl Summary for Article {
    fn summarize(&self) -> String {
        format!("{} (著者: {})", self.title, self.author)
    }
}

#[derive(Debug)]
struct Tweet {
    username: String,
    text: String,
}

impl Summary for Tweet {
    fn summarize(&self) -> String {
        format!("@{}: {}", self.username, self.text)
    }
}

// ■ トレイト境界 (Trait Bounds): ジェネリクスに制約を付ける
// Python: def notify(item: Summarizable) -> None:  # 実行時まで保証なし
// Rust:   fn notify(item: &impl Summary)            # コンパイル時に保証
fn notify(item: &impl Summary) {
    println!("  通知: {}", item.summarize());
}

// ジェネリクス + トレイト境界 (より明示的な書き方)
fn notify_all<T: Summary>(items: &[T]) {
    for item in items {
        println!("  一括通知: {}", item.summarize());
    }
}

// 複数のトレイト境界
// Python: def process(item: Displayable & Summarizable)  # 3.12+ の交差型
// Rust:   fn process(item: &(impl Summary + std::fmt::Debug))
fn describe(item: &(impl Summary + std::fmt::Debug)) {
    println!("  Debug: {:?}", item);
    println!("  Summary: {}", item.summarize());
}

// ■ derive マクロ: よく使うトレイトの自動実装
// #[derive(Debug)]       -> println!("{:?}", x) で表示可能に
// #[derive(Clone)]       -> .clone() でコピー可能に
// #[derive(PartialEq)]   -> == で比較可能に
// #[derive(Hash)]        -> HashMap のキーに使用可能に
//
// Python の __repr__, __eq__, __hash__ を自動生成するようなもの

fn demo_traits() {
    println!("--- セクション C: トレイト (Trait) ---\n");

    let article = Article {
        title: String::from("Rust入門"),
        author: String::from("山田太郎"),
        content: String::from("Rustは素晴らしい言語です..."),
    };

    let tweet = Tweet {
        username: String::from("rustacean"),
        text: String::from("Rust最高！"),
    };

    // トレイトメソッドの呼び出し
    println!("  記事: {}", article.summarize());
    println!("  ツイート: {}", tweet.summarize());

    // トレイト境界を使った関数
    println!();
    notify(&article);
    notify(&tweet);

    // ジェネリクスでの一括処理
    println!();
    let tweets = vec![
        Tweet {
            username: String::from("user1"),
            text: String::from("Hello Rust!"),
        },
        Tweet {
            username: String::from("user2"),
            text: String::from("Traits are powerful"),
        },
    ];
    notify_all(&tweets);

    // 複数トレイト境界
    println!();
    describe(&article);

    println!();
}

// [実装してみよう]
// 1. Display トレイトを Article に実装して println!("{}", article) を可能にしよう
// 2. PartialOrd を実装してソート可能にしてみよう
// 3. 独自トレイトを定義し、3つ以上の型に実装してみよう

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// セクション D: 並行処理 - Fearless Concurrency
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//
// Python との決定的な違い: GIL (Global Interpreter Lock)
//
// Python の制限:
//   - GIL により、CPython ではスレッドが真に並列実行されない
//   - マルチスレッドにしても CPU バウンドな処理は速くならない
//   - multiprocessing を使うとプロセス間通信のオーバーヘッドが大きい
//
// Rust の強み:
//   - GIL がない = 真の並列実行が可能
//   - 所有権システムがデータ競合をコンパイル時に防止
//   - 「fearless concurrency」= 安心して並行コードを書ける
//
// [考えてほしい疑問] Python で threading を使って CPU バウンドな処理を
// 並列化しようとして、速くならなかった経験は？

fn demo_concurrency() {
    println!("--- セクション D: 並行処理 ---\n");

    // ■ 基本: std::thread でスレッドを生成
    // Python: threading.Thread(target=func).start()
    // Rust:   thread::spawn(|| { ... })
    println!("  [スレッド基本]");
    let handle = thread::spawn(|| {
        // クロージャ（無名関数）をスレッドで実行
        let mut sum = 0u64;
        for i in 1..=100 {
            sum += i;
        }
        sum // 戻り値をスレッドから返せる
    });

    // join() で完了を待ち、結果を受け取る
    let result = handle.join().unwrap();
    println!("  1..100 の合計 (別スレッド) = {}", result);

    // ■ move クロージャ: 所有権をスレッドに移動
    let data = vec![1, 2, 3, 4, 5];
    let handle = thread::spawn(move || {
        // move により data の所有権がこのスレッドに移動
        // 元のスレッドでは data はもう使えない = 安全！
        let sum: i32 = data.iter().sum();
        sum
    });
    // println!("{:?}", data);  // コンパイルエラー！data は move 済み
    println!("  vec合計 (move) = {}", handle.join().unwrap());

    // ■ Arc<Mutex<T>>: スレッド安全な共有データ
    // Python: threading.Lock() で手動ロック（忘れるとバグ）
    // Rust:   Mutex<T> でロックなしにはアクセス不可能（コンパイラが強制）
    //
    // Arc = Atomic Reference Count (スレッド安全な参照カウント)
    // Mutex = 排他制御 (一度に1つのスレッドだけがアクセス可能)
    println!("\n  [Arc<Mutex<T>>]");
    let counter = Arc::new(Mutex::new(0));
    let mut handles = vec![];

    for _ in 0..10 {
        let counter = Arc::clone(&counter); // 参照カウントを増やす
        let handle = thread::spawn(move || {
            let mut num = counter.lock().unwrap(); // ロック取得
            *num += 1;
            // ロックはスコープを抜けると自動解放 (RAII パターン)
        });
        handles.push(handle);
    }

    for handle in handles {
        handle.join().unwrap();
    }
    println!("  10スレッドでカウント: {}", *counter.lock().unwrap());

    // ■ チャネル (Channel): スレッド間メッセージパッシング
    // Go の channel と同じ概念！
    // Python: queue.Queue() に相当するが、型安全。
    //
    // mpsc = Multiple Producer, Single Consumer
    println!("\n  [Channel (mpsc)]");
    let (tx, rx) = mpsc::channel();

    // 複数の送信者 (Multiple Producers)
    for i in 0..5 {
        let tx = tx.clone();
        thread::spawn(move || {
            let msg = format!("スレッド{}からのメッセージ", i);
            tx.send(msg).unwrap();
        });
    }
    drop(tx); // 元の送信者を閉じる（これがないと rx が永遠に待つ）

    // 受信側で全メッセージを受け取る
    for received in rx {
        println!("  受信: {}", received);
    }

    // ■ 並列計算の例: 配列の合計を4スレッドで分割計算
    println!("\n  [並列分割計算]");
    let data: Vec<u64> = (1..=1_000_000).collect();
    let chunk_size = data.len() / 4;
    let data = Arc::new(data);
    let mut handles = vec![];

    let start = Instant::now();
    for i in 0..4 {
        let data = Arc::clone(&data);
        let handle = thread::spawn(move || {
            let start_idx = i * chunk_size;
            let end_idx = if i == 3 { data.len() } else { (i + 1) * chunk_size };
            data[start_idx..end_idx].iter().sum::<u64>()
        });
        handles.push(handle);
    }

    let total: u64 = handles.into_iter().map(|h| h.join().unwrap()).sum();
    let duration = start.elapsed();
    println!("  4スレッド合計: {} (所要時間: {:?})", total, duration);

    println!();
}

// [実装してみよう]
// 1. Arc<Mutex<Vec<T>>> で複数スレッドからベクタに push してみよう
// 2. channel を使って「ワーカープール」パターンを実装してみよう
// 3. スレッド数を変えてパフォーマンスの変化を計測してみよう

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// セクション E: 簡単な HTTP API (標準ライブラリのみ)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//
// Python: Flask/FastAPI で数行で書けるHTTPサーバーを、
// Rust では標準ライブラリだけで自作する。
// これにより HTTP プロトコルの理解が深まる。
//
// [考えてほしい疑問] Python の Flask は内部で何をしているのか？
// TCP ソケット -> HTTP パース -> ルーティング -> レスポンス生成
// ここではその全工程を手で書く。

// ■ 簡易 JSON パーサー (外部依存なし)
fn parse_json_notes(body: &str) -> Option<(String, String)> {
    // {"title": "...", "body": "..."} を手動パース
    // 実際のプロダクションでは serde_json を使うべき
    let body = body.trim();
    if !body.starts_with('{') || !body.ends_with('}') {
        return None;
    }

    let mut title = None;
    let mut note_body = None;

    // 簡易的にキーと値を抽出
    for part in body[1..body.len() - 1].split(',') {
        let kv: Vec<&str> = part.splitn(2, ':').collect();
        if kv.len() != 2 {
            continue;
        }
        let key = kv[0].trim().trim_matches('"');
        let value = kv[1].trim().trim_matches('"');

        match key {
            "title" => title = Some(value.to_string()),
            "body" => note_body = Some(value.to_string()),
            _ => {}
        }
    }

    match (title, note_body) {
        (Some(t), Some(b)) => Some((t, b)),
        _ => None,
    }
}

// ■ ノートをJSONに変換
fn notes_to_json(notes: &[(String, String)]) -> String {
    let items: Vec<String> = notes
        .iter()
        .enumerate()
        .map(|(i, (title, body))| {
            format!(
                "{{\"id\": {}, \"title\": \"{}\", \"body\": \"{}\"}}",
                i + 1,
                title,
                body
            )
        })
        .collect();
    format!("[{}]", items.join(", "))
}

// ■ HTTP リクエストのパース
struct HttpRequest {
    method: String,
    path: String,
    body: String,
}

fn parse_http_request(stream: &std::net::TcpStream) -> Option<HttpRequest> {
    let mut reader = BufReader::new(stream);
    let mut request_line = String::new();
    reader.read_line(&mut request_line).ok()?;

    let parts: Vec<&str> = request_line.trim().split_whitespace().collect();
    if parts.len() < 2 {
        return None;
    }

    let method = parts[0].to_string();
    let path = parts[1].to_string();

    // ヘッダーを読む
    let mut content_length = 0;
    loop {
        let mut line = String::new();
        reader.read_line(&mut line).ok()?;
        let line = line.trim().to_string();
        if line.is_empty() {
            break;
        }
        if line.to_lowercase().starts_with("content-length:") {
            content_length = line.split(':').nth(1)?.trim().parse().unwrap_or(0);
        }
    }

    // ボディを読む
    let mut body = vec![0u8; content_length];
    if content_length > 0 {
        reader.read_line(&mut String::new()).ok(); // 余分な改行を消費する場合
        // 簡易的にバッファから読む
        let body_str: String = {
            let buf = reader.buffer();
            let available = buf.len().min(content_length);
            String::from_utf8_lossy(&buf[..available]).to_string()
        };
        return Some(HttpRequest {
            method,
            path,
            body: body_str,
        });
    }

    let _ = body; // unused warning 回避

    Some(HttpRequest {
        method,
        path,
        body: String::new(),
    })
}

fn demo_http_server() {
    println!("\n--- セクション E: HTTP API サーバー ---\n");
    println!("  サーバーを http://127.0.0.1:8080 で起動します");
    println!("  テスト方法:");
    println!("    curl http://127.0.0.1:8080/notes");
    println!("    curl -X POST -d '{{\"title\":\"test\",\"body\":\"hello\"}}' http://127.0.0.1:8080/notes");
    println!("  Ctrl+C で停止\n");

    // ノートデータをスレッド間で共有
    let notes: Arc<Mutex<Vec<(String, String)>>> = Arc::new(Mutex::new(vec![
        (String::from("Welcome"), String::from("Rust HTTP Server started!")),
    ]));

    let listener = TcpListener::bind("127.0.0.1:8080").expect("ポート8080がバインドできません");

    // マルチスレッドでリクエストを処理
    for stream in listener.incoming() {
        match stream {
            Ok(stream) => {
                let notes = Arc::clone(&notes);
                thread::spawn(move || {
                    handle_connection(stream, notes);
                });
            }
            Err(e) => eprintln!("接続エラー: {}", e),
        }
    }
}

fn handle_connection(
    mut stream: std::net::TcpStream,
    notes: Arc<Mutex<Vec<(String, String)>>>,
) {
    let request = match parse_http_request(&stream) {
        Some(r) => r,
        None => return,
    };

    let (status, body) = match (request.method.as_str(), request.path.as_str()) {
        // GET /notes - ノート一覧を返す
        ("GET", "/notes") => {
            let notes = notes.lock().unwrap();
            let json = notes_to_json(&notes);
            ("200 OK", json)
        }

        // POST /notes - ノートを追加
        ("POST", "/notes") => {
            if let Some((title, note_body)) = parse_json_notes(&request.body) {
                let mut notes = notes.lock().unwrap();
                notes.push((title.clone(), note_body));
                (
                    "201 Created",
                    format!("{{\"message\": \"Note '{}' created\"}}", title),
                )
            } else {
                (
                    "400 Bad Request",
                    String::from("{\"error\": \"Invalid JSON. Expected {\\\"title\\\": \\\"...\\\", \\\"body\\\": \\\"...\\\"}\"}"),
                )
            }
        }

        // その他のパス
        _ => (
            "404 Not Found",
            String::from("{\"error\": \"Not Found\"}"),
        ),
    };

    // HTTP レスポンスを送信
    let response = format!(
        "HTTP/1.1 {}\r\nContent-Type: application/json\r\nContent-Length: {}\r\n\r\n{}",
        status,
        body.len(),
        body
    );

    let _ = stream.write_all(response.as_bytes());
    let _ = stream.flush();
}

// [実装してみよう]
// 1. DELETE /notes/:id エンドポイントを追加してみよう
// 2. リクエストログを表示する機能を追加してみよう
// 3. ファイルにノートを永続化する機能を追加してみよう

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// セクション F: パフォーマンスデモ
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//
// Rust vs Python のパフォーマンス比較
//
// フィボナッチ数列 (再帰) の実行時間比較:
//
//   Python (fib(40)):
//     def fib(n):
//         if n <= 1: return n
//         return fib(n-1) + fib(n-2)
//     # 結果: 約 25〜40 秒
//
//   Rust (fib(40)):
//     fn fib(n: u64) -> u64 {
//         if n <= 1 { return n; }
//         fib(n-1) + fib(n-2)
//     }
//     # 結果: 約 0.5〜1.0 秒 (release ビルド)
//
// => Rust は Python の 30〜80 倍速い！
//
// なぜ Rust は速いのか:
//   1. ネイティブコードにコンパイル (インタプリタのオーバーヘッドなし)
//   2. GC がない (GC 一時停止がない)
//   3. ゼロコスト抽象化 (抽象化してもランタイムコストなし)
//   4. LLVM による最適化 (末尾呼び出し、インライン展開など)
//
// メモリ使用量の比較:
//   Python: 整数1つ = 約28バイト (オブジェクトヘッダ含む)
//   Rust:   i64 = 8バイト (データそのもののみ)
//   => Python は同じデータで 3〜4 倍のメモリを使う
//
// [考えてほしい疑問]
//   では、なぜ Python が使われ続けるのか？
//   -> 開発速度、エコシステム、学習コスト。
//   -> 適材適所: プロトタイピングは Python、パフォーマンスが必要な箇所は Rust。
//   -> PyO3 で Python から Rust を呼ぶハイブリッドも可能。

fn fib(n: u64) -> u64 {
    if n <= 1 {
        return n;
    }
    fib(n - 1) + fib(n - 2)
}

fn demo_performance() {
    println!("--- セクション F: パフォーマンスデモ ---\n");

    // ■ フィボナッチ計算 (再帰)
    // cargo run --release で最適化ビルドすると更に速くなる
    let n = 40;
    println!("  フィボナッチ({}) を計算中...", n);
    let start = Instant::now();
    let result = fib(n);
    let duration = start.elapsed();
    println!("  結果: fib({}) = {}", n, result);
    println!("  所要時間: {:?}", duration);
    println!("  (Python では同じ計算に 25〜40 秒かかります)");

    // ■ ベクタ操作の速度
    println!();
    let start = Instant::now();
    let sum: u64 = (1..=10_000_000u64).sum();
    let duration = start.elapsed();
    println!("  1〜10,000,000 の合計: {}", sum);
    println!("  所要時間: {:?}", duration);

    // ■ HashMap の速度
    let start = Instant::now();
    let mut map = HashMap::new();
    for i in 0..100_000 {
        map.insert(format!("key_{}", i), i);
    }
    let lookup = map.get("key_50000").unwrap();
    let duration = start.elapsed();
    println!("  HashMap 100,000件の挿入 + 検索: {:?} (値={})", duration, lookup);

    // ■ メモリ効率の説明
    println!();
    println!("  [メモリ効率]");
    println!("  Rust i64      = 8 bytes");
    println!("  Python int    = ~28 bytes (3.5倍)");
    println!("  Rust Vec<i64> = 24 bytes + 8*N bytes (ヘッダ + データ)");
    println!("  Python list   = 56 bytes + 8*N + 28*N bytes (リスト + ポインタ + オブジェクト)");
    println!(
        "  => 100万要素: Rust ~8MB vs Python ~36MB"
    );

    println!();
}

// [実装してみよう]
// 1. メモ化 (HashMap) を使ったフィボナッチを実装し、速度差を体感しよう
// 2. ソートアルゴリズム (クイックソート等) を実装してベンチマークしてみよう
// 3. cargo bench でベンチマークテストを書いてみよう (要 nightly or criterion クレート)
