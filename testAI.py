import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn import datasets
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split

#↑このプログラムでライブラリ（プログラムをやりやすくするための拡張機能）を読み込んでいる

#文法
#import A:Aというものを読み込む
#A as B:AをBとして扱う（名前の省略, いちいち書くときにフルネームはダルい）
#from sklearn import datasets
#scikit-learn（略して sklearn）には、学習用のサンプルデータが用意されている
#from sklearn.neural_network import MLPClassifier
#LPClassifier は 多層パーセプトロン（MLP） の分類器
#rom sklearn.model_selection import train_test_split
#データを 訓練用とテスト用に分けるための関数



#補足：ライブラリを読み込むときはプロジェクトファイル直下にvenv（仮想環境）を構築しておけ！
#適当にやるとこのプロジェクト以外のとこでもライブラリが干渉して競合する場合がある. 
#ゆえにこのプロジェクト内だけでライブラリを有効にしたいから, 仮想環境を構築してその中で管理する. 


#Numpy
#たくさんの数値（配列）を扱うのに便利なライブラリ
#Pandas
#データを表として扱う
#Matplotlib
#データや結果を図にして可視化するために使う
#Sklearn.datasets
#このライブラリから、今回学習に使うサンプルのデータをとってくる
#Sklearn.neural_network.MLPClassifier
#【ニューラルネットワーク】というアルゴリズム
#Sklearn.model_selection.train_test_split
#【訓練データ】と【テストデータ】を簡単に分けることができるライブラリ


#ディレクトリとは？
#以下のようなファイルの階層構造という概念の名前である
#sklearn/
# ├── __init__.py
# ├── linear_model/
# ├── neural_network/
# │    ├── __init__.py
# │    ├── _multilayer_perceptron.py
# │    └── _stochastic_optimizers.py
# ├── svm/
# └── ...


#moduleとpackage, libraryの関係について

#package（パッケージ）
#複数のモジュールをまとめたディレクトリ
#だいたいフォルダのなかに__init__.pyといファイルが入ってる. 
#ファイルの先頭に__のようにアンダーバーが入っている場合, それは触るなという意味. 
#これ系のファイルを直接読み込むのは危険（致命的なエラーが発生する可能性も）

#module（モジュール）
#pythonのファイル自体(.py)がモジュール
#Ex) math.py → import mathで読み込める. 本来このように直で読み込むことはあまりしない
#    大体ライブラリ（フォルダ）のさらに奥のフォルダ（サブパッケージ）に入っているのでパスを指定して読み込む
#    
#

iris = datasets.load_iris()

#irisという変数の中にアヤメの花データセット(学習する情報, 花びらの長さ, 色などの大量のデータ)をいれてる
#detasets.　というものを付けることでdetasets パッケージの野中の load_iris 関数を呼び出している. 
#Python での . は 「属性アクセス」 の記号
#
#モジュール.関数
#オブジェクト.メソッド
#オブジェクト.変数
#
#って感じで「あるまとまりの中の要素にアクセスする」って意味になる

#なぜただのデータなのに load_iris() という関数なのか？
#先述した通り, irisという変数にはにはデータセットを突っ込んでるが, 
#そもそもデータセットは情報がテキストでまとめられたCSVファイルに保存されている. 本来ならば
# CSVファイルを読み込む　→　numpy配列に変換　→　Bunchsに格納
#という手順を踏まなければならないが, load_iris()を呼び出すだけで, sklearnさんが全部やってくれる

#Bunchs：scikit-learn が読み込めるデータセットの形（型, クラス）

#データセットのkey
#データセットの中には様々なデータが入っている

#keys()関数を使って、iris で使える【キー】の一覧を確認できる
#キーの確認
#print(iris.keys())
#結果　ターミナル
#dict_keys(['data', 'target', 'target_names', 'DESCR', 'feature_names', 'filename'])

