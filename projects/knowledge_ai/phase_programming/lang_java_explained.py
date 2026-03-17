#!/usr/bin/env python3
"""
lang_java_explained.py - Python使いのためのJava入門ガイド

「Javaは冗長だ」── それはPythonの目で見ているからそう見えるだけ。
型安全性・コンパイル時チェック・巨大チームでの保守性。
Javaが30年近く企業の基幹システムを支え続けている理由を、
Pythonとの対比で体感的に理解するためのファイル。

実行方法:
    python lang_java_explained.py

標準ライブラリのみ使用。
"""

import textwrap


# ============================================================
# ユーティリティ
# ============================================================

def section(title: str) -> None:
    """セクション区切り"""
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)
    print()


def subsection(title: str) -> None:
    print()
    print(f"  -- {title} --")
    print()


def question(text: str) -> None:
    print(f"  [考えてほしい疑問] {text}")
    print()


def task(text: str) -> None:
    print(f"  [実装してみよう] {text}")
    print()


def point(text: str) -> None:
    print(f"    > {text}")


def code_block(title: str, code: str) -> None:
    print(f"    --- {title} ---")
    for line in textwrap.dedent(code).strip().split("\n"):
        print(f"    {line}")
    print()


def p(text: str) -> None:
    for line in textwrap.dedent(text).strip().split("\n"):
        print(f"  {line}")


def table_row(cols: list, widths: list) -> str:
    parts = []
    for col, w in zip(cols, widths):
        parts.append(str(col).ljust(w))
    return "  | " + " | ".join(parts) + " |"


def table_sep(widths: list) -> str:
    return "  +-" + "-+-".join("-" * w for w in widths) + "-+"


# ============================================================
# 1. 環境とHello World
# ============================================================

def chapter_1_hello_world():
    section("1. 環境とHello World - Java vs Python の根本的な違い")

    p("""
    Python を書いてきた人が Java に触れて最初に感じるのは「儀式の多さ」。
    でもこの「儀式」にはすべて理由がある。
    まずは Hello World を通じて、2つの言語の哲学の違いを見ていこう。
    """)

    subsection("1.1 コンパイル言語 vs インタプリタ言語")

    code_block("Python: 書いたらすぐ実行", """
    # hello.py
    print("Hello, World!")

    # 実行:
    # $ python hello.py
    # Hello, World!
    """)

    code_block("Java: コンパイルしてから実行 (2ステップ)", """
    // Main.java
    public class Main {
        public static void main(String[] args) {
            System.out.println("Hello, World!");
        }
    }

    // 実行:
    // $ javac Main.java     ← コンパイル (.class ファイルが生成される)
    // $ java Main           ← 実行 (JVMがバイトコードを実行)
    // Hello, World!
    """)

    p("""
    なぜ2ステップなのか?
    - javac: ソースコード → バイトコード (.class) に変換
    - java:  JVM (Java Virtual Machine) がバイトコードを実行
    - この仕組みのおかげで "Write Once, Run Anywhere"
    - コンパイル時に型エラーを検出 → 実行前にバグを発見できる
    """)

    subsection("1.2 ファイル名 = クラス名 の制約")

    p("""
    Python: ファイル名は自由。hello.py でも foo.py でも動く。
    Java:   public class の名前とファイル名が一致しなければならない。

    public class Main → Main.java (必須)
    public class UserService → UserService.java (必須)

    これは「ファイルを見ればクラスがわかる」という設計思想。
    大規模プロジェクトでのナビゲーションを容易にする。
    """)

    subsection("1.3 セミコロンと波括弧")

    code_block("Python: インデントでブロックを表現", """
    def greet(name):
        if name:
            print(f"Hello, {name}")
        else:
            print("Hello, stranger")
    """)

    code_block("Java: セミコロンと波括弧でブロックを表現", """
    public void greet(String name) {
        if (name != null) {
            System.out.println("Hello, " + name);
        } else {
            System.out.println("Hello, stranger");
        }
    }
    """)

    p("""
    覚えること:
    - 文の終わりにはセミコロン ; が必須
    - ブロックは { } で囲む (インデントではない)
    - if の条件式は ( ) で囲む必要がある
    - Python の print() → Java の System.out.println()
    """)

    subsection("1.4 main メソッド - エントリーポイント")

    code_block("Python", """
    # トップレベルにコードを書ける
    print("直接実行される")

    # 慣例的なエントリーポイント
    if __name__ == "__main__":
        main()
    """)

    code_block("Java", """
    public class Main {
        // この形式が唯一のエントリーポイント
        public static void main(String[] args) {
            System.out.println("ここから始まる");
        }
    }

    // public  → どこからでもアクセス可能
    // static  → インスタンスを作らなくても呼べる
    // void    → 戻り値なし
    // String[] args → コマンドライン引数 (sys.argv に相当)
    """)

    question("Java で main メソッドが static なのはなぜ?")
    point("JVM がクラスをロードしたとき、まだインスタンスが存在しない。")
    point("static ならインスタンス不要で呼び出せるため、起動点に最適。")


# ============================================================
# 2. 変数と型
# ============================================================

