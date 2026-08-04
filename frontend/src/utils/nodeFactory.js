export function createNode(nodeType, id) {
  const labels = {
    start: "Start",
    api: "API",
    llm: "LLM",
    condition: "If / Else",
    stop: "Stop",

    whatsappTrigger: "WhatsApp Trigger",
    aiExtractor: "AI Order Extractor",
    googleSheets: "Google Sheets",
    whatsappReply: "WhatsApp Reply",
  };

  return {
    id: id.toString(),
    type: "n8nNode",

    position: {
      x: 200 + Math.random() * 300,
      y: 100 + Math.random() * 300,
    },

    data: {
      label: labels[nodeType] || "Node",
      nodeType,
    },
  };
}