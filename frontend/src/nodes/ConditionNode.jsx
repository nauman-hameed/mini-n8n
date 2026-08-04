import {
  Handle,
  Position,
  useReactFlow,
} from "@xyflow/react";

import "./nodeStyles.css";

function ConditionNode({ id, data }) {
  const { updateNodeData } = useReactFlow();

  return (
    <div className="custom-node config-node">
      <Handle
        type="target"
        position={Position.Left}
      />

      <strong>If / Else</strong>

      <label>Condition</label>

      <input
        className="nodrag"
        type="text"
        placeholder="status == 200"
        value={data.condition || ""}
        onChange={(event) =>
          updateNodeData(id, {
            condition: event.target.value,
          })
        }
      />

      <div className="branch-label true-label">
        True
      </div>

      <Handle
        id="true"
        type="source"
        position={Position.Right}
        style={{ top: "65%" }}
      />

      <div className="branch-label false-label">
        False
      </div>

      <Handle
        id="false"
        type="source"
        position={Position.Right}
        style={{ top: "85%" }}
      />
    </div>
  );
}

export default ConditionNode;