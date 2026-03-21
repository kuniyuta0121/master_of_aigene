package main;

public class UserModel {
    private String name;
    private int age;

    // コンストラクタ
    public UserModel(String name, int age) {
        this.name = name;
        this.age = age;
    }

    // ゲッター
    public String getName() {
        return name;
    }

    public int getAge() {
        return age;
    }

    // セッター
    public void setName(String name) {
        this.name = name;
    }

    public void setAge(int age) {
        this.age = age;
    }
}