#各キーの説明
#sklearn/
# ├── .data ------------【データ】
# ├── .target ----------【正解ラベル】
# ├── .target_names ----【正解ラベルの情報】
# ├── .feature_names ---【データの情報】
# ├── .DESCR -----------【説明文】
# └── .filename --------【ファイルパス】

#【データ】直接的なデータ（花びらの色, 長さ, 数等）
#実際にデータの中身をprint(iris,data)で確認してみる
#結果↓
# [5.1 3.5 1.4 0.2]
# [4.9 3.  1.4 0.2]
# [4.7 3.2 1.3 0.2]
# [4.6 3.1 1.5 0.2]
#このような行列がたくさん並ぶ
#データが全部で何個あるのか, どんな形をしているのかを確認するためshape()関数を突っ込んでみる　→　print(iris.data.shape)
#結果↓
#(150, 4)
#150行, 4列の情報であることがわかる. つまり, 4つの特徴を持ったデータが150個並んでいるということだ

#【正解ラベル】.dataでの各データがどの品種なのかという情報
#中身を見る　→　print(iris.target)
#結果↓
#[0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
# 0 0 0 0 0 0 0 0 0 0 0 0 0 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
# 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 2 2 2 2 2 2 2 2 2 2 2
# 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2
# 2 2]
#さっきの各データに対応して数値が出てくる
#つまり, さっきのデータがどの品種（0,1,2）に対応しているかを示している. 

#【正解ラベルの情報】
#中身を見る　→　print(iris.target_names)
#結果↓
#['setosa' 'versicolor' 'virginica']
#さっきの正解ラベル（0,1,2）がそれぞれ（'setosa' 'versicolor' 'virginica'）という花の名前に対応していたことがわかる

#【データの情報】
#中身を見てみる　→　print(iris.feature_data)
#結果↓
#['sepal length (cm)', 'sepal width (cm)', 'petal length (cm)', 'petal width (cm)']
#データの4つの情報がそれぞれ何に対応していたのかを示している

#【説明文】
#データが 何件あるか
#特徴量（列）の説明
#ラベルの種類
#出典や注意事項
#などのメタデータを記してある部分
#中身は長いので省略

#【ファイルパス】
#中身を見てみる　→　print(iris.filename)
#結果↓
#iris.csv
#どのCSVファイルから読み込んだかを示す

df_iris = pd.DataFrame(data=iris.data, columns=iris.feature_names)

#df_irisという変数にデータフレーム化したirisのデータセットをぶち込む（detaとfeature_names）

#pandasはデータを表にしたりして整理できるライブラリEX↓

#import pandas as pd
#
#df = pd.DataFrame（[
#    [1, 11, 111],
#    [2, 22, 222],
#    [3, 33, 333],
#    [4, 44, 444]
#])
#print(df)

#結果↓
#   0  1   2
# 0 1 11 111
# 1 2 22 222
# 2 3 33 333
# 3 4 44 444

#このように配列に番号を振って行列っぽくしてくれる

#Dataframeとは
#Dataframeはpandasのクラスで, 先ほどのような行列っぽくデータを加工してくれるやつ
# [index][columns][data]で構成されていて, それぞれ行, 列, データの中身となっている
#index, columnsになんかを指定することでその行列の横にいろいろ付けてくれる. 例えば↓
#df_iris = pd.DataFrame(data=iris.data, columns=iris.feature_names)では, dataをiris.dataに指定して, 
#横の列(columns)にfeature_namesを指定して表を作ってる

df_iris['target'] = iris.target

#df_irisには現在iris.dataの情報とそれに対応するfeature_namesしかないが, df_iris['target']によって
#Dataframeに新たな列を作成している. さらに, df_iris['target'] = iris.targetとして, iris.targetの情報を
#先ほど新しく追加したtargetの列にぶち込んでる

