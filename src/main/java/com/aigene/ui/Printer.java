package com.aigene.ui;

import com.aigene.model.*;

import java.util.List;

public class Printer {

    private static final int WIDTH = 72;

    public static void header(String title) {
        String line = "=".repeat(WIDTH);
        System.out.println(Colors.CYAN + line + Colors.RESET);
        System.out.println(Colors.BOLD + Colors.CYAN + centerPad(title, WIDTH) + Colors.RESET);
        System.out.println(Colors.CYAN + line + Colors.RESET);
    }

    public static void sectionHeader(String title) {
        System.out.println();
        System.out.println(Colors.BOLD + Colors.YELLOW + "-- " + title + " " + "-".repeat(Math.max(0, WIDTH - title.length() - 4)) + Colors.RESET);
    }

    public static void separator() {
        System.out.println(Colors.DIM + "-".repeat(WIDTH) + Colors.RESET);
    }

    public static void thinSeparator() {
        System.out.println(Colors.DIM + "·".repeat(WIDTH) + Colors.RESET);
    }

    public static void blank() {
        System.out.println();
    }

    public static void info(String msg) {
        System.out.println(Colors.CYAN + "  " + msg + Colors.RESET);
    }

    public static void success(String msg) {
        System.out.println(Colors.GREEN + "  " + msg + Colors.RESET);
    }

    public static void warn(String msg) {
        System.out.println(Colors.YELLOW + "  " + msg + Colors.RESET);
    }

    public static void error(String msg) {
        System.out.println(Colors.RED + "  [ERROR] " + msg + Colors.RESET);
    }

    public static void label(String key, String value) {
        System.out.printf("  %s%-24s%s %s%n",
            Colors.DIM, key + ":", Colors.RESET, value);
    }

    public static void printSkillSummary(Skill skill, SkillStatus status, int index) {
        String statusBadge = statusBadgeColored(status);
        String priorityBadge = priorityColored(skill.getPriority());
        System.out.printf("  %s%2d.%s %s %s %-32s %s%n",
            Colors.DIM, index, Colors.RESET,
            statusBadge,
            priorityBadge,
            skill.getName(),
            Colors.DIM + skill.getDifficulty().getStars() + Colors.RESET
        );
    }

    public static void printSkillDetail(Skill skill, SkillStatus status) {
        header(skill.getName() + "  " + skill.getDifficulty().getStars());

        label("英語名", skill.getNameEn());
        label("カテゴリ", skill.getCategoryId());
        label("難易度", skill.getDifficulty().getLabel() + " " + skill.getDifficulty().getStars());
        label("優先度", priorityColored(skill.getPriority()) + " " + skill.getPriority().getLabel());
        label("学習時間目安", skill.getEstimatedHours() + "時間");
        label("学習状況", statusBadgeColored(status) + " " + status.getLabel());

        sectionHeader("概要");
        printWrapped(skill.getOverview().strip(), 2);

        sectionHeader("なぜ重要か");
        printWrapped(skill.getWhyItMatters().strip(), 2);

        sectionHeader("AI時代での意味");
        printWrapped(skill.getAiEraRelevance().strip(), 2);

        sectionHeader("学習ステップ");
        printWrapped(skill.getHowToLearn().strip(), 2);

        sectionHeader("主要トピック");
        for (String t : skill.getKeyTopics()) {
            System.out.println("  " + Colors.GREEN + "  + " + t + Colors.RESET);
        }

        if (!skill.getPrerequisites().isEmpty()) {
            sectionHeader("前提知識");
            for (String p : skill.getPrerequisites()) {
                System.out.println("  " + Colors.DIM + "  * " + p + Colors.RESET);
            }
        }

        sectionHeader("参考リソース");
        for (String r : skill.getResources()) {
            System.out.println("  " + Colors.BLUE + "  - " + r + Colors.RESET);
        }
        blank();
    }

    public static void printCategoryMenu(List<com.aigene.model.SkillCategory> categories) {
        System.out.println();
        for (int i = 0; i < categories.size(); i++) {
            var cat = categories.get(i);
            System.out.printf("  %s%2d.%s %s %-20s %s%n",
                Colors.BOLD, i + 1, Colors.RESET,
                Colors.CYAN + cat.getIcon() + Colors.RESET,
                Colors.BOLD + cat.getName() + Colors.RESET,
                Colors.DIM + cat.getDescription().substring(0, Math.min(35, cat.getDescription().length())) + "..." + Colors.RESET
            );
        }
    }

    private static void printWrapped(String text, int indent) {
        String pad = " ".repeat(indent);
        int maxWidth = WIDTH - indent;
        for (String rawLine : text.split("\n")) {
            String line = rawLine.strip();
            if (line.isEmpty()) { System.out.println(); continue; }
            while (line.length() > maxWidth) {
                int cut = line.lastIndexOf(' ', maxWidth);
                if (cut <= 0) cut = maxWidth;
                System.out.println(pad + line.substring(0, cut));
                line = line.substring(cut).stripLeading();
            }
            if (!line.isEmpty()) System.out.println(pad + line);
        }
    }

    private static String centerPad(String text, int width) {
        if (text.length() >= width) return text;
        int pad = (width - text.length()) / 2;
        return " ".repeat(pad) + text;
    }

    private static String statusBadgeColored(SkillStatus status) {
        return switch (status) {
            case COMPLETED   -> Colors.GREEN  + status.getBadge() + Colors.RESET;
            case IN_PROGRESS -> Colors.YELLOW + status.getBadge() + Colors.RESET;
            case NOT_STARTED -> Colors.DIM    + status.getBadge() + Colors.RESET;
        };
    }

    private static String priorityColored(Priority priority) {
        return switch (priority) {
            case CRITICAL -> Colors.RED    + priority.getBadge() + Colors.RESET;
            case HIGH     -> Colors.YELLOW + priority.getBadge() + Colors.RESET;
            case MEDIUM   -> Colors.CYAN   + priority.getBadge() + Colors.RESET;
            case LOW      -> Colors.DIM    + priority.getBadge() + Colors.RESET;
        };
    }
}
