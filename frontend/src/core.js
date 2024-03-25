
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

