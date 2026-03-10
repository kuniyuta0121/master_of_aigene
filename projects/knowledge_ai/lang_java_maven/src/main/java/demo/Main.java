package demo;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.reflect.TypeToken;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.*;
import java.lang.reflect.Type;
import java.nio.file.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.*;

/**
 * Maven + Repository 学習デモ
 *
 * ★ このファイルで学べること:
 *   1. Maven の依存ライブラリの使い方 (Gson, SLF4J)
 *   2. Repository パターン (データアクセスの抽象化)
 *   3. Java プロジェクト構成の慣習
 *   4. テスト (JUnit 5) との連携
 *
 * Python 対比:
 *   Maven       ≒ pip + pyproject.toml + setuptools
 *   Gson        ≒ json モジュール (ただし型安全)
 *   SLF4J       ≒ logging モジュール
 *   Repository  ≒ SQLAlchemy の Repository / Django の Manager
 *   JUnit 5     ≒ pytest
 */
public class Main {

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // 1. SLF4J ロギング
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // Python: logger = logging.getLogger(__name__)
    // Java:   private static final Logger logger = LoggerFactory.getLogger(Main.class);
    //
    // ★ SLF4J は「ファサード」(facade):
    //   - SLF4J 自体はログの「インターフェース」だけ
    //   - 実装は別ライブラリ (Logback, Log4j2, slf4j-simple 等)
    //   - pom.xml で実装を差し替え可能 → 疎結合
    //   - Python: logging モジュールは標準で一体型
    private static final Logger logger = LoggerFactory.getLogger(Main.class);

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // 2. モデル (Record)
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // Python: @dataclass
    //         class Task:
    //             id: str
    //             title: str
    //             done: bool = False
    record Task(
            String id,
            String title,
            String description,
            boolean done,
            String createdAt
    ) {
        // Gson がデシリアライズ時に使うためのファクトリメソッド
        static Task create(String title, String description) {
            return new Task(
                    UUID.randomUUID().toString().substring(0, 8),
                    title,
                    description,
                    false,
                    LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)
            );
        }

