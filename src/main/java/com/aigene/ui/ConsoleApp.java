package com.aigene.ui;

import com.aigene.data.SkillRepository;
import com.aigene.model.*;
import com.aigene.service.ProgressService;
import com.aigene.service.RecommendationService;

import java.util.*;

public class ConsoleApp {

    private final SkillRepository repository;
    private final ProgressService progressService;
    private final RecommendationService recommendationService;
    private final Scanner scanner;

    public ConsoleApp(SkillRepository repository, ProgressService progressService,
                      RecommendationService recommendationService) {
        this.repository = repository;
        this.progressService = progressService;
        this.recommendationService = recommendationService;
        this.scanner = new Scanner(System.in);
    }

    public void run() {
        showWelcome();

        if (!progressService.hasProfile()) {
            setupProfile();
        }

        mainLoop();
    }

    private void showWelcome() {
        Printer.blank();
        Printer.header("Master of AI Gene");
        Printer.blank();
        Printer.info("AIが急成長する時代に、ITエンジニアとして40〜50年食べていくための");
        Printer.info("技術体系ナビゲーションシステム");
        Printer.blank();

        var summary = recommendationService.getProgressSummary();
        long total = summary.get("total");
        long done = summary.get("completed");
        long wip = summary.get("inProgress");

        if (done > 0 || wip > 0) {
            Printer.sectionHeader("学習進捗");
            Printer.label("習得済", done + " スキル");
            Printer.label("学習中", wip + " スキル");
            Printer.label("未着手", summary.get("notStarted") + " スキル");
            Printer.label("全スキル数", total + " スキル");
            // Simple progress bar
            int barWidth = 40;
            int doneBar = (int) (done * barWidth / total);
            int wipBar  = (int) (wip  * barWidth / total);
            String bar = Colors.GREEN + "#".repeat(doneBar) + Colors.RESET
                       + Colors.YELLOW + "~".repeat(wipBar) + Colors.RESET
                       + Colors.DIM + ".".repeat(barWidth - doneBar - wipBar) + Colors.RESET;
            System.out.println("  [" + bar + "] " + done + "/" + total);
        }
        Printer.blank();
    }

    private void mainLoop() {
        while (true) {
            Printer.sectionHeader("メインメニュー");
            System.out.println("  1. スキルカテゴリを閲覧する");
            System.out.println("  2. パーソナライズドロードマップを見る");
            System.out.println("  3. スキルを検索する");
            System.out.println("  4. 学習状況を更新する");
            System.out.println("  5. マイプロフィールを確認・更新する");
            System.out.println("  6. 終了");
            Printer.blank();

            int choice = readInt("選択 (1-6): ", 1, 6);
            switch (choice) {
                case 1 -> browseCategoryMenu();
                case 2 -> showRoadmap();
                case 3 -> searchSkills();
                case 4 -> updateProgress();
                case 5 -> showAndEditProfile();
                case 6 -> { Printer.success("また明日も学習を続けましょう！"); return; }
            }
        }
    }

    // -------------------------------------------------------
    // 1. カテゴリ閲覧
    // -------------------------------------------------------
    private void browseCategoryMenu() {
        while (true) {
            Printer.header("スキルカテゴリ一覧");
            var categories = repository.getAllCategories();
            Printer.printCategoryMenu(categories);
            System.out.println();
            System.out.println("  " + Colors.DIM + "0. 戻る" + Colors.RESET);
            Printer.blank();

            int choice = readInt("カテゴリを選択 (0-" + categories.size() + "): ", 0, categories.size());
            if (choice == 0) return;

            browseSkillList(categories.get(choice - 1));
        }
    }

    private void browseSkillList(SkillCategory category) {
        while (true) {
            Printer.header(category.getIcon() + " " + category.getName());
            Printer.info(category.getDescription());
            Printer.blank();

            var skills = repository.findByCategory(category.getId());
            skills.sort(Comparator.comparingInt(s -> switch (s.getPriority()) {
                case CRITICAL -> 0; case HIGH -> 1; case MEDIUM -> 2; case LOW -> 3;
            }));

            for (int i = 0; i < skills.size(); i++) {
                var skill = skills.get(i);
                var status = progressService.getStatus(skill.getId());
                Printer.printSkillSummary(skill, status, i + 1);
            }

            System.out.println();
            System.out.println("  " + Colors.DIM + "0. 戻る" + Colors.RESET);
            Printer.blank();

            int choice = readInt("スキルを選択して詳細を表示 (0-" + skills.size() + "): ", 0, skills.size());
            if (choice == 0) return;

            showSkillDetail(skills.get(choice - 1));
        }
    }

