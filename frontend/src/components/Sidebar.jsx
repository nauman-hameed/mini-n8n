import { useState } from "react";

function Sidebar({ addNode }) {
  const [search, setSearch] = useState("");

  const availableNodes = [
    {
      type: "start",
      label: "Start",
      category: "Trigger",
    },
    {
      type: "whatsappTrigger",
      label: "WhatsApp Trigger",
      category: "Trigger",
    },
    {
      type: "api",
      label: "API",
      category: "Action",
    },
    {
      type: "googleSheets",
      label: "Google Sheets",
      category: "Data",
    },
    {
      type: "llm",
      label: "LLM",
      category: "AI",
    },
    {
      type: "aiExtractor",
      label: "AI Order Extractor",
      category: "AI",
    },
    {
      type: "condition",
      label: "If / Else",
      category: "Logic",
    },
    {
      type: "whatsappReply",
      label: "WhatsApp Reply",
      category: "Communication",
    },
    {
      type: "stop",
      label: "Stop",
      category: "Action",
    },
  ];

  const filteredNodes =
    search.trim() === ""
      ? []
      : availableNodes.filter((node) =>
          node.label.toLowerCase().includes(search.toLowerCase())
        );

  const handleNodeClick = (nodeType) => {
    addNode(nodeType);
    setSearch("");
  };

  return (
    <div
      style={{
        width: "240px",
        background: "#f3f4f6",
        padding: "20px",
        borderRight: "1px solid #ccc",
        overflowY: "auto",
      }}
    >
      <h2
        style={{
          textAlign: "center",
          marginBottom: "20px",
          fontSize: "20px",
        }}
      >
        Nodes
      </h2>

      <div
        style={{
          position: "relative",
          marginBottom: "15px",
        }}
      >
        <span
          style={{
            position: "absolute",
            left: "12px",
            top: "50%",
            transform: "translateY(-50%)",
            color: "#777",
            fontSize: "14px",
            pointerEvents: "none",
          }}
        >
          🔍
        </span>

        <input
          type="text"
          placeholder="Search nodes..."
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          style={{
            width: "100%",
            boxSizing: "border-box",
            padding: "10px 10px 10px 36px",
            borderRadius: "6px",
            border: "1px solid #bbb",
            fontSize: "14px",
            outline: "none",
          }}
        />
      </div>

      {search.trim() !== "" && filteredNodes.length === 0 && (
        <p
          style={{
            textAlign: "center",
            color: "#666",
            fontSize: "13px",
          }}
        >
          No node found
        </p>
      )}

      {filteredNodes.map((node) => (
        <button
          key={node.type}
          onClick={() => handleNodeClick(node.type)}
          style={{
            width: "100%",
            padding: "10px",
            marginBottom: "10px",
            borderRadius: "6px",
            border: "1px solid #ccc",
            background: "white",
            cursor: "pointer",
            transition: "0.2s",
          }}
          onMouseEnter={(event) => {
            event.currentTarget.style.background = "#e5e7eb";
          }}
          onMouseLeave={(event) => {
            event.currentTarget.style.background = "white";
          }}
        >
          <div
            style={{
              textAlign: "left",
            }}
          >
            <div
              style={{
                fontWeight: "bold",
                marginBottom: "3px",
                fontSize: "14px",
              }}
            >
              {node.label}
            </div>

            <div
              style={{
                fontSize: "11px",
                color: "#666",
              }}
            >
              {node.category}
            </div>
          </div>
        </button>
      ))}
    </div>
  );
}

export default Sidebar;