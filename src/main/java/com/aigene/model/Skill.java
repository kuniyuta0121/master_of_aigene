package com.aigene.model;

import java.util.List;

public class Skill {
    private final String id;
    private final String name;
    private final String nameEn;
    private final String shortDescription;
    private final String overview;
    private final String whyItMatters;
    private final String howToLearn;
    private final String aiEraRelevance;
    private final List<String> keyTopics;
    private final List<String> prerequisites;
    private final List<String> nextSkillIds;
    private final List<String> resources;
    private final Difficulty difficulty;
    private final Priority priority;
    private final int estimatedHours;
    private final String categoryId;

    private Skill(Builder builder) {
        this.id = builder.id;
        this.name = builder.name;
        this.nameEn = builder.nameEn;
        this.shortDescription = builder.shortDescription;
        this.overview = builder.overview;
        this.whyItMatters = builder.whyItMatters;
        this.howToLearn = builder.howToLearn;
        this.aiEraRelevance = builder.aiEraRelevance;
        this.keyTopics = builder.keyTopics;
        this.prerequisites = builder.prerequisites;
        this.nextSkillIds = builder.nextSkillIds;
        this.resources = builder.resources;
        this.difficulty = builder.difficulty;
        this.priority = builder.priority;
        this.estimatedHours = builder.estimatedHours;
        this.categoryId = builder.categoryId;
    }

    public String getId() { return id; }
    public String getName() { return name; }
    public String getNameEn() { return nameEn; }
    public String getShortDescription() { return shortDescription; }
    public String getOverview() { return overview; }
    public String getWhyItMatters() { return whyItMatters; }
    public String getHowToLearn() { return howToLearn; }
    public String getAiEraRelevance() { return aiEraRelevance; }
    public List<String> getKeyTopics() { return keyTopics; }
    public List<String> getPrerequisites() { return prerequisites; }
    public List<String> getNextSkillIds() { return nextSkillIds; }
    public List<String> getResources() { return resources; }
    public Difficulty getDifficulty() { return difficulty; }
    public Priority getPriority() { return priority; }
    public int getEstimatedHours() { return estimatedHours; }
    public String getCategoryId() { return categoryId; }

    public static Builder builder(String id) {
        return new Builder(id);
    }

    public static class Builder {
        private final String id;
        private String name;
        private String nameEn = "";
        private String shortDescription = "";
        private String overview = "";
        private String whyItMatters = "";
        private String howToLearn = "";
        private String aiEraRelevance = "";
        private List<String> keyTopics = List.of();
        private List<String> prerequisites = List.of();
        private List<String> nextSkillIds = List.of();
        private List<String> resources = List.of();
        private Difficulty difficulty = Difficulty.INTERMEDIATE;
        private Priority priority = Priority.MEDIUM;
        private int estimatedHours = 40;
        private String categoryId;

        public Builder(String id) { this.id = id; }

        public Builder name(String name) { this.name = name; return this; }
        public Builder nameEn(String nameEn) { this.nameEn = nameEn; return this; }
        public Builder shortDescription(String v) { this.shortDescription = v; return this; }
        public Builder overview(String v) { this.overview = v; return this; }
        public Builder whyItMatters(String v) { this.whyItMatters = v; return this; }
        public Builder howToLearn(String v) { this.howToLearn = v; return this; }
        public Builder aiEraRelevance(String v) { this.aiEraRelevance = v; return this; }
        public Builder keyTopics(List<String> v) { this.keyTopics = v; return this; }
        public Builder prerequisites(List<String> v) { this.prerequisites = v; return this; }
        public Builder nextSkillIds(List<String> v) { this.nextSkillIds = v; return this; }
        public Builder resources(List<String> v) { this.resources = v; return this; }
        public Builder difficulty(Difficulty v) { this.difficulty = v; return this; }
        public Builder priority(Priority v) { this.priority = v; return this; }
        public Builder estimatedHours(int v) { this.estimatedHours = v; return this; }
        public Builder categoryId(String v) { this.categoryId = v; return this; }

        public Skill build() { return new Skill(this); }
    }
}
