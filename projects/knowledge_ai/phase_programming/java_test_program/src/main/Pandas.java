package calculation;

import java.util.*;
import java.util.stream.Collectors;

/**
 * Python の pandas DataFrame の基本操作を Java で再現したサンプル。
 *
 * Python pandas 対応表:
 *   pd.DataFrame(data)         → new SimpleDataFrame(columns, rows)
 *   df.head(n)                 → df.head(n)
 *   df.describe()              → df.describe()
 *   df[df["age"] > 25]         → df.filter("age", v -> v > 25)
 *   df.groupby("dept").mean()  → df.groupByMean("dept", "salary")
 */
public class Pandas {

    // ===== 簡易 DataFrame =====
    static class SimpleDataFrame {
        private final List<String> columns;
        private final List<Map<String, Object>> rows;

        SimpleDataFrame(List<String> columns, List<Map<String, Object>> rows) {
            this.columns = columns;
            this.rows    = rows;
        }

        // df.head(n) — 先頭 n 行を表示
        void head(int n) {
            System.out.println("[head(" + n + ")]");
            printHeader();
            rows.stream().limit(n).forEach(this::printRow);
            System.out.println();
        }

        // len(df) — 行数
        int size() { return rows.size(); }

        // df.describe() — 数値列の基本統計 (count / mean / min / max)
        void describe() {
            System.out.println("[describe]");
            for (String col : columns) {
                List<Double> nums = rows.stream()
                        .map(r -> r.get(col))
                        .filter(v -> v instanceof Number)
                        .map(v -> ((Number) v).doubleValue())
                        .collect(Collectors.toList());
                if (nums.isEmpty()) continue;

                double sum  = nums.stream().mapToDouble(Double::doubleValue).sum();
                double mean = sum / nums.size();
                double min  = nums.stream().mapToDouble(Double::doubleValue).min().orElse(0);
                double max  = nums.stream().mapToDouble(Double::doubleValue).max().orElse(0);

                System.out.printf("  %-10s count=%-4d mean=%-8.1f min=%-8.1f max=%.1f%n",
                        col, nums.size(), mean, min, max);
            }
            System.out.println();
        }

        // df[df["col"] > threshold] — 数値フィルタ
        SimpleDataFrame filter(String col, java.util.function.Predicate<Double> pred) {
            List<Map<String, Object>> filtered = rows.stream()
                    .filter(r -> {
                        Object v = r.get(col);
                        return v instanceof Number && pred.test(((Number) v).doubleValue());
                    })
                    .collect(Collectors.toList());
            return new SimpleDataFrame(columns, filtered);
        }

        // df.groupby("col").mean(targetCol) — グループ別平均
        void groupByMean(String groupCol, String targetCol) {
            System.out.println("[groupby(\"" + groupCol + "\").mean(\"" + targetCol + "\")]");
            Map<Object, List<Double>> groups = new LinkedHashMap<>();
            for (Map<String, Object> row : rows) {
                Object key = row.get(groupCol);
                double val = ((Number) row.get(targetCol)).doubleValue();
                groups.computeIfAbsent(key, k -> new ArrayList<>()).add(val);
            }
            groups.forEach((key, vals) -> {
                double mean = vals.stream().mapToDouble(Double::doubleValue).average().orElse(0);
                System.out.printf("  %-12s %.1f%n", key, mean);
            });
            System.out.println();
        }

        // df.sort_values("col") — 昇順ソート
        SimpleDataFrame sortBy(String col) {
            List<Map<String, Object>> sorted = rows.stream()
                    .sorted(Comparator.comparingDouble(r -> ((Number) r.get(col)).doubleValue()))
                    .collect(Collectors.toList());
            return new SimpleDataFrame(columns, sorted);
        }

        private void printHeader() {
            System.out.println("  " + String.join(" | ", columns));
            System.out.println("  " + "-".repeat(columns.size() * 14));
        }

        private void printRow(Map<String, Object> row) {
            List<String> vals = columns.stream()
                    .map(c -> String.format("%-12s", row.getOrDefault(c, "null")))
                    .collect(Collectors.toList());
            System.out.println("  " + String.join(" | ", vals));
        }
    }

    // ===== サンプルデータ生成 =====
    private static SimpleDataFrame buildSampleData() {
        List<String> cols = List.of("name", "age", "dept", "salary");

        List<Map<String, Object>> rows = new ArrayList<>();
        rows.add(Map.of("name", "Alice",   "age", 30, "dept", "Engineering", "salary", 700000));
        rows.add(Map.of("name", "Bob",     "age", 24, "dept", "Sales",       "salary", 500000));
        rows.add(Map.of("name", "Carol",   "age", 35, "dept", "Engineering", "salary", 850000));
        rows.add(Map.of("name", "Dave",    "age", 28, "dept", "Sales",       "salary", 520000));
        rows.add(Map.of("name", "Eve",     "age", 40, "dept", "HR",          "salary", 620000));
        rows.add(Map.of("name", "Frank",   "age", 22, "dept", "Engineering", "salary", 650000));

        return new SimpleDataFrame(cols, rows);
    }

    // ===== メイン実行 =====
    public static void exampleMethod() {

        System.out.println("========================================");
        System.out.println("  Java で pandas 風操作のサンプル");
        System.out.println("========================================\n");

        SimpleDataFrame df = buildSampleData();

        // --- head ---
        // Python: df.head(3)
        df.head(3);

        // --- describe ---
        // Python: df.describe()
        df.describe();

        // --- filter ---
        // Python: df[df["age"] > 25]
        System.out.println("[filter: age > 25]");
        SimpleDataFrame filtered = df.filter("age", age -> age > 25);
        filtered.head(filtered.size());

        // --- groupby mean ---
        // Python: df.groupby("dept")["salary"].mean()
        df.groupByMean("dept", "salary");

        // --- sort ---
        // Python: df.sort_values("salary")
        System.out.println("[sort by salary (ascending)]");
        df.sortBy("salary").head(df.size());
    }
}