    private void showSkillDetail(Skill skill) {
        var status = progressService.getStatus(skill.getId());
        Printer.printSkillDetail(skill, status);

        System.out.println("  1. 学習状況を変更する");
        System.out.println("  0. 戻る");
        Printer.blank();

        int choice = readInt("選択 (0-1): ", 0, 1);
        if (choice == 1) {
            changeSkillStatus(skill);
        }
    }

    // -------------------------------------------------------
    // 2. ロードマップ
    // -------------------------------------------------------
    private void showRoadmap() {
        Printer.header("パーソナライズドロードマップ");
        var profile = progressService.getProfile();
        Printer.info("キャリアゴール: " + Colors.bold(profile.getCareerGoal().getLabel()));
        Printer.info(profile.getCareerGoal().getDescription());
        Printer.blank();

        Printer.sectionHeader("おすすめ学習順序（TOP 15）");
        var recs = recommendationService.getRecommendations(profile, 15);

        for (int i = 0; i < recs.size(); i++) {
            var rec = recs.get(i);
            var skill = rec.skill();
            var status = progressService.getStatus(skill.getId());

            System.out.printf("  %s%2d.%s %-30s  %s  %s%n",
                Colors.BOLD, i + 1, Colors.RESET,
                Colors.BOLD + skill.getName() + Colors.RESET,
                Colors.DIM + "[" + skill.getCategoryId() + "]" + Colors.RESET,
                Colors.YELLOW + rec.reason() + Colors.RESET
            );
            System.out.printf("      %s %s  学習目安: %d時間%n",
                progressService.getStatus(skill.getId()).getBadge(),
                skill.getDifficulty().getStars(),
                skill.getEstimatedHours()
            );
        }

        Printer.blank();
        System.out.println("  1. スキルの詳細を表示する");
        System.out.println("  0. 戻る");

        int choice = readInt("選択 (0-1): ", 0, 1);
        if (choice == 1) {
            int idx = readInt("スキル番号を入力 (1-" + recs.size() + "): ", 1, recs.size());
            showSkillDetail(recs.get(idx - 1).skill());
        }
    }

    // -------------------------------------------------------
    // 3. 検索
    // -------------------------------------------------------
    private void searchSkills() {
        Printer.header("スキル検索");
        System.out.print("  キーワードを入力: ");
        String keyword = scanner.nextLine().trim();

        if (keyword.isEmpty()) return;

        var results = repository.searchByKeyword(keyword);

        if (results.isEmpty()) {
            Printer.warn("「" + keyword + "」に一致するスキルが見つかりませんでした。");
            pressEnter();
            return;
        }

        Printer.blank();
        Printer.info(results.size() + " 件ヒット");
        Printer.blank();

        for (int i = 0; i < results.size(); i++) {
            var skill = results.get(i);
            var status = progressService.getStatus(skill.getId());
            Printer.printSkillSummary(skill, status, i + 1);
            System.out.println("      " + Colors.DIM + skill.getShortDescription() + Colors.RESET);
        }

        System.out.println();
        System.out.println("  1. 詳細を表示する");
        System.out.println("  0. 戻る");

        int choice = readInt("選択 (0-1): ", 0, 1);
        if (choice == 1) {
            int idx = readInt("スキル番号を入力 (1-" + results.size() + "): ", 1, results.size());
            showSkillDetail(results.get(idx - 1));
        }
    }

    // -------------------------------------------------------
    // 4. 進捗更新
    // -------------------------------------------------------
    private void updateProgress() {
        Printer.header("学習状況を更新する");
        Printer.info("カテゴリを選んでスキルの学習状況を更新します。");

        var categories = repository.getAllCategories();
        Printer.printCategoryMenu(categories);
        System.out.println("  " + Colors.DIM + "0. 戻る" + Colors.RESET);

        int catChoice = readInt("カテゴリ (0-" + categories.size() + "): ", 0, categories.size());
        if (catChoice == 0) return;

        var category = categories.get(catChoice - 1);
        var skills = repository.findByCategory(category.getId());

        Printer.blank();
        Printer.sectionHeader(category.getName() + " のスキル");
        for (int i = 0; i < skills.size(); i++) {
            var skill = skills.get(i);
            var status = progressService.getStatus(skill.getId());
            Printer.printSkillSummary(skill, status, i + 1);
        }

        System.out.println("  " + Colors.DIM + "0. 戻る" + Colors.RESET);
        int skillChoice = readInt("スキルを選択 (0-" + skills.size() + "): ", 0, skills.size());
        if (skillChoice == 0) return;

        changeSkillStatus(skills.get(skillChoice - 1));
    }

