import React, { useState } from 'react';
import { generateMatrix } from './matrixGenerator';
import MatrixDisplay from './MatrixDisplay';

function App() {
  const rows = 10;
  const cols = 10;
  const [matrix, setMatrix] = useState(generateMatrix(rows, cols));

  // Toggle the state of a cell
  const toggleCellState = (rowIndex, colIndex) => {
    const newMatrix = matrix.map((row, rIndex) => {
      if (rIndex === rowIndex) {
        return row.map((cell, cIndex) => {
          if (cIndex === colIndex) {
            return !cell; // Toggle the cell state
          }
          return cell;
        });
      }
      return row;
    });
    setMatrix(newMatrix);
  };

  return (
    <div className="App">
      <h1>Interactive Boolean Matrix</h1>
      <MatrixDisplay matrix={matrix} onToggle={toggleCellState} />
    </div>
  );
}

export default App;