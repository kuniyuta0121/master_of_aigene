#!/usr/bin/env python3
"""
lang_go_explained.py - Python使いのためのGo入門ガイド

「Pythonしか書けない」から「Goも読める・書ける」へ。

Go は Google が 2009 年に公開した言語で、
シンプルさ・並行処理・コンパイル速度を極限まで追求した設計になっている。
Python使いが Go を学ぶと「型」「メモリ」「並行処理」の理解が一段深くなる。

このファイルは Go のコードを Python との対比で解説する。
Go のコードは文字列として表示し、Python 側は実行可能なコメント付きで示す。

実行方法:
    python lang_go_explained.py

標準ライブラリのみ使用。
"""

import textwrap


# ============================================================
# ユーティリティ
# ============================================================

def section(title: str) -> None:
    """セクション区切り"""
    print()
    print("━" * 64)
    print(f"  {title}")
    print("━" * 64)
    print()


def subsection(title: str) -> None:
    print()
    print(f"  ── {title} ──")
    print()


def question(text: str) -> None:
    """考えてほしい疑問"""
    print(f"  [考えてほしい疑問] {text}")
    print()


def task(text: str) -> None:
    """実装タスク"""
    print(f"  [実装してみよう] {text}")
    print()


def point(text: str) -> None:
    print(f"    > {text}")


def code_block(title: str, code: str) -> None:
    print(f"    --- {title} ---")
    for line in code.strip().split("\n"):
        print(f"    {line}")
    print()


def table_row(cols: list, widths: list) -> str:
    parts = []
    for col, w in zip(cols, widths):
        parts.append(str(col).ljust(w))
    return "  | " + " | ".join(parts) + " |"


def table_sep(widths: list) -> str:
    return "  +-" + "-+-".join("-" * w for w in widths) + "-+"


# ============================================================
# 1. 環境と Hello World
# ============================================================

def chapter_1_hello_world():
    section("1. 環境と Hello World ── Go vs Python の根本的な違い")

    print(textwrap.dedent("""\
    Go と Python は「設計思想」が真逆に近い。

    Python: 「とにかく動かして試す」 ── インタプリタ、動的型付け
    Go:     「コンパイルを通ったコードは信頼できる」 ── コンパイラ、静的型付け

    しかし Go は go run で「インタプリタ風」にも実行できる:
      $ go run main.go       # コンパイル+即実行（Python的な手軽さ）
      $ go build -o app      # バイナリ生成（配布用）

    Python で言えば:
      $ python main.py       # go run main.go に相当
      $ pyinstaller main.py  # go build に相当（ただしGoの方が圧倒的にシンプル）
    """))

    subsection("1-1. Hello World 比較")

    code_block("Python", """\
# hello.py
print("Hello, World!")

# 実行: python hello.py""")

    code_block("Go", """\
// main.go
package main          // ← 全てのGoプログラムは package に属する

import "fmt"          // ← 使わない import はコンパイルエラー！

func main() {         // ← エントリーポイント。波括弧は同じ行に書く（強制）
    fmt.Println("Hello, World!")
}

// 実行: go run main.go""")

    print(textwrap.dedent("""\
    注目すべき違い:

    1. package main — Go のコードは必ずパッケージに属する
       Python にはこの概念がない（ファイル = モジュール）

    2. import "fmt" — 未使用の import はコンパイルエラーになる
       Python では未使用 import は警告(linter)だけで動く

    3. func main() — 波括弧 { は func main() と同じ行に書く
       次の行に書くとコンパイルエラー（セミコロン自動挿入の仕様）

    4. セミコロンは不要 — コンパイラが行末に自動挿入する
       Python と同じ感覚で書ける
    """))

    subsection("1-2. gofmt ── フォーマット戦争の終焉")

    print(textwrap.dedent("""\
    Python: black, autopep8, yapf ... フォーマッタが複数ある
    Go:     gofmt 一択。公式ツール。議論の余地なし。

    Go のコードは世界中どこでも同じスタイル。
    「タブ vs スペース」「括弧の位置」などの議論は Go では発生しない。

    $ gofmt -w main.go     # ファイルを直接整形
    $ goimports -w main.go  # import の整理 + gofmt
    """))

    question("Python の black も「議論不要の1スタイル」を謳っている。Go の gofmt と何が違う？")


# ============================================================
# 2. 変数と型
# ============================================================