def chapter_2_variables_and_types():
    section("2. 変数と型 - 静的型付け vs 動的型付け")

    p("""
    Python と Java の最大の違いがここにある。
    Python: 変数に型は付かない。値に型がある (動的型付け)。
    Java:   変数に型を宣言する。コンパイル時にチェックされる (静的型付け)。
    """)

    subsection("2.1 基本的な変数宣言")

    code_block("Python: 型宣言なし", """
    x = 10          # int
    name = "Alice"  # str
    pi = 3.14       # float
    active = True   # bool
    """)

    code_block("Java: 型を必ず宣言", """
    int x = 10;             // 整数
    String name = "Alice";  // 文字列
    double pi = 3.14;       // 浮動小数点
    boolean active = true;  // 真偽値
    """)

    subsection("2.2 プリミティブ型と参照型")

    p("""
    Java には「プリミティブ型」と「参照型」の2種類がある。
    Python ではすべてがオブジェクトだが、Java は性能のために区別している。
    """)

    code_block("プリミティブ型 (値そのものを格納、高速)", """
    byte   b = 127;          // 8bit整数  (-128 ~ 127)
    short  s = 32000;        // 16bit整数
    int    i = 2_000_000;    // 32bit整数 ← 最もよく使う
    long   l = 9_000_000_000L; // 64bit整数 (末尾にL)
    float  f = 3.14f;        // 32bit浮動小数点 (末尾にf)
    double d = 3.14159;      // 64bit浮動小数点 ← 最もよく使う
    boolean flag = true;     // true or false
    char   c = 'A';          // 16bit Unicode文字 (シングルクォート)
    """)

    code_block("参照型 (オブジェクトへの参照を格納)", """
    String name = "Alice";         // 文字列 (クラス)
    Integer count = 42;            // int のラッパークラス
    List<String> names = new ArrayList<>();  // リスト
    """)

    p("""
    Python との対応:
      int     → Java の int / long
      float   → Java の double (float はほぼ使わない)
      bool    → Java の boolean (小文字の true/false)
      str     → Java の String (大文字始まり = クラス)
    """)

    subsection("2.3 var による型推論 (Java 10+)")

    code_block("var: コンパイラが型を推論する", """
    // Java 10以降
    var x = 10;              // int と推論
    var name = "Alice";      // String と推論
    var list = new ArrayList<String>();  // ArrayList<String> と推論

    // ただし以下はコンパイルエラー:
    // var y;          ← 初期値がないと推論できない
    // var z = null;   ← null からは型がわからない
    """)

    p("""
    var は「Python みたいに書ける」が、裏では型が確定している。
    Python の動的型付けとは本質的に異なる。
    """)

    subsection("2.4 final - 定数を宣言する")

    code_block("Python: 定数の仕組みがない (慣例のみ)", """
    MAX_SIZE = 100   # 大文字 = 「変更しないで」の慣例
    MAX_SIZE = 200   # でも変更できてしまう... エラーにならない
    """)

    code_block("Java: final で再代入を禁止", """
    final int MAX_SIZE = 100;
    MAX_SIZE = 200;   // コンパイルエラー! 再代入不可
    """)

    subsection("2.5 null と NullPointerException")

    code_block("Python: None", """
    name = None
    print(name.upper())  # AttributeError: 'NoneType' has no attribute 'upper'
    """)

    code_block("Java: null と NPE (NullPointerException)", """
    String name = null;
    System.out.println(name.toUpperCase());
    // → NullPointerException (実行時エラー)
    // Java開発で最も遭遇するエラーの一つ
    """)

    p("""
    NullPointerException (通称NPE) は Java 開発者の宿敵。
    対策として Optional<T> が導入された (後述)。
    """)

    subsection("2.6 Boxing / Unboxing")

    code_block("プリミティブ型とラッパークラスの自動変換", """
    // Boxing: プリミティブ → ラッパーオブジェクト
    int x = 10;
    Integer boxed = x;     // 自動Boxing (int → Integer)

    // Unboxing: ラッパーオブジェクト → プリミティブ
    Integer y = Integer.valueOf(20);
    int unboxed = y;       // 自動Unboxing (Integer → int)

    // 注意: ジェネリクスにはプリミティブが使えない
    // List<int> ← コンパイルエラー
    List<Integer> numbers = new ArrayList<>();  // OK
    """)

    p("""
    Python では int もオブジェクトなのでこの区別は不要。
    Java でコレクション (List, Map) を使うときはラッパー型が必要。
    int → Integer, double → Double, boolean → Boolean
    """)


# ============================================================
# 3. 文字列
# ============================================================

def chapter_3_strings():
    section("3. 文字列 - String は不変オブジェクト")

    p("""
    Python も Java も、文字列は不変 (immutable)。
    変更するたびに新しいオブジェクトが生成される点は同じだが、
    操作の書き方がかなり異なる。
    """)

    subsection("3.1 文字列の生成とフォーマット")

    code_block("Python: f-string", """
    name = "Alice"
    age = 30
    msg = f"Hello, {name}! You are {age} years old."
    """)

    code_block("Java: String.formatted() / String.format()", """
    String name = "Alice";
    int age = 30;

    // Java 15+ : formatted()
    String msg = "Hello, %s! You are %d years old.".formatted(name, age);

    // 従来の方法:
    String msg2 = String.format("Hello, %s! You are %d years old.", name, age);

    // 文字列結合 (単純だが非効率な場合あり)
    String msg3 = "Hello, " + name + "! You are " + age + " years old.";
    """)

    subsection("3.2 equals() vs == (超重要!)")

    code_block("Python: == で値を比較", """
    a = "hello"
    b = "hello"
    print(a == b)    # True (値が同じ)
    print(a is b)    # True (たまたま同じオブジェクト、最適化による)
    """)

    code_block("Java: .equals() で値を比較 (.== は参照比較!)", """
    String a = "hello";
    String b = "hello";
    String c = new String("hello");

    System.out.println(a == b);        // true  (文字列プールで同一参照)
    System.out.println(a == c);        // false (new で別オブジェクト)
    System.out.println(a.equals(c));   // true  (値が同じ)

    // ★ 文字列比較は必ず .equals() を使う!
    // Python の == → Java の .equals()
    // Python の is → Java の ==
    """)

    p("""
    これは Java 初心者が最もハマるポイント。
    == はオブジェクトの「参照」が同じかを比較する。
    .equals() はオブジェクトの「値」が同じかを比較する。
    Python の == は Java の .equals() に相当する。
    """)

    subsection("3.3 String.join() と Text Blocks")

    code_block("Python", """
    words = ["Java", "is", "fun"]
    result = ", ".join(words)   # "Java, is, fun"
    """)

    code_block("Java", """
    var words = List.of("Java", "is", "fun");
    String result = String.join(", ", words);   // "Java, is, fun"
    """)

    code_block("Python: 三重引用符", """
    query = \"\"\"
    SELECT *
    FROM users
    WHERE active = true
    \"\"\"
    """)

    code_block("Java 15+: Text Blocks", """
    String query = \"\"\"
            SELECT *
            FROM users
            WHERE active = true
            \"\"\";
    // 先頭のインデントは閉じ三重引用符の位置で自動調整される
    """)

    subsection("3.4 StringBuilder - 大量結合の効率化")

    code_block("Python: リストに貯めて join", """
    parts = []
    for i in range(1000):
        parts.append(str(i))
    result = "".join(parts)
    """)

    code_block("Java: StringBuilder", """
    var sb = new StringBuilder();
    for (int i = 0; i < 1000; i++) {
        sb.append(i);
    }
    String result = sb.toString();

    // String 結合をループ内で行うと毎回新しいオブジェクトが生成される
    // StringBuilder は内部バッファに追記するので高速
    """)


