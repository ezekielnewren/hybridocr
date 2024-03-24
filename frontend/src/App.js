import React, { useState } from 'react';
import { generateMatrix } from './matrixGenerator';
import MatrixDisplay from './MatrixDisplay';

function App() {
  const [rows, setRows] = useState(5);
  const [cols, setCols] = useState(5);
  const [matrix, setMatrix] = useState(() => generateMatrix(5, 5));

  const setCellState = (rowIndex, colIndex, newState) => {
    const newMatrix = matrix.map((row, rIndex) => (
      rIndex === rowIndex ? row.map((cell, cIndex) => (
        cIndex === colIndex ? newState : cell
      )) : row
    ));
    setMatrix(newMatrix);
  };

  return (
    <div className="App">
      <h1>Interactive Boolean Matrix</h1>
      <MatrixDisplay matrix={matrix} setCellState={setCellState} />
    </div>
  );
}

export default App;
