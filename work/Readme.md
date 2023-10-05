# macro
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

## ReadDataToDF
   data.pickleから、scanpointsとanalysisを抽出してpandas.DataFrameにする。
  .pickleと.csvで保存する。
## ReadJson
  db.jsonのresultsの各項目について、ヒストグラムを作成する。
### jsonAnalysis
ReadJsonを自動化した。　　
すべてのヒストグラムの保存と、それぞれの項目についてsummaryをpandas.DataFrameにする。

## validateSquare
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


# data
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