#print(df_iris)で見てみる
#結果↓
#     sepal length (cm)  ...  target
#0                  5.1  ...       0
#1                  4.9  ...       0
#2                  4.7  ...       0
#3                  4.6  ...       0
#4                  5.0  ...       0
#..                 ...  ...     ...
#145                6.7  ...       2
#146                6.3  ...       2
#147                6.5  ...       2
#148                6.2  ...       2
#149                5.9  ...       2

#表として出力されているのがわかる. pandasでは行数や列数が多い場合省略されて表示されるため, 
#print(df_iris.to_string())をつかって省略せずすべてを出力することができる

data_train, data_test, target_train, target_test = train_test_split(
    iris.data, iris.target, test_size=0.2, random_state=0
    )

#データを訓練データとテストデータに分ける
#【訓練データ】AIモデルがそれらを学習する
#【テストデータ】学習したモデルにテストデータを実際に判定させて, 精度を測定する

#上記のデータセットの分類を行うのがscikit-learnの関数「train-test_split関数」である

#X_train, X_test, y_train, y_test = train_test_split(
#    X, y, test_size=0.2, random_state=42
#)

#だいたいこんな感じの構成になってて, X:入力データ, Y:ラベル, test_size:入力データ量に対するテストデータの割合, 
#train_size:test_sizeを決定することで自ずと決定する, random_state : 乱数シード, 固定すると毎回同じ分け方になる
#shuffle : デフォルトで True（データをシャッフルしてから分ける）
#実際に書いたさっきのコードの場合, iris.deta, iris.target,をデータとラベルに指定していて, 8:2の割合で
#テストデータと訓練データに分けている

clf = MLPClassifier(hidden_layer_sizes=10, activation='relu', solver='adam', max_iter=1000)

#実際にAI学習モデルを作る
#ニューラルネットワーク（Sklearn.neural_network）というアルゴリズム使用しているらしい
#cflという変数にMPLClassifier()という関数を呼び出して, ぶち込んでる
#MLPClassifierはscikit-learnが用意したクラスで, カテゴリを予測するような分類問題（花の品種を見分ける, スパムの判定等）
#で使用される
#今回は使用しなかったが, もう一つMPLRegression()というものがあり, これは回帰問題（価格予想, 気温予想）などで使用される
#さっきのコードのMPLClassifier()では, 4つの引数を設定することで, モデルをカスタマイズしている

#【hidden_layer_sizes】ニューラルネットワークの中間層（隠れ層）のニューロンを何個にするかを決める
#【activation】活性化関数に何を使うかを決める（わからん）
#【solver】最適化手法の選択（わからん）
#【max_iter】学習を繰り返す回数, 誤差が収束しない場合, 無限に繰り返すことになるため上限を設ける

clf.fit(data_train, target_train)

#fit()関数の引数に訓練データを与えることで, データを学習させることができる
#cflをただの変数からニューラルネットワークモデルに構築完了

#print(clf.score(data_train, target_train))
#score()関数をつかってどのくらい精度がいいか見てみる
#結果↓
#0.95
#つまり, 95%の確率でアヤメを識別できている

print(clf.predict(data_test))
print(target_test)

#predict 関数をつかって予想をclfに立てさせてみる
#実際にpredict()関数に渡すのはdata_testだけ, こいつからtarget_testを予想してもらう
#同時に解答のtarget_testも表示して比べてみる

print(clf.loss_curve_)

#loss_curve_にはその時の学習に対する損失（不正解？）の割合みたいなものが入ってる

plt.plot(clf.loss_curve_)
plt.title("Loss Curve")
plt.xlabel("Iteration")
plt.ylabel("Loss")
plt.grid()
plt.show()

#matplotlibでlossを表示させてみる

#plt.plot(clf.loss_curve_)  　clf.loss_curve_をプロットする
#plt.title("Loss Curve")　　　グラフタイトル
#plt.xlabel("Iteration")　　　x軸タイトル
#plt.ylabel("Loss")          y軸タイトル
#plt.grid()　　　　　　　　グリッドを表示
#plt.show()　　　　　　　　描画したグラフを画面に表示する