# ============================================================
# 4. 制御構文
# ============================================================

def chapter_4_control_flow():
    section("4. 制御構文")

    subsection("4.1 if / else")

    code_block("Python", """
    x = 10
    if x > 0:
        print("positive")
    elif x == 0:
        print("zero")
    else:
        print("negative")
    """)

    code_block("Java", """
    int x = 10;
    if (x > 0) {            // 条件式を ( ) で囲む
        System.out.println("positive");
    } else if (x == 0) {    // elif → else if
        System.out.println("zero");
    } else {
        System.out.println("negative");
    }
    """)

    subsection("4.2 for ループ")

    code_block("Python: range ベース", """
    for i in range(5):
        print(i)            # 0, 1, 2, 3, 4

    names = ["Alice", "Bob", "Carol"]
    for name in names:
        print(name)
    """)

    code_block("Java: 2種類の for", """
    // C言語スタイル (range に相当)
    for (int i = 0; i < 5; i++) {
        System.out.println(i);    // 0, 1, 2, 3, 4
    }

    // 拡張for (for-each) = Python の for-in に近い
    var names = List.of("Alice", "Bob", "Carol");
    for (var name : names) {
        System.out.println(name);
    }
    """)

    p("""
    Java の for (int i = 0; i < n; i++) を分解すると:
      int i = 0  → 初期化
      i < n      → 継続条件
      i++        → 各ループ後のインクリメント
    Python の range(n) と同じ結果だが、より細かい制御が可能。
    """)

    subsection("4.3 while と do-while")

    code_block("Python", """
    count = 0
    while count < 5:
        print(count)
        count += 1
    # do-while は Python にはない
    """)

    code_block("Java", """
    int count = 0;
    while (count < 5) {
        System.out.println(count);
        count++;
    }

    // do-while: 最低1回は実行される
    int n = 0;
    do {
        System.out.println("実行: " + n);
        n++;
    } while (n < 3);
    """)

    subsection("4.4 switch 式 (Java 14+)")

    code_block("Python 3.10+: match / case", """
    status = 200
    match status:
        case 200:
            msg = "OK"
        case 404:
            msg = "Not Found"
        case 500:
            msg = "Server Error"
        case _:
            msg = "Unknown"
    """)

    code_block("Java 14+: switch 式 (arrow構文)", """
    int status = 200;
    String msg = switch (status) {
        case 200 -> "OK";
        case 404 -> "Not Found";
        case 500 -> "Server Error";
        default  -> "Unknown";
    };
    // switch が「式」として値を返す (変数に代入可能)
    // 従来の switch 文と違い、break が不要
    """)


# ============================================================
# 5. 配列とコレクション
# ============================================================

def chapter_5_collections():
    section("5. 配列とコレクション")

    subsection("5.1 配列 (固定長)")

    code_block("Python: リストは可変長", """
    nums = [1, 2, 3]
    nums.append(4)       # OK、自由に追加できる
    """)

    code_block("Java: 配列は固定長", """
    int[] nums = {1, 2, 3};      // サイズ3で固定
    // nums に要素を追加することはできない
    int[] empty = new int[10];   // サイズ10の空配列 (全要素0)
    nums[0] = 10;                // 要素の変更はOK
    """)

    p("""
    Java の配列は Python のリストより制限が多い。
    実務では配列より ArrayList (後述) を使うことが圧倒的に多い。
    """)

    subsection("5.2 List (ArrayList)")

    code_block("Python: list", """
    names = ["Alice", "Bob"]
    names.append("Carol")
    print(names[0])          # Alice
    print(len(names))        # 3
    """)

    code_block("Java: List<String> (ArrayList)", """
    // 可変リスト
    List<String> names = new ArrayList<>();
    names.add("Alice");
    names.add("Bob");
    names.add("Carol");
    System.out.println(names.get(0));    // Alice
    System.out.println(names.size());    // 3

    // 不変リスト (Java 9+)
    var immutable = List.of("Alice", "Bob", "Carol");
    // immutable.add("Dave");  ← UnsupportedOperationException
    """)

    subsection("5.3 Map (HashMap)")

    code_block("Python: dict", """
    scores = {"Alice": 90, "Bob": 85}
    scores["Carol"] = 95
    print(scores.get("Alice"))        # 90
    print(scores.get("Dave", 0))      # 0 (デフォルト値)
    """)

    code_block("Java: Map<String, Integer> (HashMap)", """
    Map<String, Integer> scores = new HashMap<>();
    scores.put("Alice", 90);
    scores.put("Bob", 85);
    scores.put("Carol", 95);
    System.out.println(scores.get("Alice"));              // 90
    System.out.println(scores.getOrDefault("Dave", 0));   // 0

    // 不変Map (Java 9+)
    var immutable = Map.of("Alice", 90, "Bob", 85);
    """)

    subsection("5.4 Set (HashSet)")

    code_block("Python: set", """
    tags = {"java", "python", "java"}   # 重複は自動除去
    tags.add("go")
    print("java" in tags)               # True
    """)

    code_block("Java: Set<String> (HashSet)", """
    Set<String> tags = new HashSet<>();
    tags.add("java");
    tags.add("python");
    tags.add("java");                    // 重複は無視される
    tags.add("go");
    System.out.println(tags.contains("java"));   // true
    """)

    subsection("5.5 ジェネリクスの基本 <T>")

    code_block("Python: TypeVar (型ヒント)", """
    from typing import TypeVar, List
    T = TypeVar('T')

    def first(items: List[T]) -> T:
        return items[0]
    """)

    code_block("Java: ジェネリクス <T>", """
    // 型パラメータ T を使ったメソッド
    public static <T> T first(List<T> items) {
        return items.get(0);
    }

    // Java のジェネリクスはコンパイル時に型安全性を保証する
    List<String> names = List.of("Alice", "Bob");
    String name = first(names);  // 戻り値は String と推論
    """)

    p("""
    ジェネリクスのポイント:
    - <> の中に型を指定する: List<String>, Map<String, Integer>
    - プリミティブ型は使えない: List<int> は不可、List<Integer> を使う
    - Python の型ヒントは実行時に無視されるが、
      Java のジェネリクスはコンパイル時に厳密にチェックされる
    """)


