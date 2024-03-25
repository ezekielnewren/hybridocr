import React, {useState, useRef, useCallback, useEffect} from 'react';
import * as Core from './core';
import MatrixDisplay from './MatrixDisplay';


function App() {
  const [modCount, setModCount] = useState(0);
  const [size, setSize] = useState(28); // same size as MNIST
  const inputRef = useRef(null);
  const [canvas, setCanvas] = useState(new Core.Canvas(size, size));

  const drawNow = () => setModCount(v => v + 1);
  const onDraw = () => {
      draw();
  }

  useEffect(() => {
      const handleKeyDown = (event) => {
          console.log("keyDown");
          switch (event.key) {
            case 'ArrowUp': canvas.moveCursor(-1, 0); break;
            case 'ArrowDown': canvas.moveCursor(1, 0); break;
            case 'ArrowLeft': canvas.moveCursor(0, -1); break;
            case 'ArrowRight': canvas.moveCursor(0, 1); break;
            case ' ': canvas.toggleCursor(); break;
          }
          drawNow();
      };
      document.addEventListener("keydown", handleKeyDown);

      return () => {
          document.removeEventListener("keydown", handleKeyDown);
      };

  }, [canvas]);

  function newMatrix() {
      canvas.matrix = Core.newMatrix(size, size)
      drawNow();
  }

  function delay(ms) {
      return new Promise(resolve => setTimeout(resolve, ms));
  }

  async function draw() {
      let sleep = 50;
      let threshold = .1;

      let t = 0;

      for (let i = 0; i < 100; i++) {
          t = Math.random()*2-1;
          let rowChange = Math.abs(t) > threshold ? Math.sign(t) : 0;
          t = Math.random()*2-1;
          let colChange = Math.abs(t) > threshold ? Math.sign(t) : 0;
          canvas.moveCursor(rowChange, colChange);
          drawNow();
          await delay(sleep/2);

          canvas.set(Math.random() > .25 ? 1 : 0);
          drawNow();
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
        <button onClick={() => {newMatrix()}}>New Matrix</button>
      </div>
      <div>
        <input
          type="text"
          ref={inputRef}
          placeholder="Letter to generate"
        />
      <button onClick={onDraw}>Draw</button>
      </div>
      <MatrixDisplay canvas={canvas} modCount={modCount}/>
    </div>
  );
}

export default App;
