import React, { useState } from 'react';
import './UploadArea.css';

const UploadArea = ({ onFileSelect, selectedFile }) => {
  const [isDragging, setIsDragging] = useState(false);

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (file.type.startsWith('image/')) {
        onFileSelect(file);
      } else {
        alert('Please upload an image file');
      }
    }
  };

  const handleFileInput = (e) => {
    const file = e.target.files[0];
    if (file) {
      onFileSelect(file);
    }
  };

  const handleClick = () => {
    document.getElementById('file-input').click();
  };

  return (
    <div
      className={`upload-area ${isDragging ? 'dragover' : ''}`}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      onClick={handleClick}
    >
      <div className="upload-icon">📸</div>
      <p><strong>Drag & Drop</strong> your question image here</p>
      <p>or <strong>click to browse</strong></p>
      <p style={{ fontSize: '0.9em', marginTop: '10px', opacity: 0.7 }}>
        Supports: JPG, PNG (Math, Physics, Chemistry questions)
      </p>
      <input
        id="file-input"
        type="file"
        accept="image/*"
        onChange={handleFileInput}
        className="file-input"
      />
    </div>
  );
};

export default UploadArea;
