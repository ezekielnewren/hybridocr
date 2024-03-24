import React, { useState } from 'react';
import { generateMatrix } from './matrixGenerator';
import MatrixDisplay from './MatrixDisplay';

function App() {
  const [size, setSize] = useState(10); // Default rows
  const [matrix, setMatrix] = useState(() => generateMatrix(size, size));

  const initializeMatrix = () => {
    // Initialize matrix with the specified size
    setMatrix(generateMatrix(size, size));
  };

  const setCellState = (rowIndex, colIndex, newState) => {
    const newMatrix = matrix.map((row, rIndex) =>
      rIndex === rowIndex ? row.map((cell, cIndex) => (cIndex === colIndex ? newState : cell)) : row
    );
    setMatrix(newMatrix);
  };

  return (
    <div className="App">
      <h1>Interactive Boolean Matrix</h1>
      <div>
        <label>
          Size:
          <input
            type="number"
            value={size}
            onChange={(e) => setSize(parseInt(e.target.value, 10))}
            min="1"
          />
        </label>
        <button onClick={initializeMatrix}>Initialize Matrix</button>
      </div>
      <MatrixDisplay matrix={matrix} setCellState={setCellState} />
    </div>
  );
}

export default App;
