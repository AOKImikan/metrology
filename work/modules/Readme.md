how to use these macro
# 元データを読みやすい形にするモジュール
## ReadDataToDF
   data.pickleから、scanpointsとanalysisを抽出してpandas.DataFrameにする。
  .pickleと.csvで保存する。

  BAREMODULE, PCB, MODULEのそれぞれについて、pmmクラスの内容が異なるため、それぞれモジュールがある。
  + ReadDataToDF_baremodule.py
  + ReadDataToDF_module.py
  + ReadDataToDF_pcb.py   
  実行すると、dataframe型になったscan dataとanalysis dataが/work/data/に保存される。

## ReadJson
  db.jsonのresultsの各項目について、ヒストグラムを作成する。

## jsonAnalysis
  ReadJsonを自動化した。  
  すべてのヒストグラムの保存と、それぞれの項目についてsummaryをpandas.DataFrameにする。

## myModules / data_**.py
  + data_baremodule
  + data_pcb
  + data_module  

データのパスを取得するmodule.   
特定のシリアルナンバーのデータを使わないこと、特定のシリアルナンバーに対してscan numberを指定することができる。
ここで指定しない場合、00Xのうち一番大きいディレクトリのパスになる。

# ASSEMBLY MODULE Metrologyの検証用モジュール
## FiducialMarkの位置について検証するモジュール
### margin.py
検出位置と写真の中心との相対座標について解析する。
引数は、
+ -a --asic   
  TL, TR, BL, BRのいずれかを指定。
  
+ -f --flex   
  TL, TR, Bl, BRのいずれかを指定。

指定したFmarkについて、写真の中心（scanのxy）と検出点(Fmarkのxy）の距離(=margin)を計算する。
計算結果はdataframe型で管理し、csvで保存される。work/data/margin/*.csv

いずれは、Fmarkだけでなく辺の検出についても、写真を撮影する位置がずれてないか見たい。

+ -p --plot   
  これを指定すると、検出点のxy座標の分布のプロットを表示&保存する。   
  中でFmarkMarginPlot.pyを呼び出しているだけなので、FmarkMarginPlot.pyを単体で使っても同じ。

### FmarkMarginPlot.py
引数はmargin.pyと同じ。

scanのxyzのデータとanalysisのxyのデータから、写真の中心と検出位置をscatter plotする。

ただし、scanのz座標の偏差が、同じtagでまとめて計算した標準偏差×3より大きいときは、赤色で点をプロットする。
（それ以外は青）
z座標がおかしかった時、ImagePath、シリアルナンバー、z座標などのscan dataに格納されている情報なら簡単に返すことができる。
ただし検出されたxy座標を返すのはいささか大変なので、要改善。

また、写真の辺と中心を緑でプロットしている。

### validateSquare.py  
Fmarkの距離と角度を計算してヒストグラムにする。結果はcsvで保存する。  

引数は、
+ A or F
第一引数。AsicかFlexか。
+ -r --ranges   
Fmark間の距離をヒストグラムにする。   
T:上辺、B:下辺、L:左辺、R:右辺
+ -a --angles   
Fmarkの二つの辺の内積から角度(degree)をヒストグラムにする。
TR:右上の内角、BL:左下の内角

+ fmarkのmargin
+ zの分布
+ Fmarkの相対位置


## marginplot_2
## getFilelist
## scanのz座標について検証するモジュール
### STDofZ
+ -e --extract
+ --hist
  
extractは、stdがthreshold（第二引数）より大きいtagを抽出してdataframeにする。

histは、各tagのstdをヒストグラムにする。各tagのstdについて、csvで保存。

## zHist
## margin
## ReadData
## zplot
## readReults
## marginplot
## drawPoint
## draw
