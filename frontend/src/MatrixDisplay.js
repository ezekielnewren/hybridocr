import React, {useCallback, useEffect, useState} from 'react';

const MatrixDisplay = ({canvas, modCount}) => {
  const handleContextMenu = (e) => {
    e.preventDefault();
  };

  return (
    <div style={{ display: 'inline-block' }} onContextMenu={handleContextMenu}>
      {canvas.matrix.map((row, rowIndex) => (
        <div key={rowIndex} style={{ display: 'flex' }}>
          {row.map((cell, colIndex) => (
            <div
              key={colIndex}
              style={{
                width: '20px',
                height: '20px',
                backgroundColor: (rowIndex === canvas.cursor.row && colIndex === canvas.cursor.col)
                  ? (cell>0 ? '#444444' : '#dddddd')
                  : (cell>0 ? 'black' : 'white'),
                border: '1px solid rgba(0, 0, 0, 0.1)',
              }}
            ></div>
          ))}
        </div>
      ))}
    </div>
  );
};

export default MatrixDisplay;
