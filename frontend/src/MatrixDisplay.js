// MatrixDisplay.js
import React from 'react';

const MatrixDisplay = ({ matrix, onToggle }) => {
  return (
    <div style={{ display: 'inline-block' }}>
      {matrix.map((row, rowIndex) => (
        <div key={rowIndex} style={{ display: 'flex' }}>
          {row.map((cell, colIndex) => (
            <div
              key={colIndex}
              onClick={() => onToggle(rowIndex, colIndex)}
              style={{
                width: '20px',
                height: '20px',
                backgroundColor: cell ? 'black' : 'white',
                cursor: 'pointer',
              }}
            ></div>
          ))}
        </div>
      ))}
    </div>
  );
};

export default MatrixDisplay;