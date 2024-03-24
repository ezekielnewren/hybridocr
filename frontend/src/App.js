import React, { useState } from 'react';
import { generateMatrix } from './matrixGenerator';
import MatrixDisplay from './MatrixDisplay';

function App() {
  const [rows, setRows] = useState(5); // Start with a default value
  const [cols, setCols] = useState(5); // Start with a default value
  const [matrix, setMatrix] = useState(() => generateMatrix(5, 5)); // Start with a default-sized matrix

  const toggleCell = (rowIndex, colIndex) => {
    // Create a deep copy of the matrix and toggle the value
    const newMatrix = matrix.map((row, rIndex) => (
      rIndex === rowIndex ? row.map((cell, cIndex) => (
        cIndex === colIndex ? !cell : cell
      )) : row
    ));
    setMatrix(newMatrix); // Update the state with the new matrix
  };

  const initializeMatrix = () => {
    // Ensure matrix is reinitialized with false values
    setMatrix(generateMatrix(rows, cols));
  };

  return (
    <div className="App">
      <h1>Interactive Boolean Matrix</h1>
      <input
        type="number"
        placeholder="Rows"
        min="1"
        value={rows}
        onChange={(e) => setRows(parseInt(e.target.value) || 1)}
      />
      <input
        type="number"
        placeholder="Columns"
        min="1"
        value={cols}
        onChange={(e) => setCols(parseInt(e.target.value) || 1)}
      />
      <button onClick={initializeMatrix}>Initialize Matrix</button>
      <MatrixDisplay matrix={matrix} toggleCell={toggleCell} />
    </div>
  );
}

export default App;
