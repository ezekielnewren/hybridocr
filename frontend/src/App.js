import React, {useState, useRef, useCallback, useEffect} from 'react';
import * as Core from './core';
import MatrixDisplay from './MatrixDisplay';


function App() {
  const [size, setSize] = useState(10); // Default rows
  const [matrix, setMatrix] = useState(() => Core.newMatrix(size, size));
  const inputRef = useRef(null);

  const onDraw = () => {
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
      <MatrixDisplay matrix={matrix}/>
    </div>
  );
}

export default App;