    private void changeSkillStatus(Skill skill) {
        Printer.blank();
        Printer.sectionHeader("学習状況変更: " + skill.getName());
        var current = progressService.getStatus(skill.getId());
        Printer.label("現在の状況", current.getLabel());
        Printer.blank();

        System.out.println("  1. " + SkillStatus.NOT_STARTED.getBadge() + " 未着手");
        System.out.println("  2. " + SkillStatus.IN_PROGRESS.getBadge() + " 学習中");
        System.out.println("  3. " + SkillStatus.COMPLETED.getBadge() + " 習得済");
        System.out.println("  0. キャンセル");
        Printer.blank();

        int choice = readInt("選択 (0-3): ", 0, 3);
        if (choice == 0) return;

        SkillStatus newStatus = switch (choice) {
            case 1 -> SkillStatus.NOT_STARTED;
            case 2 -> SkillStatus.IN_PROGRESS;
            case 3 -> SkillStatus.COMPLETED;
            default -> throw new IllegalStateException();
        };

        progressService.setStatus(skill.getId(), newStatus);
        Printer.success("更新しました: " + skill.getName() + " → " + newStatus.getLabel());
        pressEnter();
    }

    // -------------------------------------------------------
    // 5. プロフィール
    // -------------------------------------------------------
    private void showAndEditProfile() {
        Printer.header("マイプロフィール");
        var profile = progressService.getProfile();
        Printer.label("名前", profile.getName() != null ? profile.getName() : "(未設定)");
        Printer.label("経験年数", profile.getYearsOfExperience() + "年");
        Printer.label("キャリアゴール", profile.getCareerGoal().getLabel());
        Printer.label("保存場所", progressService.getDataDir().toString());
        Printer.blank();

        System.out.println("  1. プロフィールを更新する");
        System.out.println("  0. 戻る");

        int choice = readInt("選択 (0-1): ", 0, 1);
        if (choice == 1) setupProfile();
    }

    private void setupProfile() {
        Printer.header("プロフィール設定");
        Printer.info("あなたに合ったロードマップを生成するために情報を入力してください。");
        Printer.blank();

        var profile = progressService.getProfile();

        System.out.print("  お名前（ハンドルネームでも可）: ");
        String name = scanner.nextLine().trim();
        if (!name.isEmpty()) profile.setName(name);

        System.out.print("  エンジニア経験年数（数字）: ");
        try {
            int years = Integer.parseInt(scanner.nextLine().trim());
            profile.setYearsOfExperience(years);
        } catch (NumberFormatException ignored) {}

        Printer.blank();
        Printer.sectionHeader("キャリアゴール");
        var goals = UserProfile.CareerGoal.values();
        for (int i = 0; i < goals.length; i++) {
            System.out.printf("  %d. %-28s  %s%n", i + 1,
                goals[i].getLabel(), Colors.DIM + goals[i].getDescription() + Colors.RESET);
        }
        Printer.blank();

        int goalChoice = readInt("キャリアゴール (1-" + goals.length + "): ", 1, goals.length);
        profile.setCareerGoal(goals[goalChoice - 1]);

        progressService.saveProfile(profile);
        Printer.success("プロフィールを保存しました！");
        Printer.blank();
    }

    // -------------------------------------------------------
    // Utility
    // -------------------------------------------------------
    private int readInt(String prompt, int min, int max) {
        while (true) {
            System.out.print(Colors.BOLD + "  >> " + prompt + Colors.RESET);
            try {
                int val = Integer.parseInt(scanner.nextLine().trim());
                if (val >= min && val <= max) return val;
                Printer.warn(min + " 〜 " + max + " の範囲で入力してください。");
            } catch (NumberFormatException e) {
                Printer.warn("数字を入力してください。");
            }
        }
    }

    private void pressEnter() {
        System.out.print(Colors.DIM + "  [Enterキーで続ける] " + Colors.RESET);
        scanner.nextLine();
    }
}
