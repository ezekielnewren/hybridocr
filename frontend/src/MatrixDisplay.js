import React from 'react';

const MatrixDisplay = ({ matrix, toggleCell }) => {
  return (
    <div style={{ display: 'inline-block' }}>
      {matrix.map((row, rowIndex) => (
        <div key={rowIndex} style={{ display: 'flex' }}>
          {row.map((cell, colIndex) => (
            <div
              key={colIndex}
              onClick={() => toggleCell(rowIndex, colIndex)}
              style={{
                width: '20px',
                height: '20px',
                backgroundColor: cell ? 'black' : 'white',
                border: '1px solid rgba(0, 0, 0, 0.1)', // Faint grid lines
              }}
            ></div>
          ))}
        </div>
      ))}
    </div>
  );
};

export default MatrixDisplay;
