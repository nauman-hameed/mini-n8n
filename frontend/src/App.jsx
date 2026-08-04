import { useEffect, useState } from "react";
import { useNodesState } from "@xyflow/react";

import Navbar from "./components/Navbar";
import Sidebar from "./components/Sidebar";
import Canvas from "./components/Canvas";
import CredentialsPanel from "./components/CredentialsPanel";

import { createNode } from "./utils/nodeFactory";

const NODES_STORAGE_KEY = "mini-n8n-nodes";
const EDGES_STORAGE_KEY = "mini-n8n-edges";

const getSavedData = (key) => {
  try {
    const savedData = localStorage.getItem(key);

    return savedData ? JSON.parse(savedData) : [];
  } catch (error) {
    console.error(`Could not load ${key}:`, error);
    return [];
  }
};

function App() {
  const [nodes, setNodes, onNodesChange] = useNodesState(
    () => getSavedData(NODES_STORAGE_KEY)
  );

  const [edges, setEdges] = useState(
    () => getSavedData(EDGES_STORAGE_KEY)
  );

  const [workflowResult, setWorkflowResult] =
    useState(null);

  const [showCredentials, setShowCredentials] =
    useState(false);

  useEffect(() => {
    localStorage.setItem(
      NODES_STORAGE_KEY,
      JSON.stringify(nodes)
    );
  }, [nodes]);

  useEffect(() => {
    localStorage.setItem(
      EDGES_STORAGE_KEY,
      JSON.stringify(edges)
    );
  }, [edges]);

  const addNode = (nodeType) => {
    const nodeAlreadyExists = nodes.some(
      (node) => node.data.nodeType === nodeType
    );

    if (
      (
        nodeType === "start" ||
        nodeType === "stop" ||
        nodeType === "whatsappTrigger"
      ) &&
      nodeAlreadyExists
    ) {
      const messages = {
        start: "Start node already exists.",
        stop: "Stop node already exists.",
        whatsappTrigger:
          "WhatsApp Trigger node already exists.",
      };

      alert(messages[nodeType]);
      return;
    }

    const newId = Date.now().toString();
    const newNode = createNode(nodeType, newId);

    setNodes((currentNodes) => [
      ...currentNodes,
      newNode,
    ]);
  };

  const runWorkflow = async () => {
    const hasWhatsAppTrigger = nodes.some(
      (node) =>
        node.data.nodeType === "whatsappTrigger"
    );

    if (!hasWhatsAppTrigger) {
      alert("Please add a WhatsApp Trigger node.");
      return;
    }

    if (edges.length === 0) {
      alert("Please connect the nodes.");
      return;
    }

    const unconfiguredApiNode = nodes.find(
      (node) =>
        node.data.nodeType === "api" &&
        !node.data.apiUrl
    );

    if (unconfiguredApiNode) {
      alert("Please configure the API node.");
      return;
    }

    const unconfiguredLlmNode = nodes.find(
      (node) =>
        node.data.nodeType === "llm" &&
        !node.data.prompt
    );

    if (unconfiguredLlmNode) {
      alert("Please configure the LLM node.");
      return;
    }

    const unconfiguredConditionNode = nodes.find(
      (node) =>
        node.data.nodeType === "condition" &&
        !node.data.condition
    );

    if (unconfiguredConditionNode) {
      alert("Please configure the If / Else node.");
      return;
    }

    const unconfiguredWhatsAppTrigger = nodes.find(
      (node) =>
        node.data.nodeType === "whatsappTrigger" &&
        !node.data.message
    );

    if (unconfiguredWhatsAppTrigger) {
      alert("Please configure the WhatsApp Trigger node.");
      return;
    }

    const unconfiguredAiExtractor = nodes.find(
      (node) =>
        node.data.nodeType === "aiExtractor" &&
        !node.data.prompt
    );

    if (unconfiguredAiExtractor) {
      alert("Please configure the AI Order Extractor node.");
      return;
    }

    const unconfiguredGoogleSheets = nodes.find(
      (node) =>
        node.data.nodeType === "googleSheets" &&
        (
          !node.data.sheetName ||
          !node.data.columns
        )
    );

    if (unconfiguredGoogleSheets) {
      alert("Please configure the Google Sheets node.");
      return;
    }

    const unconfiguredWhatsAppReply = nodes.find(
      (node) =>
        node.data.nodeType === "whatsappReply" &&
        !node.data.replyMessage
    );

    if (unconfiguredWhatsAppReply) {
      alert("Please configure the WhatsApp Reply node.");
      return;
    }

    try {
      setWorkflowResult(null);

      const response = await fetch(
        `${import.meta.env.VITE_BACKEND_URL}/run-workflow`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            nodes,
            edges,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        alert(data.message || "Workflow failed.");
        return;
      }

      setWorkflowResult(data.output);
    } catch (error) {
      console.error("Backend error:", error);
      alert("Backend connection failed.");
    }
  };

  const stopWorkflow = () => {
    setWorkflowResult(null);
    alert("Workflow stopped.");
  };

  return (
    <>
      <Navbar
        runWorkflow={runWorkflow}
        stopWorkflow={stopWorkflow}
        openCredentials={() =>
          setShowCredentials(true)
        }
      />

      <div
        style={{
          display: "flex",
          width: "100%",
          height: "calc(100vh - 60px)",
        }}
      >
        <Sidebar addNode={addNode} />

        <Canvas
          nodes={nodes}
          setNodes={setNodes}
          onNodesChange={onNodesChange}
          edgesInApp={edges}
          setEdgesInApp={setEdges}
        />
      </div>

      {showCredentials && (
        <CredentialsPanel
          onClose={() =>
            setShowCredentials(false)
          }
        />
      )}

      {workflowResult && (
        <div
          style={{
            position: "fixed",
            right: "20px",
            bottom: "20px",
            width: "340px",
            backgroundColor: "white",
            color: "#222",
            padding: "18px",
            borderRadius: "8px",
            boxShadow:
              "0 4px 20px rgba(0,0,0,0.35)",
            zIndex: 20,
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "12px",
            }}
          >
            <h3 style={{ margin: 0 }}>
              Workflow Result
            </h3>

            <button
              onClick={() =>
                setWorkflowResult(null)
              }
              style={{
                cursor: "pointer",
                padding: "4px 8px",
              }}
            >
              ✕
            </button>
          </div>

          <p>
            <strong>Name:</strong>{" "}
            {workflowResult.name || "-"}
          </p>

          <p>
            <strong>Phone:</strong>{" "}
            {workflowResult.phone || "-"}
          </p>

          <p>
            <strong>Address:</strong>{" "}
            {workflowResult.address || "-"}
          </p>

          <p>
            <strong>Items:</strong>{" "}
            {workflowResult.items || "-"}
          </p>

          <hr style={{ margin: "12px 0" }} />

          <p>
            <strong>WhatsApp Reply:</strong>
          </p>

          <p>
            {workflowResult.reply_message ||
              "No reply generated."}
          </p>
        </div>
      )}
    </>
  );
}

export default App;