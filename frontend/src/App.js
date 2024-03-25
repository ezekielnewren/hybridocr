import React, {useState, useRef, useCallback, useEffect} from 'react';
import { newMatrix } from './matrixGenerator';
import MatrixDisplay from './MatrixDisplay';

function App() {
  const [size, setSize] = useState(10); // Default rows
  const [matrix, setMatrix] = useState(() => newMatrix(size, size));
  const [currentCell, setCurrentCell] = useState({ row: 0, col: 0});
  const inputRef = useRef(null);

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
        <button onClick={() => {setMatrix(newMatrix(size, size))}}>New Matrix</button>
      </div>
      <div>
        <input
          type="text"
          ref={inputRef}
          placeholder="Letter to generate"
        />
      <button onClick={handleGenerateClick}>Generate</button>
      </div>
      <MatrixDisplay matrix={matrix}/>
    </div>
  );
}

export default App;
