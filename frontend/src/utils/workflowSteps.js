export function getWorkflowSteps(nodes, edges) {
  if (nodes.length === 0) {
    return [];
  }

  const nodeMap = Object.fromEntries(
    nodes.map((node) => [node.id, node])
  );

  const startNode = nodes.find((node) =>
    ["start", "whatsappTrigger"].includes(node.data?.nodeType)
  );

  if (!startNode) {
    return nodes.map((node) => node.data.nodeType);
  }

  const steps = [];
  let currentNode = startNode;
  const visited = new Set();

  while (currentNode && !visited.has(currentNode.id)) {
    visited.add(currentNode.id);
    steps.push(currentNode.data.nodeType);

    const nextEdge = edges.find(
      (edge) => edge.source === currentNode.id
    );

    if (!nextEdge) {
      break;
    }

    currentNode = nodeMap[nextEdge.target];
  }

  return steps;
}
