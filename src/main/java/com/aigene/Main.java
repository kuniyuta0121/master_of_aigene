package com.aigene;

import com.aigene.data.SkillRepository;
import com.aigene.service.ProgressService;
import com.aigene.service.RecommendationService;
import com.aigene.ui.ConsoleApp;

public class Main {

    public static void main(String[] args) {
        var repository = new SkillRepository();
        var progressService = new ProgressService();
        var recommendationService = new RecommendationService(repository, progressService);
        var app = new ConsoleApp(repository, progressService, recommendationService);
        app.run();
    }
}
