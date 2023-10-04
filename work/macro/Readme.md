how to use these macro
## ReadDataToDF
   data.pickleから、scanpointsとanalysisを抽出してpandas.DataFrameにする。
  .pickleと.csvで保存する。
  
## ReadJson
  db.jsonのresultsの各項目について、ヒストグラムを作成する。
  ### jsonAnalysis
  ReadJsonを自動化した。  
  すべてのヒストグラムの保存と、それぞれの項目についてsummaryをpandas.DataFrameにする。

## myModules
*data_**.py*
  + _baremodule
  + _pcb
  + _module  
  データのパスを取得するmodule.  
  特定のシリアルナンバーのデータを使わないこと、特定のシリアルナンバーに対してscan numberを指定することができる。
 
 ## validateSquare
  + _Asic.py
  + _Flex.py

  Fmarkの距離と角度を計算してヒストグラムにする。結果はcsvで保存する。  
  + hist4()　…　4辺の長さのヒストグラムを表示＆保存  
  + hist2()　…　対角（TRとBL）の角度のヒストグラムを表示＆保存
    
## marginplot_2
## getFilelist
## STDofZ
+ -a --asic
+ -f --flex
+ -e --extract
+ --hist  
Asic,FlexのFmarkについて、写真の中央と検出点をプロットする。  
zの座標が大きく外れている（偏差が0.03より大きい）場合、検出点を赤色で表示し、ImagePathをprintする。

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