# ============================================================
# 6. 関数 (メソッド)
# ============================================================

def chapter_6_methods():
    section("6. 関数 (メソッド) - 全てはクラスの中に")

    p("""
    Java にはトップレベル関数がない。
    すべての関数 (メソッド) はクラスに属する。
    これは Python との最大の構造的違いの一つ。
    """)

    subsection("6.1 基本的なメソッド定義")

    code_block("Python: トップレベル関数", """
    def add(a, b):
        return a + b

    result = add(3, 5)
    """)

    code_block("Java: クラス内にメソッドを定義", """
    public class Calculator {
        // public = アクセス修飾子
        // static = インスタンス不要
        // int    = 戻り値の型 (必須!)
        public static int add(int a, int b) {
            return a + b;
        }
    }

    // 呼び出し:
    int result = Calculator.add(3, 5);
    """)

    p("""
    Java のメソッド宣言に含まれる情報:
      [アクセス修飾子] [static] [戻り値の型] メソッド名(引数の型 引数名, ...) {
          // 処理
      }
    Python では不要だった「戻り値の型」「引数の型」がすべて必須。
    """)

    subsection("6.2 メソッドオーバーロード")

    code_block("Python: オーバーロードはない (デフォルト引数で代替)", """
    def greet(name, greeting="Hello"):
        print(f"{greeting}, {name}!")

    greet("Alice")               # Hello, Alice!
    greet("Bob", "Good morning") # Good morning, Bob!
    """)

    code_block("Java: 同名で引数の型/数が違うメソッドを定義可能", """
    public class Greeter {
        public static void greet(String name) {
            System.out.println("Hello, " + name + "!");
        }

        public static void greet(String name, String greeting) {
            System.out.println(greeting + ", " + name + "!");
        }

        // 引数の型が違うものも可能
        public static void greet(int userId) {
            System.out.println("Hello, User #" + userId + "!");
        }
    }

    // コンパイラが引数から適切なメソッドを選択する
    Greeter.greet("Alice");                // Hello, Alice!
    Greeter.greet("Bob", "Good morning");  // Good morning, Bob!
    Greeter.greet(42);                     // Hello, User #42!
    """)

    subsection("6.3 可変長引数")

    code_block("Python: *args", """
    def sum_all(*args):
        return sum(args)

    print(sum_all(1, 2, 3))   # 6
    """)

    code_block("Java: 型... args (varargs)", """
    public static int sumAll(int... numbers) {
        int total = 0;
        for (int n : numbers) {
            total += n;
        }
        return total;
    }

    System.out.println(sumAll(1, 2, 3));   // 6
    // 内部的には配列として扱われる
    """)


# ============================================================
# 7. クラスとオブジェクト指向
# ============================================================

def chapter_7_oop():
    section("7. クラスとオブジェクト指向")

    subsection("7.1 クラスとコンストラクタ")

    code_block("Python", """
    class User:
        def __init__(self, name, age):
            self.name = name
            self.age = age

        def greet(self):
            return f"I'm {self.name}, {self.age} years old."

    user = User("Alice", 30)
    print(user.greet())
    """)

    code_block("Java", """
    public class User {
        private String name;   // フィールド (属性)
        private int age;

        // コンストラクタ (クラス名と同じ名前, 戻り値の型なし)
        public User(String name, int age) {
            this.name = name;   // this = Python の self
            this.age = age;
        }

        public String greet() {
            return "I'm %s, %d years old.".formatted(name, age);
        }
    }

    User user = new User("Alice", 30);
    System.out.println(user.greet());
    """)

    p("""
    対応関係:
      self        → this (Java では省略可能な場面が多い)
      __init__    → コンストラクタ (クラス名と同じ)
      Python()    → new ClassName() (new キーワードが必要)
    """)

    subsection("7.2 アクセス修飾子")

    code_block("Python: 慣例ベース", """
    class MyClass:
        def __init__(self):
            self.public_var = 1      # 誰でもアクセス可
            self._protected_var = 2  # 慣例: 外部から触らないで
            self.__private_var = 3   # 名前マングリング (実質的にprivate)
    """)

    code_block("Java: コンパイラが強制", """
    public class MyClass {
        public int publicVar = 1;      // どこからでもアクセス可
        protected int protectedVar = 2; // 同パッケージ + サブクラス
        int packageVar = 3;             // 同パッケージのみ (修飾子なし)
        private int privateVar = 4;     // このクラス内のみ

        // フィールドは private にして getter/setter を提供するのが慣例
        public int getPrivateVar() {
            return privateVar;
        }
    }
    """)

    subsection("7.3 record (Java 16+) - 不変データクラス")

    code_block("Python: @dataclass", """
    from dataclasses import dataclass

    @dataclass
    class Point:
        x: float
        y: float

    p = Point(1.0, 2.0)
    print(p)            # Point(x=1.0, y=2.0)
    """)

    code_block("Java 16+: record", """
    // たった1行で不変データクラスが完成
    public record Point(double x, double y) {}

    // 自動生成されるもの:
    // - コンストラクタ
    // - getter (x(), y())
    // - equals(), hashCode(), toString()
    // - すべてのフィールドが final (不変)

    var p = new Point(1.0, 2.0);
    System.out.println(p);          // Point[x=1.0, y=2.0]
    System.out.println(p.x());      // 1.0
    """)

    subsection("7.4 interface - 振る舞いの契約")

    code_block("Python: ABC (抽象基底クラス) / Protocol", """
    from abc import ABC, abstractmethod

    class Drawable(ABC):
        @abstractmethod
        def draw(self) -> None:
            pass

    class Circle(Drawable):
        def draw(self) -> None:
            print("Drawing circle")
    """)

    code_block("Java: interface", """
    public interface Drawable {
        void draw();   // 実装なしのメソッド (抽象メソッド)
    }

    public class Circle implements Drawable {
        @Override
        public void draw() {
            System.out.println("Drawing circle");
        }
    }

    // Java は多重継承できないが、interface は複数実装可能
    public class Button implements Drawable, Clickable {
        // Drawable と Clickable 両方のメソッドを実装する
    }
    """)

    subsection("7.5 enum")

    code_block("Python: Enum", """
    from enum import Enum

    class Color(Enum):
        RED = 1
        GREEN = 2
        BLUE = 3

    print(Color.RED)        # Color.RED
    print(Color.RED.value)  # 1
    """)

    code_block("Java: enum (より強力)", """
    public enum Color {
        RED, GREEN, BLUE;
    }

    // Java の enum はクラスなのでメソッドも持てる
    public enum HttpStatus {
        OK(200, "OK"),
        NOT_FOUND(404, "Not Found"),
        INTERNAL_ERROR(500, "Internal Server Error");

        private final int code;
        private final String message;

        HttpStatus(int code, String message) {
            this.code = code;
            this.message = message;
        }

        public int getCode() { return code; }
        public String getMessage() { return message; }
    }

    HttpStatus status = HttpStatus.OK;
    System.out.println(status.getCode());    // 200
    """)


