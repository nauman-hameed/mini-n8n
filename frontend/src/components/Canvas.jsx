import { useCallback, useEffect, useState } from "react";

import {
  ReactFlow,
  addEdge,
  applyEdgeChanges,
  Background,
  Controls,
  ConnectionMode,
  Position,
} from "@xyflow/react";

import "@xyflow/react/dist/style.css";

function Canvas({
  nodes,
  setNodes,
  onNodesChange,
  edgesInApp,
  setEdgesInApp,
}) {
  const [selectedNodeId, setSelectedNodeId] =
    useState(null);

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

  const openNodeEditor = (event, node) => {
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

  const preparedNodes = nodes.map((node) => ({
    ...node,
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
  }));

  return (
    <div
      style={{
        flex: 1,
        height: "100%",
        position: "relative",
        backgroundColor: "#1e1e1e",
      }}
    >
      <ReactFlow
        nodes={preparedNodes}
        edges={edgesInApp}
        onNodesChange={onNodesChange}
        onEdgesChange={handleEdgesChange}
        onConnect={onConnect}
        onNodeDoubleClick={openNodeEditor}
        connectionMode={ConnectionMode.Loose}
        proOptions={{ hideAttribution: true }}
        fitView
      >
        <Background color="#444" gap={20} />
        <Controls />
      </ReactFlow>

      {selectedNode && (
        <div
          style={{
            position: "absolute",
            top: "20px",
            right: "20px",
            width: "300px",
            maxHeight: "calc(100% - 40px)",
            overflowY: "auto",
            backgroundColor: "white",
            color: "#222",
            padding: "18px",
            borderRadius: "8px",
            boxShadow: "0 4px 20px rgba(0,0,0,0.35)",
            zIndex: 10,
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "15px",
            }}
          >
            <h3 style={{ margin: 0 }}>
              {selectedNode.data.label} Settings
            </h3>

            <button
              onClick={() => setSelectedNodeId(null)}
              style={{
                cursor: "pointer",
                padding: "4px 8px",
              }}
            >
              ✕
            </button>
          </div>

          {selectedNode.data.nodeType === "api" && (
            <>
              <label
                style={{
                  display: "block",
                  marginBottom: "5px",
                }}
              >
                Method
              </label>

              <select
                value={selectedNode.data.method || "GET"}
                onChange={(event) =>
                  updateSelectedNode({
                    method: event.target.value,
                    label: `API (${event.target.value})`,
                  })
                }
                style={{
                  boxSizing: "border-box",
                  width: "100%",
                  padding: "8px",
                  marginBottom: "12px",
                }}
              >
                <option value="GET">GET</option>
                <option value="POST">POST</option>
              </select>

              <label
                style={{
                  display: "block",
                  marginBottom: "5px",
                }}
              >
                API URL
              </label>

              <input
                type="text"
                placeholder="https://api.example.com"
                value={selectedNode.data.apiUrl || ""}
                onChange={(event) =>
                  updateSelectedNode({
                    apiUrl: event.target.value,
                  })
                }
                style={{
                  boxSizing: "border-box",
                  width: "100%",
                  padding: "8px",
                }}
              />
            </>
          )}

          {selectedNode.data.nodeType === "llm" && (
            <>
              <label
                style={{
                  display: "block",
                  marginBottom: "5px",
                }}
              >
                Prompt
              </label>

              <textarea
                placeholder="Enter LLM prompt..."
                value={selectedNode.data.prompt || ""}
                onChange={(event) =>
                  updateSelectedNode({
                    prompt: event.target.value,
                    label: "LLM Configured",
                  })
                }
                style={{
                  boxSizing: "border-box",
                  width: "100%",
                  minHeight: "120px",
                  padding: "8px",
                  resize: "vertical",
                }}
              />
            </>
          )}

          {selectedNode.data.nodeType === "condition" && (
            <>
              <label
                style={{
                  display: "block",
                  marginBottom: "5px",
                }}
              >
                Condition
              </label>

              <input
                type="text"
                placeholder="status == 200"
                value={selectedNode.data.condition || ""}
                onChange={(event) =>
                  updateSelectedNode({
                    condition: event.target.value,
                    label: "If / Else Configured",
                  })
                }
                style={{
                  boxSizing: "border-box",
                  width: "100%",
                  padding: "8px",
                }}
              />
            </>
          )}

          {selectedNode.data.nodeType ===
            "whatsappTrigger" && (
            <>
              <label
                style={{
                  display: "block",
                  marginBottom: "5px",
                }}
              >
                Sample WhatsApp Message
              </label>

              <textarea
                placeholder="Ayesha Khan, 0300-1234567, House 4B, Street 3, DHA Phase 5, Karachi. Please send 2 Blue Kurtas."
                value={selectedNode.data.message || ""}
                onChange={(event) =>
                  updateSelectedNode({
                    message: event.target.value,
                  })
                }
                style={{
                  boxSizing: "border-box",
                  width: "100%",
                  minHeight: "140px",
                  padding: "8px",
                  resize: "vertical",
                }}
              />
            </>
          )}

          {selectedNode.data.nodeType ===
            "aiExtractor" && (
            <>
              <label
                style={{
                  display: "block",
                  marginBottom: "5px",
                }}
              >
                Extraction Prompt
              </label>

              <textarea
                placeholder="Extract name, phone, address, and items. Return only JSON."
                value={selectedNode.data.prompt || ""}
                onChange={(event) =>
                  updateSelectedNode({
                    prompt: event.target.value,
                  })
                }
                style={{
                  boxSizing: "border-box",
                  width: "100%",
                  minHeight: "140px",
                  padding: "8px",
                  resize: "vertical",
                }}
              />
            </>
          )}

          {selectedNode.data.nodeType ===
            "googleSheets" && (
            <>
              <label
                style={{
                  display: "block",
                  marginBottom: "5px",
                }}
              >
                Sheet Name
              </label>

              <input
                type="text"
                placeholder="Orders"
                value={selectedNode.data.sheetName || ""}
                onChange={(event) =>
                  updateSelectedNode({
                    sheetName: event.target.value,
                  })
                }
                style={{
                  boxSizing: "border-box",
                  width: "100%",
                  padding: "8px",
                  marginBottom: "12px",
                }}
              />

              <label
                style={{
                  display: "block",
                  marginBottom: "5px",
                }}
              >
                Columns
              </label>

              <input
                type="text"
                placeholder="Name, Phone, Address, Items"
                value={selectedNode.data.columns || ""}
                onChange={(event) =>
                  updateSelectedNode({
                    columns: event.target.value,
                  })
                }
                style={{
                  boxSizing: "border-box",
                  width: "100%",
                  padding: "8px",
                }}
              />
            </>
          )}

          {selectedNode.data.nodeType ===
            "whatsappReply" && (
            <>
              <label
                style={{
                  display: "block",
                  marginBottom: "5px",
                }}
              >
                Reply Message
              </label>

              <textarea
                placeholder="Thank you {{name}}! Your order for {{items}} has been received."
                value={
                  selectedNode.data.replyMessage || ""
                }
                onChange={(event) =>
                  updateSelectedNode({
                    replyMessage: event.target.value,
                  })
                }
                style={{
                  boxSizing: "border-box",
                  width: "100%",
                  minHeight: "130px",
                  padding: "8px",
                  resize: "vertical",
                }}
              />
            </>
          )}

          <button
            onClick={() => setSelectedNodeId(null)}
            style={{
              width: "100%",
              marginTop: "16px",
              padding: "9px",
              cursor: "pointer",
            }}
          >
            Done
          </button>
        </div>
      )}
    </div>
  );
}

export default Canvas;