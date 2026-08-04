import {
  Handle,
  Position,
  useReactFlow,
} from "@xyflow/react";

import "./nodeStyles.css";

function ApiNode({ id, data }) {
  const { updateNodeData } = useReactFlow();

  return (
    <div className="custom-node config-node">
      <Handle
        type="target"
        position={Position.Left}
      />

      <strong>API</strong>

      <label>Method</label>

      <select
        className="nodrag"
        value={data.method || "GET"}
        onChange={(event) =>
          updateNodeData(id, {
            method: event.target.value,
          })
        }
      >
        <option value="GET">GET</option>
        <option value="POST">POST</option>
      </select>

      <label>API URL</label>

      <input
        className="nodrag"
        type="text"
        placeholder="https://api.example.com"
        value={data.apiUrl || ""}
        onChange={(event) =>
          updateNodeData(id, {
            apiUrl: event.target.value,
          })
        }
      />

      <Handle
        type="source"
        position={Position.Right}
      />
    </div>
  );
}

export default ApiNode;