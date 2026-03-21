まとめ：なぜ javac では動かないのか

# NG: javac は ~/.m2 の JAR を知らない

javac Main.java → org.json が見つからないエラー

# OK: Maven が JAR をクラスパスに自動追加して渡してくれる

mvn compile → 依存 JAR を含めてコンパイル
mvn exec:java → 依存 JAR を含めて実行
Python に例えると：

# NG: python だけ呼ぶと site-packages が使えない場合がある

python main.py

# OK: venv 経由で実行すると pip install したものが使える

python -m venv .venv && source .venv/bin/activate && python main.py
Maven は「venv の有効化」と「クラスパスの設定」を一緒にやってくれるツールです。