def chapter_2_variables_and_types():
    section("2. 変数と型 ── 静的型付けの世界")

    print(textwrap.dedent("""\
    Python は動的型付け: 変数の型は実行時に決まり、いつでも変わる。
    Go は静的型付け: 変数の型はコンパイル時に決まり、二度と変わらない。

    この違いが Go を学ぶ上で最も大きな壁になる。
    """))

    subsection("2-1. 変数宣言")

    code_block("Python", """\
x = 10           # 型を書かない。int が自動的に割り当てられる
name = "Alice"   # str
x = "hello"      # OK! Python では型を変えられる""")

    code_block("Go", """\
var x int = 10           // 明示的に型を指定
var name string = "Alice"
x = "hello"              // コンパイルエラー！ int 型の変数に string は入らない

// 短縮宣言（型推論） ── Python の感覚に近い
y := 20          // := で宣言+代入。型は右辺から推論される（int）
msg := "hello"   // string と推論される
y = "world"      // コンパイルエラー！ 一度決まった型は変えられない""")

    point("var は関数の外でも使える。:= は関数の中でしか使えない。")
    point(":= は「新しい変数を作る」、= は「既存の変数に代入する」。")
    print()

    subsection("2-2. 基本型")

    code_block("Go の基本型", """\
// 整数
var i int = 42          // プラットフォーム依存（64bit OS なら int64）
var i8 int8 = 127       // -128 ~ 127
var u uint = 42          // 符号なし整数（Python にはない）

// 浮動小数点
var f float64 = 3.14    // Python の float と同じ精度
var f32 float32 = 3.14  // 精度が低い版（Python にはない）

// 文字列
var s string = "hello"  // Python の str

// 真偽値
var b bool = true       // Python の True（小文字なので注意）

// バイトとルーン
var by byte = 'A'       // uint8 のエイリアス
var r rune = 'あ'       // int32 のエイリアス（Unicode コードポイント）""")

    subsection("2-3. ゼロ値 ── Python にはない概念")

    print(textwrap.dedent("""\
    Go では全ての型に「ゼロ値」（zero value）がある。
    宣言だけして代入しなくても、変数は必ず初期値を持つ。

    Python では未代入の変数を参照すると NameError が出る。
    Go ではエラーにならず、ゼロ値が使われる。
    """))

    code_block("Go のゼロ値", """\
var i int       // 0
var f float64   // 0.0
var s string    // ""（空文字列）
var b bool      // false
var p *int      // nil（Python の None に近い）

fmt.Println(i, f, s, b, p)
// 出力: 0 0  false <nil>""")

    code_block("Python で同じことをすると", """\
# Python
print(x)  # NameError: name 'x' is not defined
# Python には「宣言だけして初期値なし」という概念がない""")

    subsection("2-4. 定数 const")

    code_block("Go", """\
const Pi = 3.14159      // 変更不可
const MaxRetry = 3

// const は := では宣言できない
// Pi = 3.0  → コンパイルエラー""")

    code_block("Python", """\
# Python には const がない。慣習で大文字にするだけ
PI = 3.14159      # 変更しないでね（でも変更できてしまう）
PI = 3.0          # Python では何も起きない""")

    subsection("2-5. ポインタ ── Python にはない概念")

    print(textwrap.dedent("""\
    ポインタは「変数のメモリ上の住所」を保持する変数。

    たとえ話:
      変数 x = 42 は「家の中に 42 という荷物がある」
      ポインタ p = &x は「その家の住所が書かれたメモ」

      *p で「住所にある家の中身を見る」（42 が返る）
      &x で「この家の住所を教えて」（住所がポインタに入る）
    """))

    code_block("Go のポインタ", """\
x := 42
p := &x          // p は x の「住所」を持つ。型は *int

fmt.Println(*p)  // 42 ← 住所をたどって中身を見る
*p = 100         // 住所をたどって中身を書き換える
fmt.Println(x)   // 100 ← x 自体が変わった！

// なぜ必要か？ Go は「値渡し」がデフォルトだから。
func double(n int) {
    n = n * 2    // これはコピーを変更しているだけ。呼び出し元に影響しない。
}

func doublePtr(n *int) {
    *n = *n * 2  // ポインタ経由で呼び出し元の値を変更する。
}""")

    code_block("Python との比較", """\
# Python は全てが「参照」。ポインタを意識する必要がない。
x = [1, 2, 3]
y = x          # y は x と同じリストを「参照」している
y.append(4)
print(x)       # [1, 2, 3, 4] ← x も変わる

# しかし int などのイミュータブル型では参照が切れる
a = 42
b = a
b = 100
print(a)       # 42 ← a は変わらない（新しいオブジェクトが作られた）""")

    point("Go のデフォルトは値渡し（コピー）。Python のデフォルトは参照渡し。")
    point("Go でポインタを使うのは「呼び出し元を変更したい」「大きな構造体のコピーを避けたい」とき。")
    print()

    question("Go で大きな構造体を関数に渡すとき、ポインタを使わないとどうなる？性能への影響は？")


# ============================================================
# 3. 文字列
# ============================================================

def chapter_3_strings():
    section("3. 文字列 ── バイト列と rune の世界")

    print(textwrap.dedent("""\
    Python の str は Unicode 文字のシーケンス。
    Go の string はバイト列（[]byte）。文字単位で扱うには rune を使う。

    この違いは日本語処理で顕著に現れる。
    """))

    subsection("3-1. 基本操作の対照")

    code_block("Python", """\
name = "Alice"
greeting = f"Hello, {name}!"         # f-string
joined = ", ".join(["a", "b", "c"])   # "a, b, c"
has = "llo" in "hello"               # True
starts = "hello".startswith("he")    # True""")

    code_block("Go", """\
name := "Alice"
greeting := fmt.Sprintf("Hello, %s!", name)  // f-string に相当
joined := strings.Join([]string{"a", "b", "c"}, ", ")  // "a, b, c"
has := strings.Contains("hello", "llo")       // true
starts := strings.HasPrefix("hello", "he")    // true""")

    subsection("3-2. Raw 文字列")

    code_block("Python", """\
path = r"C:\\Users\\alice"   # raw string""")

    code_block("Go", """\
path := `C:\\Users\\alice`     // バッククォートで raw string
multiline := `
これは
複数行の
文字列です
`  // Python の三重引用符 \"\"\" に相当""")

    subsection("3-3. rune と UTF-8")

    print(textwrap.dedent("""\
    Go の文字列はバイト列。日本語1文字は3バイト（UTF-8）。
    """))

    code_block("Go", """\
s := "こんにちは"
fmt.Println(len(s))         // 15 ← バイト数！文字数ではない
fmt.Println(len([]rune(s))) // 5  ← rune に変換すると文字数になる

// range で文字単位にイテレート
for i, r := range s {
    fmt.Printf("byte=%d rune=%c\\n", i, r)
}
// byte=0 rune=こ
// byte=3 rune=ん    ← バイトインデックスが3ずつ飛ぶ
// byte=6 rune=に
// ...
""")

    code_block("Python", """\
s = "こんにちは"
print(len(s))          # 5 ← Python は文字数を返す
print(len(s.encode())) # 15 ← バイト数が欲しいなら encode()""")

    point("Go: len(s) はバイト数。Python: len(s) は文字数。日本語で混乱しやすい。")
    print()

    question("Go で文字列を逆順にするには？ バイト列をそのまま逆にすると壊れる理由は？")


# ============================================================
# 4. 制御構文
# ============================================================

