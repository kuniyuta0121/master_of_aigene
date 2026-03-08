package com.aigene.data;

import com.aigene.data.skills.*;
import com.aigene.model.Skill;
import com.aigene.model.SkillCategory;

import java.util.*;
import java.util.stream.Collectors;
import java.util.stream.Stream;

public class SkillRepository {

    private final Map<String, Skill> skills;
    private final List<SkillCategory> categories;

    public SkillRepository() {
        this.skills = buildSkillMap();
        this.categories = buildCategories();
    }

    private Map<String, Skill> buildSkillMap() {
        return Stream.of(
                AiMlSkills.get(),
                CloudSkills.get(),
                InfraDevOpsSkills.get(),
                DataEngineeringSkills.get(),
                ArchitectureSkills.get(),
                SecuritySkills.get(),
                ProgrammingSkills.get(),
                FrontendSkills.get(),
                PmSkills.get(),
                LeadershipSkills.get()
        ).flatMap(List::stream)
         .collect(Collectors.toMap(Skill::getId, s -> s, (a, b) -> a, LinkedHashMap::new));
    }

    private List<SkillCategory> buildCategories() {
        return List.of(
            new SkillCategory("AI_ML", "AI・機械学習",
                "機械学習・深層学習・LLM活用・RAG・AIエージェント・MLOps",
                "[AI]", getIdsForCategory("AI_ML"), 1),
            new SkillCategory("CLOUD", "クラウドアーキテクチャ",
                "AWS・GCP設計・クラウドネイティブ・サーバーレス・FinOps",
                "[CL]", getIdsForCategory("CLOUD"), 2),
            new SkillCategory("INFRA_DEVOPS", "インフラ・DevOps",
                "Docker・Kubernetes・CI/CD・IaC・可観測性・SRE",
                "[OPS]", getIdsForCategory("INFRA_DEVOPS"), 3),
            new SkillCategory("DATA_ENG", "データエンジニアリング",
                "SQL高度活用・NoSQL・データパイプライン・レイクハウス・ストリーム処理",
                "[DATA]", getIdsForCategory("DATA_ENG"), 4),
            new SkillCategory("ARCHITECTURE", "アーキテクチャ設計",
                "システム設計・マイクロサービス・イベント駆動・DDD・API設計",
                "[ARCH]", getIdsForCategory("ARCHITECTURE"), 5),
            new SkillCategory("SECURITY", "セキュリティ",
                "OWASP・クラウドセキュリティ・脅威モデリング",
                "[SEC]", getIdsForCategory("SECURITY"), 6),
            new SkillCategory("PROGRAMMING", "プログラミング",
                "Pythonアドバンスド・Go・TypeScript・アルゴリズム・デザインパターン",
                "[CODE]", getIdsForCategory("PROGRAMMING"), 7),
            new SkillCategory("FRONTEND", "フロントエンド",
                "React・Next.js・Webパフォーマンス",
                "[FE]", getIdsForCategory("FRONTEND"), 8),
            new SkillCategory("PM", "プロジェクト・プロダクト管理",
                "アジャイル・プロダクトディスカバリー・OKR・ステークホルダー管理・テクニカルPM",
                "[PM]", getIdsForCategory("PM"), 9),
            new SkillCategory("LEADERSHIP", "リーダーシップ・ビジネス",
                "テクニカルリーダーシップ・ビジネス思考・コミュニケーション・チーム育成・キャリア",
                "[LEAD]", getIdsForCategory("LEADERSHIP"), 10)
        );
    }

    private List<String> getIdsForCategory(String categoryId) {
        return skills.values().stream()
            .filter(s -> categoryId.equals(s.getCategoryId()))
            .map(Skill::getId)
            .collect(Collectors.toList());
    }

    public Optional<Skill> findById(String id) {
        return Optional.ofNullable(skills.get(id));
    }

    public List<Skill> findByCategory(String categoryId) {
        return skills.values().stream()
            .filter(s -> categoryId.equals(s.getCategoryId()))
            .collect(Collectors.toList());
    }

    public List<Skill> searchByKeyword(String keyword) {
        String kw = keyword.toLowerCase();
        return skills.values().stream()
            .filter(s ->
                s.getName().toLowerCase().contains(kw) ||
                s.getNameEn().toLowerCase().contains(kw) ||
                s.getShortDescription().toLowerCase().contains(kw) ||
                s.getKeyTopics().stream().anyMatch(t -> t.toLowerCase().contains(kw))
            )
            .collect(Collectors.toList());
    }

    public List<SkillCategory> getAllCategories() {
        return categories;
    }

    public List<Skill> getAllSkills() {
        return new ArrayList<>(skills.values());
    }

    public Optional<SkillCategory> findCategoryById(String id) {
        return categories.stream().filter(c -> c.getId().equals(id)).findFirst();
    }
}
