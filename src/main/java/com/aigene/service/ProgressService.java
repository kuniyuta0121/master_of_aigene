package com.aigene.service;

import com.aigene.model.SkillStatus;
import com.aigene.model.UserProfile;

import java.io.*;
import java.nio.file.*;
import java.util.*;

public class ProgressService {

    private static final Path DATA_DIR = Path.of(System.getProperty("user.home"), ".master_of_aigene");
    private static final Path PROGRESS_FILE = DATA_DIR.resolve("progress.properties");
    private static final Path PROFILE_FILE = DATA_DIR.resolve("profile.properties");

    private final Map<String, SkillStatus> progressMap = new HashMap<>();
    private UserProfile profile;

    public ProgressService() {
        ensureDataDir();
        loadProgress();
        loadProfile();
    }

    private void ensureDataDir() {
        try {
            Files.createDirectories(DATA_DIR);
        } catch (IOException e) {
            System.err.println("データディレクトリの作成に失敗: " + e.getMessage());
        }
    }

    // --- Progress ---

    public SkillStatus getStatus(String skillId) {
        return progressMap.getOrDefault(skillId, SkillStatus.NOT_STARTED);
    }

    public void setStatus(String skillId, SkillStatus status) {
        progressMap.put(skillId, status);
        saveProgress();
    }

    public Map<String, SkillStatus> getAllProgress() {
        return Collections.unmodifiableMap(progressMap);
    }

    public long countByStatus(SkillStatus status) {
        return progressMap.values().stream().filter(s -> s == status).count();
    }

    private void loadProgress() {
        if (!Files.exists(PROGRESS_FILE)) return;
        Properties props = new Properties();
        try (InputStream in = Files.newInputStream(PROGRESS_FILE)) {
            props.load(in);
            props.forEach((k, v) -> {
                try {
                    progressMap.put((String) k, SkillStatus.valueOf((String) v));
                } catch (IllegalArgumentException ignored) {}
            });
        } catch (IOException e) {
            System.err.println("進捗データの読み込みに失敗: " + e.getMessage());
        }
    }

    private void saveProgress() {
        Properties props = new Properties();
        progressMap.forEach((k, v) -> props.setProperty(k, v.name()));
        try (OutputStream out = Files.newOutputStream(PROGRESS_FILE)) {
            props.store(out, "Master of AI Gene - Progress Data");
        } catch (IOException e) {
            System.err.println("進捗データの保存に失敗: " + e.getMessage());
        }
    }

    // --- Profile ---

    public UserProfile getProfile() {
        return profile;
    }

    public boolean hasProfile() {
        return profile != null && profile.getName() != null && !profile.getName().isBlank();
    }

    public void saveProfile(UserProfile p) {
        this.profile = p;
        Properties props = new Properties();
        props.setProperty("name", p.getName() != null ? p.getName() : "");
        props.setProperty("years", String.valueOf(p.getYearsOfExperience()));
        props.setProperty("goal", p.getCareerGoal().name());
        props.setProperty("skills", String.join(",", p.getCurrentSkillIds()));
        if (p.getNotes() != null) props.setProperty("notes", p.getNotes());
        try (OutputStream out = Files.newOutputStream(PROFILE_FILE)) {
            props.store(out, "Master of AI Gene - User Profile");
        } catch (IOException e) {
            System.err.println("プロファイルの保存に失敗: " + e.getMessage());
        }
    }

    private void loadProfile() {
        if (!Files.exists(PROFILE_FILE)) {
            profile = new UserProfile();
            return;
        }
        Properties props = new Properties();
        try (InputStream in = Files.newInputStream(PROFILE_FILE)) {
            props.load(in);
            UserProfile p = new UserProfile();
            p.setName(props.getProperty("name", ""));
            p.setYearsOfExperience(Integer.parseInt(props.getProperty("years", "0")));
            try {
                p.setCareerGoal(UserProfile.CareerGoal.valueOf(props.getProperty("goal", "PRODUCT_MANAGER")));
            } catch (IllegalArgumentException e) {
                p.setCareerGoal(UserProfile.CareerGoal.PRODUCT_MANAGER);
            }
            String skillsStr = props.getProperty("skills", "");
            if (!skillsStr.isBlank()) {
                Arrays.stream(skillsStr.split(","))
                      .map(String::trim)
                      .filter(s -> !s.isEmpty())
                      .forEach(p::addCurrentSkill);
            }
            p.setNotes(props.getProperty("notes", ""));
            profile = p;
        } catch (IOException e) {
            profile = new UserProfile();
        }
    }

    public Path getDataDir() {
        return DATA_DIR;
    }
}
