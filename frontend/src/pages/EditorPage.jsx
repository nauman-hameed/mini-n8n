import { useEffect, useRef, useState } from "react";
import { useNodesState } from "@xyflow/react";

import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import Canvas from "../components/Canvas";
import CredentialsPanel from "../components/CredentialsPanel";
import ExecutionOverlay from "../components/ExecutionOverlay";
import NotificationToast from "../components/NotificationToast";
import WorkflowResultPanel from "../components/WorkflowResultPanel";

import { createNode } from "../utils/nodeFactory";
import { getBackendUrl, syncWorkflow } from "../utils/api";
import { getWorkflowSteps } from "../utils/workflowSteps";

export default function EditorPage() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges] = useState([]);

  const [workflowResult, setWorkflowResult] = useState(null);
  const [executedNodes, setExecutedNodes] = useState([]);
  const [showCredentials, setShowCredentials] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [executionSteps, setExecutionSteps] = useState([]);
  const [executionState, setExecutionState] = useState({
    status: "idle",
    message: "",
  });
  const [notifications, setNotifications] = useState([]);

  const notificationTimers = useRef({});

  useEffect(() => {
    if (!isRunning || executionSteps.length === 0) {
      return undefined;
    }

    const timer = setInterval(() => {
      setCurrentStep((step) =>
        step < executionSteps.length - 1 ? step + 1 : step
      );
    }, 900);

    return () => clearInterval(timer);
  }, [isRunning, executionSteps]);

  useEffect(() => {
    return () => {
      Object.values(notificationTimers.current).forEach(clearTimeout);
    };
  }, []);

  const pushNotification = (type, title, message, autoDismissMs = 6000) => {
    const id = `${Date.now()}-${Math.random()}`;

    setNotifications((current) => [
      ...current,
      { id, type, title, message },
    ]);

    if (autoDismissMs > 0) {
      notificationTimers.current[id] = setTimeout(() => {
        dismissNotification(id);
      }, autoDismissMs);
    }

    return id;
  };

  const dismissNotification = (id) => {
    setNotifications((current) =>
      current.filter((notification) => notification.id !== id)
    );

    clearTimeout(notificationTimers.current[id]);
    delete notificationTimers.current[id];
  };

  const addNode = (nodeType) => {
    const nodeAlreadyExists = nodes.some(
      (node) => node.data.nodeType === nodeType
    );

    if (
      (nodeType === "start" ||
        nodeType === "stop" ||
        nodeType === "whatsappTrigger") &&
      nodeAlreadyExists
    ) {
      const messages = {
        start: "Start node already exists.",
        stop: "Stop node already exists.",
        whatsappTrigger: "WhatsApp Trigger node already exists.",
      };

      pushNotification("warning", "Cannot add node", messages[nodeType]);
      return;
    }

    const newId = Date.now().toString();
    const newNode = createNode(nodeType, newId);

    setNodes((currentNodes) => [...currentNodes, newNode]);
  };

  const runWorkflow = async () => {
    const validationError = validateWorkflow(nodes, edges);

    if (validationError) {
      pushNotification("error", "Workflow not ready", validationError);
      setExecutionState({ status: "error", message: "Validation failed" });
      return;
    }

    const steps = getWorkflowSteps(nodes, edges);

    setWorkflowResult(null);
    setExecutedNodes([]);
    setIsRunning(true);
    setCurrentStep(0);
    setExecutionSteps(steps);
    setExecutionState({
      status: "running",
      message: "Executing workflow…",
    });

    try {
      await syncWorkflow(nodes, edges);

      const response = await fetch(getBackendUrl("/run-workflow"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ nodes, edges }),
      });

      const data = await response.json();

      if (!response.ok) {
        setExecutionState({ status: "error", message: "Execution failed" });
        pushNotification(
          "error",
          "Workflow failed",
          data.message || "Something went wrong while running the workflow.",
          0
        );
        return;
      }

      setWorkflowResult(data.output);
      setExecutedNodes(data.executed_nodes || []);
      setExecutionState({
        status: "success",
        message: "Completed successfully",
      });

      const sheetsUpdated = data.output?.google_sheets?.updated_rows > 0;
      const whatsappSent = data.output?.whatsapp_send?.success;

      let successMessage = data.message || "All nodes ran without errors.";

      if (whatsappSent) {
        successMessage = `WhatsApp confirmation sent to ${data.output.whatsapp_send.to}.`;
      } else if (sheetsUpdated) {
        successMessage = `Order saved to Google Sheets (${data.output.google_sheets.updated_rows} row added).`;
      }

      pushNotification(
        "success",
        "Workflow executed successfully",
        successMessage
      );
    } catch (error) {
      console.error("Backend error:", error);
      setExecutionState({ status: "error", message: "Connection failed" });
      pushNotification(
        "error",
        "Backend connection failed",
        `Could not reach the server at ${getBackendUrl()}.`,
        0
      );
    } finally {
      setIsRunning(false);
      setCurrentStep(steps.length);
    }
  };

  const stopWorkflow = () => {
    setWorkflowResult(null);
    setExecutedNodes([]);
    setIsRunning(false);
    setCurrentStep(0);
    setExecutionSteps([]);
    setExecutionState({ status: "idle", message: "" });
    setNotifications([]);
  };

  return (
    <div className="editor-app">
      <Navbar
        runWorkflow={runWorkflow}
        stopWorkflow={stopWorkflow}
        openCredentials={() => setShowCredentials(true)}
        onGoHome={() => {}}
        homeTo="/"
        executionState={executionState}
      />

      <NotificationToast
        notifications={notifications}
        onDismiss={dismissNotification}
      />

      <div className="app-layout">
        <Sidebar addNode={addNode} />

        <Canvas
          nodes={nodes}
          setNodes={setNodes}
          onNodesChange={onNodesChange}
          edgesInApp={edges}
          setEdgesInApp={setEdges}
        />
      </div>

      {isRunning && (
        <ExecutionOverlay
          executedSteps={executionSteps}
          currentStep={currentStep}
        />
      )}

      {showCredentials && (
        <CredentialsPanel onClose={() => setShowCredentials(false)} />
      )}

      {workflowResult && !isRunning && (
        <WorkflowResultPanel
          result={workflowResult}
          executedNodes={executedNodes}
          onClose={() => setWorkflowResult(null)}
        />
      )}
    </div>
  );
}

