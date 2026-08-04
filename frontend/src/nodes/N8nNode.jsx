import { Handle, Position } from "@xyflow/react";
import { getNodeConfig } from "../utils/nodeConfig";

function N8nNode({ data, selected }) {
  const config = getNodeConfig(data.nodeType);

  return (
    <div
      className={`n8n-node${selected ? " selected" : ""}`}
      style={{ "--node-accent": config.color }}
    >
      {data.nodeType !== "start" && data.nodeType !== "whatsappTrigger" && (
        <Handle type="target" position={Position.Left} />
      )}

      <div className="n8n-node-icon">{config.icon}</div>

      <div className="n8n-node-body">
        <span className="n8n-node-label">{data.label}</span>
        <span className="n8n-node-type">{config.category}</span>
      </div>

      {data.nodeType !== "stop" && data.nodeType !== "whatsappReply" && (
        <Handle type="source" position={Position.Right} />
      )}
    </div>
  );
}

export default N8nNode;
