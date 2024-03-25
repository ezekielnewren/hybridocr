import React, {useState, useRef, useCallback, useEffect} from 'react';
import * as Core from './core';
import MatrixDisplay from './MatrixDisplay';


function App() {
  const [update, updateNow] = useState(0);
  const [size, setSize] = useState(11); // Default rows
  const [cursor, setCursor] = useState({row: 5, col: 5});
  const [matrix, setMatrix] = useState(() => Core.newMatrix(size, size));
  const inputRef = useRef(null);

  const triggerUpdate = () => updateNow(v => v + 1);
  const onDraw = () => {
      draw();
  }

  function setCellState(m, c, v) {
      console.assert(0 <= c.row && c.row < m.length);
      console.assert(0 <= c.col && c.col < m[0].length);
      m[c.row][c.col] = v;
      setMatrix(m);
  }

  const toggleCursor = useCallback(() => {
      let old = matrix[cursor.row][cursor.col];
      matrix[cursor.row][cursor.col] = old^1;
  }, [cursor, setCursor]);

  const moveCursor = useCallback((rowChange, colChange) => {
      setCursor((prev) => ({
          row: Core.clamp(prev.row+rowChange, 0, matrix.length-1),
          col: Core.clamp(prev.col+colChange, 0, matrix[0].length-1)
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

  function delay(ms) {
      return new Promise(resolve => setTimeout(resolve, ms));
  }

  async function draw() {
      // setMatrix(Core.newMatrix(size, size));
      // setCursor({row: 0, col: 0});
      let sleep = 50;
      let threshold = .1;

      let t = 0;
      let c = cursor;


      for (let i = 0; i < 100; i++) {
          t = Math.random()*2-1;
          let rowChange = Math.abs(t) > threshold ? Math.sign(t) : 0;
          t = Math.random()*2-1;
          let colChange = Math.abs(t) > threshold ? Math.sign(t) : 0;
          c.row = Core.clamp(c.row+rowChange, 0, matrix.length-1);
          c.col = Core.clamp(c.col+colChange, 0, matrix[0].length-1);
          setCursor(c);
          triggerUpdate();
          await delay(sleep/2);

          setCellState(matrix, c, Math.random() > .25 ? 1 : 0);
          triggerUpdate();
          await delay(sleep/2);
      }
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
        <button onClick={() => {setMatrix(Core.newMatrix(size, size))}}>New Matrix</button>
      </div>
      <div>
        <input
          type="text"
          ref={inputRef}
          placeholder="Letter to generate"
        />
      <button onClick={onDraw}>Draw</button>
      </div>
      <MatrixDisplay matrix={matrix} cursor={cursor}/>
    </div>
  );
}

export default App;