function validateWorkflow(nodes, edges) {
  const hasWhatsAppTrigger = nodes.some(
    (node) => node.data.nodeType === "whatsappTrigger"
  );

  if (!hasWhatsAppTrigger) {
    return "Please add a WhatsApp Trigger node.";
  }

  if (edges.length === 0) {
    return "Please connect the nodes.";
  }

  const checks = [
    {
      find: (node) => node.data.nodeType === "api" && !node.data.apiUrl,
      message: "Please configure the API node.",
    },
    {
      find: (node) => node.data.nodeType === "llm" && !node.data.prompt,
      message: "Please configure the LLM node.",
    },
    {
      find: (node) =>
        node.data.nodeType === "condition" && !node.data.condition,
      message: "Please configure the If / Else node.",
    },
    {
      find: (node) =>
        node.data.nodeType === "whatsappTrigger" && !node.data.message,
      message: "Please configure the WhatsApp Trigger node.",
    },
    {
      find: (node) =>
        node.data.nodeType === "aiExtractor" && !node.data.prompt,
      message: "Please configure the AI Order Extractor node.",
    },
    {
      find: (node) =>
        node.data.nodeType === "googleSheets" &&
        (!node.data.sheetName || !node.data.columns),
      message: "Please configure the Google Sheets node.",
    },
    {
      find: (node) =>
        node.data.nodeType === "whatsappReply" && !node.data.replyMessage,
      message: "Please configure the WhatsApp Reply node.",
    },
  ];

  for (const check of checks) {
    if (nodes.find(check.find)) {
      return check.message;
    }
  }

  return null;
}