def chapter_4_control_flow():
    section("4. 制御構文 ── for が全てを支配する")

    subsection("4-1. if 文")

    code_block("Python", """\
x = 10
if x > 5:
    print("big")
elif x > 0:
    print("positive")
else:
    print("zero or negative")""")

    code_block("Go", """\
x := 10
if x > 5 {              // 括弧は不要（書いてもいいが gofmt が消す）
    fmt.Println("big")
} else if x > 0 {
    fmt.Println("positive")
} else {
    fmt.Println("zero or negative")
}""")

    subsection("4-2. if err != nil ── Go 文化の核心")

    print(textwrap.dedent("""\
    Go のコードを読むと、3行に1回は目にするパターン:
    """))

    code_block("Go", """\
file, err := os.Open("data.txt")
if err != nil {
    return fmt.Errorf("failed to open file: %w", err)
}
defer file.Close()

// Python なら try/except で書くところを、Go では毎回明示的にチェックする。
// 冗長に見えるが「エラーを無視できない」という設計思想。""")

    code_block("Python で同等の処理", """\
try:
    file = open("data.txt")
except FileNotFoundError as e:
    raise RuntimeError(f"failed to open file: {e}") from e""")

    subsection("4-3. for ── Go 唯一のループ")

    print(textwrap.dedent("""\
    Go には while がない。for が全てのループを担う。
    """))

    code_block("C風の for", """\
// Go
for i := 0; i < 10; i++ {
    fmt.Println(i)
}

# Python
for i in range(10):
    print(i)""")

    code_block("while 相当", """\
// Go（条件だけの for = while）
n := 1
for n < 100 {
    n *= 2
}

# Python
n = 1
while n < 100:
    n *= 2""")

    code_block("無限ループ", """\
// Go
for {
    // break で抜ける
    break
}

# Python
while True:
    break""")

    code_block("range ループ（最も頻出）", """\
// Go
nums := []int{10, 20, 30}
for i, v := range nums {
    fmt.Printf("index=%d value=%d\\n", i, v)
}
// インデックスが不要なら _ で捨てる
for _, v := range nums {
    fmt.Println(v)
}

# Python
nums = [10, 20, 30]
for i, v in enumerate(nums):
    print(f"index={i} value={v}")
for v in nums:
    print(v)""")

    subsection("4-4. switch")

    code_block("Go", """\
day := "Monday"
switch day {
case "Monday":
    fmt.Println("週の始まり")    // break 不要！自動で止まる
case "Friday":
    fmt.Println("花金")
default:
    fmt.Println("普通の日")
}

// Python 3.10+ の match に似ている
// ただし Go の switch は fall through がデフォルトでない（安全）""")

    code_block("Python 3.10+", """\
day = "Monday"
match day:
    case "Monday":
        print("週の始まり")
    case "Friday":
        print("花金")
    case _:
        print("普通の日")""")

    point("Go の switch は break 不要。Java/C では break を忘れるバグが頻発するが、Go では起きない。")
    print()

    task("Go の switch で「型スイッチ (type switch)」を調べてみよう。Python の isinstance に相当する。")


# ============================================================
# 5. 関数
# ============================================================

def chapter_5_functions():
    section("5. 関数 ── 複数戻り値と defer")

    subsection("5-1. 基本的な関数定義")

    code_block("Python", """\
def add(a: int, b: int) -> int:
    return a + b""")

    code_block("Go", """\
func add(a, b int) int {     // 同じ型はまとめて書ける
    return a + b
}""")

    subsection("5-2. 複数戻り値 ── Go 最大の特徴の1つ")

    print(textwrap.dedent("""\
    Go の関数は複数の値を返せる。これはエラーハンドリングの核心。
    """))

    code_block("Go", """\
func divide(a, b float64) (float64, error) {
    if b == 0 {
        return 0, fmt.Errorf("division by zero")
    }
    return a / b, nil    // nil = エラーなし
}

// 呼び出し側
result, err := divide(10, 3)
if err != nil {
    log.Fatal(err)       // エラーならプログラム終了
}
fmt.Println(result)      // 3.3333...
""")

    code_block("Python で同じパターン", """\
def divide(a: float, b: float) -> tuple[float, Exception | None]:
    if b == 0:
        return 0, ValueError("division by zero")
    return a / b, None

# しかし Python ではこう書かない。例外を raise する:
def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("division by zero")
    return a / b""")

    point("Go は例外を投げない。戻り値でエラーを返す。これが Go の設計哲学。")
    print()

    subsection("5-3. 名前付き戻り値")

    code_block("Go", """\
func divide(a, b float64) (result float64, err error) {
    if b == 0 {
        err = fmt.Errorf("division by zero")
        return    // result=0.0(ゼロ値), err=エラー が返る
    }
    result = a / b
    return        // result=計算結果, err=nil が返る
}""")

    subsection("5-4. 関数は第一級オブジェクト")

    code_block("Go", """\
// 変数に関数を代入
square := func(n int) int { return n * n }
fmt.Println(square(5))  // 25

// 関数を引数に取る
func apply(f func(int) int, n int) int {
    return f(n)
}
fmt.Println(apply(square, 3))  // 9""")

    code_block("Python", """\
square = lambda n: n * n
print(square(5))  # 25

def apply(f, n):
    return f(n)
print(apply(square, 3))  # 9""")

    subsection("5-5. クロージャ")

    code_block("Go", """\
func counter() func() int {
    count := 0
    return func() int {
        count++           // 外側の変数をキャプチャ
        return count
    }
}

c := counter()
fmt.Println(c())  // 1
fmt.Println(c())  // 2
fmt.Println(c())  // 3""")

    code_block("Python", """\
def counter():
    count = 0
    def inc():
        nonlocal count    # nonlocal が必要
        count += 1
        return count
    return inc

c = counter()
print(c())  # 1
print(c())  # 2""")

    subsection("5-6. defer ── 関数終了時に必ず実行")

    code_block("Go", """\
func readFile(path string) error {
    f, err := os.Open(path)
    if err != nil {
        return err
    }
    defer f.Close()    // ← この関数が終わる時に必ず Close() される
                       //   return の前に自動実行
    // ... ファイルを読む処理 ...
    return nil
}""")

    code_block("Python で同等の処理", """\
# with 文（コンテキストマネージャ）が defer に相当
def read_file(path: str) -> None:
    with open(path) as f:    # ← ブロック終了時に自動 close
        # ... ファイルを読む処理 ...
        pass

# または try/finally
def read_file(path: str) -> None:
    f = open(path)
    try:
        # ... 処理 ...
        pass
    finally:
        f.close()            # ← defer f.Close() に相当""")

    point("defer は LIFO（後入れ先出し）で実行される。複数の defer は逆順に実行。")
    print()

    question("defer fmt.Println(x) と書いたとき、x の値は defer 宣言時 / 実行時のどちら？")


# ============================================================
# 6. 構造体 (struct)
# ============================================================

