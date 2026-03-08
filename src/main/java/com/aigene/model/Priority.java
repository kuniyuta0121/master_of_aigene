package com.aigene.model;

public enum Priority {
    CRITICAL("最重要", "[!!!]"),
    HIGH("高", "[ ! ]"),
    MEDIUM("中", "[ - ]"),
    LOW("低", "[   ]");

    private final String label;
    private final String badge;

    Priority(String label, String badge) {
        this.label = label;
        this.badge = badge;
    }

    public String getLabel() { return label; }
    public String getBadge() { return badge; }
}
