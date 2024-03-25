import React, {useState, useRef, useCallback, useEffect} from 'react';
import * as Core from './core';
import MatrixDisplay from './MatrixDisplay';


function App() {
  const [size, setSize] = useState(10); // Default rows
  const [cursor, setCursor] = useState({row: 0, col: 0});
  const [matrix, setMatrix] = useState(() => Core.newMatrix(size, size));
  const inputRef = useRef(null);

  const onDraw = () => {
      // your code here.
  }

  const toggleCursor = useCallback(() => {
      let old = matrix[cursor.row][cursor.col];
      matrix[cursor.row][cursor.col] = old^1;
  }, [cursor, setCursor]);

  const moveCursor = useCallback((rowChange, colChange) => {
      setCursor((prev) => ({
          row: Core.clamp(prev.row+rowChange, 0, matrix.length-1),
          col: Core.clamp(prev.col + colChange, 0, matrix[0].length-1)
      }));
  }, [matrix]);

  useEffect(() => {
      const handleKeyDown = (event) => {
          switch (event.key) {
            case 'ArrowUp': moveCursor(-1, 0); break;
            case 'ArrowDown': moveCursor(1, 0); break;
            case 'ArrowLeft': moveCursor(0, -1); break;
            case 'ArrowRight': moveCursor(0, 1); break;
            case ' ':
                moveCursor(0, 0);
                toggleCursor();
                break;
          }
      };
      document.addEventListener("keydown", handleKeyDown);

      return () => {
          document.removeEventListener("keydown", handleKeyDown);
      };

  }, [toggleCursor, moveCursor]);

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
        <button onClick={() => {setMatrix(Core.newMatrix(size, size))}}>New Matrix</button>
      </div>
      <div>
        <input
          type="text"
          ref={inputRef}
          placeholder="Letter to generate"
        />
      <button onClick={onDraw}>Generate</button>
      </div>
      <MatrixDisplay matrix={matrix} cursor={cursor}/>
    </div>
  );
}

export default App;
