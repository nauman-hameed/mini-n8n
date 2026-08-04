import { Handle, Position } from "@xyflow/react";
import "./nodeStyles.css";

function StartNode() {
  return (
    <div className="custom-node">
      <strong>Start</strong>

      <Handle
        type="source"
        position={Position.Right}
      />
    </div>
  );
}

export default StartNode;