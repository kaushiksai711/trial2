import React, { useState, useEffect, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { apiService } from '../services/api';

const KnowledgeGraph = () => {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [searchTerm, setSearchTerm] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);

  const searchGraph = useCallback(async () => {
    if (!searchTerm.trim()) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await apiService.searchKnowledgeGraph(searchTerm, 'disaster');
      if (response.success) {
        setGraphData({
          nodes: response.nodes,
          links: response.links
        });
      } else {
        setError(response.error || 'Failed to fetch graph data');
      }
    } catch (err) {
      setError('Failed to connect to the server');
      console.error('Error fetching graph data:', err);
    } finally {
      setIsLoading(false);
    }
  }, [searchTerm]);

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      searchGraph();
    }
  };

  return (
    <div className="knowledge-graph-container">
      <div className="search-container">
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Search knowledge graph..."
          className="search-input"
          disabled={isLoading}
        />
        <button 
          onClick={searchGraph} 
          disabled={isLoading || !searchTerm.trim()}
          className="search-button"
        >
          {isLoading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="graph-container">
        {graphData.nodes.length > 0 ? (
          <ForceGraph2D
            graphData={graphData}
            nodeLabel="label"
            nodeAutoColorBy="type"
            linkDirectionalParticles={2}
            linkDirectionalParticleWidth={2}
            onNodeClick={(node) => setSelectedNode(node)}
            nodeCanvasObject={(node, ctx, globalScale) => {
              const label = node.label || node.id;
              const fontSize = 12 / globalScale;
              ctx.font = `${fontSize}px Sans-Serif`;
              const textWidth = ctx.measureText(label).width;
              const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2);

              ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
              ctx.fillRect(
                node.x - bckgDimensions[0] / 2,
                node.y - bckgDimensions[1] / 2,
                ...bckgDimensions
              );

              ctx.textAlign = 'center';
              ctx.textBaseline = 'middle';
              ctx.fillStyle = node.color || 'black';
              ctx.fillText(label, node.x, node.y);
            }}
          />
        ) : (
          <div className="empty-state">
            {isLoading ? 'Loading...' : 'Enter a search term to visualize the knowledge graph'}
          </div>
        )}
      </div>

      {selectedNode && (
        <div className="node-details">
          <h3>{selectedNode.label || 'Node Details'}</h3>
          <div className="properties">
            <p><strong>Type:</strong> {selectedNode.type || 'N/A'}</p>
            {selectedNode.properties && Object.entries(selectedNode.properties).map(([key, value]) => (
              <p key={key}><strong>{key}:</strong> {String(value)}</p>
            ))}
          </div>
          <button onClick={() => setSelectedNode(null)} className="close-button">
            Close
          </button>
        </div>
      )}
    </div>
  );
};

export default KnowledgeGraph;
