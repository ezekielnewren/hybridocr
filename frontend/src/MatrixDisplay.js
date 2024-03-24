import React from 'react';

const MatrixDisplay = ({ rows, cols }) => {
  // Generate a boolean matrix
  const generateMatrix = (rows, cols) => {
    let matrix = [];
    for (let i = 0; i < rows; i++) {
      let row = [];
      for (let j = 0; j < cols; j++) {
        // This example randomly assigns true or false, but you can customize this logic
        row.push(Math.random() > 0.5);
      }
      matrix.push(row);
    }
    return matrix;
  };

  const matrix = generateMatrix(rows, cols);

  return (
    <div style={{ display: 'inline-block' }}>
      {matrix.map((row, i) => (
        <div key={i} style={{ display: 'flex' }}>
          {row.map((cell, j) => (
            <div
              key={j}
              style={{
                width: '20px',
                height: '20px',
                backgroundColor: cell ? 'black' : 'white',
              }}
            ></div>
          ))}
        </div>
      ))}
    </div>
  );
};

export default MatrixDisplay;
