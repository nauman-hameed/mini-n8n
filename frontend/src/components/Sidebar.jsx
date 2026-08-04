import { useMemo, useState } from "react";
import { NODE_CONFIG, SIDEBAR_CATEGORIES } from "../utils/nodeConfig";

function Sidebar({ addNode }) {
  const [search, setSearch] = useState("");

  const filteredCategories = useMemo(() => {
    const query = search.trim().toLowerCase();

    if (!query) {
      return SIDEBAR_CATEGORIES;
    }

    return SIDEBAR_CATEGORIES.map((category) => ({
      ...category,
      types: category.types.filter((type) => {
        const config = NODE_CONFIG[type];
        return (
          type.toLowerCase().includes(query) ||
          config.category.toLowerCase().includes(query) ||
          getLabel(type).toLowerCase().includes(query) ||
          config.description.toLowerCase().includes(query)
        );
      }),
    })).filter((category) => category.types.length > 0);
  }, [search]);

  const hasResults = filteredCategories.some(
    (category) => category.types.length > 0
  );

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <p className="sidebar-title">Node Panel</p>
        <div className="sidebar-search-wrap">
          <span className="sidebar-search-icon" aria-hidden="true">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.3-4.3" />
            </svg>
          </span>
          <input
            type="text"
            className="sidebar-search"
            placeholder="Search nodes…"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            aria-label="Search nodes"
          />
        </div>
      </div>

      <div className="sidebar-body">
        {!hasResults && (
          <p className="sidebar-empty">
            {search.trim()
              ? "No nodes match your search."
              : "Browse nodes by category below, or search to filter."}
          </p>
        )}

        {filteredCategories.map((category) =>
          category.types.length > 0 ? (
            <div key={category.label} className="sidebar-category">
              <p className="sidebar-category-label">{category.label}</p>
              {category.types.map((type) => {
                const config = NODE_CONFIG[type];
                return (
                  <button
                    key={type}
                    type="button"
                    className="node-card"
                    onClick={() => addNode(type)}
                  >
                    <span
                      className="node-card-icon"
                      style={{
                        background: `color-mix(in srgb, ${config.color} 20%, transparent)`,
                      }}
                    >
                      {config.icon}
                    </span>
                    <span className="node-card-info">
                      <span className="node-card-name">{getLabel(type)}</span>
                      <span className="node-card-desc">{config.description}</span>
                    </span>
                  </button>
                );
              })}
            </div>
          ) : null
        )}
      </div>
    </aside>
  );
}

function getLabel(type) {
  const labels = {
    start: "Start",
    whatsappTrigger: "WhatsApp Trigger",
    api: "HTTP Request",
    googleSheets: "Google Sheets",
    llm: "LLM",
    aiExtractor: "AI Order Extractor",
    condition: "If / Else",
    whatsappReply: "WhatsApp Reply",
    stop: "Stop",
  };
  return labels[type] || type;
}

export default Sidebar;
