package kvstore;

import java.time.Instant;
import java.util.*;
import java.util.concurrent.*;
import java.util.function.*;
import java.util.stream.*;

/**
 * Java 17+ モダン機能デモ: Event Sourced Key-Value Store
 *
 * Python との対比で Java を学ぶ。
 * 各セクションに「Python だとこう書く」を併記。
 */
public class Main {

    // =========================================================
    // 1. Records — Python の dataclass / NamedTuple に相当
    // =========================================================
    // Python: @dataclass(frozen=True)
    //         class Point:
    //             x: float
    //             y: float
    //
    // Java Record: イミュータブル、equals/hashCode/toString 自動生成
    record Point(double x, double y) {
        // コンパクトコンストラクタ (バリデーション)
        Point {
            if (Double.isNaN(x) || Double.isNaN(y)) {
                throw new IllegalArgumentException("NaN is not allowed");
            }
        }

        // メソッド追加可能
        double distanceTo(Point other) {
            return Math.sqrt(Math.pow(x - other.x, 2) + Math.pow(y - other.y, 2));
        }
    }

    // =========================================================
    // 2. Sealed Interfaces — Python の Union + match に相当
    // =========================================================
    // Python: type Event = SetEvent | DeleteEvent | ClearEvent  (3.12+)
    //
    // Java: sealed で許可されたサブタイプを限定
    //       → コンパイラが switch の網羅性をチェック
    sealed interface Event permits SetEvent, DeleteEvent, ClearEvent {
        Instant timestamp();
    }

    record SetEvent(String key, String value, Instant timestamp) implements Event {}
    record DeleteEvent(String key, Instant timestamp) implements Event {}
    record ClearEvent(Instant timestamp) implements Event {}

    // =========================================================
    // 3. Generics — Python の TypeVar / Generic に相当
    // =========================================================
    // Python: T = TypeVar("T")
    //         class Result(Generic[T]): ...
    //
    // Java: 型消去 (type erasure) があるが、コンパイル時型安全
    sealed interface Result<T> permits Success, Failure {
        boolean isSuccess();
    }

    record Success<T>(T value) implements Result<T> {
        @Override public boolean isSuccess() { return true; }
    }

    record Failure<T>(String error) implements Result<T> {
        @Override public boolean isSuccess() { return false; }
    }

    // Bounded Generics: T は Comparable を実装していなければならない
    static <T extends Comparable<T>> T max(T a, T b) {
        return a.compareTo(b) >= 0 ? a : b;
    }

    // =========================================================
    // 4. Event Sourced Store — メイン実装
    // =========================================================
    static class EventStore {
        // イベントログ (append-only)
        private final List<Event> events = new ArrayList<>();
        // スナップショット (現在の状態)
        private final Map<String, String> snapshot = new LinkedHashMap<>();

        // --- Command: イベントを追加して状態を更新 ---
        Result<String> set(String key, String value) {
            if (key == null || key.isBlank()) {
                return new Failure<>("Key must not be blank");
            }
            var event = new SetEvent(key, value, Instant.now());
            events.add(event);
            snapshot.put(key, value);
            return new Success<>("OK");
        }

        Result<String> delete(String key) {
            if (!snapshot.containsKey(key)) {
                return new Failure<>("Key not found: " + key);
            }
            events.add(new DeleteEvent(key, Instant.now()));
            snapshot.remove(key);
            return new Success<>("Deleted");
        }

        void clear() {
            events.add(new ClearEvent(Instant.now()));
            snapshot.clear();
        }

        // --- Query: Optional で null 安全に ---
        // Python: def get(self, key: str) -> str | None:
        //             return self.data.get(key)
        Optional<String> get(String key) {
            return Optional.ofNullable(snapshot.get(key));
        }

        Map<String, String> getAll() {
            return Collections.unmodifiableMap(snapshot);
        }

        List<Event> getEvents() {
            return Collections.unmodifiableList(events);
        }

        int size() {
            return snapshot.size();
        }
    }