# ============================================================
# 8. エラーハンドリング
# ============================================================

def chapter_8_error_handling():
    section("8. エラーハンドリング")

    subsection("8.1 try / catch / finally")

    code_block("Python: try / except / finally", """
    try:
        result = 10 / 0
    except ZeroDivisionError as e:
        print(f"Error: {e}")
    finally:
        print("Always executed")
    """)

    code_block("Java: try / catch / finally", """
    try {
        int result = 10 / 0;
    } catch (ArithmeticException e) {   // except → catch
        System.out.println("Error: " + e.getMessage());
    } finally {
        System.out.println("Always executed");
    }
    """)

    subsection("8.2 チェック例外 vs 非チェック例外 (Java独自の概念)")

    p("""
    Python の例外はすべて「非チェック」― キャッチしなくても動く。
    Java には2種類の例外がある:

    ■ チェック例外 (Checked Exception)
      - Exception を継承 (RuntimeException以外)
      - キャッチするか throws 宣言しないとコンパイルエラー
      - 例: IOException, SQLException, FileNotFoundException

    ■ 非チェック例外 (Unchecked Exception)
      - RuntimeException を継承
      - キャッチ不要 (しなくてもコンパイルは通る)
      - 例: NullPointerException, IllegalArgumentException
    """)

    code_block("Java: チェック例外は処理が強制される", """
    // チェック例外: throws 宣言が必須
    public String readFile(String path) throws IOException {
        // IOException はチェック例外 → 呼び出し側に処理を強制
        return Files.readString(Path.of(path));
    }

    // 呼び出し側も try/catch するか throws を伝搬する
    try {
        String content = readFile("data.txt");
    } catch (IOException e) {
        System.err.println("File read failed: " + e.getMessage());
    }
    """)

    p("""
    チェック例外は Java の最も議論を呼ぶ機能の一つ。
    利点: ファイルI/OやDB接続など、失敗しうる処理を忘れずに扱える。
    欠点: コードが冗長になりがち。モダンなフレームワークは非チェック例外を好む傾向。
    """)

    subsection("8.3 Optional<T> - null安全")

    code_block("Python: None チェック", """
    def find_user(user_id):
        # 見つからない場合 None を返す
        return None

    user = find_user(42)
    if user is not None:
        print(user.name)
    """)

    code_block("Java: Optional<T>", """
    public Optional<User> findUser(int userId) {
        // 見つからない場合は空のOptional
        return Optional.empty();
    }

    Optional<User> user = findUser(42);

    // 値がある場合のみ実行
    user.ifPresent(u -> System.out.println(u.name()));

    // デフォルト値を設定
    String name = user.map(User::name).orElse("Unknown");

    // 値がなければ例外
    User u = user.orElseThrow(() -> new RuntimeException("User not found"));
    """)


# ============================================================
# 9. Stream API
# ============================================================

def chapter_9_stream_api():
    section("9. Stream API - Python の内包表記に相当する世界")

    p("""
    Python の「リスト内包表記」や「itertools」に相当するのが
    Java の Stream API (Java 8+)。
    データのフィルタリング・変換・集約を宣言的に書ける。
    """)

    subsection("9.1 filter / map / collect")

    code_block("Python: リスト内包表記", """
    numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    # 偶数だけ取り出して2倍にする
    result = [x * 2 for x in numbers if x % 2 == 0]
    # [4, 8, 12, 16, 20]
    """)

    code_block("Java: Stream API", """
    var numbers = List.of(1, 2, 3, 4, 5, 6, 7, 8, 9, 10);

    List<Integer> result = numbers.stream()
        .filter(x -> x % 2 == 0)     // 偶数だけ
        .map(x -> x * 2)             // 2倍にする
        .collect(Collectors.toList()); // リストに変換
    // [4, 8, 12, 16, 20]

    // Java 16+: .toList() で簡潔に
    var result2 = numbers.stream()
        .filter(x -> x % 2 == 0)
        .map(x -> x * 2)
        .toList();
    """)

    p("""
    x -> x * 2 は「ラムダ式」。Python の lambda x: x * 2 と同じ。
    Java のラムダ式:  (引数) -> { 処理 }  または  引数 -> 式
    Python のラムダ式: lambda 引数: 式
    """)

    subsection("9.2 forEach / reduce / 集約")

    code_block("Python", """
    names = ["Alice", "Bob", "Carol"]

    # for ループ
    for name in names:
        print(name)

    # 合計
    total = sum([1, 2, 3, 4, 5])

    # reduce
    from functools import reduce
    product = reduce(lambda a, b: a * b, [1, 2, 3, 4, 5])   # 120
    """)

    code_block("Java", """
    var names = List.of("Alice", "Bob", "Carol");

    // forEach
    names.forEach(name -> System.out.println(name));
    // メソッド参照でさらに簡潔に:
    names.forEach(System.out::println);

    // 合計
    int total = List.of(1, 2, 3, 4, 5).stream()
        .mapToInt(Integer::intValue)
        .sum();

    // reduce
    int product = List.of(1, 2, 3, 4, 5).stream()
        .reduce(1, (a, b) -> a * b);   // 120
    """)

    subsection("9.3 groupingBy / toMap")

    code_block("Python: itertools.groupby / 辞書内包表記", """
    from itertools import groupby

    words = ["apple", "banana", "avocado", "blueberry", "cherry"]

    # 先頭文字でグループ化
    grouped = {}
    for word in words:
        grouped.setdefault(word[0], []).append(word)
    # {'a': ['apple', 'avocado'], 'b': ['banana', 'blueberry'], 'c': ['cherry']}
    """)

    code_block("Java: Collectors.groupingBy()", """
    var words = List.of("apple", "banana", "avocado", "blueberry", "cherry");

    Map<Character, List<String>> grouped = words.stream()
        .collect(Collectors.groupingBy(w -> w.charAt(0)));
    // {a=[apple, avocado], b=[banana, blueberry], c=[cherry]}
    """)

    subsection("9.4 Stream API 対比表")

    widths = [30, 35]
    print(table_sep(widths))
    print(table_row(["Python", "Java Stream API"], widths))
    print(table_sep(widths))
    rows = [
        ["[x for x in xs if cond]", ".filter(x -> cond)"],
        ["[f(x) for x in xs]", ".map(x -> f(x))"],
        ["for x in xs: ...", ".forEach(x -> ...)"],
        ["sum(xs)", ".mapToInt(...).sum()"],
        ["len(xs)", ".count()"],
        ["any(cond(x) for x in xs)", ".anyMatch(x -> cond(x))"],
        ["all(cond(x) for x in xs)", ".allMatch(x -> cond(x))"],
        ["sorted(xs)", ".sorted()"],
        ["sorted(xs, key=f)", ".sorted(Comparator.comparing(f))"],
        ["xs[:5]", ".limit(5)"],
        ["xs[3:]", ".skip(3)"],
        ["set(xs)", ".collect(Collectors.toSet())"],
        ["{k: v for ...}", ".collect(Collectors.toMap(...))"],
    ]
    for row in rows:
        print(table_row(row, widths))
    print(table_sep(widths))
    print()


