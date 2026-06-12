# 使用 GAP 绘制有限维代数的 AR Quiver

## 启动容器

自动启动: 点击 [![Binder](https://raw.githubusercontent.com/czhang271828/imgs/New_img//n_imgbadge_logo.svg)](https://mybinder.org/v2/gh/zhangchenchengSJTU/GAP_AR_Quiver/HEAD).

手动启动: 在 [Binder](https://mybinder.org/) 中打开 GitHub 仓库. 依次完成以下两个步骤即可, 请勿进行多余动作.

1. 确认 `GitHub repository name or URL` 一栏显示 `GitHub`. 在右侧粘贴 `https://github.com/zhangchenchengSJTU/GAP_AR_Quiver`.
2. 直接点击 `Launch` 按钮.
3. 等待环境启动完成. 随后 Binder 会自动跳转至 Jupyter Notebook 页面.

## 进入 Jupyter Notebook

进入 Jupyter Notebook 后, 浏览器上的地址形如 `https://hub.bids.mybinder.org/user/zhangchenchengsjtu-gap_ar_quiver-???????/treee`. 此时 root 目录下出现以下三项

- `Dockerfile`: 这是搭建环境的说明文件, 供开发者使用. 用户无需关注.
- `Readme.md`: 这是说明文档.
- `ARquiver`: 这是绘制 ARquiver 的文件夹. 进入该文件夹后会出现
  - `source` 文件夹, 这是存放源码的文档, 用户无需关注.
  - `run.ipynb` 文件, 这是运行脚本.
  - `example.txt`, `untitled.txt` 等文件, 这是输入 quiver 信息的文件.


## 绘制路代数

请使用 `https://q.uiver.app/` 网页绘制 quiver with relation. 绘制时请注意

- quiver 的顶点只能是简单正整数,
- quiver 的边是简单的拉丁字母或 $\LaTeX$ 格式的希腊字母, 如 `a` 或者 `\alpha`,
- 请随机寻找空白的格子输入路代数的关系 `rel: ....` .

示例图:

![image-20260612214532284](https://raw.githubusercontent.com/czhang271828/imgs/New_img//n_imgimage-20260612214532284.png)

点击网页下方 `LaTeX`, 复制 `tikzcd` 源码. 

在 `ARquiver` 文件夹中新建 `txt` 文件 `yourfile.txt`, 粘贴刚才复制的源码. 保存并退出.

## 绘制 AR quiver

请打开 `run.ipynb`. 依次运行

```python
# Compute algebra data: filename.txt -> filename.log
%run source/compute_all.py
```

```python
# Render interactive diagram: filename.log -> filename.html
%run source/render_all.py
```

此时 `ARquiver` 文件夹中将出现

- `yourfile.log`  (代数计算日志) 与
- `yourfile.html` (quiver 画布).

## 将 AR quiver 转换成常见形式

打开 `yourfile.html` 文件, 即可查看 AR quiver 的可视化图像. 

![image-20260612215317720](https://raw.githubusercontent.com/czhang271828/imgs/New_img//n_imgimage-20260612215317720.png)

先介绍与 AR quiver 相关的功能.

- 界面中的每个椭圆表示一个不可分解模, 维数向量依照 `tikzcd` 的顶点位置排列. 
- 紫色为投射且内射的对象. 红色为投射且非内射的对象, 蓝色为内射且非投射的对象.
- `Irr`: 显示/隐藏不可约态射 (黑色箭头).
- `tau`: 显示/隐藏 AR 平移 $\tau = D \mathrm{Tr}$ (金色箭头).
- `Border`: 显示/隐藏圆框. 
- `Ctrl + Z` 撤销, `Ctrl + Y` 重做.

我们需要手动完成的任务是将 AR quiver 排列成标准格式. 此处介绍一些技巧. 

*Lemma* 所有 $\tau$-轨道 (金色箭头的轨道) 不交. 投射内射对象不属于任何 $\tau$ 轨道, 除此以外的不可分解模恰好属于一个 $\tau$ 轨道. 因此, $\tau$ 轨道分为两类

- 一条直路, 从内射对象一路指向投射对象,
- 一条环路, 不经过任何投射或内射对象.

依照引理. 我们优先对投射对象 $\substack{2\\ 2 \quad 0}$ 进行操作. 请先关闭 `Irr`, 再将箭头 $\substack{2\\ 2 \quad 0} \ \ \leftarrow \ \substack{2\\ 2 \quad 2}$ 水平放置在空的地方. 长按金色箭头, 以校准下一箭头的位置. 最终得到

![image-20260612220603319](https://raw.githubusercontent.com/czhang271828/imgs/New_img//n_imgimage-20260612220603319.png)

接着打开 `Irr`, 尝试找到几乎可裂短正合列 $\substack{2\\ 2 \quad 0} \ \ \rightarrowtail \bigoplus M_i  \twoheadrightarrow \ \substack{2\\ 2 \quad 2}$ 

![image-20260612220820836](https://raw.githubusercontent.com/czhang271828/imgs/New_img//n_imgimage-20260612220820836.png)

接着关闭 `Irr`, 长按金色箭头校准. 如果存在环路, 可以用鼠标选中边, 使用 `↑` 与 `↓` 键调整箭头弧度. 经过一系列操作可得 $\tau$ 轨道

![image-20260612221253587](https://raw.githubusercontent.com/czhang271828/imgs/New_img//n_imgimage-20260612221253587.png)

我们最终得到了 AR quiver. 请关闭 `tau`, 调整 (被金色箭头挡住的) 水平黑边的弧度. 如果觉得有些边不好看, 可以双击切换深色/浅色. 最后得到

![image-20260612222112774](https://raw.githubusercontent.com/czhang271828/imgs/New_img//n_imgimage-20260612222112774.png)

## 其他功能

`Syzygy` 用于转换