def chapter_6_structs():
    section("6. 構造体 (struct) ── Python の class に相当")

    subsection("6-1. 基本的な構造体定義")

    code_block("Go", """\
type User struct {
    Name string
    Age  int
}

// インスタンス生成
u := User{Name: "Alice", Age: 30}
fmt.Println(u.Name)  // Alice""")

    code_block("Python", """\
class User:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

u = User(name="Alice", age=30)
print(u.name)  # Alice""")

    subsection("6-2. メソッド ── レシーバー付き関数")

    code_block("Go", """\
// User にメソッドを追加
func (u *User) Greet() string {
    return fmt.Sprintf("Hi, I'm %s (%d)", u.Name, u.Age)
}

// u *User は「レシーバー」。Python の self に相当。
// ポインタレシーバー (*User) にすると、メソッド内で構造体を変更できる。

u := &User{Name: "Alice", Age: 30}
fmt.Println(u.Greet())  // Hi, I'm Alice (30)""")

    code_block("Python", """\
class User:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

    def greet(self) -> str:       # self がレシーバーに相当
        return f"Hi, I'm {self.name} ({self.age})"

u = User("Alice", 30)
print(u.greet())""")

    subsection("6-3. コンストラクタパターン")

    print(textwrap.dedent("""\
    Go にはコンストラクタ（__init__）がない。
    代わりに New で始まる関数を作る慣習がある。
    """))

    code_block("Go", """\
func NewUser(name string, age int) *User {
    if age < 0 {
        age = 0
    }
    return &User{Name: name, Age: age}
}

u := NewUser("Bob", 25)""")

    subsection("6-4. 埋め込み (Embedding) ── 継承ではなくコンポジション")

    print(textwrap.dedent("""\
    Go にクラス継承は存在しない。代わりに「埋め込み」で機能を合成する。
    """))

    code_block("Go", """\
type Animal struct {
    Name string
}

func (a Animal) Speak() string {
    return a.Name + " makes a sound"
}

type Dog struct {
    Animal        // ← Animal を埋め込む（継承ではない）
    Breed string
}

d := Dog{
    Animal: Animal{Name: "Rex"},
    Breed:  "Labrador",
}
fmt.Println(d.Speak())  // Rex makes a sound
fmt.Println(d.Name)     // Rex ← Animal のフィールドに直接アクセスできる""")

    code_block("Python の継承", """\
class Animal:
    def __init__(self, name: str):
        self.name = name
    def speak(self) -> str:
        return f"{self.name} makes a sound"

class Dog(Animal):        # ← 継承
    def __init__(self, name: str, breed: str):
        super().__init__(name)
        self.breed = breed

d = Dog("Rex", "Labrador")
print(d.speak())  # Rex makes a sound""")

    point("Go の設計思想: 「継承より合成 (composition over inheritance)」を言語レベルで強制。")
    print()

    question("Go の埋め込みと Python の継承で、メソッドの衝突が起きたらどうなる？")


# ============================================================
# 7. インターフェース
# ============================================================

def chapter_7_interfaces():
    section("7. インターフェース ── Go 最大の設計思想")

    print(textwrap.dedent("""\
    Go のインターフェースは「暗黙的に実装される」。
    implements キーワードは存在しない。

    メソッドのシグネチャが一致すれば、自動的にそのインターフェースを満たす。
    これは Python のダックタイピングに似ているが、コンパイル時に検証される。
    """))

    subsection("7-1. インターフェース定義と実装")

    code_block("Go", """\
// インターフェース定義
type Writer interface {
    Write(data []byte) (int, error)
}

// 構造体
type FileWriter struct {
    Path string
}

// Write メソッドを実装 → 自動的に Writer インターフェースを満たす
func (fw *FileWriter) Write(data []byte) (int, error) {
    // ... ファイルに書き込む処理 ...
    return len(data), nil
}

// Writer を引数に取る関数（FileWriter を渡せる）
func Save(w Writer, data []byte) error {
    _, err := w.Write(data)
    return err
}""")

    code_block("Python で同等の設計", """\
from abc import ABC, abstractmethod

class Writer(ABC):                            # 抽象基底クラス
    @abstractmethod
    def write(self, data: bytes) -> int: ...

class FileWriter(Writer):                     # 明示的に継承が必要
    def __init__(self, path: str):
        self.path = path
    def write(self, data: bytes) -> int:
        # ... ファイルに書き込む処理 ...
        return len(data)

# または Protocol（Python 3.8+）← Go のインターフェースに近い
from typing import Protocol

class Writer(Protocol):
    def write(self, data: bytes) -> int: ...  # 暗黙的に満たせる""")

    point("Go: 暗黙的実装。implements 不要。ライブラリの型も後からインターフェースを満たせる。")
    point("Python ABC: 明示的継承が必要。Protocol は Go に近いが、実行時チェックがない。")
    print()

    subsection("7-2. 標準インターフェース")

    print(textwrap.dedent("""\
    Go の標準ライブラリは小さなインターフェースで設計されている:

      io.Reader:    Read(p []byte) (n int, err error)
      io.Writer:    Write(p []byte) (n int, err error)
      fmt.Stringer: String() string     ← Python の __str__ に相当
      error:        Error() string      ← Python の Exception に相当

    インターフェースは小さいほど良い（1-2メソッド）。
    これが Go の設計原則。
    """))

    subsection("7-3. 空インターフェース interface{} / any")

    code_block("Go", """\
// 空インターフェース = 全ての型が満たす = Python の Any
func printAnything(v interface{}) {
    fmt.Println(v)
}
// Go 1.18 以降は any と書ける（interface{} のエイリアス）
func printAnything(v any) {
    fmt.Println(v)
}

printAnything(42)
printAnything("hello")
printAnything(true)""")

    code_block("Python", """\
from typing import Any

def print_anything(v: Any) -> None:
    print(v)""")

    question("Go のインターフェースが「小さいほど良い」のはなぜ？大きなインターフェースの問題点は？")


# ============================================================
# 8. エラーハンドリング
# ============================================================

