# モジュール
macro/の中においてある。   
ここでは概要を述べる。詳しくはmacroの中のreadmeを参照。

## data.pickleから値を読み取る
+ ReadDataToDF_PCB.py
+ ReadDataToDF_BareModule.py
+ ReadDataToDF_module.py   
の3つ。
それぞれ、
+ scanpointのx,y,zを取得した「ScanData」
+ analysisの結果を取得した「AnalysisData」   
のdataframeを作り、「*.pickle」にして保存。
csv形式でも保存している（表形式で見やすいから）

## db.jsonから値を読み取る
+ ReadJson_PCB.py
+ ReadJson_BareModule.py
+ ReadJson_module.py
の3つ。   
引数を与えることで、db.jsonのresultsの値についてヒストグラムを作ることができる。

### 関連するモジュール
+ jsonAnalysis_*.py   
ReadJsonを自動化した。pcb, baremodule, moduleのそれぞれある。   　
すべてのresultsの項目のヒストグラムの保存と、それぞれの項目についてのsummaryをpandas.DataFrameにする。

+ myModules/data_*.py   
特定のシリアルナンバーについて、使用するスキャンのディレクトリを指定するために作った。   
「使わないシリアルナンバー」と「00Xのうち、最大値じゃないものを使うシリアルナンバー」を指定することができる。

## pickleの解析
### fiducial markの相対位置を見る
+ validateSquare.py
Fmarkの距離と角度を計算してヒストグラムにする   

Fmarkの距離と角度を計算してヒストグラムにする。結果はcsvで保存する。　　
引数でAsicFmarkかFlexFmarkか指定できる。
Fmark間の距離についてはTop,Bottom,Left,Right、   
角度についてはTopRight, BottomLeft   
のいずれかを指定して1つのヒストグラムを作る。   
それぞれについて、指定した値から外れたシリアルナンバーを特定し、標準偏差や最大値最小値などのsummaryを保存する。   
保存先＞resultsHist/validateSQ

ただし、引数に何を指定しても、毎回resultsとして作られるdataframeは同じ。要改善…。   
このresultsのdataframeもcsvとして保存される。   
保存先＞data/validateSQ


## 
## marginplot_2
## getFilelist
## STDofZ
## zHist
## margin
## ReadData
## zplot
## readReults
## marginplot
## drawPoint
## draw


# 解析した結果のありか
## scanProcessor data
### **_AnalysisData  
+ PCB
+ MODULE
+ BAREMODULE
### **_ScanData
+ PCB
+ BAREMODULE
+ MODULE

###zDataFrameDescribe
##margin
