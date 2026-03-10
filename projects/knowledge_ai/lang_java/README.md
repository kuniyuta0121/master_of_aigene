# Java Event Sourcing Store

Java 17+ のモダン機能を学ぶ最小アプリ

## 起動
```bash
# コンパイル & 実行 (Maven不要、javac のみ)
javac -d out src/main/java/kvstore/*.java
java -cp out kvstore.Main

# または直接実行 (Java 11+)
java src/main/java/kvstore/Main.java
```

## 学べること
- Records (data class の代替)
- Sealed Interfaces / Pattern Matching (Java 17+)
- Optional<T> (null安全)
- Stream API (map, filter, collect, groupingBy)
- Generics (bounded, wildcard)
- Functional Interfaces (Function, Predicate, Consumer)
- CompletableFuture (非同期処理)
- var (ローカル変数型推論)
- Text Blocks (複数行文字列)
- switch式 (arrow syntax)
