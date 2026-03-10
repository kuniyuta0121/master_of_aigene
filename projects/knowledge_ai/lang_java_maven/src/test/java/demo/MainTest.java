package demo;

import demo.Main.*;
import org.junit.jupiter.api.*;
import org.junit.jupiter.params.*;
import org.junit.jupiter.params.provider.*;

import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

/**
 * JUnit 5 テスト — Python の pytest 対比
 *
 * Python:
 *   def test_create_task():
 *       task = Task.create("title", "desc")
 *       assert task.title == "title"
 *
 * Java:
 *   @Test
 *   void createTask() {
 *       var task = Task.create("title", "desc");
 *       assertEquals("title", task.title());
 *   }
 *
 * ★ JUnit 5 の構造:
 *   @Test          — pytest の def test_xxx()
 *   @BeforeEach    — pytest の @pytest.fixture (各テスト前に実行)
 *   @BeforeAll     — pytest の @pytest.fixture(scope="class")
 *   @DisplayName   — テスト名を日本語で表示
 *   @Nested        — テストのグループ化 (pytest の class TestXxx)
 *   @ParameterizedTest — pytest の @pytest.mark.parametrize
 *   assertEquals   — assert ==
 *   assertThrows   — pytest.raises()
 */
class MainTest {

    private InMemoryTaskRepository repo;
    private TaskService service;

    // Python: @pytest.fixture(autouse=True)
    //         def setup(self):
    //             self.repo = InMemoryTaskRepo()
    //             self.service = TaskService(self.repo)
    @BeforeEach
    void setUp() {
        repo = new InMemoryTaskRepository();
        service = new TaskService(repo);
    }

    // ━━━ Task Record のテスト ━━━
    @Nested
    @DisplayName("Task Record")
    class TaskRecordTest {

        @Test
        @DisplayName("Task.create で ID と createdAt が自動生成される")
        void createGeneratesIdAndTimestamp() {
            var task = Task.create("Test", "Description");
            assertNotNull(task.id());
            assertFalse(task.id().isEmpty());
            assertNotNull(task.createdAt());
            assertFalse(task.done());
        }

        @Test
        @DisplayName("markDone で done=true になる (イミュータブル)")
        void markDoneReturnsNewInstance() {
            var original = Task.create("Test", "Desc");
            var completed = original.markDone();

            // Record はイミュータブル → 新しいインスタンスが返る
            assertFalse(original.done());     // 元は変わらない
            assertTrue(completed.done());     // 新しい方は done
            assertEquals(original.id(), completed.id());  // ID は同じ
        }

        @Test
        @DisplayName("Record の自動 equals で同値比較")
        void recordEquals() {
            // Record は自動で equals を生成 (全フィールド比較)
            // Python: @dataclass(frozen=True) と同じ
            var t1 = new Task("id1", "Title", "Desc", false, "2024-01-01");
            var t2 = new Task("id1", "Title", "Desc", false, "2024-01-01");
            assertEquals(t1, t2);
        }
    }

    // ━━━ Repository のテスト ━━━
    @Nested
    @DisplayName("InMemoryTaskRepository")
    class RepositoryTest {

        @Test
        @DisplayName("save & findById で CRUD できる")
        void saveAndFind() {
            var task = Task.create("Test", "Desc");
            repo.save(task);

            var found = repo.findById(task.id());
            assertTrue(found.isPresent());
            assertEquals(task, found.get());
        }

        @Test
        @DisplayName("存在しない ID は Optional.empty")
        void findByIdNotFound() {
            // Python: assert repo.find_by_id("xxx") is None
            // Java:   Optional.empty() で null を回避
            var found = repo.findById("nonexistent");
            assertTrue(found.isEmpty());
        }

        @Test
        @DisplayName("deleteById で削除できる")
        void deleteById() {
            var task = Task.create("Test", "Desc");
            repo.save(task);

            assertTrue(repo.deleteById(task.id()));
            assertEquals(0, repo.count());
        }

        @Test
        @DisplayName("findByDone で完了/未完了をフィルタ")
        void findByDone() {
            repo.save(Task.create("A", "").markDone());
            repo.save(Task.create("B", ""));
            repo.save(Task.create("C", "").markDone());

            assertEquals(2, repo.findByDone(true).size());
            assertEquals(1, repo.findByDone(false).size());
        }
    }

    // ━━━ Service のテスト ━━━
    @Nested
    @DisplayName("TaskService")
    class ServiceTest {

        @Test
        @DisplayName("createTask でタスクが保存される")
        void createTask() {
            var task = service.createTask("Title", "Desc");
            assertEquals(1, repo.count());
            assertEquals("Title", task.title());
        }

        @Test
        @DisplayName("completeTask で done=true になる")
        void completeTask() {
            var task = service.createTask("Title", "Desc");
            var completed = service.completeTask(task.id());

            assertTrue(completed.isPresent());
            assertTrue(completed.get().done());
        }

        @Test
        @DisplayName("存在しないタスクの complete は empty")
        void completeNonExistent() {
            var result = service.completeTask("xxx");
            assertTrue(result.isEmpty());
        }

        @Test
        @DisplayName("getSummary で正しい統計が返る")
        void getSummary() {
            service.createTask("A", "");
            service.createTask("B", "");
            var t3 = service.createTask("C", "");
            service.completeTask(t3.id());

            var summary = service.getSummary();
            assertEquals(3, summary.get("total"));
            assertEquals(1, summary.get("done"));
            assertEquals(2, summary.get("pending"));
        }
    }

    // ━━━ Parameterized Test ━━━
    // Python: @pytest.mark.parametrize("title,expected_len", [("a", 1), ("ab", 2)])
    @ParameterizedTest(name = "タイトル \"{0}\" → 長さ {1}")
    @CsvSource({
            "Hello, 5",
            "Maven, 5",
            "Java 17, 7"
    })
    @DisplayName("タイトルの長さが正しい")
    void titleLength(String title, int expectedLength) {
        var task = Task.create(title, "");
        assertEquals(expectedLength, task.title().length());
    }

    // ━━━ 例外テスト ━━━
    @Test
    @DisplayName("null ID は empty を返す (HashMap は null キー許容)")
    void nullIdReturnsEmpty() {
        // Python: assert repo.find_by_id(None) is None
        // Java: HashMap.get(null) は null → Optional.empty()
        var found = repo.findById(null);
        assertTrue(found.isEmpty());
    }

    @Test
    @DisplayName("null Task を save すると NullPointerException")
    void saveNullThrows() {
        // Python: with pytest.raises(AttributeError):
        //             repo.save(None)
        assertThrows(NullPointerException.class, () ->
                repo.save(null));
    }
}
