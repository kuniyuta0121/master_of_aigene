package com.aigene.service;

import com.aigene.data.SkillRepository;
import com.aigene.model.*;

import java.util.*;
import java.util.stream.Collectors;

public class RecommendationService {

    private final SkillRepository repository;
    private final ProgressService progressService;

    public RecommendationService(SkillRepository repository, ProgressService progressService) {
        this.repository = repository;
        this.progressService = progressService;
    }

    public record RecommendedSkill(Skill skill, int score, String reason) {}

    public List<RecommendedSkill> getRecommendations(UserProfile profile, int limit) {
        Set<String> currentSkillIds = profile.getCurrentSkillIds();
        UserProfile.CareerGoal goal = profile.getCareerGoal();

        List<RecommendedSkill> recommendations = new ArrayList<>();

        for (Skill skill : repository.getAllSkills()) {
            SkillStatus status = progressService.getStatus(skill.getId());
            if (status == SkillStatus.COMPLETED) continue;

            int score = calculateScore(skill, profile, currentSkillIds);
            String reason = buildReason(skill, goal, currentSkillIds);
            recommendations.add(new RecommendedSkill(skill, score, reason));
        }

        recommendations.sort(Comparator.comparingInt(RecommendedSkill::score).reversed());
        return recommendations.stream().limit(limit).collect(Collectors.toList());
    }

    private int calculateScore(Skill skill, UserProfile profile, Set<String> currentSkills) {
        int score = 0;

        // 優先度スコア
        score += switch (skill.getPriority()) {
            case CRITICAL -> 100;
            case HIGH -> 70;
            case MEDIUM -> 40;
            case LOW -> 10;
        };

        // キャリアゴール適合度
        score += careerGoalBonus(skill, profile.getCareerGoal());

        // 前提スキルが満たされているか
        long metPrereqs = skill.getPrerequisites().stream()
            .filter(p -> currentSkills.stream().anyMatch(cs -> cs.toLowerCase().contains(p.toLowerCase())
                         || p.toLowerCase().contains(cs.toLowerCase())))
            .count();
        if (!skill.getPrerequisites().isEmpty()) {
            score += (int) (metPrereqs * 20 / skill.getPrerequisites().size()) * 3;
        }

        // 難易度（学習中ステータスとの整合性）
        SkillStatus status = progressService.getStatus(skill.getId());
        if (status == SkillStatus.IN_PROGRESS) score += 30;

        return score;
    }

    private int careerGoalBonus(Skill skill, UserProfile.CareerGoal goal) {
        String catId = skill.getCategoryId();
        return switch (goal) {
            case PRODUCT_MANAGER -> switch (catId) {
                case "PM" -> 60;
                case "LEADERSHIP" -> 40;
                case "AI_ML" -> 30;
                case "DATA_ENG" -> 20;
                default -> 0;
            };
            case TECH_LEAD -> switch (catId) {
                case "ARCHITECTURE" -> 60;
                case "LEADERSHIP" -> 40;
                case "INFRA_DEVOPS" -> 30;
                case "SECURITY" -> 20;
                default -> 0;
            };
            case ARCHITECT -> switch (catId) {
                case "ARCHITECTURE" -> 70;
                case "INFRA_DEVOPS" -> 40;
                case "CLOUD" -> 40;
                case "SECURITY" -> 30;
                default -> 0;
            };
            case ENGINEER_SPECIALIST -> switch (catId) {
                case "AI_ML" -> 60;
                case "PROGRAMMING" -> 50;
                case "DATA_ENG" -> 30;
                default -> 0;
            };
            case ENGINEER_MANAGER -> switch (catId) {
                case "LEADERSHIP" -> 70;
                case "PM" -> 40;
                case "ARCHITECTURE" -> 20;
                default -> 0;
            };
        };
    }

    private String buildReason(Skill skill, UserProfile.CareerGoal goal, Set<String> currentSkills) {
        List<String> reasons = new ArrayList<>();

        if (skill.getPriority() == Priority.CRITICAL) {
            reasons.add("最重要スキル");
        }

        String catId = skill.getCategoryId();
        if (goal == UserProfile.CareerGoal.PRODUCT_MANAGER &&
            (catId.equals("PM") || catId.equals("LEADERSHIP"))) {
            reasons.add("PMキャリアに直結");
        }
        if (goal == UserProfile.CareerGoal.TECH_LEAD && catId.equals("ARCHITECTURE")) {
            reasons.add("テックリードに必須");
        }
        if (catId.equals("AI_ML")) {
            reasons.add("AI時代の必須技術");
        }

        SkillStatus status = progressService.getStatus(skill.getId());
        if (status == SkillStatus.IN_PROGRESS) {
            reasons.add("学習中（継続推奨）");
        }

        return reasons.isEmpty() ? "バランス良く習得を推奨" : String.join(" / ", reasons);
    }

    public Map<String, Long> getProgressSummary() {
        Map<String, Long> summary = new LinkedHashMap<>();
        long total = repository.getAllSkills().size();
        long completed = progressService.countByStatus(SkillStatus.COMPLETED);
        long inProgress = progressService.countByStatus(SkillStatus.IN_PROGRESS);
        summary.put("total", total);
        summary.put("completed", completed);
        summary.put("inProgress", inProgress);
        summary.put("notStarted", total - completed - inProgress);
        return summary;
    }

    public List<Skill> getLearningPath(UserProfile.CareerGoal goal) {
        return repository.getAllSkills().stream()
            .filter(s -> careerGoalBonus(s, goal) > 30)
            .sorted(Comparator.comparingInt((Skill s) -> switch (s.getPriority()) {
                case CRITICAL -> 0; case HIGH -> 1; case MEDIUM -> 2; case LOW -> 3;
            }))
            .collect(Collectors.toList());
    }
}
