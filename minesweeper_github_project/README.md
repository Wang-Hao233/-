# 扫雷游戏 Minesweeper

这是一个适合课程实践和 GitHub 提交的 Python 扫雷游戏项目。项目采用 **Tkinter 图形界面 + 独立游戏逻辑模块 + 单元测试** 的结构，便于演示、维护和答辩。

## 功能特点

- 三种难度：初级、中级、高级
- 左键翻开格子，右键插旗/取消插旗
- 第一次点击安全：首次翻开不会踩雷，且优先保护周围 8 个格子
- 自动展开空白区域
- 双击已翻开的数字格：当周围旗数等于数字时，自动翻开其他相邻格
- 剩余雷数、计时器、状态提示
- 胜负判定和弹窗提示
- 核心逻辑与界面分离，便于测试

## 项目结构

```text
minesweeper_github_project/
├── main.py                    # 本地启动入口
├── pyproject.toml             # 项目配置
├── README.md                  # 项目说明
├── .gitignore                 # Git 忽略文件
├── src/
│   └── minesweeper/
│       ├── __init__.py
│       ├── __main__.py        # python -m minesweeper 入口
│       ├── core.py            # 游戏核心逻辑
│       └── tk_app.py          # Tkinter 图形界面
└── tests/
    └── test_core.py           # 单元测试
```

## 运行方法

### 方式一：直接运行

```bash
python main.py
```

### 方式二：安装为可编辑包后运行

```bash
pip install -e .
python -m minesweeper
```

## 测试方法

```bash
python -m unittest discover -s tests
```

## 核心算法说明

### 1. 随机布雷

首次点击时才进行布雷，先排除首次点击位置及其相邻位置，再从剩余格子中随机抽取 `mine_count` 个位置作为地雷。

时间复杂度：`O(R*C)`，其中 `R` 为行数，`C` 为列数。

### 2. 周围雷数统计

对每一个非雷格子，遍历其周围最多 8 个邻居，统计地雷数量。

时间复杂度：`O(8*R*C)`，可简化为 `O(R*C)`。
空间复杂度：`O(R*C)`。

### 3. 空白区域展开

当玩家翻开雷数为 0 的空白格时，使用 BFS 广度优先搜索展开相邻空白格，并显示边界数字格。

时间复杂度：最坏 `O(R*C)`。
空间复杂度：最坏 `O(R*C)`。

### 4. 胜负判定

- 翻到地雷：失败。
- 所有非雷格子都被翻开：胜利。

胜利判定通过 `revealed` 集合大小与安全格数量比较完成。

## GitHub 提交流程

```bash
git init
git add .
git commit -m "完成扫雷游戏项目"
git branch -M main
git remote add origin <你的 GitHub 仓库地址>
git push -u origin main
```

## 答辩要点

1. 本项目选择扫雷游戏作为程序设计与算法综合实践项目。
2. 游戏核心算法包括随机布雷、邻域统计、BFS 自动展开、集合判重和胜负判定。
3. 项目将核心逻辑与 GUI 分离，符合模块化设计思想。
4. 使用单元测试验证首次点击安全、插旗、失败判定、胜利判定等关键逻辑。
5. 后续可扩展排行榜、存档、自定义难度、主题切换等功能。
