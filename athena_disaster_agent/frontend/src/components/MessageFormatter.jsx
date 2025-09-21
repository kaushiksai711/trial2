import React from 'react';

const MessageFormatter = ({ text }) => {
  if (!text) return null;

  // Function to process the text and convert formatting
  const formatText = (rawText) => {
    // Step 1: Handle line breaks - convert \n to actual breaks
    let processedText = rawText.replace(/\\n/g, '\n');
    
    // Step 2: Split by actual line breaks to create paragraphs
    const lines = processedText.split('\n');
    
    // Step 3: Process each line for markdown formatting
    return lines.map((line, lineIndex) => {
      if (line.trim() === '') {
        // Empty line - create spacing
        return <br key={`br-${lineIndex}`} />;
      }
      
      // Process bold markdown **text**
      const boldFormatted = processMarkdown(line);
      
      return (
        <span key={`line-${lineIndex}`} style={{ display: 'block', marginBottom: '0.25rem' }}>
          {boldFormatted}
        </span>
      );
    });
  };

  // Function to process markdown formatting
  const processMarkdown = (text) => {
    const parts = [];
    let currentIndex = 0;
    
    // Regular expression to find **bold** text
    const boldRegex = /\*\*(.*?)\*\*/g;
    let match;
    
    while ((match = boldRegex.exec(text)) !== null) {
      // Add text before the bold part
      if (match.index > currentIndex) {
        parts.push(text.substring(currentIndex, match.index));
      }
      
      // Add the bold part
      parts.push(
        <strong key={`bold-${match.index}`} style={{ fontWeight: '700', color: 'inherit' }}>
          {match[1]}
        </strong>
      );
      
      currentIndex = match.index + match[0].length;
    }
    
    // Add remaining text after the last bold part
    if (currentIndex < text.length) {
      parts.push(text.substring(currentIndex));
    }
    
    return parts;
  };

  return (
    <div className="formatted-message">
      {formatText(text)}
    </div>
  );
};

export default MessageFormatter;
