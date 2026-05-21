const difficulties = {
  easy: { rows: 9, cols: 9, mines: 10, label: "简单" },
  medium: { rows: 16, cols: 16, mines: 40, label: "中等" },
  hard: { rows: 16, cols: 30, mines: 99, label: "困难" }
};

const boardElement = document.querySelector("#board");
const difficultyElement = document.querySelector("#difficulty");
const newGameButton = document.querySelector("#new-game");
const mineCountElement = document.querySelector("#mine-count");
const timerElement = document.querySelector("#timer");
const statusElement = document.querySelector("#status");
const currentDifficultyElement = document.querySelector("#current-difficulty");
const bestTimeElement = document.querySelector("#best-time");

let currentConfig = difficulties.easy;
let currentDifficultyKey = "easy";
let board = [];
let revealedCount = 0;
let flagCount = 0;
let gameOver = false;
let timer = 0;
let timerId = null;
let longPressTimerId = null;
let longPressTriggered = false;
const longPressDelay = 550;
const bestTimePrefix = "minesweeper-best-time-";

// 初始化游戏：读取难度、清空状态并重新绘制棋盘。
function initGame() {
  currentDifficultyKey = difficultyElement.value;
  currentConfig = difficulties[currentDifficultyKey];
  board = createEmptyBoard(currentConfig.rows, currentConfig.cols);
  revealedCount = 0;
  flagCount = 0;
  gameOver = false;
  timer = 0;
  clearLongPressTimer();
  stopTimer();
  updateTimer();

  generateMines();
  calculateNumbers();
  renderBoard();
  updateMineCount();
  updateDifficultyInfo();
  updateBestTime();
  updateStatus(`${currentConfig.label}难度已开始，电脑端右键插旗，手机端长按插旗。`, "playing");
}

function createEmptyBoard(rows, cols) {
  return Array.from({ length: rows }, (_, row) =>
    Array.from({ length: cols }, (_, col) => ({
      row,
      col,
      isMine: false,
      adjacentMines: 0,
      isRevealed: false,
      isFlagged: false
    }))
  );
}

// 随机生成地雷，使用 Set 避免同一位置重复布雷。
function generateMines() {
  const minePositions = new Set();

  while (minePositions.size < currentConfig.mines) {
    const row = Math.floor(Math.random() * currentConfig.rows);
    const col = Math.floor(Math.random() * currentConfig.cols);
    minePositions.add(`${row}-${col}`);
  }

  minePositions.forEach((position) => {
    const [row, col] = position.split("-").map(Number);
    board[row][col].isMine = true;
  });
}

// 计算每个非地雷格子周围 8 个方向的地雷数量。
function calculateNumbers() {
  for (let row = 0; row < currentConfig.rows; row++) {
    for (let col = 0; col < currentConfig.cols; col++) {
      const cell = board[row][col];

      if (!cell.isMine) {
        cell.adjacentMines = getNeighbors(row, col).filter((neighbor) => neighbor.isMine).length;
      }
    }
  }
}

function renderBoard() {
  boardElement.innerHTML = "";
  boardElement.style.setProperty("--cols", currentConfig.cols);

  for (let row = 0; row < currentConfig.rows; row++) {
    for (let col = 0; col < currentConfig.cols; col++) {
      const cellButton = document.createElement("button");
      cellButton.type = "button";
      cellButton.className = "cell";
      cellButton.disabled = false;
      cellButton.dataset.row = row;
      cellButton.dataset.col = col;
      cellButton.setAttribute("aria-label", `第 ${row + 1} 行第 ${col + 1} 列`);

      cellButton.addEventListener("click", (event) => handleCellClick(event, row, col));
      cellButton.addEventListener("contextmenu", (event) => {
        event.preventDefault();
        if (longPressTriggered) {
          return;
        }
        toggleFlag(row, col);
      });
      cellButton.addEventListener("pointerdown", (event) => startLongPress(event, row, col));
      cellButton.addEventListener("pointerup", clearLongPressTimer);
      cellButton.addEventListener("pointerleave", clearLongPressTimer);
      cellButton.addEventListener("pointercancel", clearLongPressTimer);

      boardElement.appendChild(cellButton);
    }
  }
}

function handleCellClick(event, row, col) {
  if (longPressTriggered) {
    event.preventDefault();
    longPressTriggered = false;
    return;
  }

  revealCell(row, col);
}

// 手机端没有右键，长按格子时执行插旗或取消插旗。
function startLongPress(event, row, col) {
  if (event.pointerType === "mouse") {
    return;
  }

  clearLongPressTimer();
  longPressTriggered = false;

  longPressTimerId = window.setTimeout(() => {
    longPressTriggered = true;
    toggleFlag(row, col);
    window.setTimeout(() => {
      longPressTriggered = false;
    }, 800);
  }, longPressDelay);
}

function clearLongPressTimer() {
  if (longPressTimerId !== null) {
    window.clearTimeout(longPressTimerId);
    longPressTimerId = null;
  }
}