# ============================================================
# 10. 非同期処理
# ============================================================

def chapter_10_async():
    section("10. 非同期処理")

    subsection("10.1 CompletableFuture vs asyncio")

    code_block("Python: asyncio", """
    import asyncio

    async def fetch_data():
        await asyncio.sleep(1)
        return "data"

    async def main():
        result = await fetch_data()
        print(result)

    asyncio.run(main())
    """)

    code_block("Java: CompletableFuture", """
    CompletableFuture<String> future = CompletableFuture.supplyAsync(() -> {
        // 別スレッドで実行
        try { Thread.sleep(1000); } catch (InterruptedException e) {}
        return "data";
    });

    // チェーン処理 (Python の await に相当する操作)
    future
        .thenApply(data -> data.toUpperCase())   // 変換
        .thenAccept(System.out::println)          // 消費
        .join();                                  // 完了待ち
    """)

    p("""
    大きな違い:
    - Python asyncio: シングルスレッド + イベントループ
    - Java CompletableFuture: スレッドプールベース
    - Python は async/await 構文で自然に書ける
    - Java はラムダのチェーンで表現する
    """)

    subsection("10.2 スレッドプール")

    code_block("Python: concurrent.futures", """
    from concurrent.futures import ThreadPoolExecutor

    def task(n):
        return n * 2

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(task, [1, 2, 3, 4, 5]))
    # [2, 4, 6, 8, 10]
    """)

    code_block("Java: ExecutorService", """
    ExecutorService pool = Executors.newFixedThreadPool(4);

    List<Future<Integer>> futures = new ArrayList<>();
    for (int i = 1; i <= 5; i++) {
        final int n = i;
        futures.add(pool.submit(() -> n * 2));
    }

    for (var f : futures) {
        System.out.println(f.get());   // 2, 4, 6, 8, 10
    }

    pool.shutdown();
    """)

    subsection("10.3 Virtual Threads (Java 21+)")

    p("""
    Java 21 で導入された Virtual Threads は革命的。
    従来の OS スレッドと違い、数百万のスレッドを生成できる。
    Go の goroutine に近いコンセプト。
    """)

    code_block("Java 21+: Virtual Threads", """
    // 従来: OS スレッド (重い、数千が限界)
    Thread.ofPlatform().start(() -> {
        System.out.println("Platform thread");
    });

    // Virtual Thread (軽い、数百万でもOK)
    Thread.ofVirtual().start(() -> {
        System.out.println("Virtual thread");
    });

    // ExecutorService と組み合わせる
    try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
        for (int i = 0; i < 100_000; i++) {
            executor.submit(() -> {
                // 各タスクが独自の Virtual Thread で実行
                Thread.sleep(Duration.ofSeconds(1));
                return "done";
            });
        }
    }
    // 10万の同時実行タスクが軽量に処理される
    """)

    p("""
    Python との対比:
    - Python: GILにより真のマルチスレッドが制限される
    - Java:   GILがない + Virtual Threads で大規模並行処理が容易
    - Python: asyncio でI/O待ちを効率化
    - Java:   Virtual Threads で同期コードのまま大規模並行処理が可能
    """)


# ============================================================
# 11. ビルドとパッケージ管理
# ============================================================

