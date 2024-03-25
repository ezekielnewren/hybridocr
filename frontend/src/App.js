import React, {useState, useRef, useCallback, useEffect} from 'react';
import { newMatrix } from './matrixGenerator';
import MatrixDisplay from './MatrixDisplay';

function App() {
  const [size, setSize] = useState(10); // Default rows
  const [matrix, setMatrix] = useState(() => newMatrix(size, size));
  const [currentCell, setCurrentCell] = useState({ row: 0, col: 0});
  const inputRef = useRef(null);
  // const [textInput, setTextInput] = useState("");

  const initializeMatrix = () => {
    // Initialize matrix with the specified size
    setMatrix(newMatrix(size, size));
  };

  const setCellState = (rowIndex, colIndex, newState) => {
    const newMatrix = matrix.map((row, rIndex) =>
      rIndex === rowIndex ? row.map((cell, cIndex) => (cIndex === colIndex ? newState : cell)) : row
    );
    setMatrix(newMatrix);
  };

  const toggleCurrentCellState = useCallback(() => {
      let old = matrix[currentCell.row][currentCell.col];
      matrix[currentCell.row][currentCell.col] = !old;
  }, [currentCell, setMatrix]);


  const moveCurrentCell = useCallback((rowChange, colChange) => {
      setCurrentCell((prev) => ({
          row: Math.max(0, Math.min(prev.row+rowChange, matrix.length-1)),
          col: Math.max(0, Math.min(prev.col + colChange, matrix[0].length-1))
      }));
  }, [matrix]);

  useEffect(() => {
      const handleKeyDown = (event) => {
          switch (event.key) {
            case 'ArrowUp': moveCurrentCell(-1, 0); break;
            case 'ArrowDown': moveCurrentCell(1, 0); break;
            case 'ArrowLeft': moveCurrentCell(0, -1); break;
            case 'ArrowRight': moveCurrentCell(0, 1); break;
            case ' ':
                moveCurrentCell(0, 0);
                toggleCurrentCellState();
                break;
          }
      };
      document.addEventListener("keydown", handleKeyDown);

      return () => {
          document.removeEventListener("keydown", handleKeyDown);
      };

  }, [toggleCurrentCellState, moveCurrentCell]);

  const handleGenerateClick = () => {
      // your code here.
  }

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
      <div>
        <input
          type="text"
          ref={inputRef}
          placeholder="Letter to generate"
        />
      <button onClick={handleGenerateClick}>Generate</button>
      </div>
      <MatrixDisplay matrix={matrix} currentCell={currentCell} setCellState={setCellState} />
    </div>
  );
}

export default App;