def chapter_8_error_handling():
    section("8. エラーハンドリング ── Go で最も議論される設計")

    print(textwrap.dedent("""\
    Go の哲学: 「エラーは値。明示的に処理せよ。」
    Python の哲学: 「例外を投げて、必要な場所で catch せよ。」

    Go のやり方は冗長だが、「エラーを見落とす」ことがほぼ不可能になる。
    """))

    subsection("8-1. 基本パターン")

    code_block("Go", """\
result, err := doSomething()
if err != nil {
    return fmt.Errorf("doSomething failed: %w", err)  // %w でラップ
}
// ここに来た = エラーなし。result を安全に使える。""")

    code_block("Python", """\
try:
    result = do_something()
except SomeError as e:
    raise RuntimeError(f"do_something failed: {e}") from e""")

    subsection("8-2. error インターフェース")

    code_block("Go", """\
// error は単なるインターフェース
type error interface {
    Error() string
}

// カスタムエラーの作り方
type NotFoundError struct {
    ID string
}

func (e *NotFoundError) Error() string {
    return fmt.Sprintf("not found: %s", e.ID)
}

// 使う側
func findUser(id string) (*User, error) {
    // ...
    return nil, &NotFoundError{ID: id}
}""")

    code_block("Python のカスタム例外", """\
class NotFoundError(Exception):
    def __init__(self, id: str):
        self.id = id
        super().__init__(f"not found: {id}")""")

    subsection("8-3. エラーのラップとチェーン検査")

    code_block("Go", """\
// エラーをラップ
err := fmt.Errorf("database query failed: %w", originalErr)

// チェーンの中に特定のエラーがあるか検査
if errors.Is(err, sql.ErrNoRows) {
    // レコードが見つからなかった
}

// 特定の型のエラーを取り出す
var notFound *NotFoundError
if errors.As(err, &notFound) {
    fmt.Println(notFound.ID)
}""")

    code_block("Python で同等の処理", """\
try:
    result = query_database()
except Exception as e:
    raise RuntimeError("database query failed") from e

# チェーン検査
try:
    do_something()
except RuntimeError as e:
    if isinstance(e.__cause__, FileNotFoundError):
        # 元のエラーが FileNotFoundError だった
        pass""")

    subsection("8-4. panic / recover ── 本当に続行不能な場合だけ")

    print(textwrap.dedent("""\
    panic は Python の例外に近いが、使用場面が全く違う。

    panic を使う場面:
      - プログラムの初期化に失敗（設定ファイルがない等）
      - プログラマのバグ（nil ポインタ参照等）
      - 絶対に起きてはいけない状況

    panic を使わない場面:
      - ファイルが見つからない → error を返す
      - ネットワークエラー → error を返す
      - ユーザー入力が不正 → error を返す
    """))

    code_block("Go", """\
// panic: プログラムがクラッシュする
func mustParseConfig(path string) Config {
    cfg, err := parseConfig(path)
    if err != nil {
        panic(fmt.Sprintf("config parse failed: %v", err))
    }
    return cfg
}

// recover: panic を捕まえる（defer 内でのみ使える）
func safeCall(f func()) (err error) {
    defer func() {
        if r := recover(); r != nil {
            err = fmt.Errorf("recovered: %v", r)
        }
    }()
    f()
    return nil
}""")

    point("日常の Go コードで panic を見たら「設計がおかしい」と疑ってよい。")
    point("error を返すのが Go の正道。panic は最終手段。")
    print()

    question("Python では例外を投げるのが正道。Go ではエラー値を返すのが正道。どちらが良い設計か？")


# ============================================================
# 9. スライスとマップ
# ============================================================

def chapter_9_slices_and_maps():
    section("9. スライスとマップ ── Go のコレクション")

    subsection("9-1. スライス ── Python の list に相当")

    code_block("Go", """\
// 宣言と初期化
nums := []int{1, 2, 3, 4, 5}

// 要素アクセス
fmt.Println(nums[0])   // 1
fmt.Println(nums[1:3]) // [2 3] ← Python と同じスライス構文！

// 追加（重要: 返り値を受け取る必要がある）
nums = append(nums, 6)
nums = append(nums, 7, 8, 9)

// 長さとキャパシティ
fmt.Println(len(nums)) // 9（要素数）
fmt.Println(cap(nums)) // キャパシティ（確保済みメモリ）""")

    code_block("Python", """\
nums = [1, 2, 3, 4, 5]

print(nums[0])    # 1
print(nums[1:3])  # [2, 3]

nums.append(6)            # 返り値なし（Go との大きな違い）
nums.extend([7, 8, 9])

print(len(nums))  # 9
# Python にはキャパシティの概念がない""")

    subsection("9-2. make ── 長さとキャパシティの指定")

    print(textwrap.dedent("""\
    Go のスライスは「長さ (length)」と「キャパシティ (capacity)」を持つ。
    キャパシティは「背後の配列のサイズ」。

    append でキャパシティを超えると、新しい配列が確保される（コストが高い）。
    事前にキャパシティを指定すると効率的。
    """))

    code_block("Go", """\
// make(型, 長さ, キャパシティ)
s := make([]int, 0, 100)  // 長さ0、キャパシティ100
// → 100要素分のメモリを事前確保。append が高速。

// Python で近い発想:
# arr = [None] * 100  # ← 事前確保に相当するが、Go ほど厳密ではない""")

    subsection("9-3. マップ ── Python の dict に相当")

    code_block("Go", """\
// 宣言と初期化
ages := map[string]int{
    "Alice": 30,
    "Bob":   25,
}

// 要素アクセス
fmt.Println(ages["Alice"])  // 30

// 存在確認（重要パターン）
val, ok := ages["Charlie"]
if !ok {
    fmt.Println("Charlie not found")
}

// 追加・更新
ages["Charlie"] = 35

// 削除
delete(ages, "Bob")

// イテレーション
for name, age := range ages {
    fmt.Printf("%s: %d\\n", name, age)
}""")

    code_block("Python", """\
ages = {"Alice": 30, "Bob": 25}

print(ages["Alice"])         # 30

# 存在確認
val = ages.get("Charlie")    # None（Go の val, ok パターンに相当）
if "Charlie" not in ages:
    print("Charlie not found")

ages["Charlie"] = 35         # 追加
del ages["Bob"]              # 削除

for name, age in ages.items():
    print(f"{name}: {age}")""")

    point("Go の val, ok := m[key] は Python の .get() + 存在チェックを1行でやる。")
    point("Go のマップは順序が保証されない。Python 3.7+ の dict は挿入順を保持する。")
    print()

    task("Go で「単語の出現回数を数えるプログラム」を書いてみよう（map[string]int を使う）。")


