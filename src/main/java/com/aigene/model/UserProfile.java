package com.aigene.model;

import java.util.HashSet;
import java.util.Set;

public class UserProfile {
    private String name;
    private int yearsOfExperience;
    private Set<String> currentSkillIds;
    private CareerGoal careerGoal;
    private String notes;

    public enum CareerGoal {
        ENGINEER_SPECIALIST("スペシャリストエンジニア", "技術の専門性を極める"),
        TECH_LEAD("テックリード", "技術とチームをリードする"),
        PRODUCT_MANAGER("プロダクトマネージャー", "プロダクトの方向性を決める"),
        ARCHITECT("アーキテクト", "システム全体を設計する"),
        ENGINEER_MANAGER("エンジニアリングマネージャー", "エンジニアチームをマネジメントする");

        private final String label;
        private final String description;

        CareerGoal(String label, String description) {
            this.label = label;
            this.description = description;
        }

        public String getLabel() { return label; }
        public String getDescription() { return description; }
    }

    public UserProfile() {
        this.currentSkillIds = new HashSet<>();
        this.careerGoal = CareerGoal.PRODUCT_MANAGER;
        this.yearsOfExperience = 0;
    }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public int getYearsOfExperience() { return yearsOfExperience; }
    public void setYearsOfExperience(int years) { this.yearsOfExperience = years; }

    public Set<String> getCurrentSkillIds() { return currentSkillIds; }
    public void setCurrentSkillIds(Set<String> ids) { this.currentSkillIds = ids; }
    public void addCurrentSkill(String id) { this.currentSkillIds.add(id); }
    public void removeCurrentSkill(String id) { this.currentSkillIds.remove(id); }

    public CareerGoal getCareerGoal() { return careerGoal; }
    public void setCareerGoal(CareerGoal goal) { this.careerGoal = goal; }

    public String getNotes() { return notes; }
    public void setNotes(String notes) { this.notes = notes; }
}
