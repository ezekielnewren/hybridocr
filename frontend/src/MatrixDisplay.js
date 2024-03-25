import React from 'react';

const MatrixDisplay = ({ matrix, currentCell, setCellState }) => {
  // Track the mouse state
  const [isDragging, setIsDragging] = React.useState(false);
  const [dragStartValue, setDragStartValue] = React.useState(null);

  const handleMouseDown = (e, rowIndex, colIndex) => {
    const newValue = e.button === 0; // Left click sets to true (black), right click sets to false (white)
    setCellState(rowIndex, colIndex, newValue);
    setIsDragging(true);
    setDragStartValue(newValue);
    e.preventDefault(); // Prevents text selection during drag
  };

  const handleMouseEnter = (rowIndex, colIndex) => {
    if (isDragging) {
      setCellState(rowIndex, colIndex, dragStartValue);
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleContextMenu = (e) => {
    e.preventDefault();
  };

  React.useEffect(() => {
    // Listen for global mouse up events to stop dragging
    window.addEventListener('mouseup', handleMouseUp);
    return () => window.removeEventListener('mouseup', handleMouseUp);
  }, []);

  return (
    <div style={{ display: 'inline-block' }} onMouseUp={handleMouseUp} onContextMenu={handleContextMenu}>
      {matrix.map((row, rowIndex) => (
        <div key={rowIndex} style={{ display: 'flex' }}>
          {row.map((cell, colIndex) => (
            <div
              key={colIndex}
              // onMouseDown={(e) => handleMouseDown(e, rowIndex, colIndex)}
              // onMouseEnter={() => handleMouseEnter(rowIndex, colIndex)}
              style={{
                width: '20px',
                height: '20px',
                backgroundColor: rowIndex === currentCell.row && colIndex === currentCell.col
                  ? cell ? 'darkgrey' : 'lightgrey' // Current cell color based on state
                  : cell ? 'black' : 'white', // Other cells color
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