    // =========================================================
    // 5. Stream API — Python の list comprehension / itertools に相当
    // =========================================================
    static void demonstrateStreams(EventStore store) {
        System.out.println("\n── Stream API デモ ──");

        // Python: [e for e in events if isinstance(e, SetEvent)]
        var setEvents = store.getEvents().stream()
                .filter(e -> e instanceof SetEvent)
                .map(e -> (SetEvent) e)
                .toList();
        System.out.println("SET events: " + setEvents.size());

        // Python: {k: v for k, v in data.items() if v.startswith("A")}
        var filtered = store.getAll().entrySet().stream()
                .filter(e -> e.getValue().startsWith("A"))
                .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue));
        System.out.println("Values starting with 'A': " + filtered);

        // Python: from collections import Counter
        //         Counter(type(e).__name__ for e in events)
        var eventTypeCounts = store.getEvents().stream()
                .collect(Collectors.groupingBy(
                        e -> e.getClass().getSimpleName(),
                        Collectors.counting()
                ));
        System.out.println("Event type counts: " + eventTypeCounts);

        // Python: sum(len(v) for v in data.values())
        var totalValueLength = store.getAll().values().stream()
                .mapToInt(String::length)
                .sum();
        System.out.println("Total value length: " + totalValueLength);

        // reduce: Python の functools.reduce
        var allKeys = store.getAll().keySet().stream()
                .reduce((a, b) -> a + ", " + b)
                .orElse("(empty)");
        System.out.println("All keys: " + allKeys);
    }

    // =========================================================
    // 6. Pattern Matching (switch式) — Python の match/case に相当
    // =========================================================
    static String describeEvent(Event event) {
        // Python 3.10+:
        //   match event:
        //       case SetEvent(key=k, value=v): ...
        //       case DeleteEvent(key=k): ...
        //
        // Java 21 Preview (record patterns):
        //   case SetEvent(var k, var v, var t) -> ...
        // Java 17 (type pattern):
        return switch (event) {
            case SetEvent e -> "SET %s = %s".formatted(e.key(), e.value());
            case DeleteEvent e -> "DELETE %s".formatted(e.key());
            case ClearEvent e -> "CLEAR ALL";
        };
        // ★ sealed なので default 不要 — 全パターン網羅をコンパイラが保証
    }

    // =========================================================
    // 7. Functional Interfaces — Python のコールバック / lambda に相当
    // =========================================================
    // Python: def transform(data: dict, fn: Callable[[str], str]) -> dict:
    //             return {k: fn(v) for k, v in data.items()}
    static Map<String, String> transformValues(
            Map<String, String> data,
            Function<String, String> transformer
    ) {
        return data.entrySet().stream()
                .collect(Collectors.toMap(
                        Map.Entry::getKey,
                        e -> transformer.apply(e.getValue())
                ));
    }

    // Predicate 合成
    // Python: lambda x: x.startswith("A") and len(x) > 3
    static <T> Predicate<T> and(Predicate<T> a, Predicate<T> b) {
        return a.and(b);
    }

    // =========================================================
    // 8. CompletableFuture — Python の asyncio に相当
    // =========================================================
    static void demonstrateAsync() {
        System.out.println("\n── CompletableFuture (非同期処理) デモ ──");

        // Python:
        //   async def fetch(url):
        //       await asyncio.sleep(0.1)
        //       return f"data from {url}"
        //
        //   results = await asyncio.gather(fetch("a"), fetch("b"))

        var executor = Executors.newFixedThreadPool(3);

        try {
            var future1 = CompletableFuture.supplyAsync(() -> {
                sleep(100);
                return "Result from Service A";
            }, executor);

            var future2 = CompletableFuture.supplyAsync(() -> {
                sleep(150);
                return "Result from Service B";
            }, executor);

            var future3 = CompletableFuture.supplyAsync(() -> {
                sleep(50);
                return "Result from Service C";
            }, executor);

            // 全部待つ (Python: asyncio.gather)
            var allResults = CompletableFuture.allOf(future1, future2, future3)
                    .thenApply(v -> List.of(future1.join(), future2.join(), future3.join()));

            var results = allResults.get(5, TimeUnit.SECONDS);
            results.forEach(r -> System.out.println("  " + r));

            // チェーン (Python: result = await fetch("a"); processed = process(result))
            var chained = CompletableFuture.supplyAsync(() -> "raw data", executor)
                    .thenApply(String::toUpperCase)
                    .thenApply(s -> s + " [processed]")
                    .exceptionally(ex -> "Error: " + ex.getMessage());

            System.out.println("  Chained: " + chained.get(1, TimeUnit.SECONDS));

        } catch (Exception e) {
            System.err.println("Async error: " + e.getMessage());
        } finally {
            executor.shutdown();
        }
    }

    private static void sleep(long ms) {
        try { Thread.sleep(ms); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    }

    // =========================================================
    // 9. Text Blocks — Python の """triple quotes""" に相当
    // =========================================================
    static String generateReport(EventStore store) {
        // Python: f"""..."""
        // Java: Text Blocks (Java 15+)
        return """
                ╔══════════════════════════════════════╗
                ║  Event Store Report                  ║
                ╠══════════════════════════════════════╣
                ║  Total events:  %4d                 ║
                ║  Current keys:  %4d                 ║
                ║  Event types:                        ║
                %s
                ╚══════════════════════════════════════╝
                """.formatted(
                store.getEvents().size(),
                store.size(),
                store.getEvents().stream()
                        .collect(Collectors.groupingBy(e -> e.getClass().getSimpleName(), Collectors.counting()))
                        .entrySet().stream()
                        .map(e -> "                ║    %-14s %4d               ║".formatted(e.getKey(), e.getValue()))
                        .collect(Collectors.joining("\n"))
        );
    }

    // =========================================================
    // 10. var (型推論) & switch 式
    // =========================================================
    static String classifyValue(String value) {
        // Python: 型推論は自動 (動的型付け)
        // Java: var でローカル変数の型を推論 (Java 10+)
        var length = value.length();

        // switch 式 (Java 14+)
        if (length == 0) return "empty";
        if (length <= 3) return "short";
        if (length <= 10) return "medium";
        return "long";
    }

    // =========================================================
    // Main
    // =========================================================
    public static void main(String[] args) {
        System.out.println("╔══════════════════════════════════════════════════╗");
        System.out.println("║  Java 17+ Modern Features Demo                 ║");
        System.out.println("║  Event Sourced Key-Value Store                 ║");
        System.out.println("╚══════════════════════════════════════════════════╝");

        // --- Records ---
        System.out.println("\n── 1. Records ──");
        var p1 = new Point(3.0, 4.0);
        var p2 = new Point(0.0, 0.0);
        System.out.println("  Point: " + p1);  // 自動 toString
        System.out.println("  Distance: " + p1.distanceTo(p2));
        System.out.println("  Equals: " + p1.equals(new Point(3.0, 4.0)));  // 自動 equals

        // --- Sealed + Pattern Matching ---
        System.out.println("\n── 2. Sealed Interface + Pattern Matching ──");
        var store = new EventStore();
        store.set("name", "Alice");
        store.set("lang", "Java");
        store.set("level", "Advanced");
        store.delete("level");
        store.set("framework", "Spring Boot");

        store.getEvents().forEach(e ->
                System.out.println("  " + describeEvent(e)));

        // --- Generics + Result ---
        System.out.println("\n── 3. Generics (Result<T>) ──");
        var r1 = store.set("key1", "value1");
        var r2 = store.delete("nonexistent");
        System.out.println("  set key1: " + r1);     // Success
        System.out.println("  delete ??: " + r2);     // Failure
        System.out.println("  max(3,7): " + max(3, 7));

        // --- Optional ---
        System.out.println("\n── 4. Optional (null安全) ──");
        // Python: value = store.get("name") or "Unknown"
        var name = store.get("name").orElse("Unknown");
        var missing = store.get("age").orElse("N/A");
        System.out.println("  name: " + name);
        System.out.println("  age: " + missing);

        // Optional チェーン
        var upperName = store.get("name")
                .map(String::toUpperCase)
                .filter(s -> s.length() > 3)
                .orElse("too short");
        System.out.println("  upperName: " + upperName);

        // --- Stream API ---
        demonstrateStreams(store);

        // --- Functional Interfaces ---
        System.out.println("\n── 7. Functional Interfaces ──");
        var transformed = transformValues(store.getAll(), String::toUpperCase);
        System.out.println("  Uppercased: " + transformed);

        Predicate<String> startsWithA = s -> s.startsWith("A");
        Predicate<String> longerThan3 = s -> s.length() > 3;
        var combined = and(startsWithA, longerThan3);
        var matchingValues = store.getAll().values().stream()
                .filter(combined)
                .toList();
        System.out.println("  Starts with A & len>3: " + matchingValues);

        // --- CompletableFuture ---
        demonstrateAsync();

        // --- var + switch式 ---
        System.out.println("\n── 10. var & switch式 ──");
        for (var val : List.of("", "Hi", "Hello", "Hello World!")) {
            System.out.println("  \"%s\" → %s".formatted(val, classifyValue(val)));
        }

        // --- Report ---
        System.out.println("\n── Report ──");
        System.out.println(generateReport(store));

        // --- Python vs Java 比較まとめ ---
        System.out.println("""
                ┌────────────────────┬────────────────────┬────────────────────┐
                │ 機能                │ Python              │ Java 17+            │
                ├────────────────────┼────────────────────┼────────────────────┤
                │ Data Class         │ @dataclass          │ record              │
                │ Union Type         │ str | int           │ sealed interface    │
                │ Pattern Match      │ match/case          │ switch式 + pattern  │
                │ Null Safety        │ Optional[T] (型ヒント)│ Optional<T> (実装)  │
                │ Lambda             │ lambda x: x+1      │ x -> x+1           │
                │ List Comprehension │ [x for x in xs]    │ xs.stream().map()  │
                │ Async              │ async/await         │ CompletableFuture   │
                │ 型推論              │ 動的型付け           │ var (ローカル変数)   │
                │ 文字列              │ f"..."              │ "...".formatted()   │
                │ Immutable Data     │ frozen=True         │ record (デフォルト)  │
                └────────────────────┴────────────────────┴────────────────────┘
                """);
    }
}