        Task markDone() {
            return new Task(id, title, description, true, createdAt);
        }
    }

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // 3. Repository パターン
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // Python: class TaskRepository(ABC):
    //             @abstractmethod
    //             def find_all(self) -> list[Task]: ...
    //
    // ★ Repository パターンとは:
    //   - データアクセスのロジックを1箇所に集約
    //   - ビジネスロジックは「どこに保存されるか」を知らない
    //   - テスト時はインメモリ実装に差し替え可能
    //   - Spring Data JPA, Django ORM の内部でも使われている考え方

    // --- インターフェース定義 ---
    // Python: class Repository(Protocol[T]):
    //             def find_all(self) -> list[T]: ...
    interface TaskRepository {
        List<Task> findAll();
        Optional<Task> findById(String id);
        Task save(Task task);
        boolean deleteById(String id);
        List<Task> findByDone(boolean done);
        long count();
    }

    // --- インメモリ実装 ---
    // Python: class InMemoryTaskRepo:
    //             def __init__(self): self.store: dict[str, Task] = {}
    static class InMemoryTaskRepository implements TaskRepository {
        // LinkedHashMap で挿入順を保持
        private final Map<String, Task> store = new LinkedHashMap<>();

        @Override
        public List<Task> findAll() {
            return List.copyOf(store.values());
        }

        @Override
        public Optional<Task> findById(String id) {
            return Optional.ofNullable(store.get(id));
        }

        @Override
        public Task save(Task task) {
            store.put(task.id(), task);
            logger.debug("Saved task: {}", task.id());
            return task;
        }

        @Override
        public boolean deleteById(String id) {
            return store.remove(id) != null;
        }

        @Override
        public List<Task> findByDone(boolean done) {
            return store.values().stream()
                    .filter(t -> t.done() == done)
                    .toList();
        }

        @Override
        public long count() {
            return store.size();
        }
    }

    // --- JSON ファイル実装 ---
    // Python: class JsonFileTaskRepo:
    //             def __init__(self, path): self.path = Path(path)
    //             def find_all(self):
    //                 return json.loads(self.path.read_text())
    //
    // ★ Gson の使い方デモ:
    //   Python の json.dumps/loads は dict ⇔ str の変換
    //   Gson は Java オブジェクト ⇔ JSON の型安全な変換
    static class JsonFileTaskRepository implements TaskRepository {
        private final Path filePath;
        private final Gson gson;
        private final Map<String, Task> store;

        // Type token: Gson にジェネリクスの型情報を渡す
        // Python: json.loads() は dict を返すだけなので不要
        // Java: 型消去 (type erasure) があるため TypeToken で型を保持
        private static final Type TASK_LIST_TYPE =
                new TypeToken<List<Task>>() {}.getType();

        JsonFileTaskRepository(String filePath) {
            this.filePath = Path.of(filePath);
            // GsonBuilder: Python の json.dumps(indent=2) 相当
            this.gson = new GsonBuilder()
                    .setPrettyPrinting()    // indent=2
                    .serializeNulls()       // None も出力
                    .create();
            this.store = new LinkedHashMap<>();
            loadFromFile();
        }

        private void loadFromFile() {
            try {
                if (Files.exists(filePath)) {
                    String json = Files.readString(filePath);
                    List<Task> tasks = gson.fromJson(json, TASK_LIST_TYPE);
                    if (tasks != null) {
                        tasks.forEach(t -> store.put(t.id(), t));
                    }
                    logger.info("Loaded {} tasks from {}", store.size(), filePath);
                }
            } catch (IOException e) {
                logger.error("Failed to load: {}", e.getMessage());
            }
        }

        private void saveToFile() {
            try {
                Files.createDirectories(filePath.getParent());
                String json = gson.toJson(store.values().stream().toList());
                Files.writeString(filePath, json);
                logger.debug("Saved {} tasks to {}", store.size(), filePath);
            } catch (IOException e) {
                logger.error("Failed to save: {}", e.getMessage());
            }
        }

        @Override
        public List<Task> findAll() {
            return List.copyOf(store.values());
        }

        @Override
        public Optional<Task> findById(String id) {
            return Optional.ofNullable(store.get(id));
        }

        @Override
        public Task save(Task task) {
            store.put(task.id(), task);
            saveToFile();  // 永続化
            return task;
        }

        @Override
        public boolean deleteById(String id) {
            boolean removed = store.remove(id) != null;
            if (removed) saveToFile();
            return removed;
        }

        @Override
        public List<Task> findByDone(boolean done) {
            return store.values().stream()
                    .filter(t -> t.done() == done)
                    .toList();
        }

        @Override
        public long count() {
            return store.size();
        }
    }

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // 4. Service 層 (ビジネスロジック)
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // Python: class TaskService:
    //             def __init__(self, repo: TaskRepository): ...
    //
    // ★ DI (Dependency Injection) パターン:
    //   - コンストラクタで Repository を受け取る
    //   - Service は「どの Repository 実装か」を知らない
    //   - テスト時: InMemory、本番時: JsonFile を注入
    //   - Spring Boot では @Autowired で自動注入
    static class TaskService {
        private final TaskRepository repository;

        // Python: def __init__(self, repo: TaskRepository):
        //             self.repo = repo
        TaskService(TaskRepository repository) {
            this.repository = repository;
        }

        Task createTask(String title, String description) {
            var task = Task.create(title, description);
            return repository.save(task);
        }

        Optional<Task> completeTask(String id) {
            return repository.findById(id)
                    .map(Task::markDone)
                    .map(repository::save);
        }

        // Python: def get_summary(self) -> dict:
        //             tasks = self.repo.find_all()
        //             return {"total": len(tasks), "done": sum(1 for t in tasks if t.done)}
        Map<String, Object> getSummary() {
            var all = repository.findAll();
            var done = repository.findByDone(true);
            var pending = repository.findByDone(false);

            return Map.of(
                    "total", all.size(),
                    "done", done.size(),
                    "pending", pending.size(),
                    "completion_rate",
                    all.isEmpty() ? 0.0 : (double) done.size() / all.size() * 100
            );
        }

        List<Task> getAllTasks() {
            return repository.findAll();
        }

        boolean deleteTask(String id) {
            return repository.deleteById(id);
        }
    }

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // 5. Gson デモ (JSON シリアライズ/デシリアライズ)
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    static void demonstrateGson() {
        System.out.println("\n── Gson (JSON) デモ ──");
        var gson = new GsonBuilder().setPrettyPrinting().create();

        // --- オブジェクト → JSON ---
        // Python: json.dumps(task.__dict__, indent=2)
        var task = Task.create("Learn Maven", "pom.xml を理解する");
        String json = gson.toJson(task);
        System.out.println("Object → JSON:");
        System.out.println(json);

        // --- JSON → オブジェクト ---
        // Python: task = Task(**json.loads(json_str))
        // Java:   型を指定して安全にデシリアライズ
        Task restored = gson.fromJson(json, Task.class);
        System.out.println("\nJSON → Object: " + restored);
        System.out.println("Equals: " + task.equals(restored));  // Record は自動 equals

        // --- リスト → JSON → リスト ---
        // Python: json.dumps([t.__dict__ for t in tasks])
        var tasks = List.of(
                Task.create("Task 1", "First"),
                Task.create("Task 2", "Second")
        );
        String listJson = gson.toJson(tasks);

        // ★ TypeToken — ジェネリクスの型情報を保持
        // Python では不要 (動的型付けだから)
        // Java: 型消去のため List<Task> の Task 部分が消える
        //       → TypeToken で「List<Task>だよ」と教える
        Type listType = new TypeToken<List<Task>>() {}.getType();
        List<Task> restoredList = gson.fromJson(listJson, listType);
        System.out.println("\nRestored list size: " + restoredList.size());

        // --- Map → JSON (動的データ) ---
        // Python: json.dumps({"key": "value", "nested": {"a": 1}})
        var map = Map.of(
                "project", "maven-demo",
                "version", "1.0.0",
                "features", List.of("gson", "slf4j", "junit")
        );
        System.out.println("\nMap → JSON:");
        System.out.println(gson.toJson(map));
    }

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // 6. Maven ライフサイクル解説
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    static void explainMavenLifecycle() {
        System.out.println("\n── Maven ライフサイクル ──");

        // Python 対比付きで Maven コマンドを解説
        var lifecycle = List.of(
                new String[]{
                        "mvn validate",
                        "pom.xml の検証",
                        "pyproject.toml の構文チェック"
                },
                new String[]{
                        "mvn compile",
                        "src/main/java → target/classes にコンパイル",
                        "python -m py_compile *.py (ただしPythonは通常不要)"
                },
                new String[]{
                        "mvn test",
                        "src/test/java のテストを実行",
                        "pytest"
                },
                new String[]{
                        "mvn package",
                        "JAR/WAR を target/ に生成",
                        "python -m build (wheel 作成)"
                },
                new String[]{
                        "mvn install",
                        "ローカルリポジトリ (~/.m2) にインストール",
                        "pip install -e . (editable install)"
                },
                new String[]{
                        "mvn deploy",
                        "リモートリポジトリにアップロード",
                        "twine upload dist/*"
                },
                new String[]{
                        "mvn clean",
                        "target/ を削除",
                        "rm -rf dist/ build/ *.egg-info"
                }
        );

        System.out.println("""
                ┌─────────────────┬──────────────────────────────────┬─────────────────────────────┐
                │ Maven コマンド    │ 説明                              │ Python 対比                  │
                ├─────────────────┼──────────────────────────────────┼─────────────────────────────┤""");

        for (var cmd : lifecycle) {
            System.out.printf("│ %-15s │ %-32s │ %-27s │%n", cmd[0], cmd[1], cmd[2]);
        }

        System.out.println("""
                └─────────────────┴──────────────────────────────────┴─────────────────────────────┘

                ★ Maven ライフサイクルは「順序付き」:
                  mvn package を実行すると validate → compile → test → package の順に全部実行される
                  Python: tox や Makefile で手動定義する「ビルドステップ」が自動化されている

                ★ Maven リポジトリの階層:
                  1. ローカル   (~/.m2/repository)   — pip のキャッシュ相当
                  2. リモート   (Nexus, Artifactory) — 社内 PyPI サーバー相当
                  3. Central   (repo.maven.apache.org) — PyPI 相当""");
    }

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // 7. プロジェクト構成の慣習
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    static void explainProjectStructure() {
        System.out.println("\n── プロジェクト構成 ──");
        System.out.println("""
                Maven 標準ディレクトリ構成:

                my-project/
                ├── pom.xml                          # pyproject.toml + requirements.txt
                ├── src/
                │   ├── main/
                │   │   ├── java/                    # 本番コード (src/ in Python)
                │   │   │   └── com/example/
                │   │   │       ├── Main.java
                │   │   │       ├── model/           # データクラス (@dataclass)
                │   │   │       ├── repository/      # データアクセス (ORM相当)
                │   │   │       └── service/         # ビジネスロジック
                │   │   └── resources/               # 設定ファイル (config/ in Python)
                │   │       ├── application.properties
                │   │       └── logback.xml
                │   └── test/
                │       ├── java/                    # テストコード (tests/ in Python)
                │       │   └── com/example/
                │       │       └── MainTest.java
                │       └── resources/               # テスト用設定
                └── target/                          # ビルド成果物 (dist/, build/)
                    ├── classes/                     # コンパイル済み .class
                    └── my-project-1.0.0.jar         # パッケージ (.whl)

                ★ Java の慣習:
                  - パッケージ名 = 逆ドメイン (com.example.demo)
                  - ディレクトリ = パッケージ構造と一致
                  - テストは同じパッケージ名で test/ に配置
                  - Python との最大の違い: ディレクトリ構造が「強制」される""");
    }

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // 8. 依存管理の深掘り
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    static void explainDependencyManagement() {
        System.out.println("\n── 依存管理 ──");
        System.out.println("""
                ★ Maven vs pip の依存解決:

                Python (pip):
                  requests==2.31.0          # バージョン固定
                  requests>=2.31,<3.0       # 範囲指定
                  pip freeze > requirements.txt  # ロックファイル的
                  ❌ 推移的依存の自動解決が弱い
                  ❌ バージョン衝突の検出が不完全

                Java (Maven):
                  <version>2.31.0</version>       # 固定
                  <version>[2.31,3.0)</version>    # 範囲 (あまり使わない)
                  ✅ 推移的依存を自動解決
                  ✅ バージョン衝突を「nearest wins」で解決
                  ✅ mvn dependency:tree で依存ツリーを可視化

                ★ よく使うコマンド:
                  mvn dependency:tree          # 依存ツリーの全体像
                  mvn dependency:analyze       # 不要な依存の検出
                  mvn versions:display-dependency-updates  # アップデート可能な依存

                ★ BOM (Bill of Materials):
                  Python: constraints.txt
                  Java:   <dependencyManagement> で複数モジュールのバージョンを一括管理
                  例: Spring Boot の spring-boot-dependencies BOM
                      → spring-boot-starter-web, spring-boot-starter-test 等の
                        バージョンを一箇所で定義

                ★ リポジトリマネージャー:
                ┌──────────────┬──────────────────────────┬─────────────────────┐
                │ ツール        │ 説明                      │ Python 対比          │
                ├──────────────┼──────────────────────────┼─────────────────────┤
                │ Maven Central│ 公式リポジトリ (デフォルト)  │ PyPI               │
                │ Nexus        │ 社内リポジトリ管理          │ devpi / Artifactory │
                │ Artifactory  │ 社内リポジトリ (多機能)     │ devpi + α           │
                │ GitHub Pkgs  │ GitHub のパッケージ管理     │ GitHub Packages     │
                └──────────────┴──────────────────────────┴─────────────────────┘""");
    }

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // 9. Spring Boot / Gradle との関係
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    static void explainEcosystem() {
        System.out.println("\n── Java ビルドツール エコシステム ──");
        System.out.println("""
                ┌──────────┬──────────────────────────────┬────────────────────────────┐
                │ ツール    │ 特徴                          │ Python 対比                │
                ├──────────┼──────────────────────────────┼────────────────────────────┤
                │ Maven    │ XML設定・規約重視・安定        │ setuptools + pip           │
                │ Gradle   │ Groovy/Kotlin DSL・柔軟・高速 │ poetry / hatch             │
                │ Ant      │ レガシー・XML・手動設定         │ Makefile                   │
                │ sbt      │ Scala向け                     │ ―                          │
                └──────────┴──────────────────────────────┴────────────────────────────┘

                ★ Maven vs Gradle:
                  Maven:  XML で宣言的。「規約に従えば設定不要」(Convention over Configuration)
                  Gradle: コードで手続き的に書ける。Android 開発のデファクト。ビルドが速い。
                  → 新規プロジェクト: Gradle (Spring Initializr のデフォルト)
                  → エンタープライズ既存: Maven (まだ多数派)
                  → 選べるなら: Gradle (Kotlin DSL) がモダン

                ★ Spring Boot との関係:
                  Spring Boot = Java の Django/FastAPI 相当
                  1. https://start.spring.io/ でプロジェクト生成 (cookiecutter 相当)
                  2. pom.xml に spring-boot-starter-* を追加するだけ
                  3. @SpringBootApplication → 自動設定 (Auto Configuration)
                  4. @RestController @GetMapping → FastAPI の @app.get() と同じ

                  Spring Boot Starters (よく使うもの):
                  ┌─────────────────────────────────┬─────────────────────────┐
                  │ Starter                         │ Python 対比              │
                  ├─────────────────────────────────┼─────────────────────────┤
                  │ spring-boot-starter-web         │ FastAPI + Uvicorn       │
                  │ spring-boot-starter-data-jpa    │ SQLAlchemy              │
                  │ spring-boot-starter-security    │ FastAPI Security        │
                  │ spring-boot-starter-test        │ pytest + factory-boy    │
                  │ spring-boot-starter-validation  │ Pydantic                │
                  │ spring-boot-starter-actuator    │ Prometheus exporter     │
                  └─────────────────────────────────┴─────────────────────────┘""");
    }

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // Main
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    public static void main(String[] args) {
        System.out.println("╔══════════════════════════════════════════════════╗");
        System.out.println("║  Maven + Repository Pattern Demo               ║");
        System.out.println("║  Python 対比で学ぶ Java プロジェクト管理          ║");
        System.out.println("╚══════════════════════════════════════════════════╝");

        // --- Repository パターン: InMemory ---
        System.out.println("\n── Repository パターン (InMemory) ──");
        var repo = new InMemoryTaskRepository();
        var service = new TaskService(repo);

        // タスク作成
        var t1 = service.createTask("pom.xml を読む", "GAV座標とscopeを理解");
        var t2 = service.createTask("mvn package を実行", "JAR生成の流れを確認");
        var t3 = service.createTask("テストを書く", "JUnit 5 の基本を学ぶ");

        logger.info("Created {} tasks", repo.count());
        service.getAllTasks().forEach(t ->
                System.out.println("  [%s] %s - %s".formatted(
                        t.done() ? "✓" : " ", t.id(), t.title())));

        // タスク完了
        service.completeTask(t1.id());
        System.out.println("\nAfter completing '" + t1.title() + "':");
        System.out.println("  Summary: " + service.getSummary());

        // --- Repository パターン: JsonFile ---
        System.out.println("\n── Repository パターン (JsonFile) ──");
        var tmpFile = System.getProperty("java.io.tmpdir") + "/maven-demo-tasks.json";
        var jsonRepo = new JsonFileTaskRepository(tmpFile);
        var jsonService = new TaskService(jsonRepo);

        jsonService.createTask("Gson を試す", "JSON シリアライズの仕組みを学ぶ");
        jsonService.createTask("SLF4J を試す", "ロギングファサードを理解する");
        System.out.println("  Saved to: " + tmpFile);
        System.out.println("  Tasks in file: " + jsonRepo.count());

        // ★ 同じ TaskService が異なる Repository で動く = DI の威力
        // Python: service = TaskService(InMemoryRepo()) or TaskService(JsonFileRepo("path"))

        // --- Gson デモ ---
        demonstrateGson();

        // --- 解説セクション ---
        explainMavenLifecycle();
        explainProjectStructure();
        explainDependencyManagement();
        explainEcosystem();

        // --- まとめ ---
        System.out.println("""

                ╔══════════════════════════════════════════════════════════════════╗
                ║  まとめ: Python → Java の対応表                                  ║
                ╠══════════════════════════════════════════════════════════════════╣
                ║  pyproject.toml    → pom.xml                                    ║
                ║  pip install       → <dependency> (mvn が自動DL)                 ║
                ║  PyPI              → Maven Central                              ║
                ║  pip freeze        → mvn dependency:tree                         ║
                ║  pytest            → JUnit 5 (mvn test)                          ║
                ║  python -m build   → mvn package                                 ║
                ║  twine upload      → mvn deploy                                  ║
                ║  venv              → Maven はプロジェクトごとに依存解決 (衝突しない) ║
                ║  Django/FastAPI    → Spring Boot                                  ║
                ║  SQLAlchemy        → Spring Data JPA / Repository パターン         ║
                ║  logging           → SLF4J + Logback                              ║
                ║  json              → Gson / Jackson                               ║
                ╚══════════════════════════════════════════════════════════════════╝
                """);
    }
}
