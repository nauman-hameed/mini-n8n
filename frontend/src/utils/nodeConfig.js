export const NODE_CONFIG = {
  start: {
    icon: "▶",
    category: "Trigger",
    color: "#59a82d",
    description: "Begin workflow execution",
  },
  whatsappTrigger: {
    icon: "💬",
    category: "Trigger",
    color: "#25d366",
    description: "Incoming WhatsApp message",
  },
  api: {
    icon: "🌐",
    category: "Action",
    color: "#5296d5",
    description: "HTTP GET or POST request",
  },
  googleSheets: {
    icon: "📊",
    category: "Data",
    color: "#34a853",
    description: "Append row to spreadsheet",
  },
  llm: {
    icon: "🤖",
    category: "AI",
    color: "#ea4b71",
    description: "Run LLM prompt",
  },
  aiExtractor: {
    icon: "✨",
    category: "AI",
    color: "#c084fc",
    description: "Extract order from message",
  },
  condition: {
    icon: "⑂",
    category: "Logic",
    color: "#f59e0b",
    description: "Branch on condition",
  },
  whatsappReply: {
    icon: "📤",
    category: "Communication",
    color: "#25d366",
    description: "Send WhatsApp reply",
  },
  stop: {
    icon: "⏹",
    category: "Action",
    color: "#ef4444",
    description: "End workflow execution",
  },
};

export const SIDEBAR_CATEGORIES = [
  {
    label: "Triggers",
    types: ["start", "whatsappTrigger"],
  },
  {
    label: "Actions",
    types: ["api", "stop"],
  },
  {
    label: "Data",
    types: ["googleSheets"],
  },
  {
    label: "AI",
    types: ["llm", "aiExtractor"],
  },
  {
    label: "Logic",
    types: ["condition"],
  },
  {
    label: "Communication",
    types: ["whatsappReply"],
  },
];

export function getNodeConfig(nodeType) {
  return (
    NODE_CONFIG[nodeType] || {
      icon: "⚙",
      category: "Node",
      color: "#ff6d5a",
      description: "Workflow node",
    }
  );
}
