import { Handle, Position } from "@xyflow/react";
import "./nodeStyles.css";

function StopNode() {
  return (
    <div className="custom-node">
      <Handle
        type="target"
        position={Position.Left}
      />

      <strong>Stop</strong>
    </div>
  );
}

export default StopNode;