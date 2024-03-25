import React, {useCallback, useEffect, useState} from 'react';
import * as Core from './core';

const MatrixDisplay = ({matrix}) => {

  const [cursor, setCursor] = useState({row: 0, col: 0});

  const handleContextMenu = (e) => {
    e.preventDefault();
  };

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
    <div style={{ display: 'inline-block' }} onContextMenu={handleContextMenu}>
      {matrix.map((row, rowIndex) => (
        <div key={rowIndex} style={{ display: 'flex' }}>
          {row.map((cell, colIndex) => (
            <div
              key={colIndex}
              style={{
                width: '20px',
                height: '20px',
                backgroundColor: (rowIndex === cursor.row && colIndex === cursor.col)
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
