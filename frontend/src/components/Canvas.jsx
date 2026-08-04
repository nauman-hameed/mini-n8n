import { useCallback, useEffect, useMemo, useState } from "react";

import {
  ReactFlow,
  addEdge,
  applyEdgeChanges,
  Background,
  Controls,
  ConnectionMode,
  Position,
  BackgroundVariant,
} from "@xyflow/react";

import "@xyflow/react/dist/style.css";

import N8nNode from "../nodes/N8nNode";

const nodeTypes = { n8nNode: N8nNode };

function Canvas({
  nodes,
  setNodes,
  onNodesChange,
  edgesInApp,
  setEdgesInApp,
}) {
  const [selectedNodeId, setSelectedNodeId] = useState(null);

  const selectedNode = nodes.find(
    (node) => node.id === selectedNodeId
  );

  useEffect(() => {
    if (
      selectedNodeId &&
      !nodes.some((node) => node.id === selectedNodeId)
    ) {
      setSelectedNodeId(null);
    }
  }, [nodes, selectedNodeId]);

  const onConnect = useCallback(
    (connection) => {
      setEdgesInApp((currentEdges) =>
        addEdge(
          {
            ...connection,
            animated: true,
            style: { stroke: "#ff6d5a", strokeWidth: 2 },
          },
          currentEdges
        )
      );
    },
    [setEdgesInApp]
  );

  const handleEdgesChange = useCallback(
    (changes) => {
      setEdgesInApp((currentEdges) =>
        applyEdgeChanges(changes, currentEdges)
      );
    },
    [setEdgesInApp]
  );

  const openNodeEditor = (_event, node) => {
    if (
      node.data.nodeType === "start" ||
      node.data.nodeType === "stop"
    ) {
      return;
    }

    setSelectedNodeId(node.id);
  };

  const updateSelectedNode = (newData) => {
    setNodes((currentNodes) =>
      currentNodes.map((node) =>
        node.id === selectedNodeId
          ? {
              ...node,
              data: {
                ...node.data,
                ...newData,
              },
            }
          : node
      )
    );
  };

  const preparedNodes = useMemo(
    () =>
      nodes.map((node) => ({
        ...node,
        type: "n8nNode",
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
      })),
    [nodes]
  );

  return (
    <div className="canvas-area">
      <ReactFlow
        nodes={preparedNodes}
        edges={edgesInApp}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={handleEdgesChange}
        onConnect={onConnect}
        onNodeDoubleClick={openNodeEditor}
        connectionMode={ConnectionMode.Loose}
        proOptions={{ hideAttribution: true }}
        fitView
      >
        <Background
          variant={BackgroundVariant.Dots}
          color="#3a3a42"
          gap={20}
          size={1}
        />
        <Controls position="bottom-left" />
      </ReactFlow>

      {nodes.length === 0 && (
        <div className="canvas-empty">
          <div className="canvas-empty-icon">+</div>
          <p className="canvas-empty-title">Canvas is empty</p>
          <p className="canvas-empty-desc">
            Add nodes from the left panel and connect them to build your
            workflow. Double-click a node to configure it.
          </p>
        </div>
      )}

      {selectedNode && (
        <div className="panel node-editor-panel">
          <div className="panel-header">
            <h3 className="panel-title">
              {selectedNode.data.label} Settings
            </h3>
            <button
              className="btn btn-icon btn-ghost"
              onClick={() => setSelectedNodeId(null)}
              aria-label="Close settings"
            >
              ✕
            </button>
          </div>

          <div className="panel-body">
            {selectedNode.data.nodeType === "api" && (
              <>
                <label className="form-label">Method</label>
                <select
                  className="form-select"
                  value={selectedNode.data.method || "GET"}
                  onChange={(event) =>
                    updateSelectedNode({
                      method: event.target.value,
                      label: `HTTP (${event.target.value})`,
                    })
                  }
                >
                  <option value="GET">GET</option>
                  <option value="POST">POST</option>
                </select>

                <label className="form-label" style={{ marginTop: 12 }}>
                  API URL
                </label>
                <input
                  className="form-input"
                  type="text"
                  placeholder="https://api.example.com"
                  value={selectedNode.data.apiUrl || ""}
                  onChange={(event) =>
                    updateSelectedNode({ apiUrl: event.target.value })
                  }
                />
              </>
            )}

            {selectedNode.data.nodeType === "llm" && (
              <>
                <label className="form-label">Prompt</label>
                <textarea
                  className="form-textarea"
                  placeholder="Enter LLM prompt…"
                  value={selectedNode.data.prompt || ""}
                  onChange={(event) =>
                    updateSelectedNode({
                      prompt: event.target.value,
                      label: "LLM Configured",
                    })
                  }
                />
              </>
            )}

            {selectedNode.data.nodeType === "condition" && (
              <>
                <label className="form-label">Condition</label>
                <input
                  className="form-input"
                  type="text"
                  placeholder="status == 200"
                  value={selectedNode.data.condition || ""}
                  onChange={(event) =>
                    updateSelectedNode({
                      condition: event.target.value,
                      label: "If / Else Configured",
                    })
                  }
                />
              </>
            )}

            {selectedNode.data.nodeType === "whatsappTrigger" && (
              <>
                <label className="form-label">Sample WhatsApp Message</label>
                <textarea
                  className="form-textarea"
                  placeholder="Ayesha Khan, 0300-1234567, House 4B, Street 3, DHA Phase 5, Karachi. Please send 2 Blue Kurtas."
                  value={selectedNode.data.message || ""}
                  onChange={(event) =>
                    updateSelectedNode({ message: event.target.value })
                  }
                />

                <label className="form-label" style={{ marginTop: 12 }}>
                  Test Phone (optional)
                </label>
                <input
                  className="form-input"
                  type="text"
                  placeholder="923001234567"
                  value={selectedNode.data.testPhone || ""}
                  onChange={(event) =>
                    updateSelectedNode({ testPhone: event.target.value })
                  }
                />
                <p className="field-hint">
                  Used for manual runs to send a real WhatsApp confirmation.
                  Live messages use the sender&apos;s number from Meta webhook.
                </p>
              </>
            )}

            {selectedNode.data.nodeType === "aiExtractor" && (
              <>
                <label className="form-label">Extraction Prompt</label>
                <textarea
                  className="form-textarea"
                  placeholder="Extract name, phone, address, and items. Return only JSON."
                  value={selectedNode.data.prompt || ""}
                  onChange={(event) =>
                    updateSelectedNode({ prompt: event.target.value })
                  }
                />
              </>
            )}

            {selectedNode.data.nodeType === "googleSheets" && (
              <>
                <label className="form-label">Sheet Name</label>
                <input
                  className="form-input"
                  type="text"
                  placeholder="Orders"
                  value={selectedNode.data.sheetName || ""}
                  onChange={(event) =>
                    updateSelectedNode({ sheetName: event.target.value })
                  }
                />

                <label className="form-label" style={{ marginTop: 12 }}>
                  Columns
                </label>
                <input
                  className="form-input"
                  type="text"
                  placeholder="Name, Phone, Address, Items"
                  value={selectedNode.data.columns || ""}
                  onChange={(event) =>
                    updateSelectedNode({ columns: event.target.value })
                  }
                />
              </>
            )}

            {selectedNode.data.nodeType === "whatsappReply" && (
              <>
                <label className="form-label">Reply Message</label>
                <textarea
                  className="form-textarea"
                  placeholder="Thank you {{name}}! Your order for {{items}} has been received. We'll reach you at {{phone}}."
                  value={selectedNode.data.replyMessage || ""}
                  onChange={(event) =>
                    updateSelectedNode({ replyMessage: event.target.value })
                  }
                />
              </>
            )}

            <button
              className="btn btn-primary"
              style={{ width: "100%", marginTop: 16 }}
              onClick={() => setSelectedNodeId(null)}
            >
              Done
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default Canvas;
