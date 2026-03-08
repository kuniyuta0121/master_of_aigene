package com.aigene.model;

public enum Difficulty {
    BEGINNER("入門", "★☆☆☆☆"),
    INTERMEDIATE("中級", "★★★☆☆"),
    ADVANCED("上級", "★★★★☆"),
    EXPERT("エキスパート", "★★★★★");

    private final String label;
    private final String stars;

    Difficulty(String label, String stars) {
        this.label = label;
        this.stars = stars;
    }

    public String getLabel() { return label; }
    public String getStars() { return stars; }
}