# ============================================================
# 10. 並行処理 (goroutine & channel)
# ============================================================

def chapter_10_concurrency():
    section("10. 並行処理 ── goroutine & channel（Go の最大の売り）")

    print(textwrap.dedent("""\
    Go の並行処理が強力な理由:
    - goroutine は OS スレッドより遥かに軽量（数KB）
    - channel で安全にデータをやり取り
    - 「メモリを共有して通信するな。通信してメモリを共有せよ。」

    Python の並行処理の課題:
    - GIL のせいで threading は CPU バウンドに効かない
    - asyncio は I/O バウンド専用
    - multiprocessing はプロセス間通信が複雑
    """))

    subsection("10-1. goroutine ── 超軽量スレッド")

    code_block("Go", """\
func sayHello(name string) {
    fmt.Printf("Hello, %s!\\n", name)
}

// go キーワードを付けるだけで並行実行
go sayHello("Alice")    // 即座に次の行へ進む
go sayHello("Bob")

// 無名関数でも OK
go func() {
    fmt.Println("goroutine from anonymous func")
}()

// 注意: main が先に終わると goroutine も道連れで終了する""")

    code_block("Python で同等の処理", """\
import threading
import asyncio

# threading
t = threading.Thread(target=say_hello, args=("Alice",))
t.start()

# asyncio
async def say_hello(name: str):
    print(f"Hello, {name}!")

async def main():
    await asyncio.gather(
        say_hello("Alice"),
        say_hello("Bob"),
    )""")

    point("goroutine の起動コスト: 約 2KB。OS スレッド: 約 1MB。1000倍の差。")
    point("Go のランタイムが goroutine を OS スレッドに自動マッピングする (M:N スケジューリング)。")
    print()

    subsection("10-2. channel ── goroutine 間の通信パイプ")

    code_block("Go", """\
// チャネルの作成
ch := make(chan int)

// goroutine で送信
go func() {
    ch <- 42    // チャネルに値を送る（受信側がいないとブロック）
}()

// メインで受信
value := <-ch    // チャネルから値を受け取る（送信側がいないとブロック）
fmt.Println(value)  // 42""")

    code_block("Python で近い発想", """\
import queue

q = queue.Queue()

# 別スレッドで送信
def sender():
    q.put(42)

import threading
t = threading.Thread(target=sender)
t.start()

value = q.get()   # ブロックして待つ
print(value)      # 42""")

    subsection("10-3. バッファ付きチャネル")

    code_block("Go", """\
// バッファサイズ 3 のチャネル
ch := make(chan int, 3)

ch <- 1   // ブロックしない（バッファに空きがある）
ch <- 2   // ブロックしない
ch <- 3   // ブロックしない
// ch <- 4  // ← ここでブロックする（バッファが満杯）

fmt.Println(<-ch)  // 1
fmt.Println(<-ch)  // 2""")

    subsection("10-4. select ── 複数チャネルの同時待ち受け")

    code_block("Go", """\
ch1 := make(chan string)
ch2 := make(chan string)

go func() {
    time.Sleep(1 * time.Second)
    ch1 <- "one"
}()
go func() {
    time.Sleep(2 * time.Second)
    ch2 <- "two"
}()

// 先に来た方を処理
select {
case msg := <-ch1:
    fmt.Println("ch1:", msg)
case msg := <-ch2:
    fmt.Println("ch2:", msg)
case <-time.After(3 * time.Second):
    fmt.Println("timeout")
}
// → "ch1: one" が出力される（ch1 の方が先に送信するから）""")

    subsection("10-5. sync.WaitGroup ── 全 goroutine の完了を待つ")

    code_block("Go", """\
var wg sync.WaitGroup

for i := 0; i < 5; i++ {
    wg.Add(1)               // カウンタ +1
    go func(id int) {
        defer wg.Done()     // 完了時にカウンタ -1
        fmt.Printf("Worker %d done\\n", id)
    }(i)
}

wg.Wait()  // カウンタが 0 になるまでブロック""")

    code_block("Python (asyncio)", """\
async def worker(id: int):
    print(f"Worker {id} done")

async def main():
    await asyncio.gather(*[worker(i) for i in range(5)])""")

    subsection("10-6. sync.Mutex ── 排他ロック")

    code_block("Go", """\
type SafeCounter struct {
    mu    sync.Mutex
    count int
}

func (c *SafeCounter) Increment() {
    c.mu.Lock()         // ロック取得
    defer c.mu.Unlock() // 関数終了時にロック解放
    c.count++
}""")

    code_block("Python", """\
import threading

class SafeCounter:
    def __init__(self):
        self._lock = threading.Lock()
        self.count = 0

    def increment(self):
        with self._lock:      # with 文でロック管理
            self.count += 1""")

    subsection("10-7. context.Context ── タイムアウトとキャンセル")

    print(textwrap.dedent("""\
    context.Context は Go の並行処理で最も重要な概念の1つ。
    「この処理をキャンセルしたい」「タイムアウトを設定したい」を伝播する仕組み。
    """))

    code_block("Go", """\
// 5秒のタイムアウト付きコンテキスト
ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
defer cancel()

// HTTP リクエストにコンテキストを渡す
req, _ := http.NewRequestWithContext(ctx, "GET", url, nil)
resp, err := client.Do(req)
// → 5秒以内にレスポンスがなければ自動キャンセル

// 手動キャンセル
ctx, cancel := context.WithCancel(context.Background())
go func() {
    // ... 長い処理 ...
    select {
    case <-ctx.Done():
        fmt.Println("cancelled:", ctx.Err())
        return
    }
}()
cancel()  // ← goroutine をキャンセル""")

    code_block("Python で近い発想", """\
import asyncio

async def fetch(url: str):
    try:
        async with asyncio.timeout(5):  # Python 3.11+
            # ... HTTPリクエスト ...
            pass
    except asyncio.TimeoutError:
        print("timeout")""")

    point("Go の関数で context.Context を第1引数に取るのは慣習。ほぼ必須。")
    print()

    question("goroutine がリークする（終了しない）パターンは？ context で防ぐ方法は？")


# ============================================================
# 11. パッケージとモジュール
# ============================================================

