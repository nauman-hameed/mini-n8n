function Navbar({
  runWorkflow,
  stopWorkflow,
  openCredentials,
}) {
  return (
    <div
      style={{
        height: "60px",
        backgroundColor: "#1f2937",
        color: "white",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 20px",
      }}
    >
      <h2 style={{ margin: 0 }}>
        Mini n8n Workflow Builder
      </h2>

      <div>
        <button
          onClick={openCredentials}
          style={{ marginRight: "10px" }}
        >
          Credentials
        </button>

        <button
          onClick={runWorkflow}
          style={{ marginRight: "10px" }}
        >
          Run Workflow
        </button>

        <button onClick={stopWorkflow}>
          Stop Workflow
        </button>
      </div>
    </div>
  );
}

export default Navbar;