def chapter_11_build_tools():
    section("11. ビルドとパッケージ管理")

    subsection("11.1 Maven / Gradle vs pip / poetry")

    p("""
    Python のパッケージ管理は pip, poetry, uv など。
    Java は Maven または Gradle が標準。
    """)

    code_block("Python: requirements.txt / pyproject.toml", """
    # requirements.txt
    flask==3.0.0
    sqlalchemy>=2.0
    pytest

    # インストール:
    # $ pip install -r requirements.txt
    """)

    code_block("Java: pom.xml (Maven)", """
    <!-- pom.xml -->
    <project>
        <modelVersion>4.0.0</modelVersion>
        <groupId>com.example</groupId>
        <artifactId>my-app</artifactId>
        <version>1.0.0</version>

        <dependencies>
            <dependency>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-starter-web</artifactId>
                <version>3.2.0</version>
            </dependency>
        </dependencies>
    </project>

    <!-- ビルド & 実行: -->
    <!-- $ mvn clean package          ← ビルド -->
    <!-- $ java -jar target/my-app.jar ← 実行 -->
    """)

    subsection("11.2 対比表")

    widths = [20, 25, 25]
    print(table_sep(widths))
    print(table_row(["概念", "Python", "Java"], widths))
    print(table_sep(widths))
    rows = [
        ["パッケージ管理", "pip / poetry / uv", "Maven / Gradle"],
        ["依存関係ファイル", "requirements.txt", "pom.xml / build.gradle"],
        ["配布形式", ".whl / .tar.gz", ".jar / .war"],
        ["仮想環境", "venv / conda", "不要 (JVMが分離)"],
        ["実行", "python app.py", "java -jar app.jar"],
        ["REPL", "python (対話型)", "jshell (Java 9+)"],
        ["リンター", "flake8 / ruff", "Checkstyle / SpotBugs"],
        ["フォーマッタ", "black / ruff", "google-java-format"],
        ["テスト", "pytest", "JUnit 5"],
    ]
    for row in rows:
        print(table_row(row, widths))
    print(table_sep(widths))
    print()


# ============================================================
# 12. Python vs Java 対照表まとめ
# ============================================================

def chapter_12_comparison_table():
    section("12. Python vs Java 対照表まとめ")

    p("""
    ここまで学んだ内容を一覧表にまとめる。
    この表を手元に置いて Java コードを読むと理解が早い。
    """)

    widths = [22, 28, 28]
    print(table_sep(widths))
    print(table_row(["カテゴリ", "Python", "Java"], widths))
    print(table_sep(widths))
    rows = [
        ["実行方法", "python file.py", "javac + java"],
        ["型システム", "動的型付け", "静的型付け"],
        ["エントリーポイント", "if __name__...", "public static void main"],
        ["変数宣言", "x = 10", "int x = 10;"],
        ["型推論", "デフォルト", "var (Java 10+)"],
        ["定数", "慣例 (UPPER_CASE)", "final"],
        ["null/None", "None", "null"],
        ["文字列フォーマット", "f\"...{x}\"", "\"%s\".formatted(x)"],
        ["文字列比較", "==", ".equals()"],
        ["三重引用符", "\"\"\"...\"\"\"", "\"\"\"...\"\"\" (Java 15+)"],
        ["リスト", "list", "List<T> (ArrayList)"],
        ["辞書", "dict", "Map<K,V> (HashMap)"],
        ["集合", "set", "Set<T> (HashSet)"],
        ["for-each", "for x in xs:", "for (var x : xs)"],
        ["range ループ", "for i in range(n):", "for (int i=0; i<n; i++)"],
        ["関数定義", "def func():", "public void func() {}"],
        ["ラムダ", "lambda x: x+1", "x -> x + 1"],
        ["リスト操作", "[x for x in xs]", "xs.stream().map(...)"],
        ["クラス", "class Foo:", "public class Foo {}"],
        ["コンストラクタ", "__init__", "ClassName()"],
        ["self", "self", "this"],
        ["継承", "class B(A):", "class B extends A {}"],
        ["インターフェース", "ABC / Protocol", "interface"],
        ["データクラス", "@dataclass", "record (Java 16+)"],
        ["例外キャッチ", "except Exception as e:", "catch (Exception e)"],
        ["例外の種類", "全て非チェック", "チェック + 非チェック"],
        ["null安全", "Optional (typing)", "Optional<T>"],
        ["async", "async/await", "CompletableFuture"],
        ["スレッド", "threading (GIL)", "Thread (真のマルチスレッド)"],
        ["パッケージ管理", "pip / poetry", "Maven / Gradle"],
        ["テスト", "pytest", "JUnit 5"],
    ]
    for row in rows:
        print(table_row(row, widths))
    print(table_sep(widths))
    print()


# ============================================================
# 優先度順まとめ
# ============================================================

def chapter_priority_summary():
    section("優先度順まとめ - この順で覚える")

    p("""
    Tier 1: 最優先 -- これがないとコードが読めない
    --------------------------------------------------------
    """)
    point("型宣言と変数 (int x = 10; / String s = \"hello\";)")
    point("クラス構造 (public class / main メソッド)")
    point("文字列操作 (.equals() vs == は初日に覚える)")
    point("セミコロン、波括弧、括弧のルール")

    p("""
    Tier 2: 重要 -- 実務で毎日使う
    --------------------------------------------------------
    """)
    point("コレクション (List, Map, Set) と基本操作")
    point("Stream API (.filter().map().collect())")
    point("例外処理 (try/catch + チェック例外の概念)")
    point("for ループ (従来型 + 拡張for)")

    p("""
    Tier 3: 上級 -- Spring Boot を使うために必要
    --------------------------------------------------------
    """)
    point("ジェネリクス (<T>, <K,V>, ワイルドカード)")
    point("interface / 抽象クラス (DIの基盤)")
    point("アノテーション (@Override, @Autowired, @RestController 等)")
    point("ラムダ式とメソッド参照 (System.out::println)")

    p("""
    Tier 4: モダンJava -- Java 17+ の新機能
    --------------------------------------------------------
    """)
    point("record (不変データクラスを1行で)")
    point("sealed interface (継承を制限する)")
    point("Pattern Matching (switch式 + instanceof)")
    point("Virtual Threads (Java 21+ の軽量スレッド)")
    point("Text Blocks (複数行文字列)")

    print()
    p("""
    最後にアドバイス:

    Java のコードが冗長に見えるのは最初だけ。
    IDE (IntelliJ IDEA) を使えば、補完とリファクタリングで
    Python と同等以上のスピードで書ける。

    Python で身につけた「きれいなコードを書く感覚」は
    Java でもそのまま活きる。
    読みやすい変数名、適切な関数分割、明確な責務分離
    --- 言語が変わっても、良いコードの原則は同じ。
    """)

    task("Hello World を書いて javac + java の2ステップを体験する")
    task("Python で書いた簡単なクラスを Java に移植してみる")
    task("List, Map, Set を使って簡単なデータ処理を書く")
    task("Stream API で Python の内包表記を書き換えてみる")


# ============================================================
# メイン
# ============================================================

