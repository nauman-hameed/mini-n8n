import { Position } from "@xyflow/react";

export const initialNodes = [
  {
    id: "1",
    type: "default",
    position: { x: 100, y: 100 },
    data: { label: "Start", nodeType: "start" },
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
  },
  {
    id: "2",
    type: "default",
    position: { x: 300, y: 100 },
    data: { label: "API", nodeType: "api" },
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
  },
  {
    id: "3",
    type: "default",
    position: { x: 500, y: 100 },
    data: { label: "LLM", nodeType: "llm" },
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
  },
  {
    id: "4",
    type: "default",
    position: { x: 300, y: 250 },
    data: { label: "If / Else", nodeType: "condition" },
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
  },
  {
    id: "5",
    type: "default",
    position: { x: 500, y: 250 },
    data: { label: "Stop", nodeType: "stop" },
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
  },
];