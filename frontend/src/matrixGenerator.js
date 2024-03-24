export const generateMatrix = (rows, cols) => {
  let matrix = [];
  for (let i = 0; i < rows; i++) {
    let row = [];
    for (let j = 0; j < cols; j++) {
      // Randomly assigns true or false
      row.push(false);
    }
    matrix.push(row);
  }
  return matrix;
};