def chapter_11_packages():
    section("11. パッケージとモジュール")

    subsection("11-1. プロジェクトの始め方")

    code_block("Go", """\
$ mkdir myapp && cd myapp
$ go mod init github.com/yourname/myapp
# → go.mod ファイルが生成される

# ディレクトリ構造
myapp/
  go.mod          # Python の pyproject.toml に相当
  go.sum          # Python の poetry.lock に相当
  main.go
  handler/
    user.go       # package handler""")

    code_block("Python", """\
$ mkdir myapp && cd myapp
$ poetry init
# → pyproject.toml が生成される

myapp/
  pyproject.toml
  poetry.lock
  main.py
  handler/
    user.py
    __init__.py   # Go にはこれが不要""")

    subsection("11-2. 公開/非公開 ── 大文字/小文字ルール")

    print(textwrap.dedent("""\
    Go の最もユニークなルール:
      大文字で始まる名前 = public (パッケージ外からアクセス可能)
      小文字で始まる名前 = private (パッケージ内のみ)
    """))

    code_block("Go", """\
package user

type User struct {     // ← 大文字 = public
    Name string        // ← 大文字 = public
    age  int           // ← 小文字 = private（パッケージ外から見えない）
}

func NewUser() *User { // ← 大文字 = public
    return &User{}
}

func validate() bool { // ← 小文字 = private
    return true
}""")

    code_block("Python の規約", """\
class User:
    def __init__(self):
        self.name = ""       # public（規約上）
        self._age = 0        # private（規約上、アクセスは可能）
        self.__secret = ""   # name mangling（強めの private）

def _validate():             # private（規約上）
    return True""")

    point("Go の公開/非公開はコンパイラが強制する。Python の _ は規約であり、破れる。")
    print()

    subsection("11-3. 依存管理")

    code_block("Go", """\
$ go get github.com/gin-gonic/gin    # パッケージをインストール
# → go.mod に自動追加される

$ go mod tidy                         # 未使用の依存を削除""")

    code_block("Python", """\
$ pip install flask                   # パッケージをインストール
$ poetry add flask                    # poetry の場合

$ pip freeze > requirements.txt       # 依存をファイルに書き出す""")

    question("Go はなぜ __init__.py のようなファイルが不要なのか？パッケージの認識方法の違いは？")


# ============================================================
# 12. Python vs Go 対照表まとめ
# ============================================================

def chapter_12_comparison_table():
    section("12. Python vs Go 対照表まとめ")

    widths = [24, 28, 28]

    print(table_sep(widths))
    print(table_row(["概念", "Python", "Go"], widths))
    print(table_sep(widths))

    rows = [
        ["型システム",           "動的型付け",                "静的型付け"],
        ["実行方式",             "インタプリタ",              "コンパイル (go run も可)"],
        ["変数宣言",             "x = 10",                   "x := 10 / var x int"],
        ["定数",                 "慣習 (UPPER_CASE)",        "const キーワード"],
        ["ゼロ値",               "なし (NameError)",         "型ごとに定義 (0, \"\")"],
        ["ポインタ",             "なし (全て参照)",           "*T, &x"],
        ["文字列フォーマット",   "f\"Hello {name}\"",        "fmt.Sprintf(\"Hello %s\")"],
        ["リスト/配列",          "list",                     "[]T (スライス)"],
        ["辞書",                 "dict",                     "map[K]V"],
        ["ループ",               "for / while",              "for のみ"],
        ["イテレーション",       "for x in list:",           "for _, x := range list"],
        ["関数の戻り値",         "1つ (tuple で複数可)",     "複数戻り値 (ネイティブ)"],
        ["エラー処理",           "try / except",             "if err != nil"],
        ["クラス",               "class",                    "struct + メソッド"],
        ["継承",                 "class B(A):",              "埋め込み (embedding)"],
        ["インターフェース",     "ABC / Protocol",           "暗黙的実装"],
        ["公開/非公開",          "_ 規約",                   "大文字/小文字 (強制)"],
        ["並行処理",             "asyncio / threading",      "goroutine + channel"],
        ["パッケージ管理",       "pip / poetry",             "go mod"],
        ["フォーマッタ",         "black / autopep8",         "gofmt (公式唯一)"],
        ["REPL",                 "あり (python)",            "なし (公式には)"],
        ["NULL/nil",             "None",                     "nil (ポインタ等のみ)"],
        ["例外",                 "raise / except",           "panic / recover (非推奨)"],
        ["リソース管理",         "with 文",                  "defer"],
        ["ジェネリクス",         "TypeVar / Generic",        "Go 1.18+ で追加"],
    ]

    for row in rows:
        print(table_row(row, widths))

    print(table_sep(widths))
    print()


# ============================================================
# 優先度順まとめ
# ============================================================

def priority_summary():
    section("優先度順まとめ ── この順で覚える")

    print(textwrap.dedent("""\
    ★ 優先度順まとめ (この順で覚える):

    【Tier 1: 最優先 ── これがないとコードが読めない】
      - 変数宣言 (:= と var)
      - if err != nil パターン
      - 関数の複数戻り値
      - package / import / func main()

    【Tier 2: 重要 ── 実務で毎日使う】
      - スライスとマップ ([]T, map[K]V)
      - 構造体とメソッド (type, func (r *T) Method())
      - インターフェース (暗黙的実装)
      - for range ループ
      - 文字列操作 (fmt.Sprintf, strings パッケージ)

    【Tier 3: 上級 ── Go の真価を発揮】
      - goroutine と channel
      - select 文
      - context.Context
      - sync.WaitGroup / sync.Mutex

    【Tier 4: 実践 ── プロジェクトで必要】
      - パッケージ設計 (大文字/小文字ルール)
      - テスト (go test, *_test.go)
      - defer / panic / recover
      - go mod / 依存管理

    ★ 学習の進め方:
      1. まず「A Tour of Go」(https://go.dev/tour/) を一通りやる
      2. 小さな CLI ツールを1つ作る（ファイル処理、HTTP クライアントなど）
      3. HTTP サーバーを作る（net/http → gin/echo フレームワーク）
      4. goroutine を使った並行処理プログラムを書く
      5. 既存の OSS の Go コードを読む（Docker, Kubernetes など）
    """))

    task("Go の公式チュートリアル 'A Tour of Go' を完了する（所要時間: 約2-3時間）。")
    task("Python で書いた CLI ツールを Go で書き直す。エラーハンドリングの違いを体感する。")
    task("goroutine + channel で Web スクレイパーを作る。Python の asyncio 版と比較する。")