def chapter_13_project_structure():
    section("13. 中規模以上のプロジェクト構成 ── Python の flat 構成 vs Java の階層構成")

    p("""\
    Python は「フラットに並べる」文化。Java は「パッケージで階層化する」文化。
    Java のフォルダ構成は冗長に見えるが、数十人のチームで統一ルールとして機能する。
    """)

    subsection("13-1. Maven 標準レイアウト (Spring Boot)")

    code_block("Java (Spring Boot) の典型的な構成",
    """\
my-app/
├── pom.xml                          # Maven 設定 (= requirements.txt + setup.py)
├── src/
│   ├── main/
│   │   ├── java/com/example/myapp/  # パッケージ = ディレクトリ (逆ドメイン名)
│   │   │   ├── MyAppApplication.java     # @SpringBootApplication エントリポイント
│   │   │   ├── config/                   # 設定クラス (@Configuration)
│   │   │   │   ├── SecurityConfig.java
│   │   │   │   └── WebConfig.java
│   │   │   ├── controller/               # HTTP エンドポイント (@RestController)
│   │   │   │   ├── UserController.java
│   │   │   │   └── OrderController.java
│   │   │   ├── service/                  # ビジネスロジック (@Service)
│   │   │   │   ├── UserService.java
│   │   │   │   └── OrderService.java
│   │   │   ├── repository/               # DB アクセス (@Repository)
│   │   │   │   ├── UserRepository.java
│   │   │   │   └── OrderRepository.java
│   │   │   ├── model/                    # エンティティ / DTO
│   │   │   │   ├── entity/
│   │   │   │   │   ├── User.java
│   │   │   │   │   └── Order.java
│   │   │   │   └── dto/
│   │   │   │       ├── UserRequest.java
│   │   │   │       └── UserResponse.java
│   │   │   └── exception/               # カスタム例外 + ハンドラー
│   │   │       ├── ResourceNotFoundException.java
│   │   │       └── GlobalExceptionHandler.java
│   │   └── resources/
│   │       ├── application.yml           # 設定ファイル (= .env)
│   │       ├── application-dev.yml       # 開発環境用
│   │       ├── application-prod.yml      # 本番環境用
│   │       └── db/migration/            # Flyway マイグレーション
│   │           ├── V1__create_users.sql
│   │           └── V2__create_orders.sql
│   └── test/
│       └── java/com/example/myapp/      # テスト (本番と同じパッケージ構成)
│           ├── controller/
│           │   └── UserControllerTest.java
│           ├── service/
│           │   └── UserServiceTest.java
│           └── repository/
│               └── UserRepositoryTest.java
├── Dockerfile
└── docker-compose.yml
""")

    subsection("13-2. Python の典型構成との比較")

    code_block("Python (FastAPI) の典型的な構成",
    """\
my-app/
├── pyproject.toml          # Java の pom.xml に相当
├── app/
│   ├── __init__.py
│   ├── main.py             # FastAPI() エントリポイント
│   ├── config.py           # ← Java: config/ パッケージ
│   ├── routers/            # ← Java: controller/ パッケージ
│   │   ├── users.py
│   │   └── orders.py
│   ├── services/           # ← Java: service/ パッケージ
│   │   ├── user_service.py
│   │   └── order_service.py
│   ├── repositories/       # ← Java: repository/ パッケージ
│   │   └── user_repo.py
│   ├── models/             # ← Java: model/ パッケージ
│   │   ├── user.py
│   │   └── order.py
│   └── schemas/            # ← Java: dto/ (Pydantic モデル)
│       └── user_schema.py
├── tests/                  # ← Java: src/test/
│   └── test_users.py
└── alembic/                # ← Java: db/migration/ (Flyway)
    └── versions/
""")

    subsection("13-3. 対応関係まとめ")

    widths = [24, 28, 30]
    print(table_sep(widths))
    print(table_row(["概念", "Java (Spring Boot)", "Python (FastAPI)"], widths))
    print(table_sep(widths))
    rows = [
        ["エントリポイント",     "@SpringBootApplication", "app = FastAPI()"],
        ["ルーティング",         "controller/",            "routers/"],
        ["ビジネスロジック",     "service/",               "services/"],
        ["DB アクセス",          "repository/",            "repositories/"],
        ["データモデル",         "model/entity/",          "models/"],
        ["リクエスト/レスポンス","model/dto/",             "schemas/"],
        ["設定",                 "resources/application.yml","config.py + .env"],
        ["DBマイグレーション",   "Flyway (db/migration/)", "Alembic (alembic/)"],
        ["テスト",               "src/test/ (JUnit5)",     "tests/ (pytest)"],
        ["ビルド設定",           "pom.xml (Maven)",        "pyproject.toml"],
    ]
    for r in rows:
        print(table_row(r, widths))
    print(table_sep(widths))
    print()

    point("Java は「1クラス = 1ファイル」が原則。Python は複数クラスを1ファイルに書ける")
    point("Java のパッケージ名は逆ドメイン (com.example.myapp)。Python はプロジェクト名のみ")
    point("Java は src/main と src/test が分離。Python は tests/ を別ディレクトリに置く")
    point("Gradle を使う場合は pom.xml → build.gradle.kts に変わるが構成は同じ")
    print()

    question("Spring Boot の DI (Dependency Injection) は\n"
             "    controller → service → repository の依存関係を自動解決する。\n"
             "    Python で同じことをする場合、depends() や DI コンテナを自前で用意する必要がある。")


def main():
    print()
    print("=" * 70)
    print("  lang_java_explained.py")
    print("  Python使いのためのJava入門ガイド")
    print("=" * 70)
    print()
    print("  対象: Python経験者がJavaを読み書きできるようになること")
    print("  前提: Python の基本文法を理解していること")
    print()

    chapter_1_hello_world()
    chapter_2_variables_and_types()
    chapter_3_strings()
    chapter_4_control_flow()
    chapter_5_collections()
    chapter_6_methods()
    chapter_7_oop()
    chapter_8_error_handling()
    chapter_9_stream_api()
    chapter_10_async()
    chapter_11_build_tools()
    chapter_12_comparison_table()
    chapter_priority_summary()
    chapter_13_project_structure()

    print()
    print("=" * 70)
    print("  END - Javaの世界へようこそ")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
