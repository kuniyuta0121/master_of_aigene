# Java Maven + Repository パターン

Maven と Repository パターンを Python 対比で学ぶ。

## 起動

```bash
# ビルド & 実行
mvn package -q
java -jar target/maven-demo-1.0.0.jar

# テスト実行 (pytest 相当)
mvn test

# 依存ツリー表示 (pip freeze 相当)
mvn dependency:tree

# クリーンビルド
mvn clean package
```

## 学べること

### Maven (pom.xml)
- GAV座標 (groupId:artifactId:version)
- dependency の scope (compile/runtime/test/provided)
- Plugin (compiler, surefire, shade)
- ライフサイクル (validate → compile → test → package → install → deploy)
- プロファイル (dev/prod)
- リポジトリ (Maven Central, Nexus, Artifactory)
- BOM (dependencyManagement)

### Repository パターン
- インターフェースによるデータアクセス抽象化
- InMemory 実装 / JsonFile 実装 の切り替え
- DI (Dependency Injection) パターン
- Service 層の設計

### 外部ライブラリ
- Gson: JSON シリアライズ/デシリアライズ (TypeToken)
- SLF4J: ロギングファサード (実装差し替え可能)
- JUnit 5: テスト (@Test, @Nested, @ParameterizedTest)

### エコシステム
- Maven vs Gradle の比較
- Spring Boot との関係
- Spring Boot Starters の対応表
