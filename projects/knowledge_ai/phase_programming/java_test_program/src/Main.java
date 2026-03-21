// 関数を呼んで、別々の計算式を実行するJavaプログラム
import main.App;          // main パッケージの App クラス
import main.Calculation;  // main パッケージの Calculation クラス
import main.JsonGet;     // main パッケージの JsonGet クラス
import main.UserModel;        // main パッケージの UserModel クラス
import calculation.Pandas;    // calculation パッケージの Pandas クラス
import org.json.JSONObject;
// JSON処理のためのライブラリ

public class Main {

    // main/App.javaを呼び出す
    public static void callApp() {
        App.run(new String[]{});
    }

    public static void main(String[] args) {
        // 計算式1
        int result1 = Calculation.calculateExpression1(5, 3);
        System.out.println("計算式1: " + result1);

        // 計算式2
        int result2 = Calculation.calculateExpression2(5, 3);
        System.out.println("計算式2: " + result2);

        // 計算式3
        int result3 = Calculation.calculateExpression3(5, 3);
        System.out.println("計算式3: " + result3);

        // main/App.javaを呼び出す
        callApp();
        String json = JsonGet.getJson();
        JSONObject jsonObject = new JSONObject(json);
        String name = jsonObject.getString("name"); // JSONから特定の値を取得
        int age = jsonObject.getInt("age"); // JSONから特定の値を取得
        System.out.println("名前: " + name);
        System.out.println("年齢: " + age);
        UserModel user = new UserModel(name, age); // UserModelクラスのインスタンスを作成
        System.out.println("UserModel - 名前: " + user.getName() + ", 年齢: " + user.getAge());

        // pandas 風操作のサンプル
        Pandas.exampleMethod();
    }

}