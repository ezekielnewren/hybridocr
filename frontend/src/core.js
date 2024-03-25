import {useCallback} from "react";

export const newMatrix = (rows, cols) => {
  let matrix = [];
  for (let i = 0; i < rows; i++) {
    let row = [];
    for (let j = 0; j < cols; j++) {
      // Randomly assigns true or false
      row.push(0);
    }
    matrix.push(row);
  }
  return matrix;
};

export function clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
}

export class Canvas {
  constructor(rows, cols) {
    this.matrix = [];
    for (let row= 0; row<rows; row++) {
      let t = [];
      for (let col = 0; col<cols; col++) {
        t.push(0);
      }
      this.matrix.push(t);
    }
    this.cursor = {row: 0, col: 0};
  }

  toggleCursor() {
    let old = this.get();
    this.set(old^1);
  }

  moveCursor(rowChange, colChange) {
    this.cursor.row = clamp(this.cursor.row+rowChange, 0, this.matrix.length-1);
    this.cursor.col = clamp(this.cursor.col+colChange, 0, this.matrix[0].length-1);
  }

  set(value) {
    this.matrix[this.cursor.row][this.cursor.col] = value;
  }

  get() {
    return this.matrix[this.cursor.row][this.cursor.col];
  }
}