# ============================================================
# 13. プロジェクト構成
# ============================================================

def chapter_13_project_structure():
    section("13. 中規模以上のプロジェクト構成 ── Go の「Standard Layout」")

    print(textwrap.dedent("""\
    Go には公式の「標準レイアウト」はないが、コミュニティで広く使われている
    事実上の標準がある。Python の「好きにやれ」とは対照的に、
    Go は「みんな同じ構成にする」文化が強い。

    最も参考にされるのは:
      - golang-standards/project-layout (GitHub スター 45k+)
      - Go 公式ブログの "Organizing a Go module" (2023)
    """))

    subsection("13-1. 小〜中規模 (マイクロサービス / CLI)")

    code_block("Go: フラット構成 (小規模、推奨)",
    """\
my-service/
├── go.mod                 # モジュール定義 (= pyproject.toml)
├── go.sum                 # 依存ロック (= poetry.lock)
├── main.go                # エントリポイント (package main)
├── handler.go             # HTTP ハンドラー (= FastAPI の routers)
├── service.go             # ビジネスロジック
├── repository.go          # DB アクセス
├── model.go               # 構造体定義
├── handler_test.go        # テスト (同じディレクトリに _test.go)
├── service_test.go
├── Dockerfile
└── Makefile               # ビルド/テスト/lint のタスクランナー
""")

    point("Go はテストファイルを「同じディレクトリ」に置く (_test.go 接尾辞)")
    point("小規模なら1パッケージ (package main) で十分。無理に分けない")
    point("Python の tests/ ディレクトリ分離とは真逆の文化")
    print()

    subsection("13-2. 中〜大規模 (複数サービス / モノレポ)")

    code_block("Go: 標準的な中〜大規模レイアウト",
    """\
my-platform/
├── go.mod
├── go.sum
├── cmd/                           # エントリポイント群
│   ├── api-server/                # API サーバー
│   │   └── main.go                #   package main → func main()
│   ├── worker/                    # バックグラウンドワーカー
│   │   └── main.go
│   └── cli/                       # CLI ツール
│       └── main.go
├── internal/                      # ★ 外部からインポート不可 (Go の仕組み)
│   ├── handler/                   # HTTP ハンドラー
│   │   ├── user_handler.go
│   │   ├── order_handler.go
│   │   └── middleware.go
│   ├── service/                   # ビジネスロジック
│   │   ├── user_service.go
│   │   └── order_service.go
│   ├── repository/                # DB アクセス
│   │   ├── user_repo.go
│   │   └── postgres.go            # DB接続の初期化
│   ├── model/                     # ドメインモデル (構造体)
│   │   ├── user.go
│   │   └── order.go
│   └── config/                    # 設定の読み込み
│       └── config.go
├── pkg/                           # ★ 外部からインポート可能な共通ライブラリ
│   ├── logger/                    # ロガー
│   │   └── logger.go
│   └── middleware/                # 汎用ミドルウェア
│       └── auth.go
├── api/                           # API スキーマ定義
│   └── openapi.yaml               # OpenAPI (Swagger)
├── migrations/                    # DB マイグレーション
│   ├── 001_create_users.up.sql
│   └── 001_create_users.down.sql
├── scripts/                       # 運用スクリプト
│   └── seed.sh
├── deployments/                   # デプロイ設定
│   ├── Dockerfile
│   └── k8s/
│       ├── deployment.yaml
│       └── service.yaml
├── Makefile
└── README.md
""")

    subsection("13-3. Go 固有の重要ルール")

    point("internal/ — Go コンパイラが強制するアクセス制御。親モジュール以外からインポート不可")
    point("cmd/ — 複数のバイナリを1リポジトリで管理。各 main.go は薄いエントリポイント")
    point("pkg/ — 外部に公開する共通パッケージ。ただし最近は pkg/ を使わない流れもある")
    point("_test.go — テストは本番コードと同じディレクトリ。別パッケージ名 (xxx_test) も可")
    print()

    subsection("13-4. Python との対応関係")

    widths = [24, 28, 28]
    print(table_sep(widths))
    print(table_row(["概念", "Go", "Python (FastAPI)"], widths))
    print(table_sep(widths))
    rows = [
        ["エントリポイント",   "cmd/api-server/main.go", "app/main.py"],
        ["ルーティング",       "internal/handler/",      "app/routers/"],
        ["ビジネスロジック",   "internal/service/",      "app/services/"],
        ["DB アクセス",        "internal/repository/",   "app/repositories/"],
        ["データモデル",       "internal/model/",        "app/models/"],
        ["設定",               "internal/config/",       "app/config.py"],
        ["DBマイグレーション", "migrations/ (golang-migrate)","alembic/"],
        ["テスト",             "*_test.go (同じDir)",    "tests/ (別Dir)"],
        ["ビルド設定",         "go.mod + Makefile",      "pyproject.toml"],
        ["アクセス制御",       "internal/ (コンパイラ強制)","_prefix (慣習のみ)"],
        ["共通ライブラリ",     "pkg/",                   "app/utils/"],
    ]
    for r in rows:
        print(table_row(r, widths))
    print(table_sep(widths))
    print()

    question("Go の internal/ は「コンパイラが強制するプライベート」。\n"
             "    Python の _ prefix は「お願いベースのプライベート」。\n"
             "    チーム開発では、どちらが安全か？")


# ============================================================
# メイン
# ============================================================

def main():
    print()
    print("=" * 64)
    print("  Python使いのための Go 入門ガイド")
    print("  ── Python と対比しながら Go を基礎から学ぶ")
    print("=" * 64)

    chapter_1_hello_world()
    chapter_2_variables_and_types()
    chapter_3_strings()
    chapter_4_control_flow()
    chapter_5_functions()
    chapter_6_structs()
    chapter_7_interfaces()
    chapter_8_error_handling()
    chapter_9_slices_and_maps()
    chapter_10_concurrency()
    chapter_11_packages()
    chapter_12_comparison_table()
    priority_summary()
    chapter_13_project_structure()

    print()
    print("=" * 64)
    print("  おわり ── Go は「シンプルだが強力」。Python との対比で理解が深まる。")
    print("=" * 64)
    print()


if __name__ == "__main__":
    main()
