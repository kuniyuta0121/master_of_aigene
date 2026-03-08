package com.aigene.model;

public enum SkillStatus {
    NOT_STARTED("未着手", "[ ]"),
    IN_PROGRESS("学習中", "[~]"),
    COMPLETED("習得済", "[x]");

    private final String label;
    private final String badge;

    SkillStatus(String label, String badge) {
        this.label = label;
        this.badge = badge;
    }

    public String getLabel() { return label; }
    public String getBadge() { return badge; }
}
