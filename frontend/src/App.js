import React from 'react';
import MatrixDisplay from './MatrixDisplay'; // Adjust the path based on your file structure

function App() {
  return (
    <div className="App">
      <h1>Boolean Matrix</h1>
      <MatrixDisplay rows={10} cols={10} />
    </div>
  );
}

export default App;
