import {
  Handle,
  Position,
  useReactFlow,
} from "@xyflow/react";

import "./nodeStyles.css";

function LlmNode({ id, data }) {
  const { updateNodeData } = useReactFlow();

  return (
    <div className="custom-node config-node">
      <Handle
        type="target"
        position={Position.Left}
      />

      <strong>LLM</strong>

      <label>Prompt</label>

      <textarea
        className="nodrag"
        placeholder="Enter prompt..."
        value={data.prompt || ""}
        onChange={(event) =>
          updateNodeData(id, {
            prompt: event.target.value,
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

export default LlmNode;