function getNeighbors(row, col) {
  const neighbors = [];

  for (let rowOffset = -1; rowOffset <= 1; rowOffset++) {
    for (let colOffset = -1; colOffset <= 1; colOffset++) {
      if (rowOffset === 0 && colOffset === 0) {
        continue;
      }

      const nextRow = row + rowOffset;
      const nextCol = col + colOffset;

      if (isInsideBoard(nextRow, nextCol)) {
        neighbors.push(board[nextRow][nextCol]);
      }
    }
  }

  return neighbors;
}

function isInsideBoard(row, col) {
  return row >= 0 && row < currentConfig.rows && col >= 0 && col < currentConfig.cols;
}

// 翻开格子：点到空白格时递归展开周围区域。
function revealCell(row, col) {
  if (gameOver) {
    return;
  }

  const cell = board[row][col];
  if (cell.isRevealed || cell.isFlagged) {
    return;
  }

  startTimer();

  cell.isRevealed = true;
  revealedCount++;
  updateCellView(cell);

  if (cell.isMine) {
    endGame(false);
    return;
  }

  if (cell.adjacentMines === 0) {
    getNeighbors(row, col).forEach((neighbor) => revealCell(neighbor.row, neighbor.col));
  }

  checkGameEnd();
}

// 插旗或取消插旗，用于标记玩家认为有地雷的位置。
function toggleFlag(row, col) {
  if (gameOver) {
    return;
  }

  const cell = board[row][col];
  if (cell.isRevealed) {
    return;
  }

  cell.isFlagged = !cell.isFlagged;
  flagCount += cell.isFlagged ? 1 : -1;
  updateCellView(cell);
  updateMineCount();
  updateStatus(cell.isFlagged ? "已插旗。" : "已取消插旗。");
}

function updateCellView(cell) {
  const cellElement = getCellElement(cell.row, cell.col);
  cellElement.className = "cell";
  cellElement.textContent = "";

  if (cell.isFlagged && !cell.isRevealed) {
    cellElement.classList.add("flagged");
    cellElement.textContent = "旗";
    return;
  }

  if (!cell.isRevealed) {
    return;
  }

  cellElement.classList.add("revealed");

  if (cell.isMine) {
    cellElement.classList.add("mine");
    cellElement.textContent = "雷";
    return;
  }

  if (cell.adjacentMines > 0) {
    cellElement.classList.add(`number-${cell.adjacentMines}`);
    cellElement.textContent = cell.adjacentMines;
  }
}

function getCellElement(row, col) {
  return boardElement.querySelector(`[data-row="${row}"][data-col="${col}"]`);
}

// 判断胜负：所有非地雷格子翻开后即获胜。
function checkGameEnd() {
  if (gameOver) {
    return;
  }

  const safeCellCount = currentConfig.rows * currentConfig.cols - currentConfig.mines;

  if (revealedCount === safeCellCount) {
    endGame(true);
  }
}

function endGame(isWin) {
  gameOver = true;
  clearLongPressTimer();
  stopTimer();
  disableBoard();

  if (!isWin) {
    revealAllMines();
    updateStatus("游戏失败：踩到地雷了。请点击“新游戏”重新挑战。", "lose");
    return;
  }

  const isNewRecord = saveBestTime(timer);
  updateBestTime();
  updateStatus(`游戏胜利！用时 ${timer} 秒。${isNewRecord ? "刷新当前难度最佳成绩！" : ""}`, "win");
}

function revealAllMines() {
  board.flat().forEach((cell) => {
    if (cell.isMine) {
      cell.isRevealed = true;
      updateCellView(cell);
    }
  });
}

// 游戏结束后禁用所有棋盘按钮，确保玩家不能继续点击或插旗。
function disableBoard() {
  boardElement.querySelectorAll(".cell").forEach((cellElement) => {
    cellElement.disabled = true;
  });
}

function startTimer() {
  if (timerId !== null) {
    return;
  }

  timerId = window.setInterval(() => {
    timer++;
    updateTimer();
  }, 1000);
}

function stopTimer() {
  if (timerId !== null) {
    window.clearInterval(timerId);
    timerId = null;
  }
}

function updateTimer() {
  timerElement.textContent = timer;
}

function updateMineCount() {
  mineCountElement.textContent = currentConfig.mines - flagCount;
}

function updateDifficultyInfo() {
  currentDifficultyElement.textContent = currentConfig.label;
}

function getBestTime() {
  const value = window.localStorage.getItem(`${bestTimePrefix}${currentDifficultyKey}`);
  return value === null ? null : Number(value);
}

// localStorage 用于在浏览器本地保存每个难度的最短通关时间。
function saveBestTime(time) {
  const bestTime = getBestTime();

  if (bestTime === null || time < bestTime) {
    window.localStorage.setItem(`${bestTimePrefix}${currentDifficultyKey}`, String(time));
    return true;
  }

  return false;
}

function updateBestTime() {
  const bestTime = getBestTime();
  bestTimeElement.textContent = bestTime === null ? "暂无" : `${bestTime} 秒`;
}

function updateStatus(message, type = "playing") {
  statusElement.textContent = message;
  statusElement.dataset.status = type;
}

newGameButton.addEventListener("click", initGame);
difficultyElement.addEventListener("change", initGame);

initGame();
