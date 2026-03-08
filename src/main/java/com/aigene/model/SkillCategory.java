package com.aigene.model;

import java.util.List;

public class SkillCategory {
    private final String id;
    private final String name;
    private final String description;
    private final String icon;
    private final List<String> skillIds;
    private final int displayOrder;

    public SkillCategory(String id, String name, String description, String icon,
                         List<String> skillIds, int displayOrder) {
        this.id = id;
        this.name = name;
        this.description = description;
        this.icon = icon;
        this.skillIds = skillIds;
        this.displayOrder = displayOrder;
    }

    public String getId() { return id; }
    public String getName() { return name; }
    public String getDescription() { return description; }
    public String getIcon() { return icon; }
    public List<String> getSkillIds() { return skillIds; }
    public int getDisplayOrder() { return displayOrder; }
}
