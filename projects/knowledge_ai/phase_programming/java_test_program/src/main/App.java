package main;

public class App {   // ← ファイル名 App.java と一致させる
    public static void run(String[] args) {
        // 計算式1
        int result1 = Calculation.calculateExpression1(5, 3);
        System.out.println("計算式1: " + result1);

        // 計算式2
        int result2 = Calculation.calculateExpression2(5, 3);
        System.out.println("計算式2: " + result2);

        // 計算式3
        int result3 = Calculation.calculateExpression3(5, 3);
        System.out.println("計算式3: " + result3);
